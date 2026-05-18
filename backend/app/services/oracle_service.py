"""
🟡 YELLOW ZONE — Oracle data-access service.

Ratified decisions: docs/decision-log/AC-11-oracle-staff-lookup.md
(AC11-D1 … AC11-D9).

This story (AC-11) implements only `get_staff_by_employee_id`. The other
methods on `OracleService` per FUNCTIONAL_DESIGN.md §6.5
(`list_vendors`, `get_vendor_by_id`) are AC-12 / AC-15.

PII discipline:

* `EMPLOYEE_ID` is PII (DATA_MODEL.md §4.1) but is the lookup parameter
  ratified by FR-03 + ADR-009. **Always parameter-bind**, never f-string.
* `FULL_NAME` and `EMAIL` are PII and **MUST NOT be selected** by this
  query. The `StaffRecord` dataclass omits them. Any future need for
  those fields is a new, narrower query — not an extension of this one.
* Logs **never** contain the raw `employee_id`. A SHA-256 first-12 hex
  hash is used for correlation (AC11-D7) — opaque to a casual reader,
  reversible only with the original value, never alone.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal, Optional

import oracledb

from app.utils.logging import get_logger

logger = get_logger(__name__)


# AC11-D5: SQL pinned at module level, parameter-bound, no f-strings. The
# SELECT list is exhaustive — adding a column requires a code change AND
# a decision-log update, because some columns in STAFF are PII.
_SELECT_STAFF_BY_EMPLOYEE_ID = """\
SELECT STAFF_ID, EMPLOYEE_ID, ROLE, PROCUREMENT_LEVEL, IDME_VERIFIED, ACTIVE
FROM STAFF
WHERE EMPLOYEE_ID = :employee_id
"""

# Schema-driven constants. CHAR(1) Y/N columns are coerced at the
# boundary (AC11-D1); we don't propagate the database's string convention.
_YES = "Y"
_NO = "N"
_VALID_YN = frozenset({_YES, _NO})
_VALID_ROLES = frozenset({"ADMIN", "STAFF"})


@dataclass(frozen=True)
class StaffRecord:
    """The slice of `STAFF` this service is permitted to return.

    Note the deliberate absence of `FULL_NAME` and `EMAIL`. Adding them
    here means adding them to the SELECT — see PII discipline note in
    the module docstring before doing so.
    """
    staff_id: int
    employee_id: str
    role: Literal["ADMIN", "STAFF"]
    procurement_level: int
    idme_verified: bool
    active: bool


class OracleUnavailable(Exception):
    """Raised when the database is unreachable / authentication fails /
    the network is down. Callers map to 503.
    """


class OracleSchemaError(Exception):
    """Raised when a row comes back with an unexpected shape or value
    (e.g. `ROLE` not in {ADMIN, STAFF}, `IDME_VERIFIED` not in {Y, N}).
    Callers map to 500 — this indicates the DB and code have drifted.
    """


def _hash_employee_id(employee_id: str) -> str:
    """AC11-D7: short SHA-256 prefix used as a log-only correlation key.

    Opaque to a reader; reversible only with the original value. We
    deliberately don't salt — the goal is correlation across a single
    process's logs, not anti-rainbow-table secrecy.
    """
    return hashlib.sha256(employee_id.encode("utf-8")).hexdigest()[:12]


def _coerce_yn(value: object, *, column: str) -> bool:
    """`Y` → True, `N` → False, anything else → schema error."""
    if value not in _VALID_YN:
        raise OracleSchemaError(
            f"unexpected {column} value: {value!r} (expected 'Y' or 'N')"
        )
    return value == _YES


def _row_to_staff_record(row: tuple) -> StaffRecord:
    """Map a 6-column row to a `StaffRecord` with validation."""
    if len(row) != 6:
        raise OracleSchemaError(
            f"expected 6 columns in STAFF row, got {len(row)}"
        )

    staff_id, employee_id, role, procurement_level, idme_verified, active = row

    if role not in _VALID_ROLES:
        raise OracleSchemaError(
            f"unexpected ROLE value: {role!r} (expected ADMIN or STAFF)"
        )

    return StaffRecord(
        staff_id=int(staff_id),
        employee_id=str(employee_id),
        role=role,                                           # type: ignore[arg-type]
        procurement_level=int(procurement_level),
        idme_verified=_coerce_yn(idme_verified, column="IDME_VERIFIED"),
        active=_coerce_yn(active, column="ACTIVE"),
    )


def get_staff_by_employee_id(
    connection: oracledb.Connection,
    employee_id: str,
) -> Optional[StaffRecord]:
    """Look up a single STAFF row by EMPLOYEE_ID.

    Returns `None` when no row matches (AC11-D6 — not an error).
    Raises `OracleUnavailable` on connection/network failure,
    `OracleSchemaError` on a row whose values don't match the
    declared schema.
    """
    employee_id_hash = _hash_employee_id(employee_id)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                _SELECT_STAFF_BY_EMPLOYEE_ID,
                {"employee_id": employee_id},
            )
            row = cursor.fetchone()
    except oracledb.DatabaseError as exc:
        # AC11-D6 — network, auth, ORA-* errors. Never leak the original
        # message (it can contain hostname / DSN fragments).
        logger.warning(
            "oracle.staff_lookup employee_id_hash=%s outcome=unavailable err=%s",
            employee_id_hash,
            type(exc).__name__,
        )
        raise OracleUnavailable("oracle is unreachable") from exc

    if row is None:
        logger.info(
            "oracle.staff_lookup employee_id_hash=%s outcome=not_found",
            employee_id_hash,
        )
        return None

    record = _row_to_staff_record(row)

    logger.info(
        "oracle.staff_lookup employee_id_hash=%s outcome=found",
        employee_id_hash,
    )
    return record
