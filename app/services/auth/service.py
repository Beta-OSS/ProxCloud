import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import dummy_hash, hash_password, password_needs_rehash, verify_password
from app.models.user import User
from app.services.auth import rate_limit, recovery, totp

MAX_LOGIN_PASSWORD_LENGTH = 1024
_TOTP_RE = re.compile(r"\d{6}")


class RateLimited(Exception):
    pass


def authenticate(db: Session, username: str, password: str, ip: str) -> User | None:
    """Returns the user on success. None for ANY failure (unknown user, bad password, inactive)."""
    uname = rate_limit.normalize_username(username)
    if rate_limit.is_blocked(db, uname, ip):
        raise RateLimited

    user = db.scalar(select(User).where(User.username == uname)) if uname else None
    if len(password) > MAX_LOGIN_PASSWORD_LENGTH:
        verified = False
    else:
        # Always run a verification so response time doesn't reveal whether the user exists.
        verified = verify_password(user.password_hash if user else dummy_hash(), password)

    if user is None or not verified or not user.is_active:
        if user is not None and not user.is_active:
            return "inactive"
        rate_limit.record_attempt(db, uname, ip, False)
        return None

    rate_limit.record_attempt(db, uname, ip, True)
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
    return user


def verify_second_factor(db: Session, user: User, code: str) -> bool:
    """Accepts a 6-digit TOTP code or a single-use recovery code."""
    code = code.strip()[:64]
    digits = code.replace(" ", "")
    if _TOTP_RE.fullmatch(digits):
        ok = totp.verify_totp(user, digits)
    else:
        ok = recovery.consume(db, user.id, code)
    if ok:
        db.commit()
    else:
        db.rollback()
    return ok
