"""Strongly typed, environment-based configuration. No secrets live in source code."""
from functools import lru_cache

from cryptography.fernet import Fernet
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Private Cloud Portal"
    enable_api_docs: bool = False

    database_url: str
    session_secret: SecretStr
    totp_encryption_key: SecretStr
    totp_issuer: str = "ProxCloud Portal"

    cookie_secure: bool = True
    session_cookie_name: str = "portal_session"
    session_idle_minutes: int = 30
    session_max_hours: int = 12
    pending_2fa_minutes: int = 5
    twofa_max_attempts: int = 5

    login_max_failures_per_user: int = 10
    login_max_failures_per_ip: int = 20
    login_window_minutes: int = 15

    argon2_time_cost: int = 3
    argon2_memory_cost_kib: int = 65536
    argon2_parallelism: int = 4

    @field_validator("session_secret")
    @classmethod
    def _check_session_secret(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("SESSION_SECRET must be at least 32 characters")
        return v

    @field_validator("totp_encryption_key")
    @classmethod
    def _check_totp_key(cls, v: SecretStr) -> SecretStr:
        try:
            Fernet(v.get_secret_value().encode())
        except Exception as exc:  # noqa: BLE001
            raise ValueError("TOTP_ENCRYPTION_KEY must be a valid Fernet key") from exc
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
