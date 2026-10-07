import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.core.dependencies import AdminCtx, DbSession, csrf_authed, require_admin
from app.core.templating import is_htmx, render
from app.schemas.user import UserCreate, UserRead, validate_new_password
from app.services.users import (
    UserExists,
    change_password,
    create_user,
    get_user,
    list_users,
    set_active,
    user_counts,
)

# Router-level dependency: every route below requires an authenticated ADMIN,
# checked server-side.
router = APIRouter(dependencies=[Depends(require_admin)])
api_router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


# ----------------------------------------------------------------------------- HTML / HTMX

def _users_view(
    request: Request,
    db,
    ctx,
    *,
    message=None,
    errors=None,
    form=None,
    reset_password=None,
    status_code=200,
):
    return render(
        request,
        "_users_panel.html" if is_htmx(request) else "admin_users.html",
        user=ctx.user,
        csrf_token=ctx.session.csrf_token,
        users=list_users(db),
        message=message,
        errors=errors or [],
        form=form or {},
        reset_password=reset_password,
        # htmx does not swap 4xx responses by default, so errors are returned as
        # 200 for it.
        status_code=200 if is_htmx(request) else status_code,
    )


@router.get("/admin")
def admin_home(request: Request, db: DbSession, ctx: AdminCtx):
    return render(
        request,
        "admin.html",
        user=ctx.user,
        csrf_token=ctx.session.csrf_token,
        user_counts=user_counts(db),
    )


@router.get("/admin/users")
def admin_users(request: Request, db: DbSession, ctx: AdminCtx):
    return _users_view(request, db, ctx)


@router.post("/admin/users", dependencies=[Depends(csrf_authed)])
def admin_create_user(
    request: Request,
    db: DbSession,
    ctx: AdminCtx,
    username: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    is_admin: Annotated[str | None, Form()] = None,
):
    try:
        data = UserCreate(
            username=username,
            email=email,
            password=password,
            is_admin=is_admin is not None,
        )
        create_user(db, data)
    except ValidationError as exc:
        errors = [e["msg"].removeprefix("Value error, ") for e in exc.errors()]
    except UserExists:
        errors = ["Username or email is already in use."]
    else:
        if not is_htmx(request):
            return RedirectResponse("/admin/users", status_code=303)

        return _users_view(
            request,
            db,
            ctx,
            message=f"User '{data.username}' created.",
        )

    form = {
        "username": username,
        "email": email,
        "is_admin": is_admin is not None,
    }

    return _users_view(
        request,
        db,
        ctx,
        errors=errors,
        form=form,
        status_code=400,
    )


def _toggle(request: Request, db, ctx, user_id: uuid.UUID, active: bool):
    target = get_user(db, user_id)

    if target is None:
        raise HTTPException(status_code=404, detail="Not found")

    if not active and target.id == ctx.user.id:
        return _users_view(
            request,
            db,
            ctx,
            errors=["You cannot deactivate your own account."],
            status_code=400,
        )

    set_active(db, target, active)

    if not is_htmx(request):
        return RedirectResponse("/admin/users", status_code=303)

    verb = "reactivated" if active else "deactivated"

    return _users_view(
        request,
        db,
        ctx,
        message=f"User '{target.username}' {verb}.",
    )


@router.post(
    "/admin/users/{user_id}/deactivate",
    dependencies=[Depends(csrf_authed)],
)
def admin_deactivate(
    request: Request,
    db: DbSession,
    ctx: AdminCtx,
    user_id: uuid.UUID,
):
    return _toggle(request, db, ctx, user_id, False)


@router.post(
    "/admin/users/{user_id}/reactivate",
    dependencies=[Depends(csrf_authed)],
)
def admin_reactivate(
    request: Request,
    db: DbSession,
    ctx: AdminCtx,
    user_id: uuid.UUID,
):
    return _toggle(request, db, ctx, user_id, True)


@router.post(
    "/admin/users/{user_id}/reset-password",
    dependencies=[Depends(csrf_authed)],
)
def admin_reset_password(
    request: Request,
    db: DbSession,
    ctx: AdminCtx,
    user_id: uuid.UUID,
):
    target = get_user(db, user_id)

    if target is None:
        raise HTTPException(status_code=404, detail="Not found")

    # Do not allow an administrator to accidentally reset their own password
    # through this endpoint. They already have the normal password-change flow.
    if target.id == ctx.user.id:
        return _users_view(
            request,
            db,
            ctx,
            errors=[
                "You cannot reset your own password from the admin panel. "
                "Use Settings to change your password."
            ],
            status_code=400,
        )

    # 24 random bytes gives a high-entropy password while remaining reasonably
    # easy to copy.
    generated_password = secrets.token_urlsafe(18)

    # Keep this consistent with the normal user password-change flow.
    error = validate_new_password(
        generated_password,
        target.username,
    )

    if error:
        # Extremely unlikely with a cryptographically random password, but
        # don't proceed if it somehow violates the application's policy.
        return _users_view(
            request,
            db,
            ctx,
            errors=[f"Could not generate a valid password: {error}"],
            status_code=500,
        )

    # change_password() should invalidate the target user's other sessions.
    change_password(db, target, generated_password)

    return _users_view(
        request,
        db,
        ctx,
        message=f"Password reset for '{target.username}'.",
        reset_password={
            "username": target.username,
            "password": generated_password,
        },
    )


# ----------------------------------------------------------------------------- JSON API

@api_router.get("/users", response_model=list[UserRead])
def api_list_users(db: DbSession):
    return list_users(db)


@api_router.post(
    "/users",
    response_model=UserRead,
    status_code=201,
    dependencies=[Depends(csrf_authed)],
)
def api_create_user(data: UserCreate, db: DbSession):
    try:
        return create_user(db, data)
    except UserExists:
        raise HTTPException(
            status_code=409,
            detail="Username or email is already in use.",
        ) from None


def _api_toggle(db, ctx, user_id: uuid.UUID, active: bool):
    target = get_user(db, user_id)

    if target is None:
        raise HTTPException(status_code=404, detail="Not found")

    if not active and target.id == ctx.user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account.",
        )

    set_active(db, target, active)
    return target


@api_router.post(
    "/users/{user_id}/deactivate",
    response_model=UserRead,
    dependencies=[Depends(csrf_authed)],
)
def api_deactivate(
    db: DbSession,
    ctx: AdminCtx,
    user_id: uuid.UUID,
):
    return _api_toggle(db, ctx, user_id, False)


@api_router.post(
    "/users/{user_id}/reactivate",
    response_model=UserRead,
    dependencies=[Depends(csrf_authed)],
)
def api_reactivate(
    db: DbSession,
    ctx: AdminCtx,
    user_id: uuid.UUID,
):
    return _api_toggle(db, ctx, user_id, True)