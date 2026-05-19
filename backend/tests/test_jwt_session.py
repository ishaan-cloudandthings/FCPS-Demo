"""Tests for `app.auth.jwt_session` — AC-8.

Covers AC8-D14's plan:
* issue-cookie attributes (HttpOnly, SameSite=Lax, Path=/, Secure-from-env)
* claims allowlist (AC8-D12 — no `employee_id`, exact set)
* verify happy path (round-trip)
* expired / wrong-sig / wrong-alg / wrong-iss / wrong-aud / missing-claims / malformed
* bad role / bad procurement_level types
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Response
from jose import jwt as jose_jwt

from app.auth.jwt_session import (
    COOKIE_NAME,
    JWT_AUDIENCE,
    JWT_ISSUER,
    SessionClaims,
    SessionInvalid,
    issue_session_cookie,
    verify_session_jwt,
)


SECRET = "unit-test-jwt-secret-key-32-bytes-of-entropy-please"
OTHER_SECRET = "different-jwt-secret-key-also-32-bytes-of-entropy!"


# ---------------------------------------------------------------------------
# issue_session_cookie
# ---------------------------------------------------------------------------


def _issue(secure: bool = False) -> Response:
    response = Response()
    issue_session_cookie(
        response,
        staff_id=42,
        role="PROCUREMENT_SUPERVISOR",
        secret_key=SECRET,
        ttl_hours=4,
        secure=secure,
    )
    return response


def test_issue_cookie_sets_session_cookie_with_correct_attributes():
    response = _issue(secure=False)
    set_cookie = response.headers["set-cookie"]

    assert f"{COOKIE_NAME}=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "samesite=lax" in set_cookie.lower()
    assert "Path=/" in set_cookie
    # secure=False → "Secure" attribute must not appear.
    assert "Secure" not in set_cookie
    # max_age = 4 * 3600 = 14400.
    assert "Max-Age=14400" in set_cookie


def test_issue_cookie_honours_secure_flag_when_https():
    response = _issue(secure=True)
    assert "Secure" in response.headers["set-cookie"]


def test_issue_cookie_claims_allowlist_excludes_employee_id():
    """AC8-D12: a freshly issued token decodes to EXACTLY these claims."""
    response = _issue()
    # Extract the raw cookie value.
    set_cookie = response.headers["set-cookie"]
    token = set_cookie.split(f"{COOKIE_NAME}=", 1)[1].split(";", 1)[0]

    claims = jose_jwt.decode(
        token,
        SECRET,
        algorithms=["HS256"],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
    )

    # ADR-015: procurement_level is no longer part of the claim set.
    assert set(claims.keys()) == {
        "sub",
        "role",
        "iss",
        "aud",
        "iat",
        "exp",
    }
    assert "employee_id" not in claims
    assert "procurement_level" not in claims
    assert claims["sub"] == "42"               # AC8-D5: string
    assert claims["role"] == "PROCUREMENT_SUPERVISOR"
    assert claims["iss"] == JWT_ISSUER
    assert claims["aud"] == JWT_AUDIENCE
    # exp - iat ≈ 4h, within a few seconds of skew.
    assert 4 * 3600 - 5 <= claims["exp"] - claims["iat"] <= 4 * 3600 + 5


# ---------------------------------------------------------------------------
# verify_session_jwt — happy + failure modes
# ---------------------------------------------------------------------------


def _make_token(secret: str = SECRET, alg: str = "HS256", **overrides) -> str:
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
    return jose_jwt.encode(claims, secret, algorithm=alg)


def test_verify_round_trip_returns_session_claims():
    response = _issue()
    token = response.headers["set-cookie"].split(f"{COOKIE_NAME}=", 1)[1].split(";", 1)[0]

    result = verify_session_jwt(token, secret_key=SECRET)

    assert isinstance(result, SessionClaims)
    assert result.staff_id == 42                # coerced back to int
    assert result.role == "PROCUREMENT_SUPERVISOR"


def test_verify_rejects_expired_token():
    past = datetime.now(timezone.utc) - timedelta(hours=5)
    token = _make_token(
        iat=int(past.timestamp()),
        exp=int((past + timedelta(hours=4)).timestamp()),
    )
    with pytest.raises(SessionInvalid):
        verify_session_jwt(token, secret_key=SECRET)


def test_verify_rejects_wrong_signature():
    token = _make_token(secret=OTHER_SECRET)
    with pytest.raises(SessionInvalid):
        verify_session_jwt(token, secret_key=SECRET)


def test_verify_rejects_wrong_algorithm():
    """AC8-D10 — algorithm-confusion defence.

    python-jose validates the alg against the `algorithms=` allowlist; any
    algorithm other than HS256 must fail. We use 'none' to assert the
    "trust me bro" attack is rejected.
    """
    # Build a token with alg=none (no signature) — must be refused.
    # We can't go through jose.encode(algorithm="none") cleanly, so build
    # the JWT structure manually.
    import base64
    import json

    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({
            "sub": "42",
            "role": "PROCUREMENT_SUPERVISOR",
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=4)).timestamp()),
        }).encode()
    ).rstrip(b"=").decode()
    token = f"{header}.{payload}."  # no signature

    with pytest.raises(SessionInvalid):
        verify_session_jwt(token, secret_key=SECRET)


def test_verify_rejects_wrong_issuer():
    token = _make_token(iss="evil-portal")
    with pytest.raises(SessionInvalid):
        verify_session_jwt(token, secret_key=SECRET)


def test_verify_rejects_wrong_audience():
    token = _make_token(aud="evil-portal-web")
    with pytest.raises(SessionInvalid):
        verify_session_jwt(token, secret_key=SECRET)


def test_verify_rejects_token_missing_required_claim():
    # python-jose accepts arbitrary additional/missing app-level claims;
    # we enforce the app-shape ourselves.
    now = datetime.now(timezone.utc)
    claims = {
        "sub": "42",
        # "role" missing
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=4)).timestamp()),
    }
    token = jose_jwt.encode(claims, SECRET, algorithm="HS256")
    with pytest.raises(SessionInvalid):
        verify_session_jwt(token, secret_key=SECRET)


def test_verify_rejects_malformed_token():
    with pytest.raises(SessionInvalid):
        verify_session_jwt("this.is.not-a-real-jwt", secret_key=SECRET)


def test_verify_rejects_invalid_role_value():
    token = _make_token(role="SUPER_ROOT")
    with pytest.raises(SessionInvalid):
        verify_session_jwt(token, secret_key=SECRET)
