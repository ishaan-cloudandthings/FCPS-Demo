# AC-19 — seed `PROCUREMENT_ITEMS` + `APPROVED_AT`

| Field | Value |
|---|---|
| Jira story | [AC-19](https://cloudandthings.atlassian.net/browse/AC-19) — E4-S5 |
| Epic | [AC-5](https://cloudandthings.atlassian.net/browse/AC-5) |
| Zone | 🟢 Green (`backend/scripts/seed_oracle.py`) |
| Ratified on | 2026-05-18 |
| Status | Ratified — implementation may proceed |

## ADR-012 reconciliation

The Jira description says **"PROCUREMENT_ITEMS + APPROVED_AT + AUDIT_LOG"**.
[ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) removed both the
`AUDIT_LOG` table and the `BANK_DETAILS` column. This story builds only
the parts that survived:

- ✅ `PROCUREMENT_ITEMS` table (DATA_MODEL.md §4.2) plus the
  `APPROVED_AT` column per [ADR-006](../adr/ADR-006-audit-log-and-approved-at.md)
  (which is the only part of ADR-006 still in force).
- ❌ `AUDIT_LOG` — out of scope. No table, no seed rows.
- ❌ `BANK_DETAILS` column — out of scope. The CREATE TABLE statement
  omits it.

Jira description corrected as part of the commit.

## Synthetic-PII alert

`CONTACT_NAME` and `CONTACT_EMAIL` are PII per DATA_MODEL.md §4.2. All
synthetic per ADR-007. Email domain is `@test.com` (no `spp`
substring) — consistent with the AC-12 STAFF seed guardrail.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC19-D1 | Schema | Exact DATA_MODEL.md §4.2 column set **plus** `APPROVED_AT TIMESTAMP WITH TIME ZONE NULL` (ADR-006). **Minus** `BANK_DETAILS` (ADR-012). `STATUS` has a `CHECK` constraint. `CREATED_DATE`/`UPDATED_DATE` default `SYSTIMESTAMP`. |
| AC19-D2 | Idempotency | Same DROP→CREATE→batch INSERT pattern as AC-12. ORA-00942 swallowed on first run. |
| AC19-D3 | Seed count + breakdown | 15 rows matching DATA_MODEL.md §8: 5 APPROVED, 4 PENDING, 3 UNDER_REVIEW, 3 REJECTED. Categories drawn from the §8 enum (Technology, Facilities, Supplies, Services, Furniture). |
| AC19-D4 | `APPROVED_AT` semantics | Non-null only for `STATUS='APPROVED'` rows. Other statuses get `None`. Dates spread across early 2026 so detail-page sorting is varied. |
| AC19-D5 | Email synthesis | `firstname.lastname@vendor.test` for vendor contacts. Distinct from staff emails (`@test.com`) so a reader can tell vendor PII from staff PII at a glance. |
| AC19-D6 | Tests | Mock `oracledb.connect`. Assert: DROP→CREATE→15 INSERTs; CREATE includes `APPROVED_AT` and excludes `BANK_DETAILS`; CHECK constraints on STATUS; row counts per status; no `@spp.` substring in any email; APPROVED_AT is non-null iff status is APPROVED. |
| AC19-D7 | `seed()` extension | `scripts.seed_oracle.seed()` continues to handle STAFF, and now also runs the PROCUREMENT_ITEMS pipeline in the same connection / transaction. Order: drop+create STAFF, drop+create PROCUREMENT_ITEMS, insert STAFF, insert PROCUREMENT_ITEMS, commit. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/scripts/seed_oracle.py` | 🟢 Green | Add PROCUREMENT_ITEMS schema + 15-row seed + extended `seed()` pipeline |
| `backend/tests/test_seed_oracle.py` | — | Extend with ~7 new tests |
