"""Application configuration — typed, validated, env-driven.

Reads (in order) the shared cross-project env file and a local .env, with
real environment variables taking precedence. Secrets never live in code.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Shared env used across all of the user's projects (see project memory).
_SHARED_ENV = r"C:\Users\User\Aiprojects\env\.env"


class Env(StrEnum):
    dev = "dev"
    staging = "staging"
    prod = "prod"


class DataSource(StrEnum):
    seed = "seed"
    evoltsoft = "evoltsoft"
    native = "native"


class AuthMode(StrEnum):
    dev = "dev"
    oauth = "oauth"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="UE_",
        env_file=(_SHARED_ENV, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # shared env holds many unrelated keys
    )

    env: Env = Env.dev
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    data_source: DataSource = DataSource.seed
    database_url: str = "sqlite:///./urbanenergy.db"

    sentry_dsn: str = ""
    auth_mode: AuthMode = AuthMode.dev

    # --- Evoltsoft (Urban Energy vendor) — Phase 1, removable. ---
    # All env vars use the UE_ prefix, e.g. UE_EVOLTSOFT_EMAIL.
    evoltsoft_base_url: str = "https://asia-south1-urbanenergy-prod.cloudfunctions.net"
    evoltsoft_firebase_api_key: str = ""
    evoltsoft_email: str = ""
    evoltsoft_password: str = ""
    evoltsoft_business_org_id: str = ""
    evoltsoft_timeout_s: float = 20.0

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def evoltsoft_has_credentials(self) -> bool:
        return bool(
            self.evoltsoft_email and self.evoltsoft_password and self.evoltsoft_firebase_api_key
        )

    @property
    def is_prod(self) -> bool:
        return self.env is Env.prod


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — import this everywhere instead of constructing Settings."""
    return Settings()
