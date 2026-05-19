"""Tests for the dev-only persona login — `app.api.dev_auth`.

Decisions traced to `docs/decision-log/DEV-AUTH-persona-picker.md` and
ADR-014. Covers AC #DEV3, DEV4, and the request-time half of DEV2.

NOTE on the DEV2 boot-time gate: `main.py` only `include_router(dev_auth)`
when `settings.environment == "dev"`. That branch is verified by
inspection — testing it requires re-importing `main` with a different
env var, which fights the pytest fixture model. The defence-in-depth
**request-time** check (returns 404 unless dev) IS testable here via
`get_settings` dependency override, and we test that thoroughly below.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_session_issuer
from app.core.config import Settings, get_settings


@pytest.fixture
def mock_session_issuer():
    """Capture-call mock for `issue_session_cookie`. Mirrors the pattern
    in test_auth_callback.py so dev_auth and callback are testing the
    same surface.
    """
    class Holder:
        calls: list[dict[str, Any]] = []

        def __call__(self, response, *, staff_id, role) -> None:
            self.calls.append(
                {"staff_id": staff_id, "role": role}
            )
            response.set_cookie(key="session", value="test-jwt", httponly=True)

    return Holder()


@pytest.fixture
def dev_client(mock_session_issuer):
    """TestClient with the session issuer mocked. Default env = "dev"."""
    from main import app

    app.dependency_overrides[get_session_issuer] = lambda: mock_session_issuer
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def _prod_settings_override():
    """Build a Settings instance with environment=prod for the request-time
    gate test. Reuses real env vars from conftest for the required fields.
    """
    import os

    return Settings(
        idme_client_id=os.environ["IDME_CLIENT_ID"],
        idme_client_secret=os.environ["IDME_CLIENT_SECRET"],
        idme_authorize_url=os.environ["IDME_AUTHORIZE_URL"],
        idme_token_url=os.environ["IDME_TOKEN_URL"],
        idme_jwks_url=os.environ["IDME_JWKS_URL"],
        idme_issuer=os.environ["IDME_ISSUER"],
        idme_redirect_uri=os.environ["IDME_REDIRECT_URI"],
        jwt_secret_key=os.environ["JWT_SECRET_KEY"],
        environment="prod",
    )


# ---------------------------------------------------------------------------
# DEV3 — granted personas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "persona,expected_claims",
    [
        # ADR-015: 3 business roles. staff_ids align with the AC-12 seed
        # (DATA_MODEL.md §8) so future RBAC introspection lines up.
        ("procurement_supervisor", {"staff_id": 1, "role": "PROCUREMENT_SUPERVISOR"}),
        ("regular_staff",          {"staff_id": 6, "role": "REGULAR_STAFF"}),
    ],
)
def test_granted_persona_returns_200_and_mints_session(
    dev_client, mock_session_issuer, persona, expected_claims
):
    response = dev_client.post("/api/auth/dev-login", json={"persona": persona})

    assert response.status_code == 200
    assert response.json() == expected_claims
    # Session issuer was called with the same fields — single source of truth.
    assert mock_session_issuer.calls == [expected_claims]
    # Marker cookie from the mock confirms cookie path was exercised.
    assert response.cookies.get("session") == "test-jwt"


# ---------------------------------------------------------------------------
# DEV3 — denied personas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "persona,expected_reason,expected_detail_substring",
    [
        # ADR-015: NON_STAFF replaces the old LEVEL_ZERO denial.
        ("non_staff",      "NON_STAFF",      "portal access"),
        ("not_registered", "NOT_REGISTERED", "identity could not be verified"),
    ],
)
def test_denied_persona_returns_403_with_x_auth_reason(
    dev_client, persona, expected_reason, expected_detail_substring
):
    response = dev_client.post("/api/auth/dev-login", json={"persona": persona})

    assert response.status_code == 403
    assert response.headers["X-Auth-Reason"] == expected_reason
    assert expected_detail_substring in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DEV8 — unknown persona is a Pydantic validation error
# ---------------------------------------------------------------------------

def test_unknown_persona_returns_422(dev_client):
    response = dev_client.post(
        "/api/auth/dev-login", json={"persona": "superuser"}
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DEV4 — availability probe
# ---------------------------------------------------------------------------

def test_availability_probe_returns_200_in_dev(dev_client):
    response = dev_client.get("/api/auth/dev-login/available")
    assert response.status_code == 200
    assert response.json() == {"available": True}


# ---------------------------------------------------------------------------
# DEV2 (request-time gate) — env=prod → 404 on both routes
# ---------------------------------------------------------------------------

def test_dev_login_returns_404_when_environment_is_not_dev(dev_client):
    """Request-time half of the DEV2 gate.

    Even if the router is somehow registered (as it is in this test, since
    we set ENVIRONMENT=dev at boot), the handler MUST re-validate at
    request time and refuse with 404 — indistinguishable from "endpoint
    does not exist".
    """
    from main import app

    app.dependency_overrides[get_settings] = _prod_settings_override

    try:
        response = dev_client.post(
            "/api/auth/dev-login", json={"persona": "procurement_supervisor"}
        )
        assert response.status_code == 404
    finally:
        # Other overrides set by dev_client fixture cleanup will handle this,
        # but be explicit for clarity.
        app.dependency_overrides.pop(get_settings, None)


def test_availability_probe_returns_404_when_environment_is_not_dev(dev_client):
    from main import app

    app.dependency_overrides[get_settings] = _prod_settings_override

    try:
        response = dev_client.get("/api/auth/dev-login/available")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_settings, None)
