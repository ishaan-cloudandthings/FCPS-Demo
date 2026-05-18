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

    # --- Environment ---
    environment: str = "dev"


def get_settings() -> Settings:
    """FastAPI dependency. Re-instantiated per request — pydantic-settings
    is fast enough that we don't bother caching for the demo.

    Tests override this via `app.dependency_overrides[get_settings]`.
    """
    return Settings()
