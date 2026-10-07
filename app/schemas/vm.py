import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VMTemplateCreate(BaseModel):
    """Internal schema for creating a VM template catalogue entry."""

    model_config = ConfigDict(extra="forbid")

    node: str = Field(min_length=1, max_length=64)
    vmid: int = Field(gt=0)

    name: str = Field(min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=64)
    os: str | None = Field(default=None, max_length=128)
    description: str | None = None

    is_approved: bool = False


class VMTemplateRead(BaseModel):
    """Public view of a VM template."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    node: str
    vmid: int

    name: str
    version: str | None
    os: str | None
    description: str | None

    is_approved: bool

    created_at: datetime
    updated_at: datetime