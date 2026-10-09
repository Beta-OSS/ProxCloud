from __future__ import annotations

import os
from typing import Any
import asyncio
import time
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

async def proxmox_put(
    path: str,
    data: dict[str, Any] | None = None,
) -> Any:
    """Perform a PUT request against the Proxmox API."""
    url = f"{PROXMOX_URL}/api2/json{path}"

    async with httpx.AsyncClient(
        verify=PROXMOX_VERIFY_SSL,
        timeout=10.0,
    ) as client:
        response = await client.put(
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
    upid = await proxmox_post(
        f"/nodes/{node}/qemu/{vmid}/clone",
        data={
            "newid": newid,
            "name": name,
            "full": 1,
        },
    )

    await wait_for_task(node, upid)


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

async def get_vm_ip(
    node: str,
    vmid: int,
) -> str | None:
    """Return the eth0 IPv4 address of a VM, if available."""

    try:
        data = await proxmox_get(
            f"/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"
        )
    except httpx.HTTPStatusError as exc:
        # The QEMU guest agent may be unavailable or not installed.
        if exc.response.status_code == 500:
            return None

        raise

    for interface in data.get("result", []):
        if interface.get("name") != "eth0":
            continue

        for ip in interface.get("ip-addresses", []):
            if ip.get("ip-address-type") == "ipv4":
                return ip.get("ip-address")

        # eth0 exists but has no IPv4 address.
        return None

    # eth0 was not found.
    return None


async def get_vm_status(node: str, vmid: int) -> dict[str, Any]:
    return await proxmox_get(
        f"/nodes/{node}/qemu/{vmid}/status/current"
    )

async def set_vm_qemu_agent(
    node: str,
    vmid: int,
    *,
    enabled: bool = True,
) -> None:
    """Enable or disable the QEMU Guest Agent for a VM."""

    await proxmox_put(
        f"/nodes/{node}/qemu/{vmid}/config",
        data={"agent": int(enabled)},
    )

async def wait_for_task(
    node: str,
    upid: str,
    *,
    timeout: float = 300,
    poll_interval: float = 2,
) -> None:
    """Wait for a Proxmox task to finish successfully."""

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        task = await proxmox_get(
            f"/nodes/{node}/tasks/{upid}/status"
        )

        if task.get("status") == "stopped":
            if task.get("exitstatus") != "OK":
                raise RuntimeError(
                    f"Proxmox task failed: {task.get('exitstatus')}"
                )
            return

        await asyncio.sleep(poll_interval)

    raise TimeoutError(f"Proxmox task did not finish within {timeout}s")

async def proxmox_delete(path: str) -> Any:
    """Perform a DELETE request against the Proxmox API."""
    url = f"{PROXMOX_URL}/api2/json{path}"

    async with httpx.AsyncClient(
        verify=PROXMOX_VERIFY_SSL,
        timeout=10.0,
    ) as client:
        response = await client.delete(
            url,
            headers=proxmox_headers(),
        )

    response.raise_for_status()
    return response.json()["data"]
    
async def delete_vm(
    node: str,
    vmid: int,
    *,
    timeout: float = 300,
) -> None:
    """Delete a QEMU VM and wait for Proxmox to finish."""

    upid = await proxmox_delete(
        f"/nodes/{node}/qemu/{vmid}",
    )

    if not isinstance(upid, str) or not upid:
        raise RuntimeError(
            f"Proxmox did not return a task UPID when deleting VM {vmid}."
        )

    await wait_for_task(
        node=node,
        upid=upid,
        timeout=timeout,
    )

