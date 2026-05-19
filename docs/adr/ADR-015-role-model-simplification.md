# ADR-015 — Role model simplification (3 roles, no procurement levels)

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-19 |
| Author | C&T Project Lead |
| Supersedes | Partial: REQUIREMENTS.md `D-03` ("Two roles, four levels") |
| Superseded by | — |
| Related | [ADR-002](./ADR-002-role-sourced-from-oracle.md), [ADR-009](./ADR-009-idme-sub-mapping.md), [ADR-014](./ADR-014-demo-persona-login-dev-only.md) |

## Context

The original discovery + requirements work captured two orthogonal
authority dimensions on every staff record:

1. **`ROLE`** ∈ `{ADMIN, STAFF}` — used to gate admin-only screens.
2. **`PROCUREMENT_LEVEL`** ∈ `{0, 1, 2, 3}` — used to narrow the columns a
   user could see on the vendor list (REQUIREMENTS.md `D-03`).

In practice the two dimensions were tightly coupled: every `ADMIN` was
also `LEVEL = 3`, every "active" staff member sat at `LEVEL = 1` or `2`,
and `LEVEL = 0` was the denial path. The combinatorial space was
five effective access tiers (`LEVEL_ZERO`, `STAFF L1`, `STAFF L2`,
`ADMIN L3`, `NOT_REGISTERED`) where only three were ever exercised by
the design rationale and the dev personas.

This ADR collapses the model to three named roles and drops the
`PROCUREMENT_LEVEL` column entirely.

## Decision

The data model and the rest of the codebase now use a single authority
dimension — `ROLE` — with three values:

| Role | Authority |
|---|---|
| `NON_STAFF` | Has a row in `STAFF` but is **denied** access at `/api/auth/callback`. Same denial envelope as `NOT_REGISTERED` (no account-existence enumeration), but a distinct internal X-Auth-Reason value. |
| `REGULAR_STAFF` | Authenticated read access to the portal. Sees the active (approved) vendor list. |
| `PROCUREMENT_SUPERVISOR` | Authenticated read access **and** the documented authority to add / update / delete vendors. **CRUD endpoints are not yet implemented** — see "Out of scope" below. |

The `STAFF.PROCUREMENT_LEVEL` column is **dropped**. JWT claims, session
state, and the access service no longer carry a level field.

## What this changes

| Surface | Before | After |
|---|---|---|
| `STAFF.ROLE` enum | `{'ADMIN', 'STAFF'}` | `{'PROCUREMENT_SUPERVISOR', 'REGULAR_STAFF', 'NON_STAFF'}` |
| `STAFF.PROCUREMENT_LEVEL` | NUMBER(1), 0–3 | **column removed** |
| JWT claims `{sub, role, procurement_level, …}` | includes `procurement_level` | `procurement_level` removed |
| Access decision tree | `LEVEL == 0 → LEVEL_ZERO` denial | `ROLE == NON_STAFF → NON_STAFF` denial |
| X-Auth-Reason header | `LEVEL_ZERO` / `NOT_REGISTERED` | `NON_STAFF` / `NOT_REGISTERED` |
| Dev personas | `admin_l3`, `staff_l2`, `staff_l1`, `level_zero`, `not_registered` (5) | `procurement_supervisor`, `regular_staff`, `non_staff`, `not_registered` (4) |
| `AccessDenied` page variants | `LEVEL_ZERO` + `NOT_REGISTERED` | `NON_STAFF` + `NOT_REGISTERED` (same copy intent) |

## Rationale

- The level dimension never modeled anything the role couldn't have
  expressed. Every L0 user was effectively non-staff; every L3 was
  effectively a supervisor; the intermediate L1/L2 distinction was
  documented for column narrowing but never produced different
  authorisation outcomes — only different render-time decisions.
- Renaming `ADMIN` → `PROCUREMENT_SUPERVISOR` captures the business
  function (a person who supervises procurement) rather than a
  system-administrator framing that doesn't apply here.
- Renaming `STAFF` → `REGULAR_STAFF` makes the "staff" noun harder to
  confuse with the `STAFF` database table name.
- Naming `NON_STAFF` explicitly (rather than implicit "no row in STAFF"
  or "level 0") gives data stewards a clean way to mark a person as
  in-the-HR-system-but-no-portal-access.

## Out of scope (intentionally)

- **CRUD endpoints** (`POST/PUT/DELETE /api/vendors*`). The supervisor's
  authority to mutate vendor records is **documented** by this ADR but
  not implemented. A separate ADR will be required to:
  - Reverse REQUIREMENTS.md `D-01` ("Read-only portal for the demo").
  - Re-open the audit-logging question (currently scoped out by
    [ADR-012](./ADR-012-bank-details-out-of-scope.md)).
  - Add API + UI + tests for create / update / delete flows.
- **Per-role narrowing of the vendor list response.** Today every
  authenticated user (supervisor or regular staff) receives the same
  list shape. The data model now distinguishes the two roles; enforcing
  different list responses per role is a follow-up that can be tackled
  whenever the AC-17 work is reinstated.

## Consequences

**Positive**

- Smaller surface: one authority field instead of two; one less integer
  column on `STAFF`; one less claim on the JWT.
- The "level 0 ↔ non-staff" semantic confusion is gone.
- The persona panel becomes shorter and clearer (3 business roles +
  one technical denial path).

**Negative**

- Existing sessions become invalid the moment this lands — JWT claims
  shape changed. (Demo only; AC-9 logout flow handles re-login.)
- Documentation churn: REQUIREMENTS, DATA_MODEL, FUNCTIONAL_DESIGN,
  api-spec, multiple decision logs, ADR-014 persona table, design copy.
- Lost optionality: if the business ever wants four access tiers again,
  re-introducing `PROCUREMENT_LEVEL` would be a real change rather than
  a no-op column flip.

## Follow-ups

- **New ADR (TBD)** when CRUD lands — must supersede D-01, address
  audit logging, and decide who can mutate which fields.
- The `variant_tag` discriminator on `VendorListItem*` schemas still
  carries `staff_l1` / `staff_l2` / `admin` literals from the old
  model. The list endpoint always emits the `admin` (now equivalent to
  "supervisor") variant today; the discriminator stays in place for
  future per-role narrowing without forcing a schema rev now.

## References

- [REQUIREMENTS.md](../requirements/REQUIREMENTS.md) `D-03`, `FR-03`, `FR-04`, `FR-05`
- [DATA_MODEL.md](../DATA_MODEL.md) §4.1, §8
- [FUNCTIONAL_DESIGN.md](../requirements/FUNCTIONAL_DESIGN.md) §6.4, §6.6, §6.7, §7
- [api-spec.yaml](../requirements/api-spec.yaml) `SessionResponse`, `X-Auth-Reason`
