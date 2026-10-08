from __future__ import annotations

import os
from typing import Any

import httpx


PROXMOX_URL = os.environ["PROXMOX_URL"].rstrip("/")
PROXMOX_TOKEN_ID = os.environ["PROXMOX_TOKEN_ID"]
PROXMOX_TOKEN_SECRET = os.environ["PROXMOX_TOKEN_SECRET"]

# Set to "false" if you are using a certificate that the VM does not trust.
PROXMOX_VERIFY_SSL = (
    os.getenv("PROXMOX_VERIFY_SSL", "true").lower() == "true"
)


def proxmox_headers() -> dict[str, str]:
    """Return authentication headers for the Proxmox API."""
    return {
        "Authorization": (
            f"PVEAPIToken={PROXMOX_TOKEN_ID}={PROXMOX_TOKEN_SECRET}"
        )
    }


async def proxmox_get(path: str) -> Any:
    """Perform a GET request against the Proxmox API."""
    url = f"{PROXMOX_URL}/api2/json{path}"

    async with httpx.AsyncClient(
        verify=PROXMOX_VERIFY_SSL,
        timeout=10.0,
    ) as client:
        response = await client.get(
            url,
            headers=proxmox_headers(),
        )

    response.raise_for_status()

    return response.json()["data"]

async def proxmox_post(
    path: str,
    data: dict[str, Any] | None = None,
) -> Any:
    """Perform a POST request against the Proxmox API."""
    url = f"{PROXMOX_URL}/api2/json{path}"

    async with httpx.AsyncClient(
        verify=PROXMOX_VERIFY_SSL,
        timeout=10.0,
    ) as client:
        response = await client.post(
            url,
            headers=proxmox_headers(),
            data=data,
        )

    response.raise_for_status()

    return response.json()["data"]

async def get_nodes() -> list[dict[str, Any]]:
    """Return all nodes from the Proxmox cluster."""
    return await proxmox_get("/nodes")


async def get_node_vms(
    node: str,
) -> list[dict[str, Any]]:
    """Return all QEMU VMs on a Proxmox node."""
    return await proxmox_get(f"/nodes/{node}/qemu")


async def get_vm_templates() -> list[dict[str, Any]]:
    """
    Return all Proxmox QEMU VMs configured as templates.
    """
    nodes = await get_nodes()

    templates: list[dict[str, Any]] = []

    for node in nodes:
        node_name = node["node"]
        vms = await get_node_vms(node_name)

        for vm in vms:
            if vm.get("template") == 1:
                templates.append(
                    {
                        "node": node_name,
                        "vmid": vm["vmid"],
                        "name": vm.get("name"),
                    }
                )

    return templates

async def get_node_vmids(
    node: str,
) -> set[int]:
    """Return all QEMU VMIDs currently present on a Proxmox node."""

    vms = await get_node_vms(node)

    return {
        vm["vmid"]
        for vm in vms
    }

async def clone_vm(
    node: str,
    vmid: int,
    newid: int,
    name: str,
) -> None:
    await proxmox_post(
        f"/nodes/{node}/qemu/{vmid}/clone",
        {
            "newid": newid,
            "name": name,
        },
    )


async def start_vm(
    node: str,
    vmid: int,
) -> None:
    await proxmox_post(
        f"/nodes/{node}/qemu/{vmid}/status/start",
    )


async def stop_vm(
    node: str,
    vmid: int,
) -> None:
    await proxmox_post(
        f"/nodes/{node}/qemu/{vmid}/status/stop",
    )