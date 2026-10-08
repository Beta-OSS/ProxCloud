import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.core.dependencies import (
    AuthCtx,
    DbSession,
    csrf_authed,
)
from app.core.templating import render
from app.services.user_vms import start_user_vm, stop_user_vm, get_user_vm_ip

router = APIRouter(prefix="/vms")
api_router = APIRouter(prefix="/api/vms")

@router.post(
    "/{vm_id}/start",
    dependencies=[Depends(csrf_authed)],
)
async def start_vm(
    vm_id: uuid.UUID,
    db: DbSession,
    ctx: AuthCtx,
):
    await start_user_vm(
        db,
        vm_id=vm_id,
        user_id=ctx.user.id,
    )

    return RedirectResponse(
        url="/dashboard/",
        status_code=303,
    )

@router.post(
    "/{vm_id}/stop",
    dependencies=[Depends(csrf_authed)],
)
async def stop_vm(
    vm_id: uuid.UUID,
    db: DbSession,
    ctx: AuthCtx,
):
    await stop_user_vm(
        db,
        vm_id=vm_id,
        user_id=ctx.user.id,
    )

    return RedirectResponse(
        url="/dashboard/",
        status_code=303,
    )

@router.post(
    "/{vm_id}/connect",
    dependencies=[Depends(csrf_authed)],
)
async def connect_vm(
    vm_id: uuid.UUID,
    db: DbSession,
    ctx: AuthCtx,
):
    return await get_user_vm_ip(
        db,
        vm_id=vm_id,
        user_id=ctx.user.id,
    )