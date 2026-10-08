import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserVMCreate(BaseModel):
    """Internal schema for creating a user VM."""

    model_config = ConfigDict(extra="forbid")

    node: str = Field(min_length=1, max_length=64)
    vmid: int = Field(gt=0)

    name: str = Field(min_length=1, max_length=255)
    os: str | None = Field(default=None, max_length=128)
    description: str | None = None


class UserVMRead(BaseModel):
    """Public view of a user VM."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    node: str
    vmid: int

    name: str
    os: str | None
    description: str | None

    user_id: uuid.UUID

    is_active: bool

    created_at: datetime
    last_synced_at: datetime | None