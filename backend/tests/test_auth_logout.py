"""Tests for POST /api/auth/logout — AC-9.

Maps to ratified decisions in `docs/decision-log/AC-9-session-lifecycle.md`:

* AC9-D1 — 204 No Content, idempotent (always returns 204).
* AC9-D2 — cookie-clearing attributes match issue-time (Path, SameSite,
  HttpOnly, Secure) so the browser actually clears the cookie.
* AC9-D3 — endpoint is unauthenticated by design.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt

from app.auth.jwt_session import COOKIE_NAME, JWT_AUDIENCE, JWT_ISSUER


SECRET = "test-jwt-secret-key-with-at-least-32-characters-of-entropy"


def _valid_token() -> str:
    now = datetime.now(timezone.utc)
    return jose_jwt.encode(
        {
            "sub": "42",
            "role": "ADMIN",
            "procurement_level": 3,
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=4)).timestamp()),
        },
        SECRET,
        algorithm="HS256",
    )


def _assert_clears_session_cookie(set_cookie: str) -> None:
    """Assert the Set-Cookie header looks like a cookie-clearing directive.

    Browser semantics: to clear a cookie the response must carry a
    Set-Cookie for the same name with `Max-Age=0` (or an expired
    `Expires=…`), and the Path / SameSite must match the issue-time
    cookie. AC9-D2.
    """
    assert f"{COOKIE_NAME}=" in set_cookie
    # Empty value or Max-Age=0 are both valid "clear" signals.
    assert "Max-Age=0" in set_cookie or 'Expires=Thu, 01 Jan 1970' in set_cookie
    assert "Path=/" in set_cookie
    assert "samesite=lax" in set_cookie.lower()
    assert "HttpOnly" in set_cookie


def test_logout_returns_204_and_clears_session_cookie(client):
    """Authenticated user logs out — gets 204 + Set-Cookie clearing `session`."""
    response = client.post(
        "/api/auth/logout",
        cookies={COOKIE_NAME: _valid_token()},
    )

    assert response.status_code == 204
    assert response.text == ""
    _assert_clears_session_cookie(response.headers["set-cookie"])


def test_logout_returns_204_without_any_cookie(client):
    """AC9-D1 + AC9-D3 — idempotent: no cookie present is still a 204."""
    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    # Still emits a clear so the browser flushes any stale cookie state.
    _assert_clears_session_cookie(response.headers["set-cookie"])


def test_logout_returns_204_with_invalid_cookie(client):
    """AC9-D1 — invalid token does NOT cause a 401; logout never fails."""
    response = client.post(
        "/api/auth/logout",
        cookies={COOKIE_NAME: "garbage.not.a.jwt"},
    )

    assert response.status_code == 204
    _assert_clears_session_cookie(response.headers["set-cookie"])


def test_logout_cookie_clear_attrs_match_issue_time(client):
    """AC9-D2 — Path, SameSite, HttpOnly on the clear must match the issue.

    If these don't match, the browser treats the clear as a separate
    cookie and silently ignores it. Regression-guard the constants.
    """
    response = client.post("/api/auth/logout")
    set_cookie = response.headers["set-cookie"]

    # The same attributes that `issue_session_cookie` writes (other than
    # Max-Age which is 0 here vs ttl_hours*3600 there). Secure is False
    # in tests (JWT_COOKIE_SECURE=false).
    assert "Path=/" in set_cookie
    assert "samesite=lax" in set_cookie.lower()
    assert "HttpOnly" in set_cookie
    assert "Secure" not in set_cookie
