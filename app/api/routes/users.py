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


from app.services.user_vms import list_user_vms


@router.get("/dashboard")
def dashboard(
    request: Request,
    db: DbSession,
    ctx: AuthCtx,
):
    user_vms = list_user_vms(
        db,
        user_id=ctx.user.id,
    )

    return render(
        request,
        "user_actions/dashboard.html",
        user=ctx.user,
        csrf_token=ctx.session.csrf_token,
        user_vms=user_vms,
    )


def _settings(request: Request, db, ctx, *, message=None, errors=None, setup=None, codes=None, status_code=200):
    remaining = recovery.remaining(db, ctx.user.id) if ctx.user.totp_enabled else 0
    return render(
        request,
        "user_actions/settings.html",
        user=ctx.user,
        csrf_token=ctx.session.csrf_token,
        message=message,
        errors=errors or [],
        setup=setup,
        recovery_codes=codes,
        remaining=remaining,
        status_code=status_code,
    )


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


@router.get("/settings")
def settings_page(request: Request, db: DbSession, ctx: AuthCtx, msg: str | None = None):
    return _settings(request, db, ctx, message=FLASH.get(msg or ""))


@router.post("/settings/password", dependencies=[Depends(csrf_authed)])
def password_change(
    request: Request,
    db: DbSession,
    ctx: AuthCtx,
    current_password: Annotated[str, Form()] = "",
    new_password: Annotated[str, Form()] = "",
):
    error = _reauth(db, request, ctx.user, current_password) or validate_new_password(
        new_password, ctx.user.username
    )
    if error:
        return _settings(request, db, ctx, errors=[error], status_code=400)
    change_password(db, ctx.user, new_password, keep_session_id=ctx.session.id)
    return RedirectResponse("/settings?msg=password_changed", status_code=303)


@router.post("/settings/2fa/setup", dependencies=[Depends(csrf_authed)])
def twofa_setup(request: Request, db: DbSession, ctx: AuthCtx):
    if ctx.user.totp_enabled:
        return _settings(request, db, ctx, errors=["Two-factor authentication is already enabled."], status_code=400)
    secret = totp.begin_setup(db, ctx.user)
    return _settings(request, db, ctx, setup=totp.setup_context(ctx.user, secret))


@router.post("/settings/2fa/enable", dependencies=[Depends(csrf_authed)])
def twofa_enable(request: Request, db: DbSession, ctx: AuthCtx, code: Annotated[str, Form()] = ""):
    user = ctx.user
    if user.totp_enabled or not user.totp_secret:
        return _settings(request, db, ctx, errors=["Start 2FA setup first."], status_code=400)
    codes = totp.enable(db, user, code.strip().replace(" ", ""))
    if codes is None:
        secret = totp.current_secret(user)
        return _settings(
            request, db, ctx, setup=totp.setup_context(user, secret), errors=["That code is not valid."], status_code=400
        )
    return _settings(request, db, ctx, codes=codes, message="Two-factor authentication is enabled.")


@router.post("/settings/2fa/disable", dependencies=[Depends(csrf_authed)])
def twofa_disable(
    request: Request,
    db: DbSession,
    ctx: AuthCtx,
    password: Annotated[str, Form()] = "",
    code: Annotated[str, Form()] = "",
):
    if not ctx.user.totp_enabled:
        return _settings(request, db, ctx, errors=["Two-factor authentication is not enabled."], status_code=400)
    error = _reauth(db, request, ctx.user, password, code)
    if error:
        return _settings(request, db, ctx, errors=[error], status_code=400)
    totp.disable(db, ctx.user)
    return RedirectResponse("/settings?msg=2fa_disabled", status_code=303)


@router.post("/settings/2fa/recovery-codes", dependencies=[Depends(csrf_authed)])
def recovery_regenerate(
    request: Request,
    db: DbSession,
    ctx: AuthCtx,
    password: Annotated[str, Form()] = "",
    code: Annotated[str, Form()] = "",
):
    if not ctx.user.totp_enabled:
        return _settings(request, db, ctx, errors=["Two-factor authentication is not enabled."], status_code=400)
    error = _reauth(db, request, ctx.user, password, code)
    if error:
        return _settings(request, db, ctx, errors=[error], status_code=400)
    db.commit()  # persists the consumed TOTP step
    codes = recovery.regenerate(db, ctx.user)
    return _settings(request, db, ctx, codes=codes, message="New recovery codes generated. Old codes no longer work.")
