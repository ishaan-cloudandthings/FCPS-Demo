"""Tests for `app.services.access_service` — AC-13.

Maps to ratified decisions in `docs/decision-log/AC-13-access-service.md`:

* AC13-D2 — decision tree branches (parametrised).
* AC13-D3 — Oracle errors propagate, never become denials.
* AC13-D4 — `employee_id_hash` in logs, never raw `sub`.
* AC13-D5 — 5 branches + 2 error tests + PII guardrail.
"""
from __future__ import annotations

import hashlib
import logging
from unittest.mock import MagicMock, patch

import pytest

from app.services.access_service import (
    AccessDecision,
    decide_access,
)
from app.services.oracle_service import (
    OracleSchemaError,
    OracleUnavailable,
    StaffRecord,
)


SUB = "FCPS-SENSITIVE-007"


def _staff(**overrides) -> StaffRecord:
    base = dict(
        staff_id=42,
        employee_id=SUB,
        role="STAFF",
        procurement_level=2,
        idme_verified=True,
        active=True,
    )
    base.update(overrides)
    return StaffRecord(**base)


# ---------------------------------------------------------------------------
# Decision tree (AC13-D2) — five branches, evaluated in order
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "staff,expected",
    [
        # 1. NOT_FOUND
        (
            None,
            AccessDecision(granted=False, reason="NOT_FOUND"),
        ),
        # 2. NOT_VERIFIED — beats every later check
        (
            _staff(idme_verified=False, active=False, procurement_level=0),
            AccessDecision(granted=False, reason="NOT_VERIFIED"),
        ),
        # 3. INACTIVE — beats LEVEL_ZERO
        (
            _staff(active=False, procurement_level=0),
            AccessDecision(granted=False, reason="INACTIVE"),
        ),
        # 4. LEVEL_ZERO
        (
            _staff(procurement_level=0),
            AccessDecision(granted=False, reason="LEVEL_ZERO"),
        ),
        # 5. GRANTED
        (
            _staff(procurement_level=2),
            AccessDecision(
                granted=True,
                reason="GRANTED",
                staff_id=42,
                role="STAFF",
                procurement_level=2,
            ),
        ),
    ],
)
def test_decision_tree_branches(staff, expected):
    conn = MagicMock(name="connection")
    with patch(
        "app.services.access_service.get_staff_by_employee_id",
        return_value=staff,
    ):
        result = decide_access(conn, SUB)
    assert result == expected


def test_granted_admin_record_carries_all_claims():
    conn = MagicMock(name="connection")
    admin = _staff(staff_id=1, role="ADMIN", procurement_level=3, employee_id="FCPS-001")
    with patch(
        "app.services.access_service.get_staff_by_employee_id",
        return_value=admin,
    ):
        result = decide_access(conn, "FCPS-001")
    assert result == AccessDecision(
        granted=True,
        reason="GRANTED",
        staff_id=1,
        role="ADMIN",
        procurement_level=3,
    )


# ---------------------------------------------------------------------------
# Error propagation (AC13-D3)
# ---------------------------------------------------------------------------


def test_oracle_unavailable_propagates():
    conn = MagicMock(name="connection")
    with patch(
        "app.services.access_service.get_staff_by_employee_id",
        side_effect=OracleUnavailable("simulated"),
    ):
        with pytest.raises(OracleUnavailable):
            decide_access(conn, SUB)


def test_oracle_schema_error_propagates():
    conn = MagicMock(name="connection")
    with patch(
        "app.services.access_service.get_staff_by_employee_id",
        side_effect=OracleSchemaError("simulated"),
    ):
        with pytest.raises(OracleSchemaError):
            decide_access(conn, SUB)


# ---------------------------------------------------------------------------
# PII-in-logs guardrail (AC13-D4)
# ---------------------------------------------------------------------------


def test_employee_id_is_never_in_logs(caplog):
    """The raw `sub` (= EMPLOYEE_ID) must NEVER appear in any log line
    from this service, across all five decision branches plus the two
    error paths.
    """
    caplog.set_level(logging.DEBUG, logger="app.services.access_service")
    conn = MagicMock(name="connection")

    paths = [
        (None, None),                                # NOT_FOUND
        (_staff(idme_verified=False), None),         # NOT_VERIFIED
        (_staff(active=False), None),                # INACTIVE
        (_staff(procurement_level=0), None),         # LEVEL_ZERO
        (_staff(procurement_level=2), None),         # GRANTED
        (None, OracleUnavailable("x")),              # error: unavailable
        (None, OracleSchemaError("x")),              # error: schema
    ]
    for staff, raise_exc in paths:
        with patch(
            "app.services.access_service.get_staff_by_employee_id",
            side_effect=raise_exc,
            return_value=staff,
        ):
            try:
                decide_access(conn, SUB)
            except (OracleUnavailable, OracleSchemaError):
                pass

    assert SUB not in caplog.text, (
        f"PII leak: raw sub {SUB!r} appeared in logs."
    )


def test_employee_id_hash_appears_in_log_line(caplog):
    """AC13-D4 — the hash IS present so support can correlate. Pin the
    format so changes are intentional.
    """
    caplog.set_level(logging.INFO, logger="app.services.access_service")
    conn = MagicMock(name="connection")
    with patch(
        "app.services.access_service.get_staff_by_employee_id",
        return_value=_staff(procurement_level=2),
    ):
        decide_access(conn, SUB)

    expected_hash = hashlib.sha256(SUB.encode("utf-8")).hexdigest()[:12]
    assert f"employee_id_hash={expected_hash}" in caplog.text
    assert "reason=GRANTED" in caplog.text
