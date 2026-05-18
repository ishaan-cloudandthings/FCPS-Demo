"""
🔴 RED ZONE — implements AC-7 (JWKS cache).

Ratified decisions: docs/decision-log/AC-7-callback.md (AC7-D3, AC7-D4).

Fetches ID.me's JWKS endpoint and serves public keys to the ID-token
validator, keyed by `kid`. Cached in-process with a 60-min TTL.

Hard rules:
* On JWKS fetch failure, we **raise** `JWKSFetchError`. The caller MUST
  fail the auth (401). Never fall back to skipping signature verification
  (AC7-D3, AC7-D4).
* Only RS256 / RSA keys are kept; other key types are silently filtered
  out during cache population.

Concurrency: in-process dict, single Uvicorn worker. Same constraint as
the OAuth state cache (AC6-D2).
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional

import httpx

from app.utils.logging import get_logger

logger = get_logger(__name__)

JWKS_TTL_SECONDS: int = 3600  # AC7-D3 — 60 min
JWKS_FETCH_TIMEOUT_SECONDS: float = 5.0  # matches token-exchange timeout


class JWKSFetchError(Exception):
    """Raised when JWKS cannot be fetched. The auth flow MUST fail (401)."""


class JWKSCache:
    """In-process cache of ID.me's public signing keys.

    Stores raw JWK dicts (as returned by the JWKS endpoint), keyed by
    `kid`. The whole cache shares one TTL — a single fetch refreshes all
    keys at once.
    """

    def __init__(
        self,
        jwks_url: str,
        ttl_seconds: int = JWKS_TTL_SECONDS,
        http_client_factory: Optional[Callable[[], httpx.Client]] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = jwks_url
        self._ttl = ttl_seconds
        self._clock = clock
        self._client_factory = (
            http_client_factory
            or (lambda: httpx.Client(timeout=JWKS_FETCH_TIMEOUT_SECONDS))
        )
        self._keys: dict[str, dict[str, Any]] = {}  # kid -> JWK dict
        self._fetched_at: float = 0.0

    def get_key(self, kid: str) -> dict[str, Any]:
        """Return the JWK dict for `kid`, refreshing the cache if needed.

        Raises:
            JWKSFetchError: the JWKS endpoint was unreachable.
            KeyError:       the kid is unknown even after a fresh fetch.
        """
        if not self._keys or self._is_expired():
            self._refresh()

        if kid not in self._keys:
            # Force a refresh in case ID.me has rotated keys mid-TTL.
            logger.info("auth.jwks.kid_miss_refresh kid=%s", kid)
            self._refresh()

        if kid not in self._keys:
            raise KeyError(f"unknown kid {kid!r}")

        return self._keys[kid]

    # ------------------------------------------------------------------ private

    def _is_expired(self) -> bool:
        return self._clock() - self._fetched_at > self._ttl

    def _refresh(self) -> None:
        """Fetch the JWKS endpoint and replace `_keys`. Failure raises."""
        try:
            with self._client_factory() as client:
                response = client.get(self._url)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning(
                "auth.jwks.fetch_failed url=%s err=%s",
                self._url,
                type(exc).__name__,
            )
            raise JWKSFetchError(f"failed to fetch JWKS from {self._url}") from exc

        keys_in = payload.get("keys") or []
        new_keys: dict[str, dict[str, Any]] = {}
        for jwk in keys_in:
            kid = jwk.get("kid")
            if not kid:
                continue
            # AC7-D4: only RS256 / RSA keys are kept.
            kty = jwk.get("kty")
            alg = jwk.get("alg", "RS256")  # default to RS256 if alg is absent
            if kty != "RSA" or alg != "RS256":
                continue
            new_keys[kid] = jwk

        self._keys = new_keys
        self._fetched_at = self._clock()
        logger.info("auth.jwks.refreshed count=%d", len(new_keys))

    # ------------------------------------------------------------------ introspection

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._keys)
