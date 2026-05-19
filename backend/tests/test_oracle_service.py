"""Tests for `app.services.oracle_service` — AC-11.

Maps to ratified decisions in `docs/decision-log/AC-11-oracle-staff-lookup.md`:

* AC11-D1 — `StaffRecord` shape + `Y/N` → `bool` coercion.
* AC11-D5 — exact SQL, dict-bound parameters, no f-strings.
* AC11-D6 — three failure modes: `OracleUnavailable`, `OracleSchemaError`,
  return `None` on no-row.
* AC11-D7 — `employee_id_hash` in logs, never the raw value.
* AC11-D9 — dedicated PII-in-logs guardrail.

The test suite mocks at the `oracledb.connect()` boundary — no real
Oracle XE is required. An `@pytest.mark.oracle_integration` marker is
reserved for future smoke runs against a live DB.
"""
from __future__ import annotations

import logging
from unittest.mock import MagicMock

import oracledb
import pytest

from app.services.oracle_service import (
    OracleSchemaError,
    OracleUnavailable,
    StaffRecord,
    _SELECT_STAFF_BY_EMPLOYEE_ID,
    get_staff_by_employee_id,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_connection(*, fetchone_return=None, execute_raises=None) -> MagicMock:
    """Build a mock `oracledb.Connection` whose cursor returns a scripted row.

    The cursor is a context manager — matches `with connection.cursor()`
    in the service.
    """
    cursor = MagicMock(name="cursor")
    if execute_raises is not None:
        cursor.execute.side_effect = execute_raises
    cursor.fetchone.return_value = fetchone_return

    cursor_ctx = MagicMock(name="cursor_ctx")
    cursor_ctx.__enter__.return_value = cursor
    cursor_ctx.__exit__.return_value = False

    connection = MagicMock(name="connection")
    connection.cursor.return_value = cursor_ctx
    # Expose the inner cursor so tests can assert on `.execute` calls.
    connection._cursor = cursor
    return connection


# ---------------------------------------------------------------------------
# Happy paths (AC11-D1, AC11-D5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "row,expected",
    [
        (
            (1, "EMP-001", "PROCUREMENT_SUPERVISOR", "Y", "Y"),
            StaffRecord(
                staff_id=1,
                employee_id="EMP-001",
                role="PROCUREMENT_SUPERVISOR",
                idme_verified=True,
                active=True,
            ),
        ),
        (
            (2, "EMP-002", "REGULAR_STAFF", "Y", "Y"),
            StaffRecord(
                staff_id=2,
                employee_id="EMP-002",
                role="REGULAR_STAFF",
                idme_verified=True,
                active=True,
            ),
        ),
        (
            # N/N — inactive and unverified, still maps cleanly (the access
            # decision happens in access_service, not here).
            (7, "EMP-007", "REGULAR_STAFF", "N", "N"),
            StaffRecord(
                staff_id=7,
                employee_id="EMP-007",
                role="REGULAR_STAFF",
                idme_verified=False,
                active=False,
            ),
        ),
        # ADR-015: NON_STAFF is a valid row value — the row maps cleanly,
        # the denial happens in access_service.
        (
            (10, "EMP-010", "NON_STAFF", "Y", "Y"),
            StaffRecord(
                staff_id=10,
                employee_id="EMP-010",
                role="NON_STAFF",
                idme_verified=True,
                active=True,
            ),
        ),
    ],
)
def test_get_staff_by_employee_id_maps_row_to_dataclass(row, expected):
    conn = _make_connection(fetchone_return=row)

    result = get_staff_by_employee_id(conn, expected.employee_id)

    assert result == expected
    # AC11-D5 — exact SQL and dict-bound parameters.
    conn._cursor.execute.assert_called_once_with(
        _SELECT_STAFF_BY_EMPLOYEE_ID,
        {"employee_id": expected.employee_id},
    )


def test_sql_string_constant_has_no_format_placeholders():
    """AC11-D5: belt-and-braces. The SQL must NOT contain `{` (Python
    format) or `%s` (positional binding) — only the named `:employee_id`
    placeholder.
    """
    sql = _SELECT_STAFF_BY_EMPLOYEE_ID
    assert "{" not in sql
    assert "%s" not in sql
    assert ":employee_id" in sql


# ---------------------------------------------------------------------------
# Not-found path (AC11-D6)
# ---------------------------------------------------------------------------


def test_get_staff_by_employee_id_returns_none_when_no_row():
    conn = _make_connection(fetchone_return=None)
    assert get_staff_by_employee_id(conn, "EMP-404") is None


# ---------------------------------------------------------------------------
# Failure modes (AC11-D6)
# ---------------------------------------------------------------------------


def test_database_error_raises_oracle_unavailable():
    conn = _make_connection(
        execute_raises=oracledb.DatabaseError("ORA-12541: TNS:no listener"),
    )

    with pytest.raises(OracleUnavailable):
        get_staff_by_employee_id(conn, "EMP-001")


@pytest.mark.parametrize(
    "row",
    [
        # ROLE not in allowlist.
        (1, "EMP-001", "SUPERADMIN", "Y", "Y"),
        # Legacy ROLE values rejected (ADR-015).
        (1, "EMP-001", "ADMIN", "Y", "Y"),
        (1, "EMP-001", "STAFF", "Y", "Y"),
        # IDME_VERIFIED not in {Y, N}.
        (1, "EMP-001", "PROCUREMENT_SUPERVISOR", "MAYBE", "Y"),
        # ACTIVE not in {Y, N}.
        (1, "EMP-001", "PROCUREMENT_SUPERVISOR", "Y", "TRUE"),
        # Too few columns — schema drift.
        (1, "EMP-001", "PROCUREMENT_SUPERVISOR", "Y"),
    ],
)
def test_bad_row_shape_raises_schema_error(row):
    conn = _make_connection(fetchone_return=row)

    with pytest.raises(OracleSchemaError):
        get_staff_by_employee_id(conn, "EMP-001")


# ---------------------------------------------------------------------------
# PII-in-logs guardrail (AC11-D7 + AC11-D9)
# ---------------------------------------------------------------------------


def test_employee_id_is_never_in_logs(caplog):
    """The raw employee_id substring must NEVER appear in any log line
    emitted by this service, for any code path.

    We exercise found / not_found / unavailable / schema_error all in
    one test and assert across them.
    """
    employee_id = "EMP-SENSITIVE-001"

    caplog.set_level(logging.DEBUG, logger="app.services.oracle_service")

    # Path 1 — found.
    conn_found = _make_connection(
        fetchone_return=(1, employee_id, "PROCUREMENT_SUPERVISOR", "Y", "Y"),
    )
    get_staff_by_employee_id(conn_found, employee_id)

    # Path 2 — not_found.
    conn_missing = _make_connection(fetchone_return=None)
    get_staff_by_employee_id(conn_missing, employee_id)

    # Path 3 — unavailable.
    conn_down = _make_connection(
        execute_raises=oracledb.DatabaseError("simulated"),
    )
    try:
        get_staff_by_employee_id(conn_down, employee_id)
    except OracleUnavailable:
        pass

    # Path 4 — schema error.
    conn_bad = _make_connection(
        fetchone_return=(1, employee_id, "SUPERADMIN", "Y", "Y"),
    )
    try:
        get_staff_by_employee_id(conn_bad, employee_id)
    except OracleSchemaError:
        pass

    assert employee_id not in caplog.text, (
        f"PII leak: raw employee_id {employee_id!r} appeared in logs."
    )


def test_employee_id_hash_appears_in_log_line(caplog):
    """AC11-D7 — the hash IS in the log so support can correlate. This
    test pins the format so a change is intentional, not accidental.
    """
    caplog.set_level(logging.INFO, logger="app.services.oracle_service")
    conn = _make_connection(
        fetchone_return=(1, "EMP-001", "PROCUREMENT_SUPERVISOR", "Y", "Y"),
    )
    get_staff_by_employee_id(conn, "EMP-001")

    # sha256("EMP-001")[:12] = "4cd16fda6d4d" — pin the prefix.
    import hashlib

    expected_hash = hashlib.sha256(b"EMP-001").hexdigest()[:12]
    assert f"employee_id_hash={expected_hash}" in caplog.text
    assert "outcome=found" in caplog.text


# ===========================================================================
# AC-16 — PROCUREMENT_ITEMS queries
# ===========================================================================

from datetime import date, datetime

from app.services.oracle_service import (
    VendorRow,
    _BASE_COLS,
    _DETAIL_EXTRA_COLS,
    _SELECT_VENDOR_BY_ID,
    _list_vendors_sql,
    get_vendor_by_id,
    list_vendors,
)


# ---------------------------------------------------------------------------
# SQL composition (AC16-D3)
# ---------------------------------------------------------------------------


def test_list_sql_l1_shape_has_no_status_no_contact_no_approved_filter():
    sql, cols = _list_vendors_sql(
        only_approved=False, include_contact=False, include_status=False
    )
    assert "STATUS" not in cols
    assert "CONTACT_NAME" not in cols
    assert "WHERE" not in sql
    assert "BANK_DETAILS" not in sql
    assert "CONTACT_EMAIL" not in sql


def test_list_sql_l2_shape_adds_contact_name_filters_approved():
    sql, cols = _list_vendors_sql(
        only_approved=True, include_contact=True, include_status=False
    )
    assert "CONTACT_NAME" in cols
    assert "STATUS" not in cols
    assert "WHERE STATUS = 'APPROVED'" in sql
    assert "CONTACT_EMAIL" not in sql


def test_list_sql_admin_shape_has_status_and_unit_price_no_filter():
    sql, cols = _list_vendors_sql(
        only_approved=False, include_contact=True, include_status=True
    )
    assert "STATUS" in cols
    assert "UNIT_PRICE" in cols
    assert "CONTACT_NAME" in cols
    assert "WHERE" not in sql                       # admin sees all statuses
    assert "BANK_DETAILS" not in sql


def test_list_sql_never_contains_bank_details_or_contact_email():
    """ADR-012 / ADR-013 — across all 8 flag combinations."""
    for only_approved in (False, True):
        for include_contact in (False, True):
            for include_status in (False, True):
                sql, _ = _list_vendors_sql(
                    only_approved=only_approved,
                    include_contact=include_contact,
                    include_status=include_status,
                )
                assert "BANK_DETAILS" not in sql
                assert "CONTACT_EMAIL" not in sql


def test_detail_sql_includes_contact_email_and_approved_at():
    assert "CONTACT_EMAIL" in _SELECT_VENDOR_BY_ID
    assert "APPROVED_AT" in _SELECT_VENDOR_BY_ID
    # Parameter binding, no f-strings:
    assert ":item_id" in _SELECT_VENDOR_BY_ID
    assert "BANK_DETAILS" not in _SELECT_VENDOR_BY_ID


# ---------------------------------------------------------------------------
# Row mapping
# ---------------------------------------------------------------------------


def _make_cursor(rows):
    cursor = MagicMock(name="cursor")
    if isinstance(rows, list):
        cursor.fetchall.return_value = rows
        cursor.fetchone.return_value = rows[0] if rows else None
    else:
        cursor.fetchone.return_value = rows
    cursor_ctx = MagicMock()
    cursor_ctx.__enter__.return_value = cursor
    cursor_ctx.__exit__.return_value = False
    return cursor, cursor_ctx


def _conn_with_rows(rows):
    cursor, cursor_ctx = _make_cursor(rows)
    conn = MagicMock(name="connection")
    conn.cursor.return_value = cursor_ctx
    conn._cursor = cursor
    return conn


def test_list_vendors_admin_variant_maps_full_row():
    # cols order: ITEM_ID, VENDOR_NAME, ITEM_NAME, CATEGORY, CONTACT_NAME, STATUS, UNIT_PRICE
    rows = [
        (1, "Acme", "Widget", "Supplies", "Alice Vendor", "APPROVED", 9.99),
        (2, "Globex", "Gadget", "Technology", None, "PENDING", None),
    ]
    conn = _conn_with_rows(rows)
    result = list_vendors(
        conn,
        only_approved=False,
        include_contact=True,
        include_status=True,
        variant_tag="admin",
    )
    assert len(result) == 2
    assert result[0] == VendorRow(
        variant_tag="admin",
        item_id=1,
        vendor_name="Acme",
        item_name="Widget",
        category="Supplies",
        contact_name="Alice Vendor",
        status="APPROVED",
        unit_price=9.99,
    )
    assert result[1].contact_name is None
    assert result[1].unit_price is None


def test_list_vendors_l1_variant_omits_status_and_contact():
    rows = [(1, "Acme", "Widget", "Supplies")]
    conn = _conn_with_rows(rows)
    result = list_vendors(
        conn,
        only_approved=True,
        include_contact=False,
        include_status=False,
        variant_tag="staff_l1",
    )
    assert result[0].status is None
    assert result[0].contact_name is None


def test_list_vendors_rejects_unknown_status():
    rows = [(1, "Acme", "Widget", "Supplies", "Alice", "DRAFT", 1.0)]
    conn = _conn_with_rows(rows)
    with pytest.raises(OracleSchemaError):
        list_vendors(
            conn,
            only_approved=False,
            include_contact=True,
            include_status=True,
            variant_tag="admin",
        )


def test_list_vendors_rejects_invalid_variant_tag():
    conn = _conn_with_rows([])
    with pytest.raises(ValueError):
        list_vendors(
            conn,
            only_approved=False,
            include_contact=False,
            include_status=False,
            variant_tag="superadmin",  # type: ignore[arg-type]
        )


def test_list_vendors_propagates_oracle_unavailable():
    cursor, cursor_ctx = _make_cursor([])
    cursor.execute.side_effect = oracledb.DatabaseError("simulated")
    conn = MagicMock(name="connection")
    conn.cursor.return_value = cursor_ctx

    with pytest.raises(OracleUnavailable):
        list_vendors(
            conn,
            only_approved=False,
            include_contact=False,
            include_status=False,
            variant_tag="staff_l1",
        )


def test_get_vendor_by_id_returns_full_detail_row():
    cd = datetime(2026, 1, 1, 9, 0, 0)
    ud = datetime(2026, 2, 14, 10, 30, 0)
    ad = date(2026, 2, 14)
    row = (
        7, "Acme", "Widget", "Supplies",       # base cols
        "APPROVED", 9.99, "Alice Vendor",
        "alice@vendor.test", ad, cd, ud,
    )
    conn = _conn_with_rows(row)

    result = get_vendor_by_id(conn, 7)
    assert result is not None
    assert result.variant_tag == "admin_detail"
    assert result.item_id == 7
    assert result.contact_email == "alice@vendor.test"
    assert result.approved_at == ad
    assert result.created_date == cd
    assert result.updated_date == ud
    # Verify parameter binding used :item_id
    conn._cursor.execute.assert_called_once_with(
        _SELECT_VENDOR_BY_ID, {"item_id": 7}
    )


def test_get_vendor_by_id_returns_none_when_missing():
    conn = _conn_with_rows(None)
    assert get_vendor_by_id(conn, 999) is None


def test_get_vendor_by_id_propagates_oracle_unavailable():
    cursor, cursor_ctx = _make_cursor(None)
    cursor.execute.side_effect = oracledb.DatabaseError("simulated")
    conn = MagicMock(name="connection")
    conn.cursor.return_value = cursor_ctx

    with pytest.raises(OracleUnavailable):
        get_vendor_by_id(conn, 1)
