"""Pydantic request/response schemas for the auth API.

Matches the contract in `docs/requirements/api-spec.yaml`.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AuthorizeUrlResponse(BaseModel):
    """Returned by POST /api/auth/login.

    Per AC6-D10: a single field, `extra="forbid"` so the client cannot
    rely on undocumented fields creeping in.
    """

    model_config = ConfigDict(extra="forbid")
    authorize_url: str


class CallbackRequest(BaseModel):
    """POST /api/auth/callback request body.

    Per AC7-D12: both fields required, both `min_length=1`,
    `extra="forbid"` to reject any unknown keys.
    """

    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1)
    state: str = Field(min_length=1)


class SessionResponse(BaseModel):
    """POST /api/auth/callback 200 response.

    Per FUNCTIONAL_DESIGN.md §6.1 D-FD-12 + api-spec.yaml `SessionResponse`.
    The Set-Cookie header carrying the JWT is the security side; this body
    is the SPA's confirmation of what the user just got.
    """

    model_config = ConfigDict(extra="forbid")
    role: Literal["ADMIN", "STAFF"]
    procurement_level: int = Field(ge=1, le=3)
