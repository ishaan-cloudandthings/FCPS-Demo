"""
🔴 RED ZONE — demo-only persona login.

Ratified decisions:
    docs/adr/ADR-014-demo-persona-login-dev-only.md
    docs/decision-log/DEV-AUTH-persona-picker.md (DEV1 … DEV13)

This router mints session cookies WITHOUT going through ID.me. It is
intended strictly for dev environments — stakeholder demos, smoke
testing, and continuing UI work before the access service (AC-13) and
Oracle seed (AC-14) are wired up.

Defence in depth (DEV2):

  1. Boot-time:  main.py only includes this router when
     `settings.environment == "dev"`.
  2. Request-time: every handler re-reads `settings.environment` and
     raises HTTPException(404) if not dev — INDISTINGUISHABLE from
     "endpoint does not exist" outside dev. No 403, no enumeration.

The cookie minting reuses `Depends(get_session_issuer)` — the same path
as `/api/auth/callback`. There is no second JWT format; AC-8 cookie
semantics inherit unchanged.

Kill criteria are documented in ADR-014 and MUST be honoured before any
non-dev deployment.
"""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.auth import (
    _DETAIL_LEVEL_ZERO,
    _DETAIL_NOT_REGISTERED,
    get_session_issuer,
)
from app.core.config import Settings, get_settings
from app.schemas.auth import (
    DevLoginAvailableResponse,
    DevLoginRequest,
    SessionResponse,
)
from app.utils.logging import get_logger

router = APIRouter(prefix="/api/auth", tags=["auth", "dev-only"])
logger = get_logger(__name__)

# DEV3 — the persona table. Hardcoded by design; adding a persona is a
# code change, not data-driven. Keys must match DevLoginRequest's Literal.
_GRANTED_PERSONAS: dict[str, dict[str, object]] = {
    "admin_l3": {"staff_id": 1, "role": "ADMIN", "procurement_level": 3},
    "staff_l2": {"staff_id": 2, "role": "STAFF", "procurement_level": 2},
    "staff_l1": {"staff_id": 3, "role": "STAFF", "procurement_level": 1},
}

_DENIED_PERSONAS: dict[str, tuple[str, str]] = {
    # persona → (X-Auth-Reason header value, response body detail)
    "level_zero": ("LEVEL_ZERO", _DETAIL_LEVEL_ZERO),
    "not_registered": ("NOT_REGISTERED", _DETAIL_NOT_REGISTERED),
}


def _require_dev(settings: Settings) -> None:
    """DEV2 (request-time gate). Raises 404 — indistinguishable from
    "endpoint does not exist" outside dev. Never 403, never an enumeration.
    """
    if settings.environment != "dev":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/dev-login",
    status_code=status.HTTP_200_OK,
    response_model=SessionResponse,
)
def dev_login(
    payload: DevLoginRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    session_issuer: Callable[..., None] = Depends(get_session_issuer),
) -> SessionResponse:
    """Mint a session for the requested persona.

    DEV3 — five hardcoded personas:
      admin_l3 / staff_l2 / staff_l1 → 200 + session cookie
      level_zero / not_registered    → 403 + X-Auth-Reason header
    """
    _require_dev(settings)

    persona = payload.persona

    if persona in _DENIED_PERSONAS:
        header_value, detail = _DENIED_PERSONAS[persona]
        # DEV7 — mandatory DEV_AUTH_USED token in every log line.
        logger.info(
            "dev_auth.login persona=%s outcome=denied DEV_AUTH_USED",
            persona,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers={"X-Auth-Reason": header_value},
        )

    claims = _GRANTED_PERSONAS[persona]
    # DEV5 — reuse the same session issuer the real /callback uses.
    session_issuer(
        response,
        staff_id=claims["staff_id"],
        role=claims["role"],
        procurement_level=claims["procurement_level"],
    )
    logger.info(
        "dev_auth.login persona=%s outcome=granted DEV_AUTH_USED",
        persona,
    )
    return SessionResponse(
        role=claims["role"],            # type: ignore[arg-type]
        procurement_level=claims["procurement_level"],   # type: ignore[arg-type]
        staff_id=claims["staff_id"],    # type: ignore[arg-type]
    )


@router.get(
    "/dev-login/available",
    response_model=DevLoginAvailableResponse,
    status_code=status.HTTP_200_OK,
)
def dev_login_available(
    settings: Settings = Depends(get_settings),
) -> DevLoginAvailableResponse:
    """DEV4 — probe used by the SPA to decide whether to render the
    persona panel on Login. 200 in dev, 404 otherwise.
    """
    _require_dev(settings)
    return DevLoginAvailableResponse()
