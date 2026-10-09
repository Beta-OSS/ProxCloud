from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.proxmox import get_nodes, get_node_vms
from app.db.types import utcnow
from app.models.user_vm import UserVM
from app.models.vm import VMTemplate

logger = logging.getLogger(__name__)


async def sync_proxmox_state(db: Session) -> dict[str, int | bool]:
    """
    Reconcile ProxCloud's VM records with the Proxmox inventory.

    User VMs:
    - Update power state and presence for existing records.
    - Preserve records and ownership when VMs are missing.
    - Do not overwrite user-managed metadata.

    VM templates:
    - Discover new templates without approving them.
    - Update names when they change in Proxmox.
    - Remove catalogue entries for VMs that no longer exist
      or are no longer Proxmox templates.
    - Preserve administrator approval for existing templates.

    If inventory retrieval fails, make no database changes.
    """

    # Fetch the complete inventory before modifying the database.
    # Never reconcile against a partial inventory.
    inventory: dict[tuple[str, int], dict] = {}

    try:
        nodes = await get_nodes()

        for node_info in nodes:
            node = node_info["node"]
            vms = await get_node_vms(node)

            for vm_info in vms:
                vmid = int(vm_info["vmid"])

                inventory[(node, vmid)] = {
                    **vm_info,
                    "node": node,
                    "vmid": vmid,
                }

    except Exception:
        logger.exception(
            "Proxmox inventory retrieval failed; "
            "database was not synchronised."
        )
        return {
            "success": False,
            "user_vms_updated": 0,
            "user_vms_missing": 0,
            "templates_discovered": 0,
            "templates_updated": 0,
            "templates_removed": 0,
        }

    sync_time = utcnow()

    user_vms_updated = 0
    user_vms_missing = 0
    templates_discovered = 0
    templates_updated = 0
    templates_removed = 0

    try:
        # ---------------------------------------------------------
        # Reconcile existing user VM records.
        # ---------------------------------------------------------
        user_vms = list(db.scalars(select(UserVM)).all())

        for user_vm in user_vms:
            proxmox_vm = inventory.get(
                (user_vm.node, user_vm.vmid)
            )

            if proxmox_vm is None:
                # Keep the record for ownership and audit purposes.
                user_vm.is_present = False
                user_vm.power_state = "unknown"
                user_vm.last_synced_at = sync_time
                user_vms_missing += 1
                continue

            status = proxmox_vm.get("status", "unknown")

            if status not in {"running", "stopped"}:
                status = "unknown"

            user_vm.is_present = True
            user_vm.power_state = status
            user_vm.last_synced_at = sync_time

            # Preserve user_id, is_active, name, description, and os.
            user_vms_updated += 1

        # ---------------------------------------------------------
        # Identify the current Proxmox template inventory.
        # ---------------------------------------------------------
        proxmox_templates = {
            key: vm_info
            for key, vm_info in inventory.items()
            if vm_info.get("template") == 1
        }

        # Load the existing database template catalogue.
        existing_templates = {
            (template.node, template.vmid): template
            for template in db.scalars(
                select(VMTemplate)
            ).all()
        }

        # ---------------------------------------------------------
        # Discover new templates and update existing ones.
        # ---------------------------------------------------------
        for key, vm_info in proxmox_templates.items():
            node, vmid = key
            name = vm_info.get("name") or f"VM {vmid}"

            template = existing_templates.get(key)

            if template is None:
                # New templates must be approved by an administrator.
                db.add(
                    VMTemplate(
                        node=node,
                        vmid=vmid,
                        name=name,
                        is_approved=False,
                    )
                )
                templates_discovered += 1
                continue

            # Synchronise the name without overwriting approval.
            if template.name != name:
                template.name = name
                templates_updated += 1

        # ---------------------------------------------------------
        # Remove templates no longer present in Proxmox's
        # template inventory, including VMs whose template flag
        # has been removed.
        # ---------------------------------------------------------
        proxmox_template_keys = set(proxmox_templates)

        for key, template in existing_templates.items():
            if key not in proxmox_template_keys:
                db.delete(template)
                templates_removed += 1

        # Commit all reconciliation changes together.
        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            "ProxCloud database reconciliation failed."
        )
        raise

    logger.info(
        "Proxmox sync completed: "
        "%d user VMs updated, %d user VMs missing, "
        "%d templates discovered, %d templates updated, "
        "%d templates removed.",
        user_vms_updated,
        user_vms_missing,
        templates_discovered,
        templates_updated,
        templates_removed,
    )

    return {
        "success": True,
        "user_vms_updated": user_vms_updated,
        "user_vms_missing": user_vms_missing,
        "templates_discovered": templates_discovered,
        "templates_updated": templates_updated,
        "templates_removed": templates_removed,
    }