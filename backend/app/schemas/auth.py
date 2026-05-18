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
    """

    model_config = ConfigDict(extra="forbid")
    persona: Literal[
        "admin_l3",
        "staff_l2",
        "staff_l1",
        "level_zero",
        "not_registered",
    ]


class DevLoginAvailableResponse(BaseModel):
    """GET /api/auth/dev-login/available response — DEV4."""

    model_config = ConfigDict(extra="forbid")
    available: Literal[True] = True


class SessionResponse(BaseModel):
    """Returned by POST /api/auth/callback and GET /api/auth/me.

    Per FUNCTIONAL_DESIGN.md §6.1 + AC9-D4: the SPA hydrates its auth
    store from this shape on every mount, so `staff_id` is part of the
    contract. Single schema used by both endpoints — see AC-9 decision
    log for the rationale on not splitting it into a separate
    `MeResponse`.
    """

    model_config = ConfigDict(extra="forbid")
    role: Literal["ADMIN", "STAFF"]
    procurement_level: int = Field(ge=1, le=3)
    staff_id: int
