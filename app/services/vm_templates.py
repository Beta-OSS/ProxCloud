from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.vm import VMTemplate
from app.schemas.vm import VMTemplateCreate

from app.clients.proxmox import get_vm_templates

class VMTemplateExists(Exception):
    pass


def create_vm_template(
    db: Session,
    data: VMTemplateCreate,
) -> VMTemplate:
    template = VMTemplate(
        node=data.node,
        vmid=data.vmid,
        name=data.name,
        version=data.version,
        os=data.os,
        description=data.description,
        is_approved=data.is_approved,
    )

    db.add(template)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise VMTemplateExists from None

    db.refresh(template)
    return template


def get_vm_template(
    db: Session,
    id: uuid.UUID,
) -> VMTemplate | None:
    return db.get(VMTemplate, id)


def list_vm_templates(
    db: Session,
) -> list[VMTemplate]:
    return list(
        db.scalars(
            select(VMTemplate).order_by(
                VMTemplate.created_at,
                VMTemplate.name,
            )
        )
    )


def vm_template_counts(
    db: Session,
) -> dict[str, int]:
    total = (
        db.scalar(
            select(func.count()).select_from(VMTemplate)
        )
        or 0
    )

    approved = (
        db.scalar(
            select(func.count())
            .select_from(VMTemplate)
            .where(VMTemplate.is_approved.is_(True))
        )
        or 0
    )

    return {
        "total": total,
        "approved": approved,
    }


def get_vm_template_by_proxmox_id(
    db: Session,
    *,
    node: str,
    vmid: int,
) -> VMTemplate | None:
    return db.scalar(
        select(VMTemplate).where(
            VMTemplate.node == node,
            VMTemplate.vmid == vmid,
        )
    )


async def sync_vm_templates(db: Session) -> dict[str, int]:
    """Synchronise Proxmox VM templates into the local catalogue."""

    proxmox_templates = await get_vm_templates()
    created = 0
    updated = 0

    for proxmox_template in proxmox_templates:
        node = proxmox_template["node"]
        vmid = proxmox_template["vmid"]
        name = proxmox_template.get("name") or f"VM {vmid}"

        template = get_vm_template_by_proxmox_id(
            db,
            node=node,
            vmid=vmid,
        )

        if template is None:
            template = VMTemplate(
                node=node,
                vmid=vmid,
                name=name,
            )

            db.add(template)
            created += 1

        else:
            template.name = name
            updated += 1

    db.commit()

    return {
        "created": created,
        "updated": updated,
    }

def approve_vm_template(
    db: Session,
    template_id: uuid.UUID,
) -> VMTemplate | None:
    """Approve a VM template for user deployment."""

    template = get_vm_template(db, template_id)

    if template is None:
        return None

    template.is_approved = True

    db.commit()
    db.refresh(template)

    return template


def disapprove_vm_template(
    db: Session,
    template_id: uuid.UUID,
) -> VMTemplate | None:
    """Remove approval from a VM template."""

    template = get_vm_template(db, template_id)

    if template is None:
        return None

    template.is_approved = False

    db.commit()
    db.refresh(template)

    return template