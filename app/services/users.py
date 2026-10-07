import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth.sessions import destroy_user_sessions


class UserExists(Exception):
    pass


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        is_admin=data.is_admin,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UserExists from None
    return user


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at, User.username)))


def user_counts(db: Session) -> dict[str, int]:
    total = db.scalar(select(func.count()).select_from(User)) or 0
    active = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
    admins = db.scalar(select(func.count()).select_from(User).where(User.is_admin.is_(True))) or 0
    return {"total": total, "active": active, "admins": admins}


def set_active(db: Session, user: User, active: bool) -> None:
    user.is_active = active
    db.commit()
    if not active:
        destroy_user_sessions(db, user.id)  # takes effect immediately


def change_password(db: Session, user: User, new_password: str, keep_session_id: uuid.UUID | None = None) -> None:
    user.password_hash = hash_password(new_password)
    db.commit()
    destroy_user_sessions(db, user.id, keep_session_id=keep_session_id)
