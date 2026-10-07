import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, String, Uuid, false, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.types import UTCDateTime, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # Fernet-encrypted base32 secret. Never serialised to any response.
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Last accepted TOTP time-step; blocks replay of an already-used code.
    totp_last_used_step: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, onupdate=utcnow, server_default=func.now()
    )
