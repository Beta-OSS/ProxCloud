import uuid
import re

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, Response

from app.core.dependencies import (
    AuthCtx,
    DbSession,
    csrf_authed,
)
from app.core.templating import render
from app.services.user_vms import start_user_vm, stop_user_vm, get_user_vm_ip, get_user_vm, delete_user_vm
from app.services.proxmox_sync import sync_proxmox_state

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
    await sync_proxmox_state(db)
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
    await sync_proxmox_state(db)
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
    "/{vm_id}/delete",
    dependencies=[Depends(csrf_authed)],
)
async def delete_vm_route(
    vm_id: uuid.UUID,
    db: DbSession,
    ctx: AuthCtx,
):
    deleted = await delete_user_vm(
        db,
        vm_id=vm_id,
        user_id=ctx.user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="VM not found.",
        )

    return RedirectResponse(
        url="/dashboard",
        status_code=303,
    )

def generate_rdp_file(
    *,
    ip: str,
    os_name: str | None,
) -> tuple[str, str]:
    """Generate RDP configuration and a suitable download filename."""

    os_lower = (os_name or "").lower()

    # Common settings for Windows Remote Desktop clients.
    settings = [
        f"full address:s:{ip}",
        "prompt for credentials:i:1",
        "screen mode id:i:2",
        "use multimon:i:0",
        "redirectclipboard:i:1",
        "redirectprinters:i:0",
        "authentication level:i:2",
    ]

    if "windows" in os_lower:
        settings.extend([
            "enablecredsspsupport:i:1",
            "negotiate security layer:i:1",
        ])
        os_label = "Windows"

    elif any(name in os_lower for name in ("linux", "ubuntu", "debian")):
        # Some Linux RDP servers, including certain xrdp configurations,
        # do not support Network Level Authentication (CredSSP).
        settings.extend([
            "enablecredsspsupport:i:0",
        ])
        os_label = "Linux"

    else:
        # Generic profile when the OS is unspecified or unrecognised.
        settings.extend([
            "enablecredsspsupport:i:1",
        ])
        os_label = "RemoteDesktop"

    content = "\r\n".join(settings) + "\r\n"

    return content, os_label
    
@router.post(
    "/{vm_id}/connect",
    dependencies=[Depends(csrf_authed)],
)
async def connect_vm(
    vm_id: uuid.UUID,
    db: DbSession,
    ctx: AuthCtx,
):
    print("here")
    await sync_proxmox_state(db)

    # Verify ownership before attempting to connect.
    vm = get_user_vm(
        db,
        vm_id=vm_id,
        user_id=ctx.user.id,
    )

    if vm is None:
        raise HTTPException(
            status_code=404,
            detail="VM not found.",
        )

    if not vm.is_present:
        raise HTTPException(
            status_code=409,
            detail="This VM is not currently present in Proxmox.",
        )

    if vm.power_state != "running":
        raise HTTPException(
            status_code=409,
            detail="The VM must be running before you can connect.",
        )

    ip = await get_user_vm_ip(
        db,
        vm_id=vm_id,
        user_id=ctx.user.id,
    )

    if not ip:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve the VM's IP address. "
                   "Check that the guest agent is running and "
                   "the VM has an IPv4 address.",
        )

    content, os_label = generate_rdp_file(
        ip=ip,
        os_name=vm.os,
    )

    # Remove characters that are unsuitable for a download filename.
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", vm.name).strip("._")
    safe_name = safe_name or f"VM-{vm.vmid}"

    filename = f"{safe_name}-{os_label}.rdp"

    return Response(
        content=content,
        media_type="application/x-rdp",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
    