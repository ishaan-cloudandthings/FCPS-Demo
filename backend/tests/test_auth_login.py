"""Tests for POST /api/auth/login (AC-6).

Each test maps to one of the acceptance criteria recorded in
`docs/decision-log/AC-6-login-init.md`.
"""
from __future__ import annotations

import logging
from urllib.parse import parse_qs, urlparse

import pytest

from app.auth.state_cache import MAX_ENTRIES, TTL_SECONDS, OAuthStateCache


# -----------------------------------------------------------------------------
# Endpoint behaviour
# -----------------------------------------------------------------------------

def test_post_login_returns_200_with_authorize_url(client):
    """AC#1 — happy path: endpoint responds 200 with an authorize_url field."""
    response = client.post("/api/auth/login")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"authorize_url"}
    assert body["authorize_url"].startswith("https://api.id.me/oauth/authorize?")


def test_authorize_url_contains_all_five_oauth_params(client):
    """AC6-D6 — all 5 OAuth params present and correctly encoded."""
    response = client.post("/api/auth/login")
    params = parse_qs(urlparse(response.json()["authorize_url"]).query)

    assert params["client_id"] == ["test-client-id"]
    assert params["redirect_uri"] == ["http://localhost/verification/callback"]
    assert params["response_type"] == ["code"]
    assert params["scope"] == ["openid email"]
    assert "state" in params
    # token_urlsafe(32) produces ~43 chars; allow a small range.
    assert 40 <= len(params["state"][0]) <= 50


def test_state_is_stored_in_cache_after_login(client, fresh_state_cache):
    """AC#2 — state is generated and stored server-side."""
    assert len(fresh_state_cache) == 0
    response = client.post("/api/auth/login")
    assert len(fresh_state_cache) == 1

    state_in_url = parse_qs(urlparse(response.json()["authorize_url"]).query)["state"][0]
    # The state from the URL is consumable from the cache (and only once).
    assert fresh_state_cache.consume(state_in_url) is True


def test_each_call_issues_a_unique_state(client):
    """Two calls return distinct state tokens."""
    url_a = client.post("/api/auth/login").json()["authorize_url"]
    url_b = client.post("/api/auth/login").json()["authorize_url"]
    state_a = parse_qs(urlparse(url_a).query)["state"][0]
    state_b = parse_qs(urlparse(url_b).query)["state"][0]
    assert state_a != state_b


# -----------------------------------------------------------------------------
# State cache contract — AC#3 (one-shot) + AC6-D5
# -----------------------------------------------------------------------------

def test_state_is_one_shot(fresh_state_cache):
    """AC#3 — state reuse is rejected because the cache entry is one-shot."""
    token = fresh_state_cache.issue()
    assert fresh_state_cache.consume(token) is True   # first use succeeds
    assert fresh_state_cache.consume(token) is False  # second use is rejected


def test_unknown_token_consume_returns_false(fresh_state_cache):
    """Tokens never issued by this cache are rejected."""
    assert fresh_state_cache.consume("never-issued-token") is False


def test_state_expires_after_ttl():
    """AC6-D4/D5 — entries older than TTL_SECONDS are not consumable."""
    fake_time = {"now": 1_000_000.0}

    cache = OAuthStateCache(clock=lambda: fake_time["now"])
    token = cache.issue()

    # 1 second before expiry — still valid.
    fake_time["now"] += TTL_SECONDS - 1
    # Use a probe via the internal store rather than consuming (consume pops).
    assert token in cache._store

    # Now jump past TTL.
    fake_time["now"] += 2  # total: TTL_SECONDS + 1
    assert cache.consume(token) is False


def test_expired_entries_swept_on_issue():
    """AC6-D4 — lazy sweep keeps the cache from accumulating dead entries."""
    fake_time = {"now": 100.0}
    cache = OAuthStateCache(clock=lambda: fake_time["now"])

    cache.issue()
    cache.issue()
    assert len(cache) == 2

    # Advance past TTL; next issue should sweep the two expired tokens.
    fake_time["now"] += TTL_SECONDS + 1
    cache.issue()
    assert len(cache) == 1  # only the newest survives


# -----------------------------------------------------------------------------
# Capacity — AC#4 + AC6-D4
# -----------------------------------------------------------------------------

def test_state_cap_returns_503(client, fresh_state_cache):
    """AC#4 — when cache is at capacity, /api/auth/login returns 503."""
    for _ in range(MAX_ENTRIES):
        fresh_state_cache.issue()
    assert len(fresh_state_cache) == MAX_ENTRIES

    response = client.post("/api/auth/login")
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Service temporarily unavailable. Please try again shortly."
    }


# -----------------------------------------------------------------------------
# Logging discipline — AC#5 + AC6-D9
# -----------------------------------------------------------------------------

def test_state_token_is_never_logged(client, caplog):
    """AC#5 — the state token must not appear in any log record."""
    with caplog.at_level(logging.INFO):
        response = client.post("/api/auth/login")
    state = parse_qs(urlparse(response.json()["authorize_url"]).query)["state"][0]

    for record in caplog.records:
        # Check the rendered message…
        assert state not in record.getMessage()
        # …and any keyword args / extras that might have ended up in the record.
        for attr_name, attr_value in record.__dict__.items():
            if attr_name in {"args", "exc_info", "stack_info"}:
                continue
            assert state not in str(attr_value), (
                f"State token leaked into log record attr '{attr_name}'"
            )


def test_state_token_not_in_redirect_uri(client):
    """Sanity: the configured redirect_uri must not accidentally embed the state."""
    response = client.post("/api/auth/login")
    params = parse_qs(urlparse(response.json()["authorize_url"]).query)
    state = params["state"][0]
    redirect_uri = params["redirect_uri"][0]
    assert state not in redirect_uri


# -----------------------------------------------------------------------------
# Internal error handling — AC6-D11
# -----------------------------------------------------------------------------

def test_unhandled_exception_returns_friendly_500(monkeypatch, fresh_state_cache):
    """AC6-D11 — unhandled errors return 500 with a friendly body, never a trace.

    Uses `raise_server_exceptions=False` so TestClient yields the actual
    response from our exception handler instead of re-raising the original.
    """
    from fastapi.testclient import TestClient
    from app.api.auth import get_state_cache
    from main import app

    def boom():
        raise RuntimeError("simulated cache failure")

    monkeypatch.setattr(fresh_state_cache, "issue", boom)

    app.dependency_overrides[get_state_cache] = lambda: fresh_state_cache
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            response = c.post("/api/auth/login")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "Something went wrong. Please try again."}
    # Body should NOT contain any trace fragment.
    assert "RuntimeError" not in response.text
    assert "simulated cache failure" not in response.text
