"""
🟡 YELLOW ZONE — access decision service.

Ratified decisions:
    docs/decision-log/AC-13-access-service.md (AC13-D1 … AC13-D6)
    docs/decision-log/AC-7-callback.md      (AC7-D8 — contract was fixed at AC-7)
    docs/adr/ADR-015-role-model-simplification.md  ← role model + decision tree changes

Decision tree per [FUNCTIONAL_DESIGN.md §6.6](../../../docs/requirements/FUNCTIONAL_DESIGN.md),
evaluated in order (post-ADR-015):

  1. STAFF row missing            → NOT_FOUND
  2. STAFF.IDME_VERIFIED != 'Y'   → NOT_VERIFIED
  3. STAFF.ACTIVE != 'Y'          → INACTIVE
  4. STAFF.ROLE == 'NON_STAFF'    → NON_STAFF
  5. otherwise                    → GRANTED

The first three denial reasons collapse to `X-Auth-Reason: NOT_REGISTERED`
at the router boundary (no account-existence enumeration leak — FR-03 +
AC7-D9). NON_STAFF carries its own header value.

PII discipline (AC13-D4 / AC7-D11):
- `sub` is the ID.me sub which equals `STAFF.EMPLOYEE_ID` per ADR-009 — PII.
- Never log the raw value. Use the SHA-256-first-12 hash from
  `oracle_service._hash_employee_id` for log correlation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import oracledb

from app.services.oracle_service import (
    StaffRecord,
    _hash_employee_id,
    get_staff_by_employee_id,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


AccessReason = Literal[
    "GRANTED",
    "NOT_FOUND",       # no STAFF row for this sub
    "NOT_VERIFIED",    # STAFF.IDME_VERIFIED != 'Y'
    "INACTIVE",        # STAFF.ACTIVE != 'Y'
    "NON_STAFF",       # STAFF.ROLE == 'NON_STAFF' (ADR-015)
]


@dataclass(frozen=True)
class AccessDecision:
    """Outcome of `decide_access`.

    `granted=True`  → `reason="GRANTED"`; `staff_id` and `role` are populated.
    `granted=False` → `reason` is one of the denial reasons; the remaining
                      fields are None.

    Per AC7-D9 + [ADR-015](../../../docs/adr/ADR-015-role-model-simplification.md),
    the AC-7 endpoint maps the reason to `X-Auth-Reason`:
      * NON_STAFF → "NON_STAFF"
      * NOT_FOUND / NOT_VERIFIED / INACTIVE → collapsed to "NOT_REGISTERED"
    """

    granted: bool
    reason: AccessReason
    staff_id: Optional[int] = None
    role: Optional[Literal["PROCUREMENT_SUPERVISOR", "REGULAR_STAFF"]] = None


def decide_access(
    connection: oracledb.Connection,
    sub: str,
) -> AccessDecision:
    """Look up the user in Oracle STAFF and decide access.

    Raises:
        OracleUnavailable: connection/network failure — caller maps to 503.
        OracleSchemaError: row shape drift — caller propagates to 500.

    The function itself only returns `AccessDecision`; infrastructure
    errors are propagated unchanged (AC13-D3) because they are not access
    decisions and conflating them would mask outages as denials.
    """
    employee_id_hash = _hash_employee_id(sub)

    # `sub` is treated as the STAFF.EMPLOYEE_ID per ADR-009 (ID.me sub
    # mapping). oracle_service does the parameter-bound query.
    staff: Optional[StaffRecord] = get_staff_by_employee_id(connection, sub)

    decision = _evaluate(staff)

    logger.info(
        "access_service.decided employee_id_hash=%s reason=%s",
        employee_id_hash,
        decision.reason,
    )
    return decision


def _evaluate(staff: Optional[StaffRecord]) -> AccessDecision:
    """Pure decision tree — no I/O, no logging. Kept separate so tests
    can exercise it without a mock connection if they want to.
    """
    if staff is None:
        return AccessDecision(granted=False, reason="NOT_FOUND")
    if not staff.idme_verified:
        return AccessDecision(granted=False, reason="NOT_VERIFIED")
    if not staff.active:
        return AccessDecision(granted=False, reason="INACTIVE")
    if staff.role == "NON_STAFF":
        return AccessDecision(granted=False, reason="NON_STAFF")
    return AccessDecision(
        granted=True,
        reason="GRANTED",
        staff_id=staff.staff_id,
        role=staff.role,                                # type: ignore[arg-type]
    )
