"""
🔴 RED ZONE — implements AC-8 (FastAPI auth dependencies).

Ratified decisions live in:
    docs/decision-log/AC-8-jwt.md  (AC8-D7, AC8-D8, AC8-D9)
    docs/adr/ADR-015-role-model-simplification.md  ← `require_level` dropped

Two Depends factories cover the entire session-based auth surface:

* `require_authenticated`  — reads the `session` cookie, verifies the JWT,
  returns `SessionClaims`. AC8-D8: ANY failure (missing cookie / malformed
  / expired / bad-sig / bad-alg / bad-iss / bad-aud / missing-claims)
  collapses to the same 401 + body. No enumeration of which check failed.

* `require_role(*allowed)` — composes on top of `require_authenticated`.
  AC8-D9: 403 + `X-Auth-Reason: ROLE_FORBIDDEN` + the standard "no
  permission" body. Matches FUNCTIONAL_DESIGN.md §10 error model.

Per [ADR-015](../../../docs/adr/ADR-015-role-model-simplification.md),
the previous `require_level(min_level)` factory has been removed along
with `PROCUREMENT_LEVEL`; role is the single authority axis.
"""
from __future__ import annotations

from typing import Iterable

from fastapi import Cookie, Depends, HTTPException, status

from app.auth.jwt_session import (
    SessionClaims,
    SessionInvalid,
    SessionRole,
    verify_session_jwt,
)
from app.core.config import Settings, get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Centralised copy — must not drift from FUNCTIONAL_DESIGN.md §10.
_DETAIL_SESSION_INVALID = "Session invalid or expired."
_DETAIL_FORBIDDEN = "You do not have permission to view this resource."
_HEADER_ROLE_FORBIDDEN = {"X-Auth-Reason": "ROLE_FORBIDDEN"}


def require_authenticated(
    session: str | None = Cookie(default=None),
    settings: Settings = Depends(get_settings),
) -> SessionClaims:
    """Resolve the current session, or raise 401.

    AC8-D8: missing-cookie and verification-failure both yield the same
    response. We log the distinction server-side via `err=…`.
    """
    if session is None:
        logger.info("auth.session.missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_DETAIL_SESSION_INVALID,
        )

    try:
        return verify_session_jwt(session, secret_key=settings.jwt_secret_key)
    except SessionInvalid:
        # jwt_session already logged the failure class.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_DETAIL_SESSION_INVALID,
        )


def require_role(*allowed: SessionRole):
    """Dependency factory: only sessions with role in `allowed` may pass.

    Usage (per [ADR-015](../../../docs/adr/ADR-015-role-model-simplification.md)):
        @router.get(..., dependencies=[Depends(require_role("PROCUREMENT_SUPERVISOR"))])
        # or, allowing either granted role:
        def endpoint(claims = Depends(
            require_role("PROCUREMENT_SUPERVISOR", "REGULAR_STAFF")
        )): ...

    AC8-D9: 403 + X-Auth-Reason: ROLE_FORBIDDEN on mismatch.
    """
    allowed_set: frozenset[str] = frozenset(allowed)

    def _checker(
        claims: SessionClaims = Depends(require_authenticated),
    ) -> SessionClaims:
        if claims.role not in allowed_set:
            logger.info(
                "auth.role.forbidden staff_id=%s role=%s required=%s",
                claims.staff_id,
                claims.role,
                sorted(allowed_set),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_DETAIL_FORBIDDEN,
                headers=_HEADER_ROLE_FORBIDDEN,
            )
        return claims

    return _checker


__all__: Iterable[str] = (
    "require_authenticated",
    "require_role",
)
