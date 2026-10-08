from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.proxmox import clone_vm, start_vm, stop_vm
from app.models.vm import UserVM
from app.schemas.vm import UserVMCreate
from app.services.vm_templates import get_vm_template
from app.db.types import utcnow


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


def _update_user_vm_sync_time(
    db: Session,
    vm: UserVM,
) -> UserVM:
    """Update the last Proxmox synchronisation time."""

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
    vmid: int,
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

    await clone_vm(
        node=template.node,
        vmid=template.vmid,
        newid=vmid,
        name=name,
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
    """Start a user's VM."""

    vm = get_user_vm(
        db,
        vm_id=vm_id,
        user_id=user_id,
    )

    if vm is None:
        return None

    await start_vm(
        node=vm.node,
        vmid=vm.vmid,
    )

    return _update_user_vm_status(
        db,
        vm,
        is_active=True,
    )

async def stop_user_vm(
    db: Session,
    *,
    vm_id: uuid.UUID,
    user_id: uuid.UUID,
) -> UserVM | None:
    """Stop a user's VM."""

    vm = get_user_vm(
        db,
        vm_id=vm_id,
        user_id=user_id,
    )

    if vm is None:
        return None

    await stop_vm(
        node=vm.node,
        vmid=vm.vmid,
    )

    return _update_user_vm_status(
        db,
        vm,
        is_active=False,
    )