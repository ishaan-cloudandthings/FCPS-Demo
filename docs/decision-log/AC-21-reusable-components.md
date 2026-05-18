# AC-21 — Frontend reusable components

| Field | Value |
|---|---|
| Jira story | [AC-21](https://cloudandthings.atlassian.net/browse/AC-21) — E4-S7 |
| Epic | [AC-5](https://cloudandthings.atlassian.net/browse/AC-5) |
| Zone | 🟢 Green (`frontend/src/components/`) |
| Ratified on | 2026-05-18 |
| Status | Ratified — implementation may proceed |

## RBAC staging note

`VendorTable` reads the per-row `variant` field (AC-15 discriminator) and
renders the right column set. Today the API always emits `"admin"`
rows so the table renders the full set for everyone — but the
`staff_l1` / `staff_l2` branches are already in place for AC-17.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC21-D1 | `StatusBadge` | Pill with both colour AND text (NFR-04 / FR-18 — colour is never the sole signal). Colours per `brand.md`: APPROVED green, UNDER_REVIEW amber, REJECTED red, PENDING grey. |
| AC21-D2 | `SearchBar` | Controlled `<input type="search" role="searchbox">` with `<label>` (visible or visually-hidden). `onChange(value)` emitted via `useCallback`. Debounce deferred to caller — keeps the component pure. |
| AC21-D3 | `EmptyState` | Props `{ title, hint? }`. `<div role="status">` so SR users hear the message when list rows drop to zero. |
| AC21-D4 | `LoadingState` | Bounded skeleton — three placeholder rows, never an indefinite spinner. `aria-busy="true"` + `aria-live="polite"`. |
| AC21-D5 | `VendorTable` | Accepts `rows: VendorListItem[]` (any variant). Computes column set from `rows[0].variant`; empty list → renders `<EmptyState />`. Real `<table>` element with `<caption>` (visually-hidden) and scoped `<th>`. Click on a row navigates to `/vendors/:item_id`. |
| AC21-D6 | Column sets | `staff_l1`: vendor, item, category. `staff_l2`: + contact. `admin`: + status, unit price. Columns are declarative — adding a variant later is a one-line change. |
| AC21-D7 | Tests | Per component: minimum render, accessibility (status / searchbox roles, table caption / scoped headers), and (for VendorTable) variant-driven column rendering. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `frontend/src/components/StatusBadge.jsx` | 🟢 Green | New |
| `frontend/src/components/SearchBar.jsx` | 🟢 Green | New |
| `frontend/src/components/EmptyState.jsx` | 🟢 Green | New |
| `frontend/src/components/LoadingState.jsx` | 🟢 Green | New |
| `frontend/src/components/VendorTable.jsx` | 🟢 Green | New — variant-aware |
| `frontend/src/components/*.test.jsx` | — | One small test file per component |
