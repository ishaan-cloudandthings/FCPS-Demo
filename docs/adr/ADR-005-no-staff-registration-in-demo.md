# ADR-005 — Staff Registration out of scope for the demo

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude), on behalf of C&T Project Lead |
| Supersedes | — |
| Superseded by | — |

## Context

`AI_CONTEXT.md` "Key Business Domains" lists **"Staff Registration — Self-service
registration with name, work email, and employee ID"** as domain #1.
`ARCHITECTURE.md` reinforces this in:

- §6.1: an `api/staff.py` module with "Staff registration and status endpoints"
- §6.2: a `Registration.jsx` page in the frontend module map
- §7.1: a data-flow diagram showing **POST /staff** → INSERT into the STAFF table

None of the three discovery calls (2026-04-28, 2026-05-05, 2026-05-09) include a
registration journey. The 2026-04-28 call confirmed the portal is **internal
staff only**, with the two procurement coordinators and existing FCPS employees
(teachers, department heads) — all of whom have pre-existing FCPS HR records.

The 2026-05-09 call sealed this by specifying that the Oracle STAFF seed
contains 10 pre-loaded records and that the ID.me callback **looks up** a row
by `sub` (ADR-009) — never inserts.

## Decision

There is **no self-service registration** in the demo build:

- No `POST /api/staff` endpoint.
- No `Registration.jsx` page.
- No `api/staff.py` module (the file is dropped from the demo scope unless it
  also serves a non-registration purpose, which it currently does not).
- The Oracle `STAFF` table is populated **only** by `scripts/seed_oracle.py`
  (see ADR-010).
- The portal looks up an authenticated user by their ID.me `sub` and either
  grants or denies access — it never writes to `STAFF`.

Phase 2 may re-introduce registration; this ADR is not a permanent rejection.

## Consequences

**Positive**

- Sharply narrows the surface area: no validation rules, no email confirmation,
  no rate limiting on the registration form, no duplicate-detection logic.
- Aligns with the "read-only portal for the demo" decision from 2026-04-28.
- Removes a Yellow-zone API (`api/staff.py`) and its corresponding stories from
  the build plan.

**Negative**

- `AI_CONTEXT.md` and `ARCHITECTURE.md` contain stale paragraphs that imply
  registration is in scope. Until the doc updates land, new developers will be
  confused.
- Adding a staff member to the demo requires editing `seed_oracle.py` and
  re-running the seed — not a UI flow.

**Follow-ups required**

- Update `AI_CONTEXT.md` "Key Business Domains" — mark domain 1 as
  *Deferred to phase 2*.
- Update `ARCHITECTURE.md` §6.1 — remove `api/staff.py` from the module map
  unless it is repurposed.
- Update `ARCHITECTURE.md` §6.2 — remove `Registration.jsx` from the page list.
- Update `ARCHITECTURE.md` §7.1 — remove the `POST /staff → INSERT` arrow
  from the data-flow diagram.
- Update `AI_ZONES.md` Yellow zone — remove `Registration.jsx` and the
  registration scope of `api/staff.py`.

## References

- `docs/discovery/CALL_NOTES_2026-04-28.md` — "What Is Out of Scope" + "What
  the portal needs to do (high level)"
- `docs/discovery/CALL_NOTES_2026-05-09.md` — STAFF seed contents (10 records)
- `docs/requirements/REQUIREMENTS.md` §1.3 (out-of-scope), §2.2 (role/level
  matrix assumes pre-loaded STAFF)
- `docs/requirements/FUNCTIONAL_DESIGN.md` §2 (conflict C-03)
- `ADR-009` — ID.me `sub` → STAFF.EMPLOYEE_ID mapping (assumes row exists)
- `ADR-010` — `seed_oracle.py` as schema authority
