# AC-18 — `procurement.py` router (list + detail, auth-only)

| Field | Value |
|---|---|
| Jira story | [AC-18](https://cloudandthings.atlassian.net/browse/AC-18) — E4-S4 |
| Epic | [AC-5](https://cloudandthings.atlassian.net/browse/AC-5) |
| Zone | 🟡 Yellow (`backend/app/api/procurement.py`) |
| Ratified on | 2026-05-18 |
| Status | Ratified — implementation may proceed |

## ADR-012 reconciliation

The Jira description says **"GET /api/vendors/{id} + audit_service (fail-closed)"**.
[ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) removed `audit_service`
and the whole audit-log posture. This story builds only the detail endpoint
(plus, see below, the list endpoint). **No `audit_service` calls.**

## RBAC staging note

Per the 2026-05-18 direction, this story also ships the **list endpoint**
that AC-17 would have created — but with **no RBAC enforcement**. Every
authenticated user sees the full vendor list with `variant_tag="admin"`.
When AC-17 is built live, the only change in `procurement.py` is the
import of `rbac_service` and a one-line edit to the list handler. See
inline `# TODO(AC-17)` markers.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC18-D1 | Router location | `backend/app/api/procurement.py` with prefix `/api/vendors`. |
| AC18-D2 | Endpoints | `GET /api/vendors` (list) and `GET /api/vendors/{item_id}` (detail). Both depend on `require_authenticated` only. **Not** `require_role`; **not** `require_level`. |
| AC18-D3 | Response models | List endpoint → `list[VendorListItemAdmin]` (today's everyone-sees-everything mode). Detail endpoint → `VendorDetail`. Both use the AC-15 schemas. |
| AC18-D4 | List handler shape | Calls `list_vendors(connection, only_approved=False, include_contact=True, include_status=True, variant_tag="admin")` and maps each `VendorRow` → `VendorListItemAdmin`. |
| AC18-D5 | Detail handler shape | Calls `get_vendor_by_id(connection, item_id)`. `None` → 404 with `{"detail": "Vendor not found."}`. Otherwise maps `VendorRow` → `VendorDetail`. |
| AC18-D6 | Connection injection | `Depends(get_oracle_connection)` — same per-request connection pattern as the AC-13 access flow. |
| AC18-D7 | Oracle errors | `OracleUnavailable` → 503 with the shared canonical body (`_DETAIL_SERVICE_UNAVAILABLE` from `app.api.auth`). `OracleSchemaError` → propagates to the global 500 handler. |
| AC18-D8 | Logging | `procurement.list count=<n>` on success; `procurement.detail item_id=<n> outcome=<found\|not_found>` on detail. Never log PII fields (contact_name / contact_email). |
| AC18-D9 | Tests | TestClient + override `get_oracle_connection` + override `require_authenticated`. Cover: list happy path (admin variant rows), detail happy path, 404 on missing detail, 503 on `OracleUnavailable`, 401 unauthenticated (both endpoints). |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/app/api/procurement.py` | 🟡 Yellow | **New** — router + 2 handlers |
| `backend/main.py` | 🟡 Yellow | `include_router(procurement_router)` |
| `backend/tests/test_procurement_api.py` | — | New (~8 tests) |
