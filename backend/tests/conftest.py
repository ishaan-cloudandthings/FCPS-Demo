"""Shared pytest fixtures.

We don't load a real `.env` file in tests — env vars are set per-test via
monkeypatch so each test is hermetic. The `FastAPI app.dependency_overrides`
mechanism is used to inject test-scoped settings + state caches.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide the required IDME_* env vars for every test."""
    monkeypatch.setenv("IDME_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("IDME_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("IDME_AUTHORIZE_URL", "https://api.id.me/oauth/authorize")
    monkeypatch.setenv("IDME_TOKEN_URL", "https://api.id.me/oauth/token")
    monkeypatch.setenv("IDME_JWKS_URL", "https://api.id.me/.well-known/jwks.json")
    monkeypatch.setenv("IDME_ISSUER", "https://api.id.me")
    monkeypatch.setenv("IDME_REDIRECT_URI", "http://localhost/verification/callback")
    monkeypatch.setenv("IDME_SCOPE", "openid email")


@pytest.fixture
def fresh_state_cache():
    """A fresh OAuthStateCache for each test that needs one."""
    from app.auth.state_cache import OAuthStateCache

    return OAuthStateCache()


@pytest.fixture
def client(fresh_state_cache):
    """TestClient with the in-process state cache replaced per-test."""
    # Import here so the env fixture runs before app/main import-time code.
    from app.api.auth import get_state_cache
    from main import app

    app.dependency_overrides[get_state_cache] = lambda: fresh_state_cache
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
