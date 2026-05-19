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


class DevLoginRequest(BaseModel):
    """POST /api/auth/dev-login request body.

    Per [ADR-014](../../../../docs/adr/ADR-014-demo-persona-login-dev-only.md)
    + DEV8: `persona` is a closed Literal — unknown personas 422 at
    Pydantic. Adding a new persona is a code change, not data-driven.

    Per [ADR-015](../../../../docs/adr/ADR-015-role-model-simplification.md),
    the persona list collapsed from 5 to 4: three business roles + the
    `not_registered` technical denial path.
    """

    model_config = ConfigDict(extra="forbid")
    persona: Literal[
        "procurement_supervisor",
        "regular_staff",
        "non_staff",
        "not_registered",
    ]


class DevLoginAvailableResponse(BaseModel):
    """GET /api/auth/dev-login/available response — DEV4."""

    model_config = ConfigDict(extra="forbid")
    available: Literal[True] = True


class SessionResponse(BaseModel):
    """Returned by POST /api/auth/callback and GET /api/auth/me.

    Per [ADR-015](../../../../docs/adr/ADR-015-role-model-simplification.md),
    `role` is the single authority field; `procurement_level` was
    dropped. The SPA hydrates its auth store from this shape on every
    mount (AC9-D4).
    """

    model_config = ConfigDict(extra="forbid")
    role: Literal["PROCUREMENT_SUPERVISOR", "REGULAR_STAFF"]
    staff_id: int
