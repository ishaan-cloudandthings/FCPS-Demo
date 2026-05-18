"""
🔴 RED ZONE — implements AC-6 (POST /api/auth/login), AC-7 (POST /api/auth/callback),
and AC-9 (POST /api/auth/logout + GET /api/auth/me).

Ratified decisions live in:
    docs/decision-log/AC-6-login-init.md
    docs/decision-log/AC-7-callback.md
    docs/decision-log/AC-9-session-lifecycle.md
"""
from __future__ import annotations

from typing import Callable, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.dependencies import require_authenticated
from app.auth.id_token_validator import IDTokenInvalid, validate_id_token
from app.auth.idme_client import IDMEUnreachable, exchange_code_for_token
from app.auth.jwks_cache import JWKSCache
from app.auth.jwt_session import (
    SessionClaims,
    delete_session_cookie,
    issue_session_cookie,
)
from app.auth.state_cache import OAuthStateCache, StateCacheError
from app.core.config import Settings, get_settings
from app.core.database import get_oracle_connection
from app.schemas.auth import AuthorizeUrlResponse, CallbackRequest, SessionResponse
from app.services.access_service import AccessDecision, decide_access
from app.services.oracle_service import OracleUnavailable
from app.utils.logging import get_logger

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = get_logger(__name__)

# Module-level singletons.
#
# AC6-D2 / AC7-D3: single Uvicorn worker is a hard assumption for the demo.
# Under `--workers 1`, every request lands on the same Python process and
# shares these instances. Multi-worker deploys would need shared stores.
_state_cache: OAuthStateCache = OAuthStateCache()
_jwks_cache: Optional[JWKSCache] = None


def get_state_cache() -> OAuthStateCache:
    """FastAPI dependency returning the process-wide OAuth state cache."""
    return _state_cache


def get_jwks_cache(settings: Settings = Depends(get_settings)) -> JWKSCache:
    """FastAPI dependency returning the process-wide JWKS cache.

    Lazily constructed on first request so we don't fetch the JWKS at
    import-time (which would couple module import to network I/O).
    Tests override this via `app.dependency_overrides`.
    """
    global _jwks_cache
    if _jwks_cache is None:
        _jwks_cache = JWKSCache(jwks_url=str(settings.idme_jwks_url))
    return _jwks_cache


# Indirection point so tests can inject mocks (AC7-D8 + AC13-D1).
def get_access_decider(
    connection=Depends(get_oracle_connection),
) -> Callable[[str], AccessDecision]:
    """FastAPI dependency returning the access-decision callable.

    AC13-D1: closure binds the Oracle connection (yielded by the
    per-request `get_oracle_connection` dependency). Keeps the endpoint's
    decider signature `(sub) -> AccessDecision`, unchanged since AC-7.

    Production: returns a closure over `decide_access` + connection.
    Tests: override to return a mock that records its call.
    """

    def _wrapped(sub: str) -> AccessDecision:
        return decide_access(connection, sub)

    return _wrapped


def get_session_issuer(
    settings: Settings = Depends(get_settings),
) -> Callable[..., None]:
    """FastAPI dependency returning the JWT-cookie issuer callable.

    AC8-D2: the underlying `jwt_session.issue_session_cookie` takes
    `secret_key`, `ttl_hours`, and `secure` as extra kwargs. We bind them
    here from Settings so the endpoint (and AC-7 mocks) keep the original
    `(response, *, staff_id, role, procurement_level)` signature.

    Production: returns a closure over `issue_session_cookie` + settings.
    Tests: override to return a mock that records its call.
    """

    def _wrapped(
        response,
        *,
        staff_id: int,
        role,
        procurement_level: int,
    ) -> None:
        issue_session_cookie(
            response,
            staff_id=staff_id,
            role=role,
            procurement_level=procurement_level,
            secret_key=settings.jwt_secret_key,
            ttl_hours=settings.jwt_ttl_hours,
            secure=settings.jwt_cookie_secure,
        )

    return _wrapped


@router.post(
    "/login",
    response_model=AuthorizeUrlResponse,
    status_code=status.HTTP_200_OK,
)
def begin_login(
    request: Request,
    settings: Settings = Depends(get_settings),
    cache: OAuthStateCache = Depends(get_state_cache),
) -> AuthorizeUrlResponse:
    """Begin the ID.me OAuth flow.

    Behaviour:
      1. Issue a new one-shot `state` token (cached server-side, 10 min TTL).
      2. Build the ID.me authorize URL with the 5 OAuth params (AC6-D6).
      3. Return the URL as JSON. The SPA performs the redirect.

    Failure modes:
      * Cache at capacity        → 503 with friendly body (AC6-D4)
      * Any other unhandled error → 500 via the global handler (AC6-D11)
    """
    try:
        state = cache.issue()
    except StateCacheError:
        # AC6-D4: bounded cache; over-cap is a friendly 503, not a 500.
        # AC6-D9: never log the state token (we don't have one yet here).
        logger.warning("auth.login.state_cache_full")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again shortly.",
        )

    # AC6-D6: all 5 OAuth params, properly URL-encoded.
    query = urlencode(
        {
            "client_id": settings.idme_client_id,
            "redirect_uri": str(settings.idme_redirect_uri),
            "response_type": "code",
            "scope": settings.idme_scope,
            "state": state,
        }
    )
    authorize_base = str(settings.idme_authorize_url).rstrip("/")
    authorize_url = f"{authorize_base}?{query}"

    # AC6-D9: log ip + user-agent only. Do NOT log the state token.
    logger.info(
        "auth.login.start ip=%s user_agent=%s",
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
    )

    return AuthorizeUrlResponse(authorize_url=authorize_url)


# ---------------------------------------------------------------------------
# AC-7 — POST /api/auth/callback
# ---------------------------------------------------------------------------

# Body copy is centralised so it can't drift from FUNCTIONAL_DESIGN.md §10.
_DETAIL_STATE_EXPIRED = "Authentication request expired. Please verify again."
_DETAIL_IDME_UNREACHABLE = "Identity provider unreachable."
_DETAIL_ID_TOKEN_INVALID = "Identity verification failed."
_DETAIL_LEVEL_ZERO = (
    "Access denied. Your account does not have procurement clearance."
)
_DETAIL_NOT_REGISTERED = (
    "Your identity has been verified but you are not registered in the "
    "FCPS procurement system. Contact your procurement coordinator."
)
# AC13-D6: shared with AC-6's state-cache-full 503 — single canonical copy.
_DETAIL_SERVICE_UNAVAILABLE = (
    "Service temporarily unavailable. Please try again shortly."
)


@router.post(
    "/callback",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
def complete_login(
    payload: CallbackRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    state_cache: OAuthStateCache = Depends(get_state_cache),
    jwks_cache: JWKSCache = Depends(get_jwks_cache),
    access_decider: Callable[[str], AccessDecision] = Depends(get_access_decider),
    session_issuer: Callable[..., None] = Depends(get_session_issuer),
) -> SessionResponse:
    """Complete the ID.me OAuth flow.

    Order of operations (AC7-D6):

      1. Validate `state` against the cache (one-shot).      → 400 on fail
      2. Exchange `code` for token at ID.me /oauth/token.    → 502 on fail
      3. Validate ID token signature + claims (JWKS).        → 401 on fail
      4. Dispatch to `access_service.decide_access(sub)`.    → 403 on deny
      5. Issue JWT cookie + return {role, procurement_level}.

    Per AC7-D11: `sub` is treated as PII — never logged, never returned,
    never embedded in the JWT (the JWT carries `staff_id`).
    """
    # ---- 1. State validation (AC7-D6, D-FD-09) ----
    if not state_cache.consume(payload.state):
        # AC7-D10: never log the state token itself.
        logger.warning("auth.callback.invalid_state")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_DETAIL_STATE_EXPIRED,
        )

    logger.info("auth.callback.start")

    # ---- 2. Token exchange (D-FD-10) ----
    try:
        token_response = exchange_code_for_token(
            token_url=str(settings.idme_token_url),
            client_id=settings.idme_client_id,
            client_secret=settings.idme_client_secret,
            code=payload.code,
            redirect_uri=str(settings.idme_redirect_uri),
        )
    except IDMEUnreachable:
        # idme_client already logged the failure class.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_DETAIL_IDME_UNREACHABLE,
        )

    id_token = token_response.get("id_token")
    if not id_token:
        # ID.me responded 2xx but without an id_token — treat as auth failure.
        logger.warning("auth.callback.id_token_missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_DETAIL_ID_TOKEN_INVALID,
        )

    # ---- 3. ID token validation (D-FD-11) ----
    try:
        claims = validate_id_token(
            id_token,
            jwks_cache=jwks_cache,
            expected_issuer=settings.idme_issuer,
            expected_audience=settings.idme_client_id,
        )
    except IDTokenInvalid as exc:
        # AC7-D10: log the failure class only; never the token contents.
        logger.warning("auth.callback.id_token_invalid err=%s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_DETAIL_ID_TOKEN_INVALID,
        )

    sub = claims["sub"]  # AC7-D11: PII; never log/return this directly.

    # ---- 4. Access decision (D-FD-12) ----
    # AC13-D6: Oracle infrastructure failures surface as 503. The access
    # service already logged the failure class via oracle_service; no
    # additional logging here.
    try:
        decision = access_decider(sub)
    except OracleUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_DETAIL_SERVICE_UNAVAILABLE,
        )

    if not decision.granted:
        # AC7-D9: map reason → X-Auth-Reason header value.
        if decision.reason == "LEVEL_ZERO":
            header_value = "LEVEL_ZERO"
            detail = _DETAIL_LEVEL_ZERO
        else:
            # NOT_FOUND / NOT_VERIFIED / INACTIVE collapse to NOT_REGISTERED
            # — no account-existence enumeration.
            header_value = "NOT_REGISTERED"
            detail = _DETAIL_NOT_REGISTERED

        logger.info("auth.callback.denied reason=%s", decision.reason)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers={"X-Auth-Reason": header_value},
        )

    # ---- 5. Grant: issue JWT cookie + return body ----
    # Stub call delegated to AC-8 (`jwt_session.issue_session_cookie`).
    session_issuer(
        response,
        staff_id=decision.staff_id,
        role=decision.role,
        procurement_level=decision.procurement_level,
    )

    # AC7-D10: log the non-PII outcome only.
    logger.info(
        "auth.callback.granted staff_id=%s role=%s level=%s",
        decision.staff_id,
        decision.role,
        decision.procurement_level,
    )

    return SessionResponse(
        role=decision.role,
        procurement_level=decision.procurement_level,
        staff_id=decision.staff_id,         # AC9-D4
    )


# ---------------------------------------------------------------------------
# AC-9 — POST /api/auth/logout, GET /api/auth/me
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> Response:
    """End the current session.

    AC9-D1 + AC9-D3: idempotent and unauthenticated. We always clear the
    cookie and return 204, even if there was no valid session — this is
    the only way the SPA can recover cleanly when its session has already
    expired server-side.
    """
    delete_session_cookie(response, secure=settings.jwt_cookie_secure)
    logger.info("auth.logout")                  # AC9-D6: no PII
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/me",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_session(
    claims: SessionClaims = Depends(require_authenticated),
) -> SessionResponse:
    """Return the current session's claims.

    AC9-D5: failure is handled by `require_authenticated` — same 401 +
    body envelope as every other protected endpoint. AC9-D6: success path
    logs nothing — called on every SPA mount, would flood logs.
    """
    return SessionResponse(
        role=claims.role,
        procurement_level=claims.procurement_level,
        staff_id=claims.staff_id,
    )
