# AC-15 — Pydantic per-level vendor schemas

| Field | Value |
|---|---|
| Jira story | [AC-15](https://cloudandthings.atlassian.net/browse/AC-15) — E4-S1 |
| Epic | [AC-5](https://cloudandthings.atlassian.net/browse/AC-5) — RBAC and Vendor Data Access |
| Zone | 🟢 Green (`backend/app/schemas/vendors.py`) |
| Ratified on | 2026-05-18 |
| Status | Ratified — implementation may proceed |

## PII / scope notes

- `CONTACT_NAME` is PII; `CONTACT_EMAIL` is PII (DATA_MODEL.md §4.2). All
  synthetic per ADR-007.
- `CONTACT_EMAIL` is **detail-only** per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md);
  no list schema includes it. `VendorListItemL2.contact_email` was removed in that ADR.
- `BANK_DETAILS` is fully out of scope per [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md);
  no schema includes it.

## Why per-level schemas now, when RBAC isn't enforced yet

The 4 variants are pre-staged for the AC-17 live demo. Today every API
response uses the `"admin"` list variant (everyone sees everything). When
AC-17 is built live, `rbac_service.params_for(role, level)` selects the
right variant and the frontend re-renders automatically — no FE code
changes during the demo. The `variant` discriminator field is what makes
that handoff possible.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC15-D1 | One file | All vendor schemas in `backend/app/schemas/vendors.py`. Keeps the discriminator literals colocated. |
| AC15-D2 | Discriminator field | Each schema carries a `variant: Literal["staff_l1" \| "staff_l2" \| "admin" \| "admin_detail"]` field. Matches the api-spec.yaml `const:` values verbatim. |
| AC15-D3 | `extra="forbid"` everywhere | Mirrors AC-7's `CallbackRequest` / `SessionResponse` discipline. Drift in either direction is a 422. |
| AC15-D4 | Nullable fields | `contact_name`, `contact_email`, `unit_price`, `approved_at` are nullable per api-spec. `vendor_name`, `item_name`, `category`, `status` are required and non-null. |
| AC15-D5 | `VendorStatus` enum | `Literal["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED"]` — single source of truth for the four statuses. |
| AC15-D6 | Tests | Round-trip tests per schema: minimum-required payload validates, extra fields rejected, wrong `variant` literal rejected, nullable fields accept None. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/app/schemas/vendors.py` | 🟢 Green | **New** — 4 Pydantic schemas + `VendorStatus` type alias |
| `backend/tests/test_vendor_schemas.py` | — | New (~10 tests) |
