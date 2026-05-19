# ADR-002 — Role Sourced from Oracle, Not ID.me

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude) — extracted from ARCHITECTURE.md §11 by architecture refactor |
| Supersedes | — |
| Superseded by | — |

## Context

The portal has two distinct authorisation outcomes:

- **Admin (procurement coordinator)** — sees all `PROCUREMENT_ITEMS`
  regardless of status.
- **Staff (teacher)** — sees only `PROCUREMENT_ITEMS` where
  `STATUS = 'APPROVED'`.

ID.me, the identity provider, can in principle carry custom claims (such as
"role") inside the ID token. The alternative is to use ID.me purely for
identity assertion and look up role from a system controlled by Staff Procurement Portal.

Staff Procurement Portal HR data — including which staff are procurement coordinators — already
lives in the Oracle `STAFF` table. That table is the source of truth for
employment status, role, and procurement clearance level.

## Decision

The user's role (`ADMIN` or `STAFF`) is read from the Oracle `STAFF` table
after a successful ID.me verification. ID.me is used to prove identity only;
it is not consulted for authorisation data. The backend issues the JWT with
the role claim populated from the Oracle lookup, not from any ID.me claim.

## Rationale

- Staff Procurement Portal HR data lives in Oracle. Oracle is the authoritative source for role
  and clearance.
- Embedding role in ID.me claims would require Staff Procurement Portal to manage claims — out
  of scope.
- Separation of concerns: ID.me answers "who are you?", Oracle answers
  "what can you do?".

## Consequences

**Positive**

- Authorisation decisions follow the Staff Procurement Portal source of truth. Role changes in
  Oracle take effect on the next login without any ID.me coordination.
- ID.me integration stays minimal — `openid email` scope is sufficient; no
  custom claim mapping required.
- Clean separation of concerns simplifies the threat model: a compromised
  ID.me claim cannot grant ADMIN access; an attacker would also need to
  alter the Oracle row.

**Negative**

- The system depends on the Oracle `STAFF` table being current. A staff
  member added to ID.me but not yet to Oracle cannot log in. This is a
  feature, not a bug, but onboarding processes must reflect it.
- Every login incurs at least one Oracle round-trip on top of the ID.me
  exchange. Acceptable at demo scale.

**Follow-ups required**

- Document the ID.me-to-Oracle linkage explicitly (see ADR-009, which fixes
  the `sub`-to-`EMPLOYEE_ID` mapping).
- Onboarding runbook for production: add the user to Oracle `STAFF` **before**
  inviting them to ID.me.

## References

- `docs/ARCHITECTURE.md` — §8.2 (Authorisation), the originating doc
- `docs/DATA_MODEL.md` — `STAFF` table definition, role and clearance columns
- `docs/discovery/CALL_NOTES_2026-05-05.md` — data-ownership discussion
- `ADR-009` — ID.me `sub` mapped to `STAFF.EMPLOYEE_ID` (operational
  consequence of this decision)
