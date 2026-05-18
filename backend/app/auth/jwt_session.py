"""
🔴 RED ZONE — implements AC-8 (JWT issuance + verification).

Ratified decisions live in:
    docs/decision-log/AC-8-jwt.md
    (D-FD-01..07 from FUNCTIONAL_DESIGN.md §6.4 + AC8-D1..D14)

This module is the single source of truth for the session JWT contract:

* Issue (AC8-D2): `issue_session_cookie` signs an HS256 JWT with claims
  `{sub=str(staff_id), role, procurement_level, iss="fcps-portal",
  aud="fcps-portal-web", iat, exp}` and attaches it as the `session`
  cookie — `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` env-driven.
* Verify (AC8-D10): `verify_session_jwt` calls
  `jose.jwt.decode(..., algorithms=["HS256"], ...)` — explicit allowlist
  defends against algorithm-confusion attacks. Never trusts the header's
  `alg`. Returns a frozen `SessionClaims` on success; any failure raises
  `SessionInvalid` so the dependency layer can collapse all 401 causes
  into a single user-facing response (AC8-D8).
* Logging (AC8-D13): `jwt.issued staff_id=… role=… level=…` on success;
  `jwt.verify_failed err=<error_class>` on failure. The token itself is
  NEVER logged.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Response
from jose import jwt as jose_jwt
from jose.exceptions import JWTError

from app.utils.logging import get_logger

logger = get_logger(__name__)

# --- Contract constants (AC8-D4, D-FD-04, AC8-D6, AC8-D10, D-FD-06) ---
COOKIE_NAME: str = "session"                 # AC8-D4
COOKIE_SAMESITE: str = "lax"                 # D-FD-04
COOKIE_PATH: str = "/"                       # D-FD-04
JWT_ISSUER: str = "fcps-portal"              # AC8-D6
JWT_AUDIENCE: str = "fcps-portal-web"        # AC8-D6
ALLOWED_ALGORITHMS: list[str] = ["HS256"]    # AC8-D10 / D-FD-01
CLOCK_SKEW_SECONDS: int = 30                 # D-FD-06

SessionRole = Literal["ADMIN", "STAFF"]
_VALID_ROLES: frozenset[str] = frozenset({"ADMIN", "STAFF"})


@dataclass(frozen=True)
class SessionClaims:
    """Decoded, validated session claims. AC8-D3.

    Never constructed directly by callers — `verify_session_jwt` is the
    only producer. The frozen dataclass makes it safe to pass around.
    """
    staff_id: int
    role: SessionRole
    procurement_level: int


class SessionInvalid(Exception):
    """Raised by `verify_session_jwt` on ANY validation failure.

    AC8-D8: the dependency layer maps every cause (missing / malformed /
    expired / bad-sig / bad-alg / bad-iss / bad-aud / missing-claims) to
    the same 401 response. The exception message is for server logs only.
    """


def issue_session_cookie(
    response: Response,
    *,
    staff_id: int,
    role: SessionRole,
    procurement_level: int,
    secret_key: str,
    ttl_hours: int,
    secure: bool,
) -> None:
    """Sign a session JWT and attach it as the `session` cookie.

    AC8-D2: extends the AC-7 stub signature with `secret_key`, `ttl_hours`,
    and `secure` — injected by `get_session_issuer` from Settings so this
    function stays pure and trivially unit-testable.

    Claims layout is fixed by D-FD-02 and AC8-D12 (claims allowlist test).
    EMPLOYEE_ID is deliberately NOT included (REQUIREMENTS.md D-07).
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=ttl_hours)

    claims = {
        "sub": str(staff_id),               # AC8-D5: JWT convention — sub is a string
        "role": role,
        "procurement_level": procurement_level,
        "iss": JWT_ISSUER,                  # AC8-D6
        "aud": JWT_AUDIENCE,                # AC8-D6
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }

    token = jose_jwt.encode(claims, secret_key, algorithm=ALLOWED_ALGORITHMS[0])

    # D-FD-04: HttpOnly, SameSite=Lax, Path=/, Secure env-driven.
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=ttl_hours * 3600,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
        secure=secure,
    )

    # AC8-D13: log non-PII outcome. NEVER log the token itself.
    logger.info(
        "jwt.issued staff_id=%s role=%s level=%s",
        staff_id,
        role,
        procurement_level,
    )


def delete_session_cookie(response: Response, *, secure: bool) -> None:
    """Clear the `session` cookie on the given response.

    AC9-D2: the cookie-clearing attributes MUST match the issue-time
    attributes — `Path`, `SameSite`, `HttpOnly`, `Secure` — otherwise the
    browser treats this as a different cookie and silently ignores the
    clear. Reusing `COOKIE_*` constants here is the guarantee.
    """
    response.delete_cookie(
        key=COOKIE_NAME,
        path=COOKIE_PATH,
        samesite=COOKIE_SAMESITE,
        httponly=True,
        secure=secure,
    )


def verify_session_jwt(token: str, *, secret_key: str) -> SessionClaims:
    """Verify a session JWT end-to-end and return its claims.

    AC8-D10: `algorithms=["HS256"]` is an explicit allowlist; the header's
    `alg` is never trusted. AC8-D8: any failure raises `SessionInvalid` —
    no caller-visible distinction between causes.
    """
    try:
        claims = jose_jwt.decode(
            token,
            secret_key,
            algorithms=ALLOWED_ALGORITHMS,            # AC8-D10
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"leeway": CLOCK_SKEW_SECONDS},   # D-FD-06
        )
    except JWTError as exc:
        # Wraps expired / bad-aud / bad-iss / bad-sig / bad-alg / malformed.
        logger.warning("jwt.verify_failed err=%s", type(exc).__name__)
        raise SessionInvalid(f"decode failed: {type(exc).__name__}") from exc

    # The decoder validates structural claims (iss/aud/exp/iat) but not
    # our application-specific shape. Enforce that here.
    sub = claims.get("sub")
    role = claims.get("role")
    level = claims.get("procurement_level")

    if sub is None or role is None or level is None:
        logger.warning("jwt.verify_failed err=MissingClaim")
        raise SessionInvalid("missing required claim")

    try:
        staff_id = int(sub)                          # AC8-D5: coerce back to int
    except (TypeError, ValueError) as exc:
        logger.warning("jwt.verify_failed err=BadSub")
        raise SessionInvalid("sub is not an integer") from exc

    if role not in _VALID_ROLES:
        logger.warning("jwt.verify_failed err=BadRole")
        raise SessionInvalid(f"role {role!r} not in allowlist")

    if not isinstance(level, int) or isinstance(level, bool):
        # bool is a subclass of int — exclude it explicitly.
        logger.warning("jwt.verify_failed err=BadLevel")
        raise SessionInvalid("procurement_level must be int")

    return SessionClaims(
        staff_id=staff_id,
        role=role,                                   # type: ignore[arg-type]
        procurement_level=level,
    )
