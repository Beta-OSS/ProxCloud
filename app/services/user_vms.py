from __future__ import annotations

import uuid
import asyncio
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.types import utcnow
from app.core.config import get_settings

from app.clients.proxmox import clone_vm, start_vm, stop_vm, get_node_vmids, get_vm_ip, get_vm_status, set_vm_qemu_agent, delete_vm
from app.models.user_vm import UserVM
from app.schemas.user_vm import UserVMCreate
from app.services.vm_templates import get_vm_template


## User VM Data Access Layer (not called directly by API endpoints)

def list_user_vms(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> list[UserVM]:
    """List all VMs owned by a user."""

    return list(
        db.scalars(
            select(UserVM)
            .where(UserVM.user_id == user_id)
            .order_by(
                UserVM.created_at,
                UserVM.name,
            )
        )
    )


def get_user_vm(
    db: Session,
    *,
    vm_id: uuid.UUID,
    user_id: uuid.UUID,
) -> UserVM | None:
    """Get a VM belonging to a specific user."""

    return db.scalar(
        select(UserVM).where(
            UserVM.id == vm_id,
            UserVM.user_id == user_id,
        )
    )

async def _get_next_vm_id(
    db: Session,
    *,
    node: str,
) -> int:
    settings = get_settings()

    db_vmids = set(
        db.scalars(
            select(UserVM.vmid).where(
                UserVM.node == node,
                UserVM.vmid >= settings.user_vm_vmid_min,
                UserVM.vmid <= settings.user_vm_vmid_max,
            )
        )
    )

    proxmox_vmids = await get_node_vmids(node)

    used_vmids = db_vmids | proxmox_vmids

    for vmid in range(
        settings.user_vm_vmid_min,
        settings.user_vm_vmid_max + 1,
    ):
        if vmid not in used_vmids:
            return vmid

    raise RuntimeError(
        f"No available VMIDs on node '{node}' "
        f"in range "
        f"{settings.user_vm_vmid_min}-{settings.user_vm_vmid_max}."
    )

def _add_user_vm(
    db: Session,
    *,
    data: UserVMCreate,
    user_id: uuid.UUID,
) -> UserVM:
    """Create a UserVM database record."""

    vm = UserVM(
        node=data.node,
        vmid=data.vmid,
        name=data.name,
        os=data.os,
        description=data.description,
        user_id=user_id,
        is_active=False,
    )

    db.add(vm)
    db.commit()
    db.refresh(vm)

    return vm


def _remove_user_vm(
    db: Session,
    vm: UserVM,
) -> None:
    """Remove a UserVM database record."""

    db.delete(vm)
    db.commit()


def _update_user_vm_identity(
    db: Session,
    vm: UserVM,
    *,
    name: str,
    description: str | None,
) -> UserVM:
    """Update the database identity/display information for a VM."""

    vm.name = name
    vm.description = description

    db.commit()
    db.refresh(vm)

    return vm


async def _sync_user_vm_state(
    db: Session,
    vm: UserVM,
) -> UserVM:
    """Refresh a VM's runtime state from Proxmox."""

    status_data = await get_vm_status(
        node=vm.node,
        vmid=vm.vmid,
    )

    status = status_data.get("status", "unknown")
    if status not in {"running", "stopped"}:
        status = "unknown"

    vm.power_state = status
    vm.is_present = True
    vm.last_synced_at = utcnow()

    db.commit()
    db.refresh(vm)

    return vm


def _update_user_vm_status(
    db: Session,
    vm: UserVM,
    *,
    is_active: bool,
) -> UserVM:
    """Update the database active state of a VM."""

    vm.is_active = is_active

    db.commit()
    db.refresh(vm)

    return vm

# User VM Service Layer

async def clone_user_vm(
    db: Session,
    *,
    template_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    description: str | None = None,
) -> UserVM:
    """Clone an approved VM template for a user."""

    template = get_vm_template(
        db,
        template_id,
    )

    if template is None:
        raise ValueError("VM template not found.")

    if not template.is_approved:
        raise ValueError("VM template is not approved.")

    vmid = await _get_next_vm_id(
        db,
        node=template.node,
    )

    await clone_vm(
        node=template.node,
        vmid=template.vmid,
        newid=vmid,
        name=name,
    )

    await set_vm_qemu_agent(
        node=template.node,
        vmid=vmid,
        enabled=True,
    )

    vm = _add_user_vm(
        db,
        data=UserVMCreate(
            node=template.node,
            vmid=vmid,
            name=name,
            os=template.os,
            description=description,
        ),
        user_id=user_id,
    )

    return vm

async def start_user_vm(
    db: Session,
    *,
    vm_id: uuid.UUID,
    user_id: uuid.UUID,
) -> UserVM | None:
    """Request VM startup and synchronise its Proxmox state."""

    vm = get_user_vm(
        db,
        vm_id=vm_id,
        user_id=user_id,
    )

    if vm is None:
        return None

    if not vm.is_present:
        raise ValueError("VM is not present in Proxmox.")

    await start_vm(
        node=vm.node,
        vmid=vm.vmid,
    )

    return await _sync_user_vm_state(db, vm)


async def stop_user_vm(
    db: Session,
    *,
    vm_id: uuid.UUID,
    user_id: uuid.UUID,
) -> UserVM | None:
    """Request VM shutdown and synchronise its Proxmox state."""

    vm = get_user_vm(
        db,
        vm_id=vm_id,
        user_id=user_id,
    )

    if vm is None:
        return None

    if not vm.is_present:
        raise ValueError("VM is not present in Proxmox.")

    await stop_vm(
        node=vm.node,
        vmid=vm.vmid,
    )

    return await _sync_user_vm_state(db, vm)


async def get_user_vm_ip(
    db: Session,
    *,
    vm_id: uuid.UUID,
    user_id: uuid.UUID,
) -> str | None:
    """Get the IP address of a user's VM."""

    vm = get_user_vm(
        db,
        vm_id=vm_id,
        user_id=user_id,
    )

    if vm is None:
        return None

    ip = await get_vm_ip(
        node=vm.node,
        vmid=vm.vmid,
    )

    return ip

async def delete_user_vm(
    db: Session,
    *,
    vm_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Delete a user's VM from Proxmox and the database.

    If the VM is already missing from Proxmox, remove only
    the database record.

    Returns False if the user does not own the VM.
    Raises an exception if Proxmox deletion fails.
    """

    vm = get_user_vm(
        db,
        vm_id=vm_id,
        user_id=user_id,
    )

    if vm is None:
        return False

    # Check Proxmox directly instead of relying on a potentially
    # stale is_present value from the last inventory sync.
    proxmox_vmids = await get_node_vmids(vm.node)

    if vm.vmid in proxmox_vmids:
        # This must wait for successful deletion, or raise.
        await delete_vm(
            node=vm.node,
            vmid=vm.vmid,
        )

    # Only remove the database record after the Proxmox
    # deletion succeeds, or if the VM was already missing.
    db.delete(vm)
    db.commit()

    return True