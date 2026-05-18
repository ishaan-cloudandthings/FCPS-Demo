# AC-20 — Frontend foundations: ProtectedRoute + authenticated AppHeader

| Field | Value |
|---|---|
| Jira story | [AC-20](https://cloudandthings.atlassian.net/browse/AC-20) — E4-S6 |
| Epic | [AC-5](https://cloudandthings.atlassian.net/browse/AC-5) |
| Zone | 🟡 Yellow (`frontend/src/components/`) |
| Ratified on | 2026-05-18 |
| Status | Ratified — implementation may proceed |

## Scope reconciliation with AC-10

The Jira description lists "apiFetch + store + ProtectedRoute + Header".
**apiFetch and the Zustand auth store already shipped in AC-10** (see
[AC-10 scaffold](../../frontend/README.md)). This story is scoped to the
parts not already in main:

- `ProtectedRoute` — wraps `/vendors` and `/vendors/:id` so unauthenticated
  users bounce to `/`.
- `AppHeader` — the **authenticated** header (user pill + Log out button)
  distinct from `AuthShellHeader` (anonymous shell — login / callback /
  access-denied).
- Wire `App.jsx` to use both.

## RBAC staging note

`ProtectedRoute` checks **auth only** today (status === "authenticated").
A `level` prop is reserved for AC-17 (when `require_level(...)` becomes
real on the backend), but the prop has no effect yet. Comment + grep
marker `TODO(AC-17)` in the file.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| AC20-D1 | `ProtectedRoute` shape | `<ProtectedRoute>{children}</ProtectedRoute>` wraps any element. Reads `useAuthStore` — if `status === "loading"`, render nothing (or a minimal skeleton); if `"unauthenticated"`, `<Navigate to="/?reason=session_expired" replace />`; if `"authenticated"`, render children. |
| AC20-D2 | Loading state | Empty fragment (`null`) — the auth bootstrap takes < 100 ms in practice; flashing a skeleton is worse UX than a single blank frame. |
| AC20-D3 | `AppHeader` shape | New `frontend/src/components/AppHeader.jsx`. Brand wordmark on the left, user pill (`Signed in · {role} · L{procurement_level} · #{staff_id}`) + "Log out" button on the right. Logout = `POST /api/auth/logout` then `setUnauthenticated()` and `navigate("/")`. |
| AC20-D4 | Authenticated layout shell | Header + main + footer pattern, mirroring `AuthShellHeader`/Footer. AC-22 will render its pages inside this. |
| AC20-D5 | Wire-up | `App.jsx` — `<Route path="/vendors" element={<ProtectedRoute><VendorList /></ProtectedRoute>} />`. Same pattern for `/vendors/:item_id` (added in AC-22). VendorList placeholder updated to render inside `AppHeader` shell. |
| AC20-D6 | Tests | RTL: ProtectedRoute renders children when authenticated; redirects when unauthenticated; renders nothing when loading. AppHeader renders user pill; logout button POSTs `/api/auth/logout`, resets store, navigates `/`. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `frontend/src/components/ProtectedRoute.jsx` | 🟡 Yellow | **New** |
| `frontend/src/components/AppHeader.jsx` | 🟡 Yellow | **New** |
| `frontend/src/components/AppShell.jsx` | 🟡 Yellow | **New** — `<AppShell>` wraps children with `AppHeader` + `AuthShellFooter` |
| `frontend/src/App.jsx` | 🟡 Yellow | Wrap `/vendors` route with `ProtectedRoute` |
| `frontend/src/pages/VendorList.jsx` | 🟡 Yellow | Render inside `AppShell` (placeholder remains; AC-22 fills the body) |
| `frontend/src/components/ProtectedRoute.test.jsx` | — | New (3 tests) |
| `frontend/src/components/AppHeader.test.jsx` | — | New (3 tests) |
