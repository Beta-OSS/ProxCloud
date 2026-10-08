from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, Response

from app.core.config import get_settings
from app.core.dependencies import (
    ANON_CSRF_COOKIE,
    DbSession,
    PendingCtx,
    client_ip,
    csrf_anon,
    csrf_authed,
    csrf_pending,
)
from app.core.security import new_anon_csrf
from app.core.templating import render
from app.models.auth import STAGE_ACTIVE, STAGE_PENDING_2FA
from app.services.auth import rate_limit
from app.services.auth.service import RateLimited, authenticate, verify_second_factor
from app.services.auth.sessions import create_session, destroy_session, purge_expired

router = APIRouter()


def _set_session_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        s.session_cookie_name, token, httponly=True, secure=s.cookie_secure, samesite="lax", path="/"
    )


def _login_page(request: Request, *, error: str | None = None, status_code: int = 200, username: str = ""):
    s = get_settings()
    form_token, cookie_value = new_anon_csrf()
    response = render(
        request, "login/login.html", csrf_token=form_token, error=error, username=username, status_code=status_code
    )
    response.set_cookie(
        ANON_CSRF_COOKIE, cookie_value, httponly=True, secure=s.cookie_secure, samesite="lax", path="/", max_age=3600
    )
    return response


@router.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/login")
def login_page(request: Request):
    return _login_page(request)


@router.post("/login", dependencies=[Depends(csrf_anon)])
def login_submit(
    request: Request,
    db: DbSession,
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
):
    s = get_settings()
    ip = client_ip(request)
    try:
        user = authenticate(db, username, password, ip)
        print(user)
    except RateLimited:
        return _login_page(request, error="Too many failed attempts. Please try again later.", status_code=429)
    if user is "inactive":
        return _login_page(request, error="This account is currently inactive. Please contact an admin..", status_code=401, username=username[:64])
    if user is None:
        return _login_page(request, error="Invalid username or password.", status_code=401, username=username[:64])

    # Never reuse a pre-existing session id: drop any old one, issue a brand-new token.
    old = request.cookies.get(s.session_cookie_name)
    if old:
        destroy_session(db, old)
    purge_expired(db)
    rate_limit.purge_old(db)

    stage = STAGE_PENDING_2FA if user.totp_enabled else STAGE_ACTIVE
    token, _ = create_session(db, user, stage, ip, request.headers.get("user-agent"))
    response = RedirectResponse("/2fa" if user.totp_enabled else "/dashboard", status_code=303)
    _set_session_cookie(response, token)
    return response


@router.get("/2fa")
def twofa_page(request: Request, ctx: PendingCtx):
    return render(request, "login/twofa.html", csrf_token=ctx.session.csrf_token)


@router.post("/2fa", dependencies=[Depends(csrf_pending)])
def twofa_submit(request: Request, db: DbSession, ctx: PendingCtx, code: Annotated[str, Form()] = ""):
    s = get_settings()
    ip = client_ip(request)
    if rate_limit.is_blocked(db, ctx.user.username, ip):
        destroy_session(db, request.cookies[s.session_cookie_name])
        return _login_page(request, error="Too many failed attempts. Please try again later.", status_code=429)

    if verify_second_factor(db, ctx.user, code):
        destroy_session(db, request.cookies[s.session_cookie_name])
        token, _ = create_session(db, ctx.user, STAGE_ACTIVE, ip, request.headers.get("user-agent"))
        response = RedirectResponse("/dashboard", status_code=303)
        _set_session_cookie(response, token)
        return response

    rate_limit.record_attempt(db, ctx.user.username, ip, False)
    ctx.session.failed_attempts += 1
    db.commit()
    if ctx.session.failed_attempts >= s.twofa_max_attempts:
        destroy_session(db, request.cookies[s.session_cookie_name])
        return _login_page(request, error="Too many incorrect codes. Please sign in again.", status_code=401)
    return render(
        request, "login/twofa.html", csrf_token=ctx.session.csrf_token, error="Invalid code.", status_code=401
    )


@router.post("/logout", dependencies=[Depends(csrf_authed)])
def logout(request: Request, db: DbSession):
    s = get_settings()
    token = request.cookies.get(s.session_cookie_name)
    if token:
        destroy_session(db, token)
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(s.session_cookie_name, path="/")
    return response
