"""Tests for GET /api/auth/me — AC-9.

Maps to ratified decisions in `docs/decision-log/AC-9-session-lifecycle.md`:

* AC9-D4 — response shape includes `staff_id` alongside `role` +
  `procurement_level` (SPA hydration target per FD §7.2).
* AC9-D5 — failure mode reuses `require_authenticated` — same 401 +
  `"Session invalid or expired."` body envelope.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt

from app.auth.jwt_session import COOKIE_NAME, JWT_AUDIENCE, JWT_ISSUER


SECRET = "test-jwt-secret-key-with-at-least-32-characters-of-entropy"


def _token(**overrides) -> str:
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
    return jose_jwt.encode(claims, SECRET, algorithm="HS256")


def test_me_returns_session_claims_when_authenticated(client):
    """AC9-D4 — 200 with {role, procurement_level, staff_id}."""
    response = client.get("/api/auth/me", cookies={COOKIE_NAME: _token()})

    assert response.status_code == 200
    assert response.json() == {
        "role": "PROCUREMENT_SUPERVISOR",
        "staff_id": 42,                          # AC9-D4: int, not the str sub
    }


def test_me_returns_401_when_no_cookie(client):
    """AC9-D5 — same envelope as require_authenticated."""
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Session invalid or expired."}


def test_me_returns_401_when_token_expired(client):
    """AC9-D5 — expiry triggers the SPA's session-expired redirect (FD §7.2)."""
    past = datetime.now(timezone.utc) - timedelta(hours=5)
    expired = _token(
        iat=int(past.timestamp()),
        exp=int((past + timedelta(hours=4)).timestamp()),
    )

    response = client.get("/api/auth/me", cookies={COOKIE_NAME: expired})

    assert response.status_code == 401
    assert response.json() == {"detail": "Session invalid or expired."}
