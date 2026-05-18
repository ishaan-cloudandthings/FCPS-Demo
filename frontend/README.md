# FCPS Procurement Portal — Frontend

React SPA. See:

- [`../docs/requirements/FUNCTIONAL_DESIGN.md`](../docs/requirements/FUNCTIONAL_DESIGN.md) §7 — component contracts.
- [`../docs/design/`](../docs/design/) — HTML mockups + `DESIGN_RATIONALE.md`.
- [`../docs/design/brand.md`](../docs/design/brand.md) — colour + type tokens (mirrored in `tailwind.config.js`).

## Stack

- **Vite 4.5** (Node-16 compatible) + **React 18** + **React Router 6**.
- **Tailwind CSS 3** — brand tokens live in `tailwind.config.js`.
- **Zustand** for state (auth slice per FD §7.5).
- **Native `fetch`** wrapped by `services/apiFetch.js`.
- **Vitest 0.34 + React Testing Library** for component tests.

> **Heads-up:** Vite 5 / Vitest 1+ requires Node ≥18. The pinned versions
> here run on Node 16. Bump both when the dev environment upgrades.

## Dev

```bash
cd frontend
npm install
npm run dev         # Vite on :5173, proxies /api → :8000
npm run test        # vitest
npm run build       # production bundle into dist/
```

The Vite dev server proxies `/api/*` to the FastAPI backend on
`http://localhost:8000` so the SPA and the API share an origin in dev
(matching the prod Nginx topology — see `docs/ARCHITECTURE.md` §8.1).

Run the backend separately:

```bash
cd ../backend
.venv/bin/uvicorn main:app --reload --port 8000
```

## Demo-mode persona picker (dev only)

When the backend runs with `ENVIRONMENT=dev`, the Login page renders an
extra "Demo mode · dev only" panel with five outlined buttons that sign
you in as a hardcoded persona — no ID.me, no Oracle. See
[ADR-014](../docs/adr/ADR-014-demo-persona-login-dev-only.md) and the
code-level decisions in
[`docs/decision-log/DEV-AUTH-persona-picker.md`](../docs/decision-log/DEV-AUTH-persona-picker.md).

| Button | Outcome | Lands on |
|---|---|---|
| `Admin` | 200, `{role: ADMIN, procurement_level: 3}` | `/vendors` |
| `Staff L2` | 200, `{role: STAFF, procurement_level: 2}` | `/vendors` |
| `Staff L1` | 200, `{role: STAFF, procurement_level: 1}` | `/vendors` |
| `Level 0` | 403 + `X-Auth-Reason: LEVEL_ZERO` | `/access-denied` |
| `Not registered` | 403 + `X-Auth-Reason: NOT_REGISTERED` | `/access-denied` |

The SPA learns whether to render the panel by probing
`GET /api/auth/dev-login/available` on Login mount. Outside `dev`, the
backend returns 404 and the panel is invisible. There is no frontend env
flag — the backend is the single source of truth.

## What's in the AC-10 scaffold

| Path | Purpose | Source-of-truth |
|---|---|---|
| `src/pages/Login.jsx` | `/` and `/?reason=…` — "Verify with ID.me" CTA + banner | `docs/design/01-login.html` |
| `src/pages/VerificationCallback.jsx` | `/verification/callback` — POST + 10 s bounded timeout | `docs/design/02-verification-callback.html` |
| `src/pages/AccessDenied.jsx` | `/access-denied` — **placeholder** for AC-11 | `docs/design/05-access-denied.html` |
| `src/pages/VendorList.jsx` | `/vendors` — **placeholder** for AC-12 | `docs/design/03-vendor-list.html` |
| `src/services/apiFetch.js` | Thin `fetch` wrapper — `credentials: include`, typed errors | FD §7.6 |
| `src/store/auth.js` | Zustand auth slice | FD §7.5 |
| `src/hooks/useAuthBootstrap.js` | Calls GET /api/auth/me once on App mount | FD §7.2 |
| `src/components/AuthShellHeader.jsx` | Anonymous-shell header | `01-login.html`, `05-access-denied.html` |
| `src/components/AuthShellFooter.jsx` | Anonymous-shell footer | `01-login.html` |
| `src/components/SkipLink.jsx` | Skip-to-main accessibility link | DESIGN_RATIONALE §80 |
| `tailwind.config.js` | Brand tokens + animations | `docs/design/brand.md` |
