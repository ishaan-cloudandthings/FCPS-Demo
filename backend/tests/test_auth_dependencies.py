"""Tests for `app.auth.dependencies` — AC-8.

Covers AC8-D14's plan for the two surviving Depends factories
(per ADR-015, `require_level` was removed along with `PROCUREMENT_LEVEL`):

* require_authenticated     — success, missing cookie, invalid token
* require_role              — role match + role mismatch (X-Auth-Reason)
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from app.auth.dependencies import (
    require_authenticated,
    require_role,
)
from app.auth.jwt_session import (
    COOKIE_NAME,
    JWT_AUDIENCE,
    JWT_ISSUER,
    SessionClaims,
)


SECRET = "test-jwt-secret-key-with-at-least-32-characters-of-entropy"


def _make_token(secret: str = SECRET, **overrides) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "42",
        "role": "PROCUREMENT_SUPERVISOR",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=4)).timestamp()),
    }
    claims.update(overrides)
    return jose_jwt.encode(claims, secret, algorithm="HS256")


@pytest.fixture
def app_with_routes() -> FastAPI:
    """A throw-away FastAPI app wiring each dependency to a test endpoint."""
    app = FastAPI()

    @app.get("/auth/me")
    def me(claims: SessionClaims = Depends(require_authenticated)):
        return {
            "staff_id": claims.staff_id,
            "role": claims.role,
        }

    @app.get("/supervisor-only")
    def supervisor_only(
        claims: SessionClaims = Depends(require_role("PROCUREMENT_SUPERVISOR")),
    ):
        return {"ok": True, "staff_id": claims.staff_id}

    return app


@pytest.fixture
def client(app_with_routes) -> TestClient:
    return TestClient(app_with_routes)


# ---------------------------------------------------------------------------
# require_authenticated
# ---------------------------------------------------------------------------


def test_require_authenticated_success(client: TestClient):
    token = _make_token()
    response = client.get("/auth/me", cookies={COOKIE_NAME: token})

    assert response.status_code == 200
    assert response.json() == {
        "staff_id": 42,
        "role": "PROCUREMENT_SUPERVISOR",
    }


def test_require_authenticated_missing_cookie_returns_401(client: TestClient):
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Session invalid or expired."}


def test_require_authenticated_invalid_token_returns_401(client: TestClient):
    response = client.get(
        "/auth/me", cookies={COOKIE_NAME: "not.a.real.jwt"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Session invalid or expired."}


def test_require_authenticated_rejects_legacy_role(client: TestClient):
    """ADR-015 — `ADMIN` / `STAFF` are not in the allowlist any more."""
    token = _make_token(role="ADMIN")
    response = client.get("/auth/me", cookies={COOKIE_NAME: token})
    assert response.status_code == 401  # caught by jwt_session's _VALID_ROLES


# ---------------------------------------------------------------------------
# require_role
# ---------------------------------------------------------------------------


def test_require_role_supervisor_passes_for_supervisor(client: TestClient):
    token = _make_token(role="PROCUREMENT_SUPERVISOR")
    response = client.get("/supervisor-only", cookies={COOKIE_NAME: token})
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_require_role_supervisor_forbidden_for_regular_staff(client: TestClient):
    token = _make_token(role="REGULAR_STAFF")
    response = client.get("/supervisor-only", cookies={COOKIE_NAME: token})

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to view this resource."
    }
    assert response.headers.get("X-Auth-Reason") == "ROLE_FORBIDDEN"
