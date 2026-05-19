# AC-14 — Frontend Access Denied page (`/access-denied`)

| Field | Value |
|---|---|
| Jira story | [AC-14](https://cloudandthings.atlassian.net/browse/AC-14) — E3-S2 Frontend Access Denied page |
| Epic | [AC-4](https://cloudandthings.atlassian.net/browse/AC-4) — Procurement Data Access |
| Zone | 🟡 Yellow (`frontend/src/pages/AccessDenied.jsx`) |
| Ratified on | 2026-05-18 |
| Ratified by | C&T Project Lead |
| Status | Ratified — implementation may proceed |
| Visual source | [docs/design/05-access-denied.html](../design/05-access-denied.html) |
| Rationale | [DESIGN_RATIONALE.md §"Screen 5 — Access Denied"](../design/DESIGN_RATIONALE.md) |

## Decisions

> **2026-05-19 supersession** — [ADR-015](../adr/ADR-015-role-model-simplification.md)
> collapsed the role model to three roles (`PROCUREMENT_SUPERVISOR`,
> `REGULAR_STAFF`, `NON_STAFF`) and dropped `PROCUREMENT_LEVEL` entirely.
> Decisions ratified below remain on the historical record; the live code
> base now reflects ADR-015. Concrete renames: `ADMIN` → `PROCUREMENT_SUPERVISOR`,
> `STAFF` → `REGULAR_STAFF`, `LEVEL_ZERO` → `NON_STAFF`,
> `procurement_level` removed from claims and queries.


| # | Decision | Ratified value |
|---|---|---|
| AC14-D1 | Variant selection | Driven by **route state**, not a separate API call. Upstream callers (`VerificationCallback`, `DevPersonaPanel`) read `X-Auth-Reason` from the 403 response (`err.headers.get('X-Auth-Reason')`) and pass `{ reason: "LEVEL_ZERO" \| "NOT_REGISTERED" }` via `navigate("/access-denied", { state: { reason }, replace: true })`. AccessDenied reads via `useLocation().state?.reason`. |
| AC14-D2 | Default variant | If no route state present (e.g. direct URL hit / refresh), render the **LEVEL_ZERO** copy. Per DESIGN_RATIONALE.md §"Behaviour": "the safe default". |
| AC14-D3 | "Back to Staff Procurement Portal" target | `POST /api/auth/logout` (clears the cookie idempotently) then `navigate("/")`. **Always lands back on Login** — confirmed by user, supersedes the design rationale's optional `FRONTEND_URL` external jump. Keeps the demo entirely local. |
| AC14-D4 | Anonymous-shell layout | Reuses `AuthShellHeader` + `AuthShellFooter` + `SkipLink`. No user pill in the header — DESIGN_RATIONALE.md §"Why the header is the Login-style header". |
| AC14-D5 | Accessibility | `<main id="main">` landmark for the SkipLink target. Lock icon `aria-hidden`. CTA has `aria-label="Back to Staff Procurement Portal — signs you out and returns to the Staff Procurement Portal site"`. `role="alert"` deliberately NOT on the heading (rationale §765). `document.title` set to `Access Denied | Staff Procurement`. |
| AC14-D6 | Tests | 5 RTL tests: LEVEL_ZERO copy renders, NOT_REGISTERED copy renders, no-state defaults to LEVEL_ZERO, CTA POSTs logout + navigates to `/`, the SkipLink + main landmark are present. |
| AC14-D7 | Cross-cutting updates | `VerificationCallback.jsx` and `Login.jsx` `DevPersonaPanel` must read `X-Auth-Reason` from the 403 response and pass it via route state. Today both navigate to `/access-denied` with no state — under AC14-D2 that would silently land on the wrong variant for `NOT_REGISTERED` denials. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `frontend/src/pages/AccessDenied.jsx` | 🟡 Yellow | **Replace** the AC-10 placeholder with the real component |
| `frontend/src/pages/VerificationCallback.jsx` | 🟡 Yellow | Read `X-Auth-Reason` on 403, pass via route state (AC14-D7) |
| `frontend/src/pages/Login.jsx` | 🟡 Yellow | DevPersonaPanel: same X-Auth-Reason → route state threading |
| `frontend/src/pages/AccessDenied.test.jsx` | — | **New** (~5 tests) |
| `frontend/src/pages/VerificationCallback.test.jsx` | — | Update 403 test to assert `state.reason` is set |
| `frontend/src/pages/Login.test.jsx` | — | Update Admin-click test signature (no behavioural change) |

## Open follow-ups

- **External `FRONTEND_URL`** for "Back to Staff Procurement Portal" — out of scope per AC14-D3.
  Re-open if/when the demo deploys to an Staff Procurement Portal domain and the destination
  is no longer the in-app login.
- **Help-desk contact** in the callout — design rationale §781 open
  follow-up. Stays as the vague "contact your procurement coordinator"
  copy until Staff Procurement Portal provides a real contact (REQUIREMENTS.md §10 OQ-07).
