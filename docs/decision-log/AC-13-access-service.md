# AC-13 — Access decision service + X-Auth-Reason wiring

| Field | Value |
|---|---|
| Jira story | [AC-13](https://cloudandthings.atlassian.net/browse/AC-13) — E3-S1 Access decision service + X-Auth-Reason wiring |
| Epic | [AC-4](https://cloudandthings.atlassian.net/browse/AC-4) — Procurement Data Access |
| Zone | 🟡 Yellow (`backend/app/services/access_service.py` + downstream wiring in `backend/app/api/auth.py`) |
| Ratified on | 2026-05-18 |
| Ratified by | C&T Project Lead |
| Status | Ratified — implementation may proceed |

## PII alert

> **2026-05-19 supersession** — [ADR-015](../adr/ADR-015-role-model-simplification.md)
> collapsed the role model to three roles (`PROCUREMENT_SUPERVISOR`,
> `REGULAR_STAFF`, `NON_STAFF`) and dropped `PROCUREMENT_LEVEL` entirely.
> Decisions ratified below remain on the historical record; the live code
> base now reflects ADR-015. Concrete renames: `ADMIN` → `PROCUREMENT_SUPERVISOR`,
> `STAFF` → `REGULAR_STAFF`, `LEVEL_ZERO` → `NON_STAFF`,
> `procurement_level` removed from claims and queries.


`sub` is the ID.me sub claim, which per [ADR-009](../adr/ADR-009-idme-sub-mapping.md) maps to `STAFF.EMPLOYEE_ID` — PII. Discipline (matches AC-11 / AC7-D11):

* Parameter-bind only (delegated to `oracle_service.get_staff_by_employee_id`).
* Never log raw `sub`; use the SHA-256-first-12 hash from `oracle_service._hash_employee_id`.
* `sub` never enters the JWT (FR-05); the granted decision returns `staff_id` instead.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC13-D1 | Connection injection | Closure pattern, mirroring AC-8's `get_session_issuer`. `get_access_decider(connection = Depends(get_oracle_connection))` returns a callable `(sub: str) -> AccessDecision` that holds the connection. AC-7's endpoint signature for the decider stays unchanged. |
| AC13-D2 | Decision tree | Verbatim from FUNCTIONAL_DESIGN.md §6.6, evaluated in order: `None → NOT_FOUND`; `!idme_verified → NOT_VERIFIED`; `!active → INACTIVE`; `level==0 → LEVEL_ZERO`; else `GRANTED`. |
| AC13-D3 | Oracle errors | `OracleUnavailable` and `OracleSchemaError` **propagate** — they are infrastructure failures, not access decisions. The router maps them. |
| AC13-D4 | Logging | `access_service.decided employee_id_hash=<12hex> reason=<…>` at INFO. Identical hash format to AC-11. Never the raw `sub`. |
| AC13-D5 | Tests | 5 parametrised decision-tree branches; 2 error-propagation tests; 1 PII-in-logs guardrail (raw `sub` never in caplog across all 5+2 paths). |
| AC13-D6 | Router-side 503 mapping | `/api/auth/callback` catches `OracleUnavailable` from `access_decider(sub)` and raises HTTP 503 with body `{"detail": "Service temporarily unavailable. Please try again shortly."}` (matches AC-6's state-cache-full copy verbatim — single canonical 503 message). `OracleSchemaError` propagates to the global 500 handler (unrecoverable, must be logged). |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/app/services/access_service.py` | 🟡 Yellow | Replace stub body with real decision-tree implementation |
| `backend/app/api/auth.py` | 🔴 Red | `get_access_decider` becomes a closure over the Oracle connection; `/callback` catches `OracleUnavailable` and raises 503 |
| `backend/tests/test_access_service.py` | — | **New** (~8 tests) |
| `backend/tests/test_auth_callback.py` | — | Update `mock_access_decision` to match the closure signature; add a callback-503-on-OracleUnavailable test |

## Open follow-ups

- The `/callback` happy path now requires Oracle + the seed (AC-12) **and** ID.me sandbox creds (ADR-007) — full end-to-end only works after those are stood up. Dev mode persona login (ADR-014) remains the demo path until then.
