# Decision Log

This folder records non-ADR decisions made during the build of the FCPS
Procurement Portal — implementation choices, tooling picks, story-scoped
Red Zone ratifications, operational settings, and anything else where
"there's a reason we did it this way" should be discoverable later.

## ADR vs decision-log — when to use which

| Use [`docs/adr/`](../adr/) when… | Use this folder when… |
|---|---|
| The decision changes the architecture or constraints other parts of the system | The decision is local to one story, module, or build choice |
| It's worth reading by anyone joining the project | It's only worth reading if you're touching that specific code |
| It's likely to be cited in future ADRs | It's a one-off choice with a contained blast radius |
| Examples: `EC2 + Docker Compose`, `ID.me sandbox only`, `Bank details out of scope` | Examples: `which Python lib to use for X`, `the 12 design choices for story AC-6`, `pytest config conventions` |

If you're unsure, default to **this folder**. Promoting later is easy;
demoting an over-formal ADR is awkward.

## Conventions

- **Story-scoped files** named `<JIRA-KEY>-<short-slug>.md` — e.g.
  `AC-6-login-init.md`. Used when the decisions are tied to a single
  story.
- **Topical files** named with a descriptive slug — e.g.
  `testing-conventions.md`, `state-cache-pattern.md`. Used for
  cross-cutting choices.
- Every file should have a **metadata header** (story or topic, date,
  who approved) and a **decisions table** so the file is skimmable.
- Code that implements ratified decisions should reference the file in a
  short header comment so a reader of the code can find the rationale.

## Index

| File | Topic | Date |
|---|---|---|
| [AC-6-login-init.md](./AC-6-login-init.md) | Red Zone decisions for story AC-6 (POST /api/auth/login) | 2026-05-18 |
| [AC-7-callback.md](./AC-7-callback.md) | Red Zone decisions for story AC-7 (POST /api/auth/callback) | 2026-05-18 |
| [AC-8-jwt.md](./AC-8-jwt.md) | Red Zone decisions for story AC-8 (JWT issuance + verification + auth dependencies) | 2026-05-18 |
| [AC-9-session-lifecycle.md](./AC-9-session-lifecycle.md) | Red Zone decisions for story AC-9 (POST /api/auth/logout + GET /api/auth/me) | 2026-05-18 |
| [DEV-AUTH-persona-picker.md](./DEV-AUTH-persona-picker.md) | Red Zone code-level decisions for the dev-only persona login (see ADR-014) | 2026-05-18 |
| [AC-11-oracle-staff-lookup.md](./AC-11-oracle-staff-lookup.md) | Yellow Zone decisions for story AC-11 (Oracle connection factory + STAFF query) | 2026-05-18 |
| [AC-12-seed-staff.md](./AC-12-seed-staff.md) | Green Zone decisions for story AC-12 (seed_oracle.py STAFF schema + 10 records) + dev_auth staff_id realignment | 2026-05-18 |
| [AC-13-access-service.md](./AC-13-access-service.md) | Yellow Zone decisions for story AC-13 (decide_access decision tree + OracleUnavailable → 503) | 2026-05-18 |
| [AC-14-access-denied.md](./AC-14-access-denied.md) | Yellow Zone decisions for story AC-14 (frontend AccessDenied page + X-Auth-Reason → route state) | 2026-05-18 |
| [AC-15-vendor-schemas.md](./AC-15-vendor-schemas.md) | Green Zone decisions for story AC-15 (per-level Pydantic vendor schemas) | 2026-05-18 |
| [AC-16-procurement-queries.md](./AC-16-procurement-queries.md) | Yellow Zone decisions for story AC-16 (`list_vendors` + `get_vendor_by_id`) | 2026-05-18 |
| [AC-18-procurement-router.md](./AC-18-procurement-router.md) | Yellow Zone decisions for story AC-18 (procurement router; list + detail, auth-only) | 2026-05-18 |
| [AC-19-seed-procurement-items.md](./AC-19-seed-procurement-items.md) | Green Zone decisions for story AC-19 (PROCUREMENT_ITEMS seed + APPROVED_AT) | 2026-05-18 |
| [AC-20-frontend-foundations.md](./AC-20-frontend-foundations.md) | Yellow Zone decisions for story AC-20 (ProtectedRoute + authenticated AppHeader) | 2026-05-18 |
| [AC-21-reusable-components.md](./AC-21-reusable-components.md) | Green Zone decisions for story AC-21 (VendorTable + 4 supporting components) | 2026-05-18 |
| [AC-22-vendor-pages.md](./AC-22-vendor-pages.md) | Yellow Zone decisions for story AC-22 (frontend vendor list + detail pages) | 2026-05-18 |
| [demo-zero-config-boot.md](./demo-zero-config-boot.md) | Zero-config boot posture: built-in demo defaults in Settings + non-dev guard | 2026-05-19 |
| [demo-inmem-vendor-fallback.md](./demo-inmem-vendor-fallback.md) | Dev-only in-memory fallback for `/api/vendors*` when Oracle is unreachable | 2026-05-19 |
