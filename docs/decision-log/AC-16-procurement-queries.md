# AC-16 — Oracle PROCUREMENT_ITEMS queries (`list_vendors`, `get_vendor_by_id`)

| Field | Value |
|---|---|
| Jira story | [AC-16](https://cloudandthings.atlassian.net/browse/AC-16) — E4-S2 |
| Epic | [AC-5](https://cloudandthings.atlassian.net/browse/AC-5) |
| Zone | 🟡 Yellow (`backend/app/services/oracle_service.py`) |
| Ratified on | 2026-05-18 |
| Status | Ratified — implementation may proceed |

## PII discipline (per ADR-013, ADR-012)

- `CONTACT_NAME` and `CONTACT_EMAIL` are PII (DATA_MODEL.md §4.2).
- `list_vendors()` selects `CONTACT_NAME` only when `include_contact=True`.
  Never selects `CONTACT_EMAIL` — that's detail-only per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md).
- `get_vendor_by_id()` selects both `CONTACT_NAME` and `CONTACT_EMAIL`
  (admin detail page is the **only** caller).
- `BANK_DETAILS` is never selected by any query in this file
  ([ADR-012](../adr/ADR-012-bank-details-out-of-scope.md)). A test asserts
  the literal string `BANK_DETAILS` does not appear in any SQL constant.

## RBAC staging note

The flag parameters on `list_vendors` (`only_approved`, `include_contact`,
`include_status`, `variant_tag`) are pre-staged for the AC-17 live demo.
Today the procurement router calls them in their most-permissive form
("everyone sees everything") and the queries return the admin shape.
AC-17 wires `rbac_service.params_for(...)` to drive these flags.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC16-D1 | Method shape | Two functions: `list_vendors(connection, *, only_approved, include_contact, include_status, variant_tag) -> list[VendorRow]` and `get_vendor_by_id(connection, item_id) -> VendorRow \| None`. Function-not-class — matches AC-11's `get_staff_by_employee_id` style. |
| AC16-D2 | `VendorRow` dataclass | Frozen dataclass with the **union** of fields any caller might need, marked Optional where appropriate. Includes a `variant_tag` field set by the service so router responses can route to the right Pydantic schema. List queries set `status`/`unit_price`/`contact_name` to `None` when the variant doesn't include them; `contact_email` / `approved_at` / `created_date` / `updated_date` are detail-only. |
| AC16-D3 | SQL construction | Module-level constants with optional column / WHERE fragments composed via Python `str.format` — but **never** with user input. The `WHERE STATUS = 'APPROVED'` clause is a static literal; column lists are picked from a fixed allowlist. Parameter-bind on `item_id` only. |
| AC16-D4 | `APPROVED_AT` | Column lives on `PROCUREMENT_ITEMS` per [ADR-006](../adr/ADR-006-audit-log-and-approved-at.md). Selected only by `get_vendor_by_id`. AC-19 adds it to the seed schema. |
| AC16-D5 | Failure modes | Reuses `OracleUnavailable` / `OracleSchemaError` from AC-11. `get_vendor_by_id` returns `None` on no-row. Status / variant_tag values are validated server-side; unknown values raise `OracleSchemaError`. |
| AC16-D6 | Logging | `oracle.vendor_list count=<n> only_approved=<bool> include_contact=<bool>` and `oracle.vendor_get item_id=<n> outcome=<found\|not_found>`. No PII (no contact name, no email). |
| AC16-D7 | Tests | Mock `oracledb` at the cursor boundary (same as AC-11). Cover: SQL composition for all 4 flag combinations, row-to-VendorRow mapping (variant_tag selection), status validation, OracleUnavailable propagation, BANK_DETAILS never in any SQL, contact_email never in list SQL. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/app/services/oracle_service.py` | 🟡 Yellow | Add `VendorRow`, `list_vendors`, `get_vendor_by_id`, module-level SQL constants |
| `backend/tests/test_oracle_service.py` | — | Extend with ~12 new tests |
