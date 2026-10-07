import secrets

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.core.security import keyed_hash
from app.db.types import utcnow
from app.models.auth import RecoveryCode
from app.models.user import User

ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"  # no 0/1/i/l/o
CODE_COUNT = 10


def _normalize(code: str) -> str:
    return code.strip().lower().replace("-", "").replace(" ", "")


def _digest(code: str) -> str:
    return keyed_hash(_normalize(code), "recovery-code")


def _generate_one() -> str:
    raw = "".join(secrets.choice(ALPHABET) for _ in range(10))
    return f"{raw[:5]}-{raw[5:]}"


def regenerate(db: Session, user: User) -> list[str]:
    """Replaces all codes. Plaintext is returned once and never stored (only keyed hashes)."""
    codes: set[str] = set()
    while len(codes) < CODE_COUNT:
        codes.add(_generate_one())
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
    db.add_all(RecoveryCode(user_id=user.id, code_hash=_digest(c)) for c in codes)
    db.commit()
    return sorted(codes)


def consume(db: Session, user_id, code: str) -> bool:
    """Single-use. The UPDATE is atomic, so a code cannot be redeemed twice concurrently."""
    if len(_normalize(code)) != 10:
        return False
    result = db.execute(
        update(RecoveryCode)
        .where(
            RecoveryCode.user_id == user_id,
            RecoveryCode.code_hash == _digest(code),
            RecoveryCode.used_at.is_(None),
        )
        .values(used_at=utcnow())
    )
    db.commit()
    return result.rowcount == 1


def remaining(db: Session, user_id) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(RecoveryCode)
            .where(RecoveryCode.user_id == user_id, RecoveryCode.used_at.is_(None))
        )
        or 0
    )


def delete_all(db: Session, user_id) -> None:
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user_id))
