"""
🔴 RED ZONE — implements AC-7 (ID.me HTTP client).

Ratified decisions: docs/decision-log/AC-7-callback.md (AC7-D1, AC7-D2,
AC7-D7) and FUNCTIONAL_DESIGN.md §6.1 D-FD-10.

`httpx`-based client for ID.me's OAuth `/oauth/token` endpoint. Used by
`POST /api/auth/callback` to exchange the authorization code for an ID
token.

Hard contract:
* 5 s timeout (D-FD-10).
* Any non-2xx response, network error, or JSON-parse failure is wrapped
  in `IDMEUnreachable`. The caller maps that to HTTP 502.
"""
from __future__ import annotations

from typing import TypedDict

import httpx

from app.utils.logging import get_logger

logger = get_logger(__name__)

TOKEN_EXCHANGE_TIMEOUT_SECONDS: float = 5.0  # D-FD-10


class IDMETokenResponse(TypedDict, total=False):
    """Subset of the ID.me /oauth/token response we care about."""

    access_token: str
    id_token: str
    expires_in: int
    token_type: str


class IDMEUnreachable(Exception):
    """Raised when token exchange cannot complete. Caller returns 502."""


def exchange_code_for_token(
    *,
    token_url: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    timeout_seconds: float = TOKEN_EXCHANGE_TIMEOUT_SECONDS,
) -> IDMETokenResponse:
    """POST to ID.me /oauth/token to exchange an authorisation `code` for
    an `id_token`.

    Form-encoded body per OAuth 2.0 spec. ID.me's sandbox accepts both
    form-encoded and JSON; we use form-encoded to match the most common
    convention and ID.me's docs.
    """
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        # AC7-D10: log the error class only, never the request body.
        logger.warning(
            "auth.idme.token_exchange_failed err=%s",
            type(exc).__name__,
        )
        raise IDMEUnreachable("ID.me token exchange failed") from exc
