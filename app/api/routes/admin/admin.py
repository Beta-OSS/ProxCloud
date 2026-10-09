from fastapi import APIRouter, Depends, Request

from app.core.dependencies import AdminCtx, DbSession, require_admin
from app.core.templating import render
from app.services.users import user_counts
from app.services.proxmox_sync import sync_proxmox_state

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)],)


@router.get("")
async def admin_home(
    request: Request,
    db: DbSession,
    ctx: AdminCtx,
):
    await sync_proxmox_state(db)
    return render(
        request,
        "admin/admin.html",
        user=ctx.user,
        csrf_token=ctx.session.csrf_token,
        user_counts=user_counts(db),
    )