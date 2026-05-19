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
from datetime import date, datetime
from typing import Literal, Optional

import oracledb

from app.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# AC-16 — PROCUREMENT_ITEMS schema (DATA_MODEL.md §4.2 + ADR-006 APPROVED_AT)
# ---------------------------------------------------------------------------

# Variant tags match the Pydantic schemas in app.schemas.vendors (AC15-D2).
VariantTag = Literal["staff_l1", "staff_l2", "admin", "admin_detail"]
VendorStatus = Literal["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED"]

_VALID_VARIANT_TAGS = frozenset({"staff_l1", "staff_l2", "admin", "admin_detail"})
_VALID_STATUSES = frozenset({"PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED"})


# AC11-D5: SQL pinned at module level, parameter-bound, no f-strings. The
# SELECT list is exhaustive — adding a column requires a code change AND
# a decision-log update, because some columns in STAFF are PII.
#
# ADR-015: `PROCUREMENT_LEVEL` removed; `ROLE` is the single authority.
_SELECT_STAFF_BY_EMPLOYEE_ID = """\
SELECT STAFF_ID, EMPLOYEE_ID, ROLE, IDME_VERIFIED, ACTIVE
FROM STAFF
WHERE EMPLOYEE_ID = :employee_id
"""

# Schema-driven constants. CHAR(1) Y/N columns are coerced at the
# boundary (AC11-D1); we don't propagate the database's string convention.
_YES = "Y"
_NO = "N"
_VALID_YN = frozenset({_YES, _NO})

# ADR-015: three roles. NON_STAFF is a STAFF-table value that triggers
# denial in access_service; never reaches a session.
StaffRole = Literal["PROCUREMENT_SUPERVISOR", "REGULAR_STAFF", "NON_STAFF"]
_VALID_STAFF_ROLES = frozenset(
    {"PROCUREMENT_SUPERVISOR", "REGULAR_STAFF", "NON_STAFF"}
)


@dataclass(frozen=True)
class StaffRecord:
    """The slice of `STAFF` this service is permitted to return.

    Per [ADR-015](../../../docs/adr/ADR-015-role-model-simplification.md):
    `procurement_level` removed; `role` is the single authority field.

    Note the deliberate absence of `FULL_NAME` and `EMAIL`. Adding them
    here means adding them to the SELECT — see PII discipline note in
    the module docstring before doing so.
    """
    staff_id: int
    employee_id: str
    role: StaffRole
    idme_verified: bool
    active: bool


class OracleUnavailable(Exception):
    """Raised when the database is unreachable / authentication fails /
    the network is down. Callers map to 503.
    """


class OracleSchemaError(Exception):
    """Raised when a row comes back with an unexpected shape or value
    (e.g. `ROLE` not in the ADR-015 allowlist, `IDME_VERIFIED` not in
    {Y, N}). Callers map to 500 — this indicates the DB and code have
    drifted.
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
    """Map a 5-column row to a `StaffRecord` with validation."""
    if len(row) != 5:
        raise OracleSchemaError(
            f"expected 5 columns in STAFF row, got {len(row)}"
        )

    staff_id, employee_id, role, idme_verified, active = row

    if role not in _VALID_STAFF_ROLES:
        raise OracleSchemaError(
            f"unexpected ROLE value: {role!r} "
            f"(expected one of {sorted(_VALID_STAFF_ROLES)})"
        )

    return StaffRecord(
        staff_id=int(staff_id),
        employee_id=str(employee_id),
        role=role,                                           # type: ignore[arg-type]
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


# ---------------------------------------------------------------------------
# AC-16 — PROCUREMENT_ITEMS queries
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VendorRow:
    """Union shape returned by `list_vendors` and `get_vendor_by_id`.

    The fields a caller actually receives depend on the variant_tag:
    list rows for L1 omit `status` / `unit_price` / `contact_name`
    (they're `None`); detail rows fill everything in. The router maps
    `variant_tag` → the matching Pydantic schema in
    `app.schemas.vendors`.

    Per AC15-D2 / AC16-D2, the dataclass deliberately models the union
    so the service layer can return a single concrete type. Pydantic at
    the response boundary enforces per-variant shape.
    """
    variant_tag: VariantTag
    item_id: int
    vendor_name: str
    item_name: str
    category: str
    # List-shape-narrowing fields:
    status: Optional[VendorStatus] = None
    unit_price: Optional[float] = None
    contact_name: Optional[str] = None
    # Detail-only (ADR-013):
    contact_email: Optional[str] = None
    # ADR-006 — admin detail "Approved on: <date>"
    approved_at: Optional[date] = None
    # Detail-only metadata
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None


# AC16-D3: column lists picked from a fixed allowlist. NEVER include
# user input here — these constants compose the SELECT list, not WHERE.
# BANK_DETAILS is deliberately absent everywhere (ADR-012).
_BASE_COLS = ["ITEM_ID", "VENDOR_NAME", "ITEM_NAME", "CATEGORY"]
_CONTACT_NAME_COL = ["CONTACT_NAME"]
_ADMIN_LIST_EXTRA_COLS = ["STATUS", "UNIT_PRICE"]
_DETAIL_EXTRA_COLS = [
    "STATUS",
    "UNIT_PRICE",
    "CONTACT_NAME",
    "CONTACT_EMAIL",
    "APPROVED_AT",
    "CREATED_DATE",
    "UPDATED_DATE",
]

# Static WHERE clause string — no parameter binding needed (no user input).
# AC16-D3: literal "APPROVED" is a hard-coded enum value, not user input.
_WHERE_APPROVED_ONLY = "WHERE STATUS = 'APPROVED'"


def _list_vendors_sql(
    *,
    only_approved: bool,
    include_contact: bool,
    include_status: bool,
) -> tuple[str, list[str]]:
    """Compose the SELECT for `list_vendors`. Returns (sql, ordered-col-list).

    The col-list is returned so `_row_to_vendor_row` can map by index
    deterministically.
    """
    cols = list(_BASE_COLS)
    if include_contact:
        cols += _CONTACT_NAME_COL
    if include_status:
        cols += _ADMIN_LIST_EXTRA_COLS

    select_cols = ", ".join(cols)
    where = _WHERE_APPROVED_ONLY if only_approved else ""
    sql = f"SELECT {select_cols} FROM PROCUREMENT_ITEMS {where} ORDER BY ITEM_ID"
    return sql, cols


# AC16-D3: detail SQL is a fixed string; only `item_id` is bound.
_SELECT_VENDOR_BY_ID = (
    "SELECT "
    + ", ".join(_BASE_COLS + _DETAIL_EXTRA_COLS)
    + " FROM PROCUREMENT_ITEMS WHERE ITEM_ID = :item_id"
)


def _coerce_status(value: object) -> VendorStatus:
    if value not in _VALID_STATUSES:
        raise OracleSchemaError(
            f"unexpected STATUS value: {value!r} (expected one of {sorted(_VALID_STATUSES)})"
        )
    return value  # type: ignore[return-value]


def _row_to_vendor_row(
    row: tuple,
    cols: list[str],
    *,
    variant_tag: VariantTag,
) -> VendorRow:
    """Map a SELECT row to `VendorRow` by column-list order."""
    if len(row) != len(cols):
        raise OracleSchemaError(
            f"row has {len(row)} columns, expected {len(cols)}"
        )

    by_col = dict(zip(cols, row))

    status = by_col.get("STATUS")
    if status is not None:
        status = _coerce_status(status)

    return VendorRow(
        variant_tag=variant_tag,
        item_id=int(by_col["ITEM_ID"]),
        vendor_name=str(by_col["VENDOR_NAME"]),
        item_name=str(by_col["ITEM_NAME"]),
        category=str(by_col["CATEGORY"]),
        status=status,
        unit_price=(
            float(by_col["UNIT_PRICE"])
            if by_col.get("UNIT_PRICE") is not None
            else None
        ),
        contact_name=by_col.get("CONTACT_NAME"),
        contact_email=by_col.get("CONTACT_EMAIL"),
        approved_at=by_col.get("APPROVED_AT"),
        created_date=by_col.get("CREATED_DATE"),
        updated_date=by_col.get("UPDATED_DATE"),
    )


def list_vendors(
    connection: oracledb.Connection,
    *,
    only_approved: bool,
    include_contact: bool,
    include_status: bool,
    variant_tag: VariantTag,
) -> list[VendorRow]:
    """Return all PROCUREMENT_ITEMS rows shaped per the flags.

    `variant_tag` is the discriminator the API will emit (AC15-D2).
    Today the router always passes `"admin"` ("everyone sees everything");
    AC-17 wires `rbac_service.params_for(...)` to vary by role.

    Raises:
        OracleUnavailable: on connection/network failure (caller → 503).
    """
    if variant_tag not in _VALID_VARIANT_TAGS:
        raise ValueError(f"invalid variant_tag: {variant_tag!r}")

    sql, cols = _list_vendors_sql(
        only_approved=only_approved,
        include_contact=include_contact,
        include_status=include_status,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
    except oracledb.DatabaseError as exc:
        logger.warning(
            "oracle.vendor_list outcome=unavailable err=%s",
            type(exc).__name__,
        )
        raise OracleUnavailable("oracle is unreachable") from exc

    result = [_row_to_vendor_row(r, cols, variant_tag=variant_tag) for r in rows]

    logger.info(
        "oracle.vendor_list count=%d only_approved=%s include_contact=%s",
        len(result),
        only_approved,
        include_contact,
    )
    return result


def get_vendor_by_id(
    connection: oracledb.Connection,
    item_id: int,
) -> Optional[VendorRow]:
    """Return the full PROCUREMENT_ITEMS row for `item_id`, or None.

    This is the only path that selects `CONTACT_EMAIL` (ADR-013).
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_SELECT_VENDOR_BY_ID, {"item_id": item_id})
            row = cursor.fetchone()
    except oracledb.DatabaseError as exc:
        logger.warning(
            "oracle.vendor_get item_id=%s outcome=unavailable err=%s",
            item_id,
            type(exc).__name__,
        )
        raise OracleUnavailable("oracle is unreachable") from exc

    if row is None:
        logger.info(
            "oracle.vendor_get item_id=%s outcome=not_found",
            item_id,
        )
        return None

    detail_cols = _BASE_COLS + _DETAIL_EXTRA_COLS
    record = _row_to_vendor_row(row, detail_cols, variant_tag="admin_detail")

    logger.info(
        "oracle.vendor_get item_id=%s outcome=found",
        item_id,
    )
    return record
