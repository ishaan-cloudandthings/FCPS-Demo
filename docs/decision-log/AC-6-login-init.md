# AC-6 — POST /api/auth/login: ratified Red Zone decisions

| Field | Value |
|---|---|
| Jira story | [AC-6](https://cloudandthings.atlassian.net/browse/AC-6) — E1-S1 ID.me login initiation |
| Epic | [AC-2](https://cloudandthings.atlassian.net/browse/AC-2) — Identity Verification |
| Zone | 🔴 Red (`backend/app/auth/`, `backend/app/api/auth.py`) per `AI_ZONES.md` |
| Ratified on | 2026-05-18 |
| Ratified by | C&T Project Lead |
| Status | Ratified — implementation may proceed |

## What's in this file

`AI_POLICY.md` § 🔴 Red rules say *"Human must approve all decisions on
record before AI writes a single line."* This file is that "on record"
artefact for story AC-6.

It captures:

1. The pre-existing FD decisions that apply to this story (D-FD-08).
2. The new, story-specific decisions surfaced and ratified for this
   build (AC6-D1 … AC6-D12).
3. The AC text clarification that resulted from the surfacing.

## Decisions ratified

### From FUNCTIONAL_DESIGN.md §6.1 — D-FD-08

`POST /api/auth/login` generates a 32-byte URL-safe `state`, stores it in
a short-lived server-side cache (in-process dict, TTL 10 min, one-shot),
and returns the full ID.me `authorize_url` JSON. SPA performs the
redirect.

### Story-specific decisions

| # | Decision | Ratified value |
|---|---|---|
| AC6-D1 | State token generation | `secrets.token_urlsafe(32)` — 32-byte URL-safe; ~43 char output |
| AC6-D2 | State cache backing + scale | In-process Python dict, single Uvicorn worker (`--workers 1`). Multi-worker → Redis is phase 2 (see FD OQ-FD-02). |
| AC6-D3 | Thread safety | No explicit `threading.Lock` — Uvicorn async + single-threaded event loop makes dict ops atomic between awaits. A lock would mislead readers. |
| AC6-D4 | Cache cleanup | Lazy expiry: check + pop on every read/issue. Cap at **1024 entries**; over-cap returns HTTP 503. No background sweeper. |
| AC6-D5 | State entry shape | `{state_token: (issued_at, used=False)}`. `consume()` pops the entry and reports valid/invalid in one call — enforces one-shot semantics. |
| AC6-D6 | Authorize URL construction | All 5 OAuth params: `client_id`, `redirect_uri`, `state`, `scope=openid email`, `response_type=code`. Built via `urllib.parse.urlencode`. |
| AC6-D7 | Where the redirect URI comes from | Explicit env var `IDME_REDIRECT_URI` — not derived from `FRONTEND_URL`. Must match exactly what's registered in the ID.me console (2026-05-05 IT Lead warning). |
| AC6-D8 | ID.me URLs in env | `IDME_CLIENT_ID`, `IDME_AUTHORIZE_URL`, `IDME_REDIRECT_URI` all explicit env vars; validated at startup by `pydantic-settings`. |
| AC6-D9 | Logging | One info log per call: `auth.login.start` with `ip` + `user_agent`. **State token must never appear in any log.** |
| AC6-D10 | Response shape | `{"authorize_url": "<full URL>"}` — Pydantic `AuthorizeUrlResponse` with `extra="forbid"`. Matches api-spec.yaml. |
| AC6-D11 | Internal error handling | Global FastAPI exception handler returns 500 with body `{"detail": "Something went wrong. Please try again."}`. No stack traces in browser-facing response (NFR-12). |
| AC6-D12 | No CSRF on this endpoint | This POST doesn't mutate user-visible state, runs same-origin (Nginx serves both SPA and API), and is the entry-point of the auth flow. CSRF token would be ceremony. |

## AC text clarification

The original AC-6 included:

> *"As an operator, I should see ID.me network outages surface as HTTP 502 with body 'Identity provider unreachable.'"*

This was misplaced. `POST /api/auth/login` does **not** call ID.me — it
only composes the authorize URL. The 502 case belongs to AC-7 (callback),
which performs the token exchange. The bullet has been **removed from
AC-6** and is already present on AC-7.

The final AC list for AC-6 is:

1. As an unauthenticated staff member, I can click "Verify with ID.me" and be redirected to the ID.me sign-in screen.
2. As the backend, I should generate a single-use 32-byte URL-safe `state` and store it in a 10-minute cache.
3. As a security reviewer, I can confirm `state` reuse is rejected because the cache entry is one-shot.
4. As an operator, if the state cache is at capacity (1024 entries), the endpoint returns HTTP 503 with a user-friendly body.
5. As a security reviewer, I can confirm the state token is never written to application logs.

## Code that references this file

The header comment of every file implementing AC-6 should cite this
decision log so a future reader of the code can find the rationale:

- `backend/app/api/auth.py` (🔴 Red)
- `backend/app/auth/state_cache.py` (🔴 Red)

## Open follow-ups

- When the demo is over and we move toward production, AC6-D2 (in-process
  single-worker state cache) must be revisited — Redis or another shared
  store will be needed for multi-worker deploy.
- AC6-D4's 1024-entry cap is a hard-coded constant; if the demo audience
  is unusually large, raise it.
