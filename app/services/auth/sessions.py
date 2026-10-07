import uuid
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_token, new_token
from app.db.types import utcnow
from app.models.auth import STAGE_ACTIVE, STAGE_PENDING_2FA, UserSession
from app.models.user import User


def create_session(
    db: Session, user: User, stage: str, ip: str, user_agent: str | None
) -> tuple[str, UserSession]:
    """Returns (raw_token, row). Only the hash of the token is stored."""
    s = get_settings()
    now = utcnow()
    lifetime = (
        timedelta(minutes=s.pending_2fa_minutes)
        if stage == STAGE_PENDING_2FA
        else timedelta(hours=s.session_max_hours)
    )
    token = new_token()
    row = UserSession(
        token_hash=hash_token(token),
        user_id=user.id,
        stage=stage,
        csrf_token=new_token(),
        created_at=now,
        last_seen_at=now,
        expires_at=now + lifetime,
        failed_attempts=0,
        ip=ip[:45],
        user_agent=(user_agent or "")[:255],
    )
    db.add(row)
    db.commit()
    return token, row


def resolve_session(db: Session, token: str, stage: str) -> tuple[UserSession, User] | None:
    """Validates expiry, idle timeout, account state and stage. Returns None if anything is off."""
    s = get_settings()
    row = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if row is None:
        return None
    now = utcnow()
    idle = timedelta(minutes=s.session_idle_minutes)
    if row.expires_at <= now or (row.stage == STAGE_ACTIVE and now - row.last_seen_at > idle):
        db.delete(row)
        db.commit()
        return None
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        db.delete(row)
        db.commit()
        return None
    if row.stage != stage:
        return None
    if now - row.last_seen_at > timedelta(seconds=60):
        row.last_seen_at = now
        db.commit()
    return row, user


def destroy_session(db: Session, token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == hash_token(token)))
    db.commit()


def destroy_user_sessions(db: Session, user_id: uuid.UUID, keep_session_id: uuid.UUID | None = None) -> None:
    stmt = delete(UserSession).where(UserSession.user_id == user_id)
    if keep_session_id is not None:
        stmt = stmt.where(UserSession.id != keep_session_id)
    db.execute(stmt)
    db.commit()


def purge_expired(db: Session) -> None:
    db.execute(delete(UserSession).where(UserSession.expires_at < utcnow()))
    db.commit()
