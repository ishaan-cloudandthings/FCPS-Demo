# ADR-012 — Bank details and audit logging out of scope for the demo

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-16 |
| Author | C&T BA (Claude), on behalf of C&T Project Lead |
| Supersedes | The `AUDIT_LOG` portion of [ADR-006](./ADR-006-audit-log-and-approved-at.md) only — the `APPROVED_AT` portion of ADR-006 remains in force. |
| Superseded by | — |

## Context

Through the 2026-04-28 / 2026-05-05 / 2026-05-09 discovery calls and the
2026-05-14 interview, the rationale for the Staff Procurement Portal
demo centred partly on **protecting `BANK_DETAILS`** — the sensitive
financial field on `PROCUREMENT_ITEMS`. That single field drove a chain of
downstream requirements:

- **FR-13** — every `BANK_DETAILS` access is audit-logged
- **NFR-07**, **NFR-13** — BANK_DETAILS visually distinct + RBAC-gated
- **AUDIT_LOG** table — created specifically to record those accesses
  ([ADR-006](./ADR-006-audit-log-and-approved-at.md))
- The `BankDetailsCard.jsx` frontend component
- A fail-closed posture on `GET /api/vendors/{id}` (audit write must succeed
  or the response is not served — FUNCTIONAL_DESIGN.md §6.2)
- The audit-log "Your access has been logged" UX on the detail screen
- The whole motivating quote from the 2026-04-28 Procurement Coordinator:
  *"that spreadsheet has bank account numbers in it"*

On 2026-05-16, after reviewing the v2 design mockups, **the Project Lead
elected to remove `BANK_DETAILS` from the demo scope entirely**. Reasons
not enumerated in the call; this ADR captures the resulting scope decision
without inferring rationale.

## Decision

The following are **out of scope** for the demo:

1. **`BANK_DETAILS` field** — not rendered on any screen, not returned in
   any API response, not filtered by any RBAC flag.
2. **`AUDIT_LOG` table** — not created, not seeded, not written. The
   `audit_service` module is not built.
3. **The "your access has been logged" UX** on the vendor detail screen.
4. **Fail-closed audit posture** on `GET /api/vendors/{id}` — the endpoint
   is now a simple admin-only read.

`PROCUREMENT_ITEMS.BANK_DETAILS` continues to exist as a **column in the
Oracle schema** per `DATA_MODEL.md` (a locked reference doc) — but the
application code does not select it, return it, or display it. The column
is dead-but-present. A future ADR may drop the column from the schema; for
the demo we leave the DATA_MODEL.md spec untouched.

## What remains in force from ADR-006

- **`PROCUREMENT_ITEMS.APPROVED_AT`** (new TIMESTAMP column) is still
  required — drives FR-15 ("Approved on: \<date\>" display in the admin
  detail view).
- The seed in `scripts/seed_oracle.py` still creates this column and
  populates plausible values for the 5 APPROVED seed rows.

## Consequences

**Positive**

- Significantly smaller demo footprint:
  - One fewer Oracle table (`AUDIT_LOG`)
  - One fewer backend service (`audit_service.py`)
  - One fewer frontend component (`BankDetailsCard.jsx`)
  - Detail-endpoint logic simplifies: no fail-closed posture, no transaction
    coupling between read and audit
  - Three Jira stories shrink or simplify (AC-18 / AC-19 / AC-21)
- Cleaner security story for the demo audience: there are no longer two
  classes of data (sensitive vs ordinary); every field is just data.
- Removes the ADR-006 caveat about DATA_MODEL.md being stale on `AUDIT_LOG`
  — the table was never going to land, so DATA_MODEL.md was never wrong.

**Negative**

- The primary motivating concern from the 2026-04-28 call —
  *"that spreadsheet has bank account numbers in it"* — is no longer addressed
  by the demo. Reviewers may note this gap.
- The LEVEL 2 vs LEVEL 3 distinction narrows: ADMIN's remaining
  differentiators are (a) seeing non-APPROVED statuses, (b) status filter,
  (c) row drill-in to the detail view. The "ADMIN sees the sensitive
  financial field" framing disappears.
- Phase 2 will need to re-introduce both bank-detail handling AND
  audit-logging together if Staff Procurement Portal wants the original posture back. This ADR
  is the explicit reference point for that future work.

**Follow-ups required**

- Update `REQUIREMENTS.md` → v0.3 (remove FR-13, FR-14, NFR-07, NFR-10,
  NFR-13; remove D-04; edit FR-11; remove BANK_DETAILS / AUDIT_LOG rows
  from data tables; add new out-of-scope row).
- Update `FUNCTIONAL_DESIGN.md` → v0.3 (remove §6.8 audit service; remove
  `include_bank` flag from §6.7; drop `bank_details` from §6.9 schemas;
  remove `BankDetailsCard` from §7; remove 500-on-audit error path from §10;
  resolve conflict C-05 to "scope-removed").
- Update `api-spec.yaml` (remove `bank_details` from `VendorListItemAdmin`
  + `VendorDetail`; remove the 500 audit-failure response on
  `GET /api/vendors/{vendor_id}`).
- Update the 8 affected Jira issues (AC-5, AC-15, AC-16, AC-17, **AC-18**,
  AC-19, AC-21, AC-22).
- Update `04-vendor-detail.html` and `DESIGN_RATIONALE.md`.
- ADR-006's metadata table updated to flag the partial supersession.

## References

- [ADR-006](./ADR-006-audit-log-and-approved-at.md) — partially superseded
  here (AUDIT_LOG portion only; APPROVED_AT remains)
- `docs/requirements/REQUIREMENTS.md` v0.2 — FR-13, FR-14, NFR-07, NFR-10,
  NFR-13, D-04 are removed in v0.3
- `docs/requirements/FUNCTIONAL_DESIGN.md` §6.7, §6.8, §6.9, §7, §10, §12
- 2026-05-16 design-review session (Project Lead directive)
