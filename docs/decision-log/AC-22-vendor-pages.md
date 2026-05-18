# AC-22 — Frontend vendor list + detail pages

| Field | Value |
|---|---|
| Jira story | [AC-22](https://cloudandthings.atlassian.net/browse/AC-22) — E4-S8 |
| Epic | [AC-5](https://cloudandthings.atlassian.net/browse/AC-5) |
| Zone | 🟡 Yellow (`frontend/src/pages/`) |
| Ratified on | 2026-05-18 |
| Status | Ratified — implementation may proceed |

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC22-D1 | `VendorList.jsx` data fetch | On mount, call `GET /api/vendors`. While in flight → `<LoadingState />`. Success → `<VendorTable />`. 401 from `apiFetch` resets the auth store and the parent `ProtectedRoute` redirects (no per-page 401 handling). Other failures render an inline error message. |
| AC22-D2 | Client-side filter | Local `searchTerm` state filters rows by `vendor_name` case-insensitive substring (FUNCTIONAL_DESIGN.md §7.7). `<SearchBar />` controls it. Filtered-to-empty renders the empty state with a "no results for X" message. |
| AC22-D3 | `VendorDetail.jsx` route | New route `GET /vendors/:item_id`, wrapped by `ProtectedRoute`. Fetches `GET /api/vendors/{item_id}` once on mount. 404 → renders a friendly "Vendor not found" card with a back link. |
| AC22-D4 | Detail layout | Single-column card with header (vendor name + status badge), `<dl>` of fields (item, category, contact name, contact email, unit price, approved-at if APPROVED), and a "Back to vendors" link. Mirrors `docs/design/04-vendor-detail.html` structurally but kept lean (full visual fidelity is a polish pass). |
| AC22-D5 | Page-title discipline | `document.title = "Vendors \| FCPS Procurement"` on list mount; `"{vendor_name} \| FCPS Procurement"` on detail load. |
| AC22-D6 | Tests | RTL: list happy path renders rows from `/api/vendors`; client-side filter narrows visible rows; loading state shows before fetch resolves. Detail: 200 renders the fields; 404 renders the friendly card. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `frontend/src/pages/VendorList.jsx` | 🟡 Yellow | Replace AC-20 placeholder with the real list page |
| `frontend/src/pages/VendorDetail.jsx` | 🟡 Yellow | New — detail page |
| `frontend/src/App.jsx` | 🟡 Yellow | Add `/vendors/:item_id` route wrapped in `ProtectedRoute` |
| `frontend/src/pages/VendorList.test.jsx` | — | New |
| `frontend/src/pages/VendorDetail.test.jsx` | — | New |
