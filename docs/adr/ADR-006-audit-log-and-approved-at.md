# ADR-006 — Add `AUDIT_LOG` table and `PROCUREMENT_ITEMS.APPROVED_AT`

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude), on behalf of C&T Tech Lead |
| Supersedes | — |
| Superseded by | — |

## Context

The 2026-05-09 call made two explicit data-model decisions that
`docs/DATA_MODEL.md` has **not** yet been updated for. Both flow from concrete
requirements:

1. **`AUDIT_LOG` table.** REQUIREMENTS.md FR-13 obliges the system to record
   every read of a vendor's `BANK_DETAILS`. The FCPS Procurement Coordinator's
   quote on the call was: *"If anyone asks who's been looking at that data, we
   have a record."* The audit row stores **who** (`STAFF_ID`), **what**
   (`VENDOR_ID`), and **when** (`ACCESSED_AT`) — never the `BANK_DETAILS` value
   itself.

2. **`PROCUREMENT_ITEMS.APPROVED_AT`.** REQUIREMENTS.md FR-15 obliges the
   admin detail view to display *"Approved on: \<date\>"* when a vendor's
   status is `APPROVED`. There is no existing column on
   `PROCUREMENT_ITEMS` that captures this date; `UPDATED_DATE` is overwritten
   on any change.

`docs/DATA_MODEL.md` is a locked reference document — per `CLAUDE.md`, edits
require explicit instruction. This ADR is that authorisation.

## Decision

### Add table `AUDIT_LOG`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `LOG_ID` | `NUMBER (PK, IDENTITY)` | NO | Auto-increment primary key |
| `STAFF_ID` | `NUMBER` | NO | FK → `STAFF.STAFF_ID`, `ON DELETE RESTRICT` |
| `VENDOR_ID` | `NUMBER` | NO | FK → `PROCUREMENT_ITEMS.ITEM_ID`, `ON DELETE RESTRICT` |
| `ACCESSED_AT` | `TIMESTAMP WITH TIME ZONE` | NO | UTC; set at write time |

Indexes:

- `IDX_AUDIT_VENDOR_ACCESSED (VENDOR_ID, ACCESSED_AT DESC)` — "who has accessed this vendor lately?"
- `IDX_AUDIT_STAFF_ACCESSED  (STAFF_ID, ACCESSED_AT DESC)` — "what has this staff member looked at?"

Constraints: none beyond the FKs.

**Retention:** indefinite for the demo (REQUIREMENTS.md NFR-10). No purge job
exists. Phase 2 will revisit with FCPS data governance.

**Confidentiality:** `BANK_DETAILS` is **never** written to `AUDIT_LOG` or to
application logs. The logger formatter strips any key matching `bank|secret|password`
as a belt-and-braces guard.

### Add column `PROCUREMENT_ITEMS.APPROVED_AT`

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `APPROVED_AT` | `TIMESTAMP WITH TIME ZONE` | YES | Set when `STATUS` transitions to `APPROVED`; `NULL` otherwise |

There is no `CHECK` constraint binding `APPROVED_AT` to `STATUS = 'APPROVED'`
because the demo does not edit status (read-only portal); the seed script will
populate the field directly for the 5 APPROVED rows.

## Consequences

**Positive**

- Satisfies FR-13 (audit) and FR-15 (approval date display).
- Compliance posture is provable: every `BANK_DETAILS` read is recorded.
- The seed script in `scripts/seed_oracle.py` (E4-S5 / AC-19) can now be
  written against a final schema.

**Negative**

- `DATA_MODEL.md` needs an authorised update before the seed script lands.
- A second timestamp column on `PROCUREMENT_ITEMS` (`APPROVED_AT` alongside
  `CREATED_DATE` and `UPDATED_DATE`) slightly complicates the model. Accepted
  because it is the only place to express "approval moment".

**Follow-ups required**

- Update `docs/DATA_MODEL.md` §4 entity definitions to include `AUDIT_LOG` and
  the new column.
- Update `docs/DATA_MODEL.md` §5 indexes table.
- Update `docs/DATA_MODEL.md` §8 seed-data section — note `AUDIT_LOG` starts
  empty; the 5 APPROVED `PROCUREMENT_ITEMS` rows have synthetic `APPROVED_AT`
  values.
- Implement in `scripts/seed_oracle.py` (E4-S5 / Jira AC-19).
- Implement audit write in the detail endpoint (E4-S4 / Jira AC-18) — fail-closed
  per FR-13.

## References

- `docs/discovery/CALL_NOTES_2026-05-09.md` — "Decisions Made on This Call"
  (AUDIT_LOG schema); Procurement Coordinator quote on bank-details access
- `docs/requirements/REQUIREMENTS.md` — FR-13, FR-15, NFR-10, §11
  data-model implications
- `docs/requirements/FUNCTIONAL_DESIGN.md` — §2 conflicts C-05 and C-06, §12
- Jira: AC-18 (audit write), AC-19 (seed schema)
