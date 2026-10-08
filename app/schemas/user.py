import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,31}$")
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


def validate_new_password(password: str, username: str | None = None) -> str | None:
    """Returns an error message, or None if the password is acceptable."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Password must be at most {MAX_PASSWORD_LENGTH} characters."
    if username and password.lower() == username.lower():
        return "Password must not be the same as the username."
    return None


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    email: EmailStr
    password: str = Field(repr=False)
    is_admin: bool = False

    @field_validator("username", "email", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        v = v.lower()
        if not USERNAME_RE.fullmatch(v):
            raise ValueError("Username must be 3-32 characters: letters, digits, '.', '_' or '-'.")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        problem = validate_new_password(v)
        if problem:
            raise ValueError(problem)
        return v


class UserRead(BaseModel):
    """Public view of a user. Deliberately has no password_hash or TOTP fields beyond the flag."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_admin: bool
    totp_enabled: bool
    created_at: datetime


class MeRead(UserRead):
    csrf_token: str
