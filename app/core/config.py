"""Strongly typed, environment-based configuration. No secrets live in source code. Deployment-specific values are supplied through the environment."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str

@lru_cache
def get_settings() -> Settings:
    return Settings()