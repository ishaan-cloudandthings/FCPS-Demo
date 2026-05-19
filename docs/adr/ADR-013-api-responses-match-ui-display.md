# ADR-013 — API responses match UI display: `contact_email` moved to detail-only

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-16 |
| Author | C&T BA (Claude), on behalf of C&T Tech Lead + Project Lead |
| Supersedes | — |
| Superseded by | — |
| Resolves | OQ-08 in `REQUIREMENTS.md` v0.4 §10 |

## Context

`REQUIREMENTS.md` v0.4 §10 raised **OQ-08**: the `GET /api/vendors` response
for `LEVEL = 2` (and for `ADMIN`) contains `contact_email`, but no UI surface
ever renders it. The L2 staff view's list page displays only the contact's
name; the admin's list page does the same; only the admin-only detail view
(`GET /api/vendors/{id}` → `VendorDetail`) renders the email. L2 staff have
no access to the detail view (FR-12), so an L2 user can never see the email
through the UI — yet it sits in the API response payload, inspectable in
browser devtools.

This violates a principle the project has already adopted twice:

1. **[ADR-012](./ADR-012-bank-details-out-of-scope.md)** removed
   `bank_details` from every API response, not just from the UI. The
   architect-level argument: *"if the UI never renders it, the API
   shouldn't return it — the field is exposable in browser devtools
   regardless."*
2. **`FUNCTIONAL_DESIGN.md` §6.9** explicitly designed the Pydantic L1
   schema with **no `contact_*` fields at all**, on the grounds that
   *"over-disclosure is structurally impossible"*.

`contact_email` in the L2 list response is the only field in the entire
API surface that **violates** this principle. It's PII (per
`DATA_MODEL.md` §7) and currently dead weight in the response.

The legitimate counter-argument is **"don't couple the API contract to
today's UI design"** — but that argument requires a plausible second
consumer (a different UI, an export, a generic component that
over-fetches). The demo has none of those: one frontend, bespoke
`VendorTable` variants per role (FD §7.4), client-side search on
`vendor_name` only (FR-16). There is no path by which `contact_email`
becomes useful at L2.

## Decision

**API responses contain only fields rendered by their corresponding UI.**
As a corollary, `contact_email` is removed from the `GET /api/vendors`
list response at every role/level, and lives only in the
`GET /api/vendors/{id}` admin-only detail response.

Final field layout for the vendor schemas:

| Schema | Endpoint | `contact_name` | `contact_email` |
|---|---|:---:|:---:|
| `VendorListItemL1` | `GET /api/vendors` (LEVEL 1) | — | — |
| `VendorListItemL2` | `GET /api/vendors` (LEVEL 2) | ✓ | — |
| `VendorListItemAdmin` | `GET /api/vendors` (ADMIN) | ✓ | — |
| `VendorDetail` | `GET /api/vendors/{id}` (ADMIN only) | ✓ | ✓ |

This is the same pattern ADR-012 established for `bank_details`:
exactly one schema in the whole API surface contains a PII field, and
exactly one screen renders it.

## Rationale

- **Consistency.** Matches the precedent set by ADR-012 and the L1
  Pydantic schema design rationale (FD §6.9).
- **Security posture.** Every screen-level exposure of `contact_email`
  is now strictly equal to every API-level exposure. There is no path
  by which an L2 user's browser tab contains email data the L2 user
  isn't authorised to see — because the API simply doesn't return it.
- **Easier security review.** "Every PII field is returned by exactly
  one schema, on exactly one endpoint, rendered by exactly one screen."
  One sentence, no exceptions.
- **No real cost.** The detail view is admin-only; L2 users can never
  reach it. So dropping email from L2's list response loses nothing they
  could have used.

## Consequences

**Positive**

- Smaller API surface for the L2/Admin list endpoints.
- `oracle_service.list_vendors` SELECT becomes one column smaller.
- The L1 schema's "over-disclosure is structurally impossible"
  guarantee now extends to L2.
- One less open question.

**Negative**

- If Staff Procurement Portal later wants L2 staff to see contact_email somewhere
  (e.g., a future export, a future "my favourite vendors" view), an API
  change is required. Acceptable cost for a tightly-scoped demo.
- `rbac_service.list_query_params` has a slightly less expressive flag
  set — there is no longer a need for an "include_contact_email" flag
  separate from "include_contact" (which now means "name only").

**Follow-ups required**

- Update `REQUIREMENTS.md` → v0.5: rewrite FR-11 (drop `contact_email`
  from L2/Admin list responses); update §2.2 note; close OQ-08.
- Update `FUNCTIONAL_DESIGN.md` → v0.4: §6.5 `oracle_service.list_vendors`
  SELECT list; §6.9 Pydantic schemas (drop `contact_email` from
  `VendorListItemL2` and `VendorListItemAdmin`); §9 PII handling table.
- Update `api-spec.yaml`: drop `contact_email` from `VendorListItemL2`
  and `VendorListItemAdmin` schemas + their examples.
- Update `DESIGN_RATIONALE.md` Screen 3: "What adapts by role" table;
  "Contact column" rationale.
- Update Jira: **AC-15** (Pydantic schemas), **AC-16** (Oracle queries
  — drop `CONTACT_EMAIL` from the list SELECT), **AC-17** (RBAC service
  flag wording).
- `DATA_MODEL.md` — **no change**. The `CONTACT_EMAIL` column stays in
  `PROCUREMENT_ITEMS`. The application code simply doesn't select it
  for list responses.

## References

- `REQUIREMENTS.md` v0.4 — OQ-08 (the question this ADR resolves)
- [ADR-012](./ADR-012-bank-details-out-of-scope.md) — the precedent for
  this principle
- `FUNCTIONAL_DESIGN.md` §6.9 — Pydantic L1 schema rationale
- `docs/design/DESIGN_RATIONALE.md` Screen 3 — Contact column UI design
