"""Tests for POST /api/auth/callback (AC-7).

Each test maps to a ratified decision in
`docs/decision-log/AC-7-callback.md` or an FD §6.1 D-FD-* decision.

Test-side bootstrap:

* We generate a per-session RSA keypair and turn the public key into a
  JWK. The mock JWKS endpoint serves that single key.
* We craft ID tokens at test time, signing them with the private key.
  This lets us test happy paths and every malformed/invalid variant
  without coupling to ID.me.
* `respx` intercepts httpx calls to ID.me's token and JWKS endpoints.
* The AC-8 + AC-13 stubs are overridden via FastAPI `dependency_overrides`
  to capture the call (success path) or simulate denial (failure paths).
"""
from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwk as jose_jwk
from jose import jwt as jose_jwt

from app.auth.jwks_cache import JWKSCache
from app.services.access_service import AccessDecision


# -----------------------------------------------------------------------------
# Keypair + JWK fixtures (session-scoped — generation is the slow part)
# -----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def rsa_keypair() -> dict[str, Any]:
    """Generate an RSA-2048 keypair once per session.

    Returns a dict with:
      - private_pem: bytes — PEM-encoded private key for signing tokens
      - public_jwk:  dict   — JWK dict to serve from the mock JWKS endpoint
      - kid:         str    — the key id (we control it)
    """
    kid = "test-key-1"
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    # Derive the public JWK using python-jose.
    public_jwk = jose_jwk.RSAKey(
        algorithm="RS256",
        key=private_pem.decode(),
    ).public_key().to_dict()
    # python-jose returns bytes for n/e — coerce to str for JSON-serialisation.
    for k, v in list(public_jwk.items()):
        if isinstance(v, bytes):
            public_jwk[k] = v.decode()
    public_jwk["kid"] = kid
    public_jwk["use"] = "sig"
    public_jwk["alg"] = "RS256"
    return {"private_pem": private_pem.decode(), "public_jwk": public_jwk, "kid": kid}


def _sign_token(
    rsa_keypair: dict[str, Any],
    *,
    sub: str = "FCPS-001",
    iss: str = "https://api.id.me",
    aud: str = "test-client-id",
    exp_offset: int = 300,
    iat_offset: int = 0,
    alg: str = "RS256",
    kid: str | None = None,
) -> str:
    """Sign and return an ID token with the given claims."""
    now = int(time.time())
    headers = {"kid": kid if kid is not None else rsa_keypair["kid"]}
    return jose_jwt.encode(
        claims={
            "sub": sub,
            "iss": iss,
            "aud": aud,
            "iat": now + iat_offset,
            "exp": now + exp_offset,
        },
        key=rsa_keypair["private_pem"],
        algorithm=alg,
        headers=headers,
    )


# -----------------------------------------------------------------------------
# App + dependency-override fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def fresh_jwks_cache(rsa_keypair) -> JWKSCache:
    """A JWKSCache that, on its first httpx GET, gets our test JWK.

    We don't pre-seed the cache — that would mask bugs in the lazy-fetch
    path. Instead, the `respx_mock` fixture below mocks the JWKS endpoint
    URL so the cache's real fetch logic runs.
    """
    return JWKSCache(jwks_url="https://api.id.me/.well-known/jwks.json")


@pytest.fixture
def mock_access_decision():
    """A captured-call mock for the AC-13 access_service stub.

    Returns a small holder so tests can read what `sub` was passed and
    change the returned decision per test:

        mock_access_decision.set(AccessDecision(granted=True, ...))
        ... call endpoint ...
        assert mock_access_decision.received_sub == "FCPS-001"
    """
    class Holder:
        decision = AccessDecision(
            granted=True,
            reason="GRANTED",
            staff_id=42,
            role="STAFF",
            procurement_level=2,
        )
        received_sub: str | None = None

        def set(self, decision: AccessDecision) -> None:
            self.decision = decision

        def __call__(self, sub: str) -> AccessDecision:
            self.received_sub = sub
            return self.decision

    return Holder()


@pytest.fixture
def mock_session_issuer():
    """A captured-call mock for the AC-8 jwt_session stub."""
    class Holder:
        calls: list[dict[str, Any]] = []

        def __call__(self, response, *, staff_id, role, procurement_level) -> None:
            self.calls.append(
                {
                    "staff_id": staff_id,
                    "role": role,
                    "procurement_level": procurement_level,
                }
            )
            # Set a marker cookie so callers can verify the issuer was invoked.
            response.set_cookie(key="session", value="test-jwt", httponly=True)

    return Holder()


@pytest.fixture
def callback_client(
    fresh_state_cache,
    fresh_jwks_cache,
    mock_access_decision,
    mock_session_issuer,
):
    """TestClient with state cache, JWKS cache, access-decider, and
    session-issuer all overridable.

    Tests modify `mock_access_decision.decision` to simulate denials
    before issuing the request.
    """
    from app.api.auth import (
        get_access_decider,
        get_jwks_cache,
        get_session_issuer,
        get_state_cache,
    )
    from main import app

    app.dependency_overrides[get_state_cache] = lambda: fresh_state_cache
    app.dependency_overrides[get_jwks_cache] = lambda: fresh_jwks_cache
    app.dependency_overrides[get_access_decider] = lambda: mock_access_decision
    app.dependency_overrides[get_session_issuer] = lambda: mock_session_issuer
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def good_state(fresh_state_cache) -> str:
    """Issue a single state token from the test cache."""
    return fresh_state_cache.issue()


def _mock_idme_token(respx_mock, id_token: str) -> None:
    """Make /oauth/token return a body containing the given id_token."""
    respx_mock.post("https://api.id.me/oauth/token").mock(
        return_value=httpx.Response(200, json={"id_token": id_token, "token_type": "Bearer"})
    )


def _mock_idme_jwks(respx_mock, public_jwk: dict) -> None:
    """Serve the test public JWK from the JWKS endpoint."""
    respx_mock.get("https://api.id.me/.well-known/jwks.json").mock(
        return_value=httpx.Response(200, json={"keys": [public_jwk]})
    )


# -----------------------------------------------------------------------------
# Happy path
# -----------------------------------------------------------------------------

@respx.mock
def test_callback_happy_path_returns_200(
    callback_client, good_state, rsa_keypair, mock_access_decision, mock_session_issuer
):
    """D-FD-09..12 — full flow ends in 200 with role + level + session cookie."""
    _mock_idme_token(respx, _sign_token(rsa_keypair))
    _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "test-code", "state": good_state},
    )

    assert response.status_code == 200
    body = response.json()
    # AC9-D4: callback response now also includes staff_id.
    assert body == {"role": "STAFF", "procurement_level": 2, "staff_id": 42}
    # AC7-D11: access_service receives `sub`, not `staff_id`.
    assert mock_access_decision.received_sub == "FCPS-001"
    # AC-8 stub was invoked with the GRANTED fields.
    assert mock_session_issuer.calls == [
        {"staff_id": 42, "role": "STAFF", "procurement_level": 2}
    ]
    # Session cookie set by the mock issuer.
    assert response.cookies.get("session") == "test-jwt"


# -----------------------------------------------------------------------------
# State validation — AC7-D6 step 1
# -----------------------------------------------------------------------------

def test_callback_unknown_state_returns_400(callback_client):
    """Unknown `state` → 400 with the canonical body."""
    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "test-code", "state": "never-issued"},
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Authentication request expired. Please verify again."
    }


def test_callback_state_one_shot_replay_returns_400(
    callback_client, good_state, rsa_keypair
):
    """State replay is rejected (AC6-D5 + D-FD-09)."""
    with respx.mock:
        _mock_idme_token(respx, _sign_token(rsa_keypair))
        _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

        # First use succeeds.
        ok = callback_client.post(
            "/api/auth/callback",
            json={"code": "c1", "state": good_state},
        )
        assert ok.status_code == 200

        # Second use rejected.
        replay = callback_client.post(
            "/api/auth/callback",
            json={"code": "c2", "state": good_state},
        )
        assert replay.status_code == 400


# -----------------------------------------------------------------------------
# ID.me reachability — D-FD-10
# -----------------------------------------------------------------------------

@respx.mock
def test_callback_idme_5xx_returns_502(callback_client, good_state):
    """ID.me returning 5xx → 502 with the canonical body."""
    respx.post("https://api.id.me/oauth/token").mock(
        return_value=httpx.Response(503, json={"error": "service unavailable"})
    )
    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 502
    assert response.json() == {"detail": "Identity provider unreachable."}


@respx.mock
def test_callback_idme_timeout_returns_502(callback_client, good_state):
    """ID.me hanging long enough to time out → 502."""
    respx.post("https://api.id.me/oauth/token").mock(
        side_effect=httpx.ConnectTimeout("simulated timeout")
    )
    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 502


# -----------------------------------------------------------------------------
# ID token validation — D-FD-11 / AC7-D4 / AC7-D5
# -----------------------------------------------------------------------------

@respx.mock
def test_callback_expired_id_token_returns_401(callback_client, good_state, rsa_keypair):
    """exp in the past (beyond skew) → 401."""
    expired_token = _sign_token(rsa_keypair, exp_offset=-3600, iat_offset=-3700)
    _mock_idme_token(respx, expired_token)
    _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Identity verification failed."}


@respx.mock
def test_callback_wrong_audience_returns_401(callback_client, good_state, rsa_keypair):
    """aud mismatch → 401."""
    token = _sign_token(rsa_keypair, aud="some-other-client")
    _mock_idme_token(respx, token)
    _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 401


@respx.mock
def test_callback_wrong_issuer_returns_401(callback_client, good_state, rsa_keypair):
    """iss mismatch → 401."""
    token = _sign_token(rsa_keypair, iss="https://attacker.example.com")
    _mock_idme_token(respx, token)
    _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 401


@respx.mock
def test_callback_unknown_kid_returns_401(callback_client, good_state, rsa_keypair):
    """A token signed with a key whose kid isn't in JWKS → 401."""
    token = _sign_token(rsa_keypair, kid="not-in-jwks")
    _mock_idme_token(respx, token)
    _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 401


@respx.mock
def test_callback_jwks_unreachable_returns_401(callback_client, good_state, rsa_keypair):
    """JWKS endpoint fails → 401 (never silently degrade — AC7-D3)."""
    _mock_idme_token(respx, _sign_token(rsa_keypair))
    respx.get("https://api.id.me/.well-known/jwks.json").mock(
        return_value=httpx.Response(503)
    )
    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 401


@respx.mock
def test_callback_missing_id_token_returns_401(callback_client, good_state):
    """ID.me returns 200 with no id_token → 401 (treat as auth failure)."""
    respx.post("https://api.id.me/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "only"})
    )
    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 401


# -----------------------------------------------------------------------------
# Access decisions — D-FD-12 / AC7-D9
# -----------------------------------------------------------------------------

@respx.mock
def test_callback_level_zero_returns_403_with_header(
    callback_client, good_state, rsa_keypair, mock_access_decision
):
    """LEVEL_ZERO → 403 + X-Auth-Reason: LEVEL_ZERO + the LEVEL_ZERO copy."""
    mock_access_decision.set(
        AccessDecision(granted=False, reason="LEVEL_ZERO")
    )
    _mock_idme_token(respx, _sign_token(rsa_keypair))
    _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 403
    assert response.headers["X-Auth-Reason"] == "LEVEL_ZERO"
    assert response.json()["detail"] == (
        "Access denied. Your account does not have procurement clearance."
    )


@pytest.mark.parametrize("reason", ["NOT_FOUND", "NOT_VERIFIED", "INACTIVE"])
@respx.mock
def test_callback_unregistered_collapses_to_not_registered(
    callback_client, good_state, rsa_keypair, mock_access_decision, reason
):
    """NOT_FOUND/NOT_VERIFIED/INACTIVE all collapse to X-Auth-Reason: NOT_REGISTERED."""
    mock_access_decision.set(AccessDecision(granted=False, reason=reason))
    _mock_idme_token(respx, _sign_token(rsa_keypair))
    _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

    response = callback_client.post(
        "/api/auth/callback",
        json={"code": "c", "state": good_state},
    )
    assert response.status_code == 403
    assert response.headers["X-Auth-Reason"] == "NOT_REGISTERED"
    assert "not registered in the FCPS procurement system" in response.json()["detail"]


# -----------------------------------------------------------------------------
# Request-body validation — AC7-D12
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "body",
    [
        {},
        {"code": ""},
        {"state": ""},
        {"code": "c", "state": "s", "extra": "field"},  # extra=forbid
    ],
)
def test_callback_invalid_body_returns_422(callback_client, body):
    response = callback_client.post("/api/auth/callback", json=body)
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# Logging discipline — AC7-D10
# -----------------------------------------------------------------------------

@respx.mock
def test_callback_never_logs_sensitive_values(
    callback_client, good_state, rsa_keypair, caplog
):
    """code, state, id_token, sub must never appear in any log record."""
    sensitive_code = "very-secret-auth-code"
    sub = "FCPS-LEAK-CHECK"
    token = _sign_token(rsa_keypair, sub=sub)
    _mock_idme_token(respx, token)
    _mock_idme_jwks(respx, rsa_keypair["public_jwk"])

    with caplog.at_level(logging.INFO):
        callback_client.post(
            "/api/auth/callback",
            json={"code": sensitive_code, "state": good_state},
        )

    forbidden_values = [sensitive_code, good_state, token, sub]
    for record in caplog.records:
        msg = record.getMessage()
        for v in forbidden_values:
            assert v not in msg, f"value leaked into log: '{v}' in {msg!r}"
