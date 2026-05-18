"""
🔴 RED ZONE — interface defined for AC-7; body to be filled in by AC-8.

Ratified decision: docs/decision-log/AC-7-callback.md (AC7-D8).

Defines the contract that AC-8 will implement per
[ADR-004](../../../docs/adr/ADR-004-session-cookie-and-jwt.md):

* Sign a JWT (HS256) with claims `{sub=staff_id, role, procurement_level,
  iss, aud, iat, exp}`.
* TTL via `JWT_TTL_HOURS` env var (default 4 h).
* Set as `session` cookie — `HttpOnly`, `SameSite=Lax`, `Path=/`.
* `Secure` flag env-driven (`JWT_COOKIE_SECURE`, default `false`) per
  ADR-008 for the demo's HTTP-only deployment.

AC-7's callback endpoint imports `issue_session_cookie` via
`Depends(get_session_issuer)` so tests can inject a mock that records
the call without actually signing anything.
"""
from __future__ import annotations

from typing import Literal

from fastapi import Response


SessionRole = Literal["ADMIN", "STAFF"]


def issue_session_cookie(
    response: Response,
    *,
    staff_id: int,
    role: SessionRole,
    procurement_level: int,
) -> None:
    """Sign a JWT for this session and attach it as the `session` cookie
    on the given response.

    To be implemented by AC-8. Signature is contractually fixed here.
    """
    raise NotImplementedError(
        "jwt_session.issue_session_cookie is implemented by AC-8. "
        "Tests should override the `get_session_issuer` FastAPI dependency."
    )
