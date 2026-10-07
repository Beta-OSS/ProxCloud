from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.core.dependencies import AuthCtx, DbSession, client_ip, csrf_authed
from app.core.security import verify_password
from app.core.templating import render
from app.models.user import User
from app.schemas.user import MeRead, UserRead, validate_new_password
from app.services.auth import rate_limit, recovery, totp
from app.services.users import change_password

router = APIRouter()
api_router = APIRouter(prefix="/api")

FLASH = {
    "password_changed": "Password updated. Your other sessions were signed out.",
    "2fa_disabled": "Two-factor authentication has been disabled.",
}


@api_router.get("/me", response_model=MeRead)
def me(ctx: AuthCtx) -> MeRead:
    return MeRead(**UserRead.model_validate(ctx.user).model_dump(), csrf_token=ctx.session.csrf_token)


@router.get("/dashboard")
def dashboard(request: Request, db: DbSession, ctx: AuthCtx):
    return render(request, "dashboard.html", user=ctx.user, csrf_token=ctx.session.csrf_token)


def _reauth(db, request: Request, user: User, password: str, code: str | None = None) -> str | None:
    """Re-verifies password (and optionally a TOTP code) for sensitive actions. Rate limited."""
    ip = client_ip(request)
    if rate_limit.is_blocked(db, user.username, ip):
        return "Too many failed attempts. Please try again later."
    ok = len(password) <= 1024 and verify_password(user.password_hash, password)
    if ok and code is not None:
        ok = totp.verify_totp(user, code.strip().replace(" ", ""))
    if not ok:
        db.rollback()
        rate_limit.record_attempt(db, user.username, ip, False)
        return "Incorrect password or code."
    return None
