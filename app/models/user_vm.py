import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.types import UTCDateTime, utcnow


class UserVM(Base):
    __tablename__ = "user_vms"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    # Proxmox identity
    node: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    vmid: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # VM metadata/display data
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    os: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Ownership
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )

    # VM state
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )