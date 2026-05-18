# DEV-AUTH — Demo persona picker: ratified Red Zone decisions

| Field | Value |
|---|---|
| Jira story | n/a — tooling change ratified directly (not in the AC-* backlog) |
| ADR | [ADR-014 — Demo persona login for `dev` environments only](../adr/ADR-014-demo-persona-login-dev-only.md) |
| Zone | 🔴 Red (`backend/app/api/dev_auth.py` — mints session cookies) |
| Ratified on | 2026-05-18 |
| Ratified by | C&T Project Lead |
| Status | Ratified — implementation may proceed |

## What's in this file

ADR-014 captures the architectural decision. This file captures the
**code-level** ratified decisions DEV1 … DEV13 — the things a contributor
opening `dev_auth.py` needs to find to defend any line of code in there.

## Story-specific decisions

| # | Decision | Ratified value |
|---|---|---|
| DEV1 | Router location | New file `backend/app/api/dev_auth.py` with prefix `/api/auth`. Routes: `POST /api/auth/dev-login` and `GET /api/auth/dev-login/available`. Colocated with the real auth surface so a reader of `app/api/` sees the full auth picture in one folder. |
| DEV2 | Env-gate (defence in depth) | **Boot-time:** `main.py` only `include_router(dev_auth.router)` when `settings.environment == "dev"`. **Request-time:** every handler re-reads `settings.environment` and raises `HTTPException(404)` if not dev. 404, not 403 — indistinguishable from "endpoint does not exist". |
| DEV3 | Persona table | `admin_l3` → 200 + session `{staff_id=1, ADMIN, L3}`. `staff_l2` → 200 + `{staff_id=2, STAFF, L2}`. `staff_l1` → 200 + `{staff_id=3, STAFF, L1}`. `level_zero` → 403 + `X-Auth-Reason: LEVEL_ZERO` + body matching `_DETAIL_LEVEL_ZERO`. `not_registered` → 403 + `X-Auth-Reason: NOT_REGISTERED` + body matching `_DETAIL_NOT_REGISTERED`. Both denied-bodies imported from `app.api.auth` so they cannot drift. |
| DEV4 | Probe endpoint | `GET /api/auth/dev-login/available` → 200 `{"available": true}` in dev, 404 otherwise. SPA renders the persona panel only on 200. |
| DEV5 | Session-issue path | Reuses `Depends(get_session_issuer)` — same `issue_session_cookie` as `/callback` (AC-7/AC-8). Cookie attributes and JWT claims inherit AC-8 verbatim. No second JWT format. |
| DEV6 | Auth requirement | None — endpoint is unauthenticated by design (it mints sessions). Calling twice replaces the cookie — idempotent. |
| DEV7 | Logging | `dev_auth.login persona=<key> outcome=<granted\|denied> DEV_AUTH_USED` at INFO. The literal token `DEV_AUTH_USED` is mandatory in every log line for prod-leak detection. The session JWT itself is never logged (AC8-D13). |
| DEV8 | Request schema | Pydantic `DevLoginRequest { persona: Literal[admin_l3, staff_l2, staff_l1, level_zero, not_registered] }`, `extra="forbid"`. Unknown persona → 422 (Pydantic validation). Adding a new persona is a code change, not data-driven. |
| DEV9 | Frontend probe behaviour | Login.jsx fetches `/api/auth/dev-login/available` once on mount. 200 → render panel. 404 (and any other failure) is **silent** — no error banner, no console noise, no log; production builds are visually identical to the ID.me-only product. |
| DEV10 | ADR + decision log linkage | ADR-014 is the architectural record; this file is the code-level record. Both cross-reference. Any change to either must update the other. |
| DEV11 | Tests | **Backend** (~7): one per persona response shape (5), one for non-dev environment returning 404 for both routes (1), one for the probe endpoint in dev (1). **Frontend** (~3): probe-200 renders panel, probe-404 hides panel, click `Admin` → POST + navigate `/vendors`. |
| DEV12 | UI treatment | Five outlined buttons (white bg, light grey border) stacked vertically in the sign-in panel. Labels are simple persona names: `Admin`, `Staff L2`, `Staff L1`, `Level 0`, `Not registered`. Small divider above reading **"Demo mode · dev only"**. No descriptions on the buttons (per stakeholder preference). |
| DEV13 | Kill criteria (also in ADR-014) | Remove `dev_auth.py`, schema entries, tests, and the Login.jsx panel when **either**: (a) the demo programme has wrapped and no further stakeholder showings are scheduled, OR (b) any non-dev environment is being provisioned. Architect signoff required to delete the env-gate without removing the code. |

## Files this change creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/app/api/dev_auth.py` | 🔴 Red | **New** — router + handlers + persona table |
| `backend/app/schemas/auth.py` | 🟡 Yellow | Add `DevLoginRequest`, `DevLoginAvailableResponse` |
| `backend/main.py` | 🟡 Yellow | Conditionally `include_router(dev_auth.router)` |
| `backend/tests/test_dev_auth.py` | — | New (~7 tests) |
| `frontend/src/pages/Login.jsx` | 🟡 Yellow | Add probe + persona panel |
| `frontend/src/pages/Login.test.jsx` | — | Extend with ~3 panel tests |
| `docs/adr/ADR-014-demo-persona-login-dev-only.md` | — | New |
| `docs/adr/README.md` | — | Index update |
| `docs/decision-log/README.md` | — | Index update |
| `AI_ZONES.md` | — | List `backend/app/api/dev_auth.py` under Red Zone |
| `docs/requirements/REQUIREMENTS.md` | — | Add dev-only exception to FR-01 |
| `docs/requirements/FUNCTIONAL_DESIGN.md` | — | Section §6.1 mentions `dev_auth` (boundary, not body) |
| `docs/requirements/api-spec.yaml` | — | Add the two dev endpoints; mark dev-only |
| `frontend/README.md` | — | Document the persona panel |

## Open follow-ups

- **Backend log alerting** — if/when a real log aggregator is wired up,
  alert on `DEV_AUTH_USED` appearing in non-dev environments. Today's
  stdout-only logging makes this manual.
- **Kill date** — to be set when the demo programme has a known wrap
  date. Until then, the kill criteria in ADR-014 are conditional.
