"""
🔴 RED ZONE — implements AC-7 (ID-token validation).

Ratified decisions: docs/decision-log/AC-7-callback.md (AC7-D4, AC7-D5)
and FUNCTIONAL_DESIGN.md §6.1 D-FD-11.

Validates an ID token from ID.me:

* `alg` is exactly `RS256` — checked first against the header, then
  enforced again as an explicit `algorithms=` argument to `jose.jwt.decode`
  (defence in depth — AC7-D4).
* Signature is verified against the appropriate JWKS key (looked up by
  `kid` via `JWKSCache`).
* `iss` matches the expected issuer.
* `aud` matches our `client_id`.
* `exp` and `iat` honoured with 30 s clock-skew tolerance (AC7-D5).

Any failure raises `IDTokenInvalid`. The caller maps that to HTTP 401.
"""
from __future__ import annotations

from typing import Any

from jose import jwt as jose_jwt
from jose.exceptions import JWTError

from app.auth.jwks_cache import JWKSCache, JWKSFetchError
from app.utils.logging import get_logger

logger = get_logger(__name__)

CLOCK_SKEW_SECONDS: int = 30          # AC7-D5
ALLOWED_ALGORITHMS: list[str] = ["RS256"]  # AC7-D4 — defence in depth


class IDTokenInvalid(Exception):
    """Raised when an ID token fails validation. Caller maps to 401."""


def validate_id_token(
    token: str,
    *,
    jwks_cache: JWKSCache,
    expected_issuer: str,
    expected_audience: str,
) -> dict[str, Any]:
    """Validate an ID token end-to-end and return its claims dict.

    Never returns partially-validated claims — any failure raises.
    """
    # 1. Header-only inspection to find the kid and pre-check the alg.
    try:
        header = jose_jwt.get_unverified_header(token)
    except JWTError as exc:
        raise IDTokenInvalid("malformed token header") from exc

    alg = header.get("alg")
    if alg not in ALLOWED_ALGORITHMS:
        # AC7-D4: refuse anything we don't explicitly allow.
        raise IDTokenInvalid(f"alg {alg!r} not allowed")

    kid = header.get("kid")
    if not kid:
        raise IDTokenInvalid("token header missing kid")

    # 2. Look up the signing key. JWKS failure must not silently degrade.
    try:
        jwk = jwks_cache.get_key(kid)
    except JWKSFetchError as exc:
        raise IDTokenInvalid("JWKS unreachable; cannot validate signature") from exc
    except KeyError as exc:
        raise IDTokenInvalid(f"signing key {kid!r} not in JWKS") from exc

    # 3. Full decode: signature + iss + aud + exp + iat with skew.
    try:
        claims = jose_jwt.decode(
            token,
            jwk,
            algorithms=ALLOWED_ALGORITHMS,           # AC7-D4 (belt-and-braces)
            audience=expected_audience,
            issuer=expected_issuer,
            options={"leeway": CLOCK_SKEW_SECONDS},  # AC7-D5
        )
    except JWTError as exc:
        # Wraps expired / bad-aud / bad-iss / bad-sig / etc.
        raise IDTokenInvalid(
            f"token validation failed: {type(exc).__name__}"
        ) from exc

    if "sub" not in claims:
        raise IDTokenInvalid("token missing sub claim")

    return claims
