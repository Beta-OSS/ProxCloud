import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.core.dependencies import (
    AuthCtx,
    DbSession,
    csrf_authed,
)
from app.core.templating import render
from app.services.user_vms import clone_user_vm
from app.services.vm_templates import list_approved_vm_templates


router = APIRouter(prefix="/add-vm")


@router.get("/")
def vm_templates(
    request: Request,
    db: DbSession,
    ctx: AuthCtx,
):
    templates = list_approved_vm_templates(db)

    return render(
        request,
        "user_actions/new_user_vm.html",
        user=ctx.user,
        csrf_token=ctx.session.csrf_token,
        vm_templates=templates,
    )


@router.post(
    "/{template_id}/clone",
    dependencies=[Depends(csrf_authed)],
)
async def clone_vm_template(
    template_id: uuid.UUID,
    db: DbSession,
    ctx: AuthCtx,
    name: str = Form(...),
    description: str | None = Form(None),
):
    await clone_user_vm(
        db,
        template_id=template_id,
        user_id=ctx.user.id,
        name=name,
        description=description,
    )

    return RedirectResponse(
        url="/dashboard/",
        status_code=303,
    )