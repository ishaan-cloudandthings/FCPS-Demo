# AC-9 — Session lifecycle (logout + /me): ratified Red Zone decisions

| Field | Value |
|---|---|
| Jira story | [AC-9](https://cloudandthings.atlassian.net/browse/AC-9) — E1-S4 Session lifecycle endpoints (logout + /me) |
| Epic | [AC-2](https://cloudandthings.atlassian.net/browse/AC-2) — Identity Verification |
| Zone | 🔴 Red (`backend/app/api/auth.py`, `backend/app/auth/`) |
| Ratified on | 2026-05-18 |
| Ratified by | C&T Project Lead |
| Status | Ratified — implementation may proceed |

## What's in this file

Per `AI_POLICY.md` § 🔴 Red rules, every decision is on record before
code is written. This file captures the story-specific decisions
AC9-D1 … AC9-D8 plus the one cross-cutting documentation correction
(api-spec.yaml `SessionResponse` ← FD §6.1).

The pre-existing FD decisions in scope are §6.1 (logout + /me endpoint
contracts) and §7.2 (SPA mount calls /me; 401 → `/?reason=session_expired`).

## Story-specific decisions

| # | Decision | Ratified value |
|---|---|---|
| AC9-D1 | Logout response | 204 No Content, no body. Always 204, even if no/invalid session cookie present — idempotent. `response.delete_cookie(...)` is a no-op on the browser side if the cookie was already absent. |
| AC9-D2 | Logout cookie-clearing attributes | Must match the **issue-time attributes** exactly, otherwise the browser sees a different cookie and the clear is silently ignored. New helper `delete_session_cookie(response, *, secure)` in `app/auth/jwt_session.py` reuses `COOKIE_NAME`, `COOKIE_PATH`, `COOKIE_SAMESITE` constants. |
| AC9-D3 | Logout auth requirement | **No `Depends(require_authenticated)`**. Endpoint is unauthenticated by design — protects against the "I can't log out because my session expired" failure loop. |
| AC9-D4 | `/me` response shape | **Include `staff_id`** in the response per FD §6.1 + §7.2 (SPA hydrates `{role, procurement_level, staff_id}` on every mount). Extends `SessionResponse` rather than introducing a new `MeResponse` — schema simplicity over a near-duplicate. AC-7's `/callback` response also gains `staff_id` as a result (additive, no behaviour change). |
| AC9-D5 | `/me` failure mode | Reuse `Depends(require_authenticated)` directly — same 401 + body `{"detail": "Session invalid or expired."}` envelope as every other protected endpoint. No new failure logic in this story. |
| AC9-D6 | Logging | `auth.logout` at INFO (no PII). `/me` logs **nothing on success** — called on every SPA mount, would flood logs. The existing `require_authenticated` 401 path already logs `auth.session.missing` / `jwt.verify_failed` at WARNING; that's enough. |
| AC9-D7 | Tests | ~7 cases: logout-clears-cookie, logout-204-without-cookie (idempotent), logout-204-with-invalid-cookie (idempotent), logout-cookie-attrs-match-issue-time, /me-returns-claims-when-authed, /me-returns-401-when-no-cookie, /me-returns-401-when-token-expired. |
| AC9-D8 | api-spec.yaml correction | Update `components.schemas.SessionResponse` to include `staff_id: integer` and add it to `required`. This is a documentation-debt fix — the FD and api-spec disagreed; FD wins because the SPA hydration code already targets that shape. |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/app/auth/jwt_session.py` | 🔴 Red | Add `delete_session_cookie` helper |
| `backend/app/api/auth.py` | 🔴 Red | Add `POST /api/auth/logout` and `GET /api/auth/me`; `/callback` response now also includes `staff_id` |
| `backend/app/schemas/auth.py` | 🟡 Yellow | Extend `SessionResponse` with `staff_id: int` |
| `docs/requirements/api-spec.yaml` | — | Update `SessionResponse` schema to include `staff_id` |
| `backend/tests/test_auth_logout.py` | — | New (~4 tests) |
| `backend/tests/test_auth_me.py` | — | New (~3 tests) |
| `backend/tests/test_auth_callback.py` | — | Minor: existing assertion may need `staff_id` added |

## Open follow-ups

- **CSRF** — `SameSite=Lax` is the only CSRF mitigation on the demo
  (ADR-008). The logout endpoint accepts POST without a CSRF token,
  matching every other state-changing endpoint here. Acceptable for the
  demo; production would gain a synchroniser-token or double-submit
  cookie pattern.
- **Logout while ID.me session is still live** — out of scope. We clear
  only our own cookie; the ID.me session may still grant a fresh login
  on next /login click. FD §6.4 D-FD-07 already documents that "no
  refresh tokens" implies re-verification, which is the intended UX.
