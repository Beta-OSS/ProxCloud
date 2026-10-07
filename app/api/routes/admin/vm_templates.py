from fastapi import APIRouter, Depends, HTTPException, Request
import uuid

from app.core.dependencies import (
    AdminCtx,
    DbSession,
    csrf_authed,
    require_admin,
)
from app.core.templating import is_htmx, render
from app.services.vm_templates import (
    approve_vm_template,
    disapprove_vm_template,
    list_vm_templates,
    sync_vm_templates,
)

router = APIRouter(prefix="/admin/vm-templates", dependencies=[Depends(require_admin)],)
api_router = APIRouter(prefix="/api/admin/vm-templates", dependencies=[Depends(require_admin)],)


def _vm_templates_view(
    request: Request,
    db,
    ctx,
    *,
    message=None,
    errors=None,
    status_code=200,
):
    return render(
        request,
        "_vm_templates_panel.html"
        if is_htmx(request)
        else "admin_vm_templates.html",
        user=ctx.user,
        csrf_token=ctx.session.csrf_token,
        vm_templates=list_vm_templates(db),
        message=message,
        errors=errors or [],
        status_code=200 if is_htmx(request) else status_code,
    )


@router.get("")
def vm_templates_page(
    request: Request,
    db: DbSession,
    ctx: AdminCtx,
):
    return _vm_templates_view(
        request,
        db,
        ctx,
    )

@router.post(
    "/sync",
    dependencies=[Depends(csrf_authed)],
)
async def sync_vm_templates_route(
    request: Request,
    db: DbSession,
    ctx: AdminCtx,
):
    try:
        result = await sync_vm_templates(db)

    except Exception:
        return _vm_templates_view(
            request,
            db,
            ctx,
            errors=["Unable to synchronise VM templates."],
            status_code=502,
        )

    return _vm_templates_view(
        request,
        db,
        ctx,
        message=(
            f"Synchronisation complete: "
            f"{result['created']} created, "
            f"{result['updated']} updated."
        ),
    )

@router.post(
    "/{template_id}/approve",
    dependencies=[Depends(csrf_authed)],
)
def approve_vm_template_route(
    request: Request,
    template_id: uuid.UUID,
    db: DbSession,
    ctx: AdminCtx,
):
    template = approve_vm_template(
        db,
        template_id,
    )

    if template is None:
        raise HTTPException(
            status_code=404,
            detail="VM template not found.",
        )

    return _vm_templates_view(
        request,
        db,
        ctx,
        message=f"VM template '{template.name}' approved.",
    )


@router.post(
    "/{template_id}/disapprove",
    dependencies=[Depends(csrf_authed)],
)
def disapprove_vm_template_route(
    request: Request,
    template_id: uuid.UUID,
    db: DbSession,
    ctx: AdminCtx,
):
    template = disapprove_vm_template(
        db,
        template_id,
    )

    if template is None:
        raise HTTPException(
            status_code=404,
            detail="VM template not found.",
        )

    return _vm_templates_view(
        request,
        db,
        ctx,
        message=f"VM template '{template.name}' disapproved.",
    )