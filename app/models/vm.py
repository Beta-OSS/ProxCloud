import uuid
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.types import UTCDateTime, utcnow


class VMTemplate(Base):
    __tablename__ = "vm_templates"

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

    # Template metadata/display data
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    version: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    os: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Catalogue state
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
        nullable=False,
    )