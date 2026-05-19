"""Application settings via pydantic-settings.

Demo-mode zero-config boot
==========================

Every required field has a **demo default** so a fresh `git clone` boots
without any `.env` file or environment variables — point of this is that
the persona panel is visible from `npm run dev` + `uvicorn main:app`,
nothing else.

Hard rule: those demo defaults are only allowed when
`ENVIRONMENT == "dev"`. The `_refuse_demo_defaults_outside_dev`
validator refuses to construct `Settings` if any non-dev environment
ends up using the built-in `_DEMO_JWT_SECRET` (or any other sentinel
demo value).

See `docs/decision-log/demo-zero-config-boot.md` for the trade-off
rationale and the rollback path before any non-dev deployment.
"""
from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Demo sentinels (must stay constant — model_validator detects them) ---
# Length-32+ string so the existing `min_length=32` check still binds when
# someone overrides via env var with a too-short value.
_DEMO_JWT_SECRET = (
    "spp-demo-only-jwt-secret-rotate-before-any-prod-use-32+chars"
)
_DEMO_ORACLE_USER = "spp_demo_user"
_DEMO_ORACLE_PASSWORD = "spp_demo_password"
_DEMO_IDME_CLIENT_ID = "demo-client-id"
_DEMO_IDME_CLIENT_SECRET = "demo-client-secret"

_DEMO_SENTINELS: dict[str, str] = {
    "jwt_secret_key": _DEMO_JWT_SECRET,
    "oracle_user": _DEMO_ORACLE_USER,
    "oracle_password": _DEMO_ORACLE_PASSWORD,
    "idme_client_id": _DEMO_IDME_CLIENT_ID,
    "idme_client_secret": _DEMO_IDME_CLIENT_SECRET,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- ID.me OAuth ---
    # Demo defaults won't authenticate against real ID.me — set real
    # sandbox creds in `.env` to exercise the real flow.
    idme_client_id: str = Field(default=_DEMO_IDME_CLIENT_ID, min_length=1)
    idme_client_secret: str = Field(default=_DEMO_IDME_CLIENT_SECRET, min_length=1)
    idme_authorize_url: AnyHttpUrl = AnyHttpUrl("https://api.id.me/oauth/authorize")
    idme_token_url: AnyHttpUrl = AnyHttpUrl("https://api.id.me/oauth/token")
    idme_jwks_url: AnyHttpUrl = AnyHttpUrl("https://api.id.me/.well-known/jwks.json")
    idme_issuer: str = Field(default="https://api.id.me", min_length=1)
    idme_redirect_uri: AnyHttpUrl = AnyHttpUrl(
        "http://localhost:5173/verification/callback"
    )
    idme_scope: str = "openid email"

    # --- JWT session (AC-8 / ADR-004 / D-FD-01..07) ---
    # AC8-D11: min_length 32 binds even with the demo default in place.
    jwt_secret_key: str = Field(default=_DEMO_JWT_SECRET, min_length=32)
    jwt_ttl_hours: int = 4
    jwt_cookie_secure: bool = False

    # --- Oracle (AC-11 / NFR-17 thin mode) ---
    # Connection is attempted lazily; backend boots without Oracle running,
    # /api/vendors* will 503 until docker-compose stands Oracle XE up.
    oracle_host: str = "localhost"
    oracle_port: int = 1521
    oracle_service_name: str = "XEPDB1"
    oracle_user: str = Field(default=_DEMO_ORACLE_USER, min_length=1)
    oracle_password: str = Field(default=_DEMO_ORACLE_PASSWORD, min_length=1)

    # --- Environment ---
    environment: str = "dev"

    @model_validator(mode="after")
    def _refuse_demo_defaults_outside_dev(self) -> "Settings":
        """Hard guard: demo sentinels are allowed only in `dev`.

        Anywhere else (staging, prod, anything not "dev") must have
        real values supplied via env. This prevents the demo posture
        from accidentally promoting to a real deployment.
        """
        if self.environment == "dev":
            return self
        leaked = [
            field
            for field, sentinel in _DEMO_SENTINELS.items()
            if getattr(self, field) == sentinel
        ]
        if leaked:
            raise ValueError(
                f"ENVIRONMENT={self.environment!r} but demo sentinels are in use "
                f"for: {leaked}. Set real values via environment variables before "
                f"booting outside dev."
            )
        return self

    def is_using_demo_jwt_secret(self) -> bool:
        """True iff the built-in demo JWT secret is in force (dev only).

        `main.py` uses this for the startup warning banner.
        """
        return self.jwt_secret_key == _DEMO_JWT_SECRET


def get_settings() -> Settings:
    """FastAPI dependency. Re-instantiated per request — pydantic-settings
    is fast enough that we don't bother caching for the demo.

    Tests override this via `app.dependency_overrides[get_settings]`.
    """
    return Settings()
