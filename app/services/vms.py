from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.vm import VirtualMachine
from app.schemas.vm import VMCreate

import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/vms", tags=["vms"])

PROXMOX_URL = os.environ["PROXMOX_URL"].rstrip("/")
PROXMOX_TOKEN_ID = os.environ["PROXMOX_TOKEN_ID"]
PROXMOX_TOKEN_SECRET = os.environ["PROXMOX_TOKEN_SECRET"]

# Set to "false" if you are using a certificate that the VM does not trust.
PROXMOX_VERIFY_SSL = os.getenv("PROXMOX_VERIFY_SSL", "true").lower() == "true"

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

async def sync_vms() -> list[dict[str, Any]]:
    """
    Return all Proxmox VMs that are configured as templates.
    """
    
    try:
        nodes = await proxmox_get("/nodes")
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to contact Proxmox API",
        ) from exc

    templates: list[dict[str, Any]] = []

    for node in nodes:
        
        node_name = node["node"]
        try:
            vms = await proxmox_get(
                f"/nodes/{node_name}/qemu"
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Unable to query Proxmox node {node_name}",
            ) from exc

        for vm in vms:
            if vm.get("template") == 1:
                templates.append(
                    {
                        "node": node_name,
                        "vmid": vm["vmid"],
                        "name": vm.get("name"),
                        "status": vm.get("status"),
                        "template": True,
                    }
                )

    return templates

