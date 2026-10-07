from datetime import timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.types import utcnow
from app.models.auth import LoginAttempt


def normalize_username(username: str) -> str:
    return username.strip().lower()[:64]


def _failures(db: Session, column, value: str) -> int:
    cutoff = utcnow() - timedelta(minutes=get_settings().login_window_minutes)
    return (
        db.scalar(
            select(func.count())
            .select_from(LoginAttempt)
            .where(column == value, LoginAttempt.succeeded.is_(False), LoginAttempt.created_at > cutoff)
        )
        or 0
    )


def is_blocked(db: Session, username: str, ip: str) -> bool:
    s = get_settings()
    return (
        _failures(db, LoginAttempt.username, username) >= s.login_max_failures_per_user
        or _failures(db, LoginAttempt.ip, ip) >= s.login_max_failures_per_ip
    )


def record_attempt(db: Session, username: str, ip: str, succeeded: bool) -> None:
    db.add(LoginAttempt(username=username, ip=ip[:45], succeeded=succeeded))
    db.commit()


def purge_old(db: Session) -> None:
    db.execute(delete(LoginAttempt).where(LoginAttempt.created_at < utcnow() - timedelta(days=1)))
    db.commit()
