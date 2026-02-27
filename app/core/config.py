"""Application configuration via pydantic-settings.

Settings are loaded from environment variables and an optional .env file.
Access settings via the cached :func:`get_settings` function — do **not**
instantiate :class:`Settings` directly in application code.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="Financial PDF Converter Project", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Runtime environment (development, staging, production)")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    api_prefix: str = Field(default="/api", description="URL prefix for all API routes")

    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8123"],
        description="List of origins allowed for CORS requests",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton.

    The result is memoised by :func:`functools.lru_cache`; call
    ``get_settings.cache_clear()`` in tests to force re-evaluation.
    """
    return Settings()
