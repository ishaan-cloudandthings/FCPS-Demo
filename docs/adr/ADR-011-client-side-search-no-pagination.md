# ADR-011 — Client-side search and no pagination

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude), on behalf of C&T Tech Lead |
| Supersedes | — |
| Superseded by | — |

## Context

2026-05-09 call, "Decisions Made on This Call":

> "Client-side search only. No server-side search endpoint for the demo."
>
> "No pagination. ~40 approved vendors and ~120 total — fits on one page."

The dataset is bounded and small: roughly 120 vendor rows in total,
of which ~40 are `APPROVED`. A client-side substring filter over 120 rows
runs in well under 10 ms on any reasonable browser; server-side pagination
would add complexity (offset/limit, total counts, consistency across pages)
for no demo benefit.

`docs/requirements/REQUIREMENTS.md` FR-16 captures this; this ADR records the
*architectural* commitment behind it.

## Decision

- `GET /api/vendors` returns the **full** RBAC-filtered list in a single
  response. There are no `?page` / `?limit` query parameters, no
  total-count metadata, and no `Link` headers.
- The SPA filters the list **client-side** by Vendor Name (case-insensitive
  substring) with a 150 ms debounce.
- The Admin view additionally provides a **Status dropdown filter**, also
  applied client-side.
- There is **no `GET /api/vendors/search`** endpoint. Any future server-side
  search is a phase-2 architectural change.
- The dataset assumption — ~120 rows, ~40 APPROVED — is documented as a
  **phase-2 scaling trigger** in `REQUIREMENTS.md` NFR-02. If the actual
  dataset ever exceeds ~500 rows in production, this decision must be revisited.

## Consequences

**Positive**

- One endpoint per resource, one shape per role/level (see api-spec.yaml
  `oneOf` discriminator).
- No edge cases around inconsistent counts mid-pagination.
- Predictable performance: NFR-02 (`GET /api/vendors` p95 < 500 ms) is
  trivially met because the query is a single small projection.
- Client-side filtering responds instantly to keystrokes — the search box
  feels snappy.

**Negative**

- A future-scale ceiling. Crossing ~500 rows would make the client payload
  noticeable on slow networks. Documented as a phase-2 trigger.
- No URL-based deep linking to a search query (back-button friendliness is
  reduced). Acceptable for a demo.

**Follow-ups required**

- None for the demo.
- Add a note to a phase-2 architectural-debt list: "If vendor dataset exceeds
  ~500 rows, introduce server-side search/pagination."

## References

- `docs/discovery/CALL_NOTES_2026-05-09.md` — "Decisions Made on This Call"
- `docs/requirements/REQUIREMENTS.md` — FR-16, NFR-02, §1.3 out-of-scope
- `docs/requirements/FUNCTIONAL_DESIGN.md` — §7.7, §13
- `docs/requirements/api-spec.yaml` — `GET /api/vendors` (no query params)
