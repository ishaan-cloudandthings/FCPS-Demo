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
            (1, "FCPS-001", "ADMIN", 3, "Y", "Y"),
            StaffRecord(
                staff_id=1,
                employee_id="FCPS-001",
                role="ADMIN",
                procurement_level=3,
                idme_verified=True,
                active=True,
            ),
        ),
        (
            (2, "FCPS-002", "STAFF", 2, "Y", "Y"),
            StaffRecord(
                staff_id=2,
                employee_id="FCPS-002",
                role="STAFF",
                procurement_level=2,
                idme_verified=True,
                active=True,
            ),
        ),
        (
            # N/N — inactive and unverified, still maps cleanly (the access
            # decision happens in access_service, not here).
            (7, "FCPS-007", "STAFF", 1, "N", "N"),
            StaffRecord(
                staff_id=7,
                employee_id="FCPS-007",
                role="STAFF",
                procurement_level=1,
                idme_verified=False,
                active=False,
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
    assert get_staff_by_employee_id(conn, "FCPS-404") is None


# ---------------------------------------------------------------------------
# Failure modes (AC11-D6)
# ---------------------------------------------------------------------------


def test_database_error_raises_oracle_unavailable():
    conn = _make_connection(
        execute_raises=oracledb.DatabaseError("ORA-12541: TNS:no listener"),
    )

    with pytest.raises(OracleUnavailable):
        get_staff_by_employee_id(conn, "FCPS-001")


@pytest.mark.parametrize(
    "row",
    [
        # ROLE not in allowlist.
        (1, "FCPS-001", "SUPERADMIN", 3, "Y", "Y"),
        # IDME_VERIFIED not in {Y, N}.
        (1, "FCPS-001", "ADMIN", 3, "MAYBE", "Y"),
        # ACTIVE not in {Y, N}.
        (1, "FCPS-001", "ADMIN", 3, "Y", "TRUE"),
        # Too few columns — schema drift.
        (1, "FCPS-001", "ADMIN", 3, "Y"),
    ],
)
def test_bad_row_shape_raises_schema_error(row):
    conn = _make_connection(fetchone_return=row)

    with pytest.raises(OracleSchemaError):
        get_staff_by_employee_id(conn, "FCPS-001")


# ---------------------------------------------------------------------------
# PII-in-logs guardrail (AC11-D7 + AC11-D9)
# ---------------------------------------------------------------------------


def test_employee_id_is_never_in_logs(caplog):
    """The raw employee_id substring must NEVER appear in any log line
    emitted by this service, for any code path.

    We exercise found / not_found / unavailable / schema_error all in
    one test and assert across them.
    """
    employee_id = "FCPS-SENSITIVE-001"

    caplog.set_level(logging.DEBUG, logger="app.services.oracle_service")

    # Path 1 — found.
    conn_found = _make_connection(
        fetchone_return=(1, employee_id, "ADMIN", 3, "Y", "Y"),
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
        fetchone_return=(1, employee_id, "SUPERADMIN", 3, "Y", "Y"),
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
        fetchone_return=(1, "FCPS-001", "ADMIN", 3, "Y", "Y"),
    )
    get_staff_by_employee_id(conn, "FCPS-001")

    # sha256("FCPS-001")[:12] = "4cd16fda6d4d" — pin the prefix.
    import hashlib

    expected_hash = hashlib.sha256(b"FCPS-001").hexdigest()[:12]
    assert f"employee_id_hash={expected_hash}" in caplog.text
    assert "outcome=found" in caplog.text
