# AC-11 — Oracle connection factory + STAFF query: ratified decisions

| Field | Value |
|---|---|
| Jira story | [AC-11](https://cloudandthings.atlassian.net/browse/AC-11) — E2-S1 Oracle connection factory + STAFF query |
| Epic | [AC-3](https://cloudandthings.atlassian.net/browse/AC-3) — Procurement Data Access |
| Zones | 🟢 Green (`backend/app/core/database.py`) + 🟡 Yellow (`backend/app/services/oracle_service.py`) |
| Ratified on | 2026-05-18 |
| Ratified by | C&T Project Lead |
| Status | Ratified — implementation may proceed |

## What's in this file

Yellow Zone doesn't require the formal pre-code ratification ritual that
Red Zone does, but this story crosses the PII boundary (`STAFF`
table) and the database boundary at the same time — both deserve an
explicit record.

## PII alert (per [DATA_MODEL.md §4.1](../DATA_MODEL.md))

- **`EMPLOYEE_ID` is PII** and is the bound parameter on the query.
  Allowed because the entire ID.me-`sub` → `EMPLOYEE_ID` mapping is
  ratified by **FR-03 + [ADR-009](../adr/ADR-009-idme-sub-mapping.md)**.
  Discipline going forward: **parameter-bind only** (never f-string),
  **never log the raw value** (matches AC7-D11 and AC8-D13).
- **`FULL_NAME` and `EMAIL` are PII and MUST NOT be selected** in this
  story's query, despite living in the same table. The
  `StaffRecord` dataclass omits them — any future code that needs them
  must add a *separate, narrower* query rather than extending this one.

No policy is being violated; calling it out so the PII discipline is
unambiguous for any reviewer.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC11-D1 | `StaffRecord` shape | `@dataclass(frozen=True)` with exactly `staff_id: int, employee_id: str, role: Literal["ADMIN","STAFF"], procurement_level: int, idme_verified: bool, active: bool`. The `CHAR(1)` `Y/N` columns are coerced to `bool` at the service boundary — no `Y/N` strings escape this layer. |
| AC11-D2 | Connection lifecycle | Per-request `oracledb.connect()` via FastAPI dependency `get_oracle_connection()` that yields and then closes. **No pool** for the demo (NFR-17 thin mode + single-worker per AC6-D2). Pool is a phase-2 follow-up if/when multi-worker. |
| AC11-D3 | Env vars | New Settings fields: `oracle_host: str`, `oracle_port: int = 1521`, `oracle_service_name: str = "XE"`, `oracle_user: str`, `oracle_password: str`. All credentials required at startup; Pydantic enforces. No defaults for `oracle_user` / `oracle_password` (must come from env). |
| AC11-D4 | Thin-mode enforcement | `oracledb.connect(...)` only — **never** `oracledb.init_oracle_client()`. NFR-17 means no Oracle Client install. Module-level comment in `database.py` calls this out so a future contributor doesn't bring it back. |
| AC11-D5 | Query string location | Module-level constant `_SELECT_STAFF_BY_EMPLOYEE_ID` in `oracle_service.py`. Readable, grep-friendly. Bound params via dict (`{"employee_id": …}`). Exact SQL matches FUNCTIONAL_DESIGN.md §6.5: `SELECT STAFF_ID, EMPLOYEE_ID, ROLE, PROCUREMENT_LEVEL, IDME_VERIFIED, ACTIVE FROM STAFF WHERE EMPLOYEE_ID = :employee_id`. |
| AC11-D6 | Failure modes | Connection / network / bad-credentials → raise `OracleUnavailable`. Row with unexpected shape or values → raise `OracleSchemaError`. No matching row → return `None` (not an error). Both exception classes live in `oracle_service.py`. The router will map `OracleUnavailable` to 503 (later story). |
| AC11-D7 | Logging | Log a SHA-256-hex first-12-chars **hash** of the employee_id, never the raw value. Format: `oracle.staff_lookup employee_id_hash=<12hex> outcome=<found\|not_found>`. Enough to correlate a session's lookups without leaking PII. |
| AC11-D8 | Tests | `oracledb` is mocked at the `connect()` boundary. The fixture returns a fake connection whose cursor yields scripted rows. Tests assert: SQL string, bound params, row → dataclass mapping, `Y`/`N` → `bool` coercion, all three failure modes, and a PII-in-logs guardrail. A `pytest.mark.oracle_integration` marker is reserved for future smoke runs against real Oracle XE — not used in the AC-11 suite. |
| AC11-D9 | PII-in-logs guardrail | A dedicated test scans `caplog.text` for the raw `employee_id` substring after every code path (found, not_found, unavailable, schema-error) and asserts it never appears. Mirrors `test_state_token_is_never_logged` from AC-6. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/app/core/database.py` | 🟢 Green | **New** — `get_oracle_connection()` FastAPI dependency (yield/close) |
| `backend/app/services/oracle_service.py` | 🟡 Yellow | **New** — `StaffRecord`, `OracleUnavailable`, `OracleSchemaError`, `get_staff_by_employee_id` |
| `backend/app/core/config.py` | 🟢 Green | Add `oracle_*` Settings fields |
| `backend/.env.example` | — | Add `ORACLE_*` block |
| `backend/requirements.txt` | — | Add `oracledb` |
| `backend/tests/conftest.py` | — | Add `ORACLE_*` env vars to `_env` fixture |
| `backend/tests/test_database.py` | — | New (~2 tests) |
| `backend/tests/test_oracle_service.py` | — | New (~7 tests) |

## Open follow-ups

- **Connection pooling** — out of scope for the demo per AC11-D2.
  Revisit if/when multi-worker uvicorn is introduced.
- **Integration smoke tests** — `pytest.mark.oracle_integration` marker is
  reserved but no real-Oracle CI runner exists yet. Will be wired up
  when Oracle XE is in docker-compose.
- **`list_vendors` and `get_vendor_by_id`** — also part of `OracleService`
  per FD §6.5 but **out of scope for AC-11**. AC-12 / AC-15 implement
  those.
