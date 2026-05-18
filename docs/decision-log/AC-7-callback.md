# AC-7 — POST /api/auth/callback: ratified Red Zone decisions

| Field | Value |
|---|---|
| Jira story | [AC-7](https://cloudandthings.atlassian.net/browse/AC-7) — E1-S2 ID.me callback (code exchange + ID-token validation) |
| Epic | [AC-2](https://cloudandthings.atlassian.net/browse/AC-2) — Identity Verification |
| Zone | 🔴 Red (`backend/app/auth/`, `backend/app/api/auth.py`) |
| Ratified on | 2026-05-18 |
| Ratified by | C&T Project Lead |
| Status | Ratified — implementation may proceed |

## What's in this file

Per `AI_POLICY.md` § 🔴 Red rules, every decision is on record before code
is written. This file is that record for AC-7.

It captures:

1. The pre-existing FD §6.1 decisions (D-FD-09 … D-FD-12) that apply to
   this story.
2. The new, story-specific decisions surfaced and ratified for this build
   (AC7-D1 … AC7-D13).
3. The dependency strategy for AC-8 (JWT) and AC-13 (access decision),
   which are not yet implemented but whose interfaces AC-7 must define.

## Decisions ratified from FUNCTIONAL_DESIGN.md §6.1

### D-FD-09 — state validation
`POST /api/auth/callback` accepts `{code, state}` JSON. Validates `state`
against the in-process cache from AC-6 (one-shot, 10-min TTL). Unknown or
expired state → **400** with body `"Authentication request expired. Please verify again."`

### D-FD-10 — token exchange
HTTP POST to ID.me `/oauth/token` with form-encoded `client_id`,
`client_secret`, `code`, `grant_type=authorization_code`, `redirect_uri`.
**5 s timeout.** Network error or non-2xx response → **502** with body
`"Identity provider unreachable."`

### D-FD-11 — ID-token validation
Verify `iss`, `aud == client_id`, `exp`, `iat`. Signature via ID.me JWKS,
cached in-process 60 min. Any failure → **401** with body
`"Identity verification failed."`

### D-FD-12 — dispatch
After validation, call `access_service.decide_access(sub)`. On `GRANTED`,
set the JWT cookie + return `{role, procurement_level}`. On any denial,
**403** with the correct user-facing copy + `X-Auth-Reason` header.

## Story-specific decisions

| # | Decision | Ratified value |
|---|---|---|
| AC7-D1 | HTTP client library | `httpx` (already in requirements; modern, easy to mock with `respx`). |
| AC7-D2 | HTTP client transport | Synchronous `httpx.Client`, per-request (not module-level). |
| AC7-D3 | JWKS cache backing | In-process `dict[kid → jwk]`. 60-min TTL across the whole cache. Single-Uvicorn-worker assumption (same as AC6-D2). On JWKS fetch failure, **raise** — never fall back to unverified validation. |
| AC7-D4 | JWT algorithm allowlist for ID-token validation | **`["RS256"]` only.** Pass explicit `algorithms` arg to `python-jose`. Reject any other `alg` including `none` and `HS*`. |
| AC7-D5 | Clock-skew tolerance | 30 s on `exp` and `iat` — matches D-FD-06 used by our own JWT in AC-8. |
| AC7-D6 | Order of operations | (1) parse + validate body, (2) consume `state` (cheap; fail fast on replay), (3) POST `/oauth/token` to ID.me, (4) validate ID token, (5) extract `sub`, (6) dispatch to `access_service`, (7) issue JWT or 403. |
| AC7-D7 | State-valid + ID.me-5xxs case | State has already been consumed; user must restart from `/`. Response is 502 per D-FD-10. The SPA handles this on the callback page (AC-10). |
| AC7-D8 | Dependency strategy for AC-8 + AC-13 | **Define interfaces here, ship stub bodies that raise `NotImplementedError`.** AC-7's endpoint calls them via FastAPI `Depends` so tests can mock both. AC-8 replaces the body of `jwt_session.issue_session_cookie`; AC-13 replaces the body of `access_service.decide_access`. No AC-7 changes needed when those land. |
| AC7-D9 | `X-Auth-Reason` header mapping | `LEVEL_ZERO` → `LEVEL_ZERO` (body uses the LEVEL_ZERO copy). `NOT_FOUND` / `NOT_VERIFIED` / `INACTIVE` → collapse to `NOT_REGISTERED` (body uses the NOT_REGISTERED copy). Matches FD §6.6 + ADR-013. |
| AC7-D10 | Logging | `auth.callback.start`, `auth.callback.invalid_state`, `auth.callback.idme_unreachable`, `auth.callback.id_token_invalid`, `auth.callback.granted` (with `staff_id`, `role`, `procurement_level` — none PII), `auth.callback.denied reason=…`. **Never log:** `code`, `state`, `id_token`, raw `sub`, response body. |
| AC7-D11 | `sub` handling | `sub` is PII-equivalent. Passed to `access_service.decide_access()` and never logged or returned. `staff_id` (Oracle PK) is what flows into the JWT — `sub` never enters the cookie. |
| AC7-D12 | Validation of `CallbackRequest` | Pydantic `BaseModel`, `extra="forbid"`; `code` and `state` both `min_length=1`. Anything else → 422 (FastAPI default for body validation). |
| AC7-D13 | Tests | `pytest` + `respx` for `httpx` mocking + `python-jose` for crafting test ID tokens (signed with a per-test RSA keypair; the mocked JWKS endpoint serves the public key). Coverage: every branch in the order-of-operations above. |

## Dependency strategy detail (AC7-D8)

Two new modules ship with **stubs**, not real implementations:

| File | Function | What ships | What replaces it later |
|---|---|---|---|
| `app/auth/jwt_session.py` | `issue_session_cookie(response, *, staff_id, role, procurement_level) -> None` | `raise NotImplementedError("AC-8 will implement this")` | AC-8 fills in the body (HS256 JWT, HttpOnly cookie, 4 h TTL — per ADR-004). |
| `app/services/access_service.py` | `decide_access(sub: str) -> AccessDecision` | `raise NotImplementedError("AC-13 will implement this")` | AC-13 fills in the body (Oracle STAFF lookup, decision tree per FD §6.6). |

The dataclass `AccessDecision` (signature + fields) is fully defined here
because the AC-7 endpoint reads it. AC-13 keeps the dataclass and fills
the function body.

The endpoint uses `Depends(get_access_decider)` and
`Depends(get_session_issuer)` rather than importing the functions
directly, so tests can inject mocks without monkeypatching.

## What code references this file

- `backend/app/api/auth.py` (🔴) — header comment
- `backend/app/auth/idme_client.py` (🔴) — header comment
- `backend/app/auth/jwks_cache.py` (🔴) — header comment
- `backend/app/auth/id_token_validator.py` (🔴) — header comment
- `backend/app/auth/jwt_session.py` (🔴) — header comment (stub for AC-8)
- `backend/app/services/access_service.py` (🟡) — header comment (stub for AC-13)

## Open follow-ups

- When AC-8 lands, remove the `raise NotImplementedError` in
  `jwt_session.issue_session_cookie` and implement per ADR-004.
- When AC-13 lands, do the same for `access_service.decide_access`.
- The JWKS cache lazy-fetches on first call. Consider an **explicit
  startup warm-up** in main.py if 1st-request latency matters for the
  demo. Currently we accept the one-time cold start.
- AC-7 does NOT implement refresh tokens or session revocation. Out of
  scope per D-FD-07.
