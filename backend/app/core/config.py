"""Application settings via pydantic-settings.

Per AC6-D8: required env vars are validated at startup; missing vars cause
the app to fail fast rather than at first request.

Each story adds the fields it needs. AC-6 needs only the ID.me OAuth fields
listed below. Future stories (AC-7, AC-8) will extend the model.
"""
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- ID.me OAuth ---
    # AC6-D8 + AC7 (FD §6.1 D-FD-09..12): explicit env vars, no derivation.
    # AC6-D7: redirect_uri must match exactly what's registered in the
    # ID.me developer console (2026-05-05 IT Lead warning).
    idme_client_id: str = Field(min_length=1)
    idme_client_secret: str = Field(min_length=1)  # AC-7: token exchange
    idme_authorize_url: AnyHttpUrl
    idme_token_url: AnyHttpUrl                     # AC-7: code → id_token
    idme_jwks_url: AnyHttpUrl                      # AC-7: ID-token signature
    idme_issuer: str = Field(min_length=1)         # AC-7: expected `iss` claim
    idme_redirect_uri: AnyHttpUrl
    idme_scope: str = "openid email"

    # --- JWT session (AC-8 / ADR-004 / D-FD-01..07) ---
    # AC8-D11: min_length 32 enforces HS256 security floor (256-bit / 32-byte key).
    jwt_secret_key: str = Field(min_length=32)
    jwt_ttl_hours: int = 4                # D-FD-03 default
    jwt_cookie_secure: bool = False       # D-FD-04 / ADR-008 — env-driven

    # --- Oracle (AC-11 / NFR-17 thin mode) ---
    # AC11-D3: credentials required at startup, no defaults — fails fast
    # if .env is incomplete rather than at first query.
    oracle_host: str = Field(min_length=1)
    oracle_port: int = 1521
    oracle_service_name: str = "XE"
    oracle_user: str = Field(min_length=1)
    oracle_password: str = Field(min_length=1)

    # --- Environment ---
    environment: str = "dev"


def get_settings() -> Settings:
    """FastAPI dependency. Re-instantiated per request — pydantic-settings
    is fast enough that we don't bother caching for the demo.

    Tests override this via `app.dependency_overrides[get_settings]`.
    """
    return Settings()
