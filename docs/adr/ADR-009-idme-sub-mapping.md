# ADR-009 — ID.me `sub` mapped to `STAFF.EMPLOYEE_ID`

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude), on behalf of C&T Tech Lead |
| Supersedes | — |
| Superseded by | — |

## Context

After ID.me verification, the backend has the user's ID-token claims, of which
the `sub` claim is the only stable identifier. ID.me does not return the FCPS
employee ID; that is FCPS's internal HR identifier.

The backend must reconcile these two identifiers — "the person ID.me just
verified" and "the row in our STAFF table that says what they can do" — into a
single access decision (see ADR-002 in `ARCHITECTURE.md` §11).

The 2026-05-09 call made the mapping decision explicit:

> "ID.me `sub` mapped to `EMPLOYEE_ID` in Oracle. The mapping is confirmed —
> `EMPLOYEE_ID` in the STAFF table stores the ID.me subject identifier."

`ARCHITECTURE.md` §7.1 shows the lookup in the data-flow diagram but does not
specify the mapping; `DATA_MODEL.md` §4.1 describes `EMPLOYEE_ID` as "FCPS
employee identifier" without naming its source.

## Decision

- `STAFF.EMPLOYEE_ID` is the **storage column for the ID.me `sub`** identifier
  for the duration of the demo.
- After successful ID-token validation, the backend executes:

  ```sql
  SELECT STAFF_ID, EMPLOYEE_ID, ROLE, PROCUREMENT_LEVEL, IDME_VERIFIED, ACTIVE
  FROM STAFF
  WHERE EMPLOYEE_ID = :sub
  ```

- `scripts/seed_oracle.py` seeds synthetic `sub` values shaped like `FCPS-001`
  … `FCPS-010` because the ID.me sandbox issues predictable `sub` values for
  sandbox test users that map to FCPS-side identifiers by convention.
- `EMPLOYEE_ID` is classified as PII (see `DATA_MODEL.md` §7) and is therefore:
  - **never** returned in any API response,
  - **never** written to application logs,
  - **never** embedded in the JWT (see ADR-004).

## Consequences

**Positive**

- A single, stable join from identity (ID.me) to authorisation (Oracle STAFF).
- No additional mapping table is required, which keeps the demo schema small
  (two tables for the core workflow, plus `AUDIT_LOG` for compliance).
- Sandbox `sub` values are deterministic, enabling reliable end-to-end tests.

**Negative**

- The `EMPLOYEE_ID` column is now **overloaded**: it stores both the
  FCPS-internal employee identifier *and* the ID.me sandbox `sub`. For
  production, the real ID.me's `sub` format may not match FCPS HR IDs and we
  would need to split into:
  - `STAFF.EMPLOYEE_ID` — FCPS internal ID
  - `STAFF.IDME_SUB` — identity provider key
  This is a phase-2 concern, not a demo blocker.

**Follow-ups required**

- Update `ARCHITECTURE.md` §7.1 — label the Oracle lookup arrow with `:sub`
  so the mapping is explicit in the diagram.
- Update `DATA_MODEL.md` §4.1 `EMPLOYEE_ID` description to read: *"Unique.
  Stores the ID.me `sub` for the demo (see ADR-009). FCPS HR identifier in
  production (phase-2 split required)."*
- Phase-2 backlog: ADR to split `EMPLOYEE_ID` / `IDME_SUB`.

## References

- `docs/discovery/CALL_NOTES_2026-05-09.md` — "Decisions Made on This Call"
- `docs/requirements/REQUIREMENTS.md` — FR-03, §6 data table
- `docs/requirements/FUNCTIONAL_DESIGN.md` — §6.5, §6.6
- `docs/DATA_MODEL.md` — §4.1, §7
- `ADR-002` (inline in ARCHITECTURE.md §11) — Role sourced from Oracle, not ID.me
- `ADR-004` — `EMPLOYEE_ID` is **not** in the JWT
