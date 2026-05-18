"""
🟡 YELLOW ZONE — interface defined for AC-7; body to be filled in by AC-13.

Ratified decision: docs/decision-log/AC-7-callback.md (AC7-D8).

This module is the contract between AC-7 (callback) and AC-13 (access
decision). AC-7 calls `decide_access(sub)` and receives an `AccessDecision`.
AC-13 will implement the real Oracle STAFF lookup + decision tree
(FUNCTIONAL_DESIGN.md §6.6).

For now, the function body raises `NotImplementedError`. AC-7's tests
inject a mock via `Depends(get_access_decider)` in
`backend/app/api/auth.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


AccessReason = Literal[
    "GRANTED",
    "NOT_FOUND",       # no STAFF row for this sub
    "NOT_VERIFIED",    # STAFF.IDME_VERIFIED != 'Y'
    "INACTIVE",        # STAFF.ACTIVE != 'Y'
    "LEVEL_ZERO",      # STAFF.PROCUREMENT_LEVEL == 0
]


@dataclass(frozen=True)
class AccessDecision:
    """Outcome of `decide_access`.

    `granted=True`  → `reason="GRANTED"`; `staff_id`/`role`/`procurement_level`
                      are all populated.
    `granted=False` → `reason` is one of the denial reasons above; the
                      remaining fields are None.

    Per AC7-D9, the AC-7 endpoint maps the reason to `X-Auth-Reason`:
      * LEVEL_ZERO → "LEVEL_ZERO"
      * NOT_FOUND / NOT_VERIFIED / INACTIVE → collapsed to "NOT_REGISTERED"
        (no account-existence enumeration leak).
    """

    granted: bool
    reason: AccessReason
    staff_id: Optional[int] = None
    role: Optional[Literal["ADMIN", "STAFF"]] = None
    procurement_level: Optional[int] = None


def decide_access(sub: str) -> AccessDecision:
    """Look up the user in Oracle STAFF and decide access.

    Decision tree (FUNCTIONAL_DESIGN.md §6.6), evaluated in order:
      1. STAFF row missing            → NOT_FOUND
      2. STAFF.IDME_VERIFIED != 'Y'   → NOT_VERIFIED
      3. STAFF.ACTIVE != 'Y'          → INACTIVE
      4. STAFF.PROCUREMENT_LEVEL == 0 → LEVEL_ZERO
      5. otherwise                    → GRANTED

    To be implemented by AC-13 (Jira). The signature and dataclass are
    contractually fixed here — AC-13 must not change them.
    """
    raise NotImplementedError(
        "access_service.decide_access is implemented by AC-13. "
        "Tests should override the `get_access_decider` FastAPI dependency."
    )
