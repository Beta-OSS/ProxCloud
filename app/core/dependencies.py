"""Backend enforcement of authentication, authorization and CSRF.

Every protected route must depend on one of these. Hiding UI elements is cosmetic only.
"""
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import ct_eq, verify_anon_csrf
from app.db.database import get_db
from app.models.auth import STAGE_ACTIVE, STAGE_PENDING_2FA, UserSession
from app.models.user import User
from app.services.auth.sessions import resolve_session

ANON_CSRF_COOKIE = "portal_csrf"

DbSession = Annotated[Session, Depends(get_db)]


@dataclass
class AuthContext:
    session: UserSession
    user: User


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _context(request: Request, db: Session, stage: str) -> AuthContext:
    token = request.cookies.get(get_settings().session_cookie_name)
    resolved = resolve_session(db, token, stage) if token else None
    if resolved is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return AuthContext(*resolved)


def current_pending(request: Request, db: DbSession) -> AuthContext:
    return _context(request, db, STAGE_PENDING_2FA)


def current_auth(request: Request, db: DbSession) -> AuthContext:
    return _context(request, db, STAGE_ACTIVE)


def require_admin(ctx: Annotated[AuthContext, Depends(current_auth)]) -> AuthContext:
    if not ctx.user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return ctx


PendingCtx = Annotated[AuthContext, Depends(current_pending)]
AuthCtx = Annotated[AuthContext, Depends(current_auth)]
AdminCtx = Annotated[AuthContext, Depends(require_admin)]


async def _submitted_token(request: Request) -> str:
    header = request.headers.get("x-csrf-token")
    if header:
        return header
    content_type = request.headers.get("content-type", "")
    if content_type.startswith(("application/x-www-form-urlencoded", "multipart/form-data")):
        value = (await request.form()).get("csrf_token")
        if isinstance(value, str):
            return value
    return ""


async def csrf_authed(request: Request, ctx: AuthCtx) -> None:
    if not ct_eq(await _submitted_token(request), ctx.session.csrf_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")


async def csrf_pending(request: Request, ctx: PendingCtx) -> None:
    if not ct_eq(await _submitted_token(request), ctx.session.csrf_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed")


async def csrf_anon(request: Request) -> None:
    """Login form: no session exists yet, so use an HMAC-signed double-submit cookie."""
    if not verify_anon_csrf(await _submitted_token(request), request.cookies.get(ANON_CSRF_COOKIE, "")):
        raise HTTPException(status_code=403, detail="CSRF validation failed")
