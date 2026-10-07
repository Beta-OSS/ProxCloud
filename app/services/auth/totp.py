import base64
import io
import time

import pyotp
import qrcode
import qrcode.image.svg
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ct_eq, decrypt_secret, encrypt_secret
from app.models.user import User
from app.services.auth import recovery

STEP = 30


def begin_setup(db: Session, user: User) -> str:
    """Stores a fresh (encrypted) secret; 2FA stays disabled until a code is confirmed."""
    secret = pyotp.random_base32()
    user.totp_secret = encrypt_secret(secret)
    user.totp_enabled = False
    user.totp_last_used_step = None
    db.commit()
    return secret


def current_secret(user: User) -> str | None:
    return decrypt_secret(user.totp_secret) if user.totp_secret else None


def setup_context(user: User, secret: str) -> dict[str, str]:
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.username, issuer_name=get_settings().totp_issuer)
    img = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    qr = "data:image/svg+xml;base64," + base64.b64encode(buf.getvalue()).decode()
    return {"secret": secret, "uri": uri, "qr": qr}


def verify_totp(user: User, code: str, now: float | None = None) -> bool:
    """Accepts +/-1 step of clock drift. Rejects any step <= the last accepted one (replay).

    Mutates user.totp_last_used_step on success; the caller commits.
    """
    if not user.totp_secret or len(code) != 6 or not code.isdigit():
        return False
    totp = pyotp.TOTP(decrypt_secret(user.totp_secret))
    current_step = int((now if now is not None else time.time()) // STEP)
    for step in (current_step - 1, current_step, current_step + 1):
        if ct_eq(totp.at(step * STEP), code):
            if user.totp_last_used_step is not None and step <= user.totp_last_used_step:
                return False
            user.totp_last_used_step = step
            return True
    return False


def enable(db: Session, user: User, code: str) -> list[str] | None:
    """Confirms the pending secret with a code. Returns recovery codes on success."""
    if not verify_totp(user, code):
        db.rollback()
        return None
    user.totp_enabled = True
    db.commit()
    return recovery.regenerate(db, user)


def disable(db: Session, user: User) -> None:
    user.totp_enabled = False
    user.totp_secret = None
    user.totp_last_used_step = None
    recovery.delete_all(db, user.id)
    db.commit()
