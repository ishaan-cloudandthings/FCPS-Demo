# AC-8 — JWT issuance + verification + auth dependencies: ratified Red Zone decisions

| Field | Value |
|---|---|
| Jira story | [AC-8](https://cloudandthings.atlassian.net/browse/AC-8) — E1-S3 JWT issuance + verification + FastAPI auth dependencies |
| Epic | [AC-2](https://cloudandthings.atlassian.net/browse/AC-2) — Identity Verification |
| Zone | 🔴 Red (`backend/app/auth/`) |
| Ratified on | 2026-05-18 |
| Ratified by | C&T Project Lead |
| Status | Ratified — implementation may proceed |

## What's in this file

Per `AI_POLICY.md` § 🔴 Red rules, every decision is on record before
code is written. This file captures:

1. The pre-existing FD §6.4 decisions D-FD-01 … D-FD-07.
2. The story-specific decisions AC8-D1 … AC8-D14.
3. The minor extension to AC-7's `get_session_issuer` (settings
   injection) — within the contract AC7-D8 left open.

## Decisions ratified from FUNCTIONAL_DESIGN.md §6.4

| ID | Decision |
|---|---|
| **D-FD-01** | Algorithm: **HS256** (matches `python-jose` default + ARCHITECTURE.md `JWT_ALGORITHM`). Asymmetric algorithms rejected for a single-host demo. |
| **D-FD-02** | Claims: `{ sub=staff_id, role, procurement_level, iat, exp, iss="fcps-portal", aud="fcps-portal-web" }`. `EMPLOYEE_ID` is NOT included (REQUIREMENTS.md D-07). |
| **D-FD-03** | Expiry: `exp = iat + JWT_TTL_HOURS × 3600`. Default 4. Reads env at startup; no hot-reload. |
| **D-FD-04** | Cookie attributes: `HttpOnly`, `SameSite=Lax`, `Path=/`. `Secure` flag env-driven (`JWT_COOKIE_SECURE`, default `false`) — flips to `true` when HTTPS lands (ADR-008). |
| **D-FD-05** | Secret rotation out of scope. `JWT_SECRET_KEY` env var only. Any change requires redeploy and invalidates all sessions (acceptable). |
| **D-FD-06** | Clock-skew tolerance: 30 s on `exp` and `iat`. |
| **D-FD-07** | No refresh tokens. On expiry the user re-verifies via ID.me — matches a 4 h TTL on a demo. |

## Story-specific decisions

| # | Decision | Ratified value |
|---|---|---|
| AC8-D1 | JWT library | `python-jose` (already a dep from AC-7's ID-token validation). Reuse the same library + idioms. |
| AC8-D2 | `issue_session_cookie` signature extension | The AC-7 stub took `(response, *, staff_id, role, procurement_level)`. AC-8 extends with `secret_key`, `ttl_hours`, `secure` — closure built by `get_session_issuer` injects them from settings. AC-7's endpoint code (and tests that mock `get_session_issuer`) are unchanged — within AC7-D8's "signature contractually fixed" because `get_session_issuer` is the contract, and the underlying function may extend. |
| AC8-D3 | `SessionClaims` dataclass | Frozen dataclass: `staff_id: int`, `role: Literal["ADMIN","STAFF"]`, `procurement_level: int`. Lives in `app/auth/jwt_session.py`. |
| AC8-D4 | Cookie name | `"session"` — matches the value AC-7's `mock_session_issuer` writes for test compatibility. |
| AC8-D5 | JWT `sub` format | `str(staff_id)` — JWT convention is for `sub` to be a string. The verifier coerces back to `int`. |
| AC8-D6 | `iss` and `aud` | `iss="fcps-portal"`, `aud="fcps-portal-web"`. Hard-coded constants — internal namespacing, not deployment-variable. |
| AC8-D7 | Dependencies module | `app/auth/dependencies.py` per FUNCTIONAL_DESIGN.md §6.3. Three Depends factories: `require_authenticated`, `require_role`, `require_level`. |
| AC8-D8 | `require_authenticated` failure mode | **Same 401 + body for ANY failure** (missing cookie / malformed / expired / bad signature / bad alg). Body `{"detail": "Session invalid or expired."}`. No enumeration about which check failed. Server-side log distinguishes via `err=...`. |
| AC8-D9 | `require_role` / `require_level` failure | 403 + `X-Auth-Reason: ROLE_FORBIDDEN` + body `{"detail": "You do not have permission to view this resource."}`. Matches FUNCTIONAL_DESIGN.md §10 error model. |
| AC8-D10 | Algorithm-confusion defence | `jose.jwt.decode(..., algorithms=["HS256"])` — explicit allowlist. **Never** trust the JWT header's `alg` field. Same pattern as AC7-D4 for the ID token. |
| AC8-D11 | `JWT_SECRET_KEY` constraints | **`min_length=32`** characters at the Settings level — Pydantic enforces at boot. HS256 security floor is 256 bits / 32 bytes. |
| AC8-D12 | `EMPLOYEE_ID` exclusion | Verified by **claims allowlist test**: a freshly issued token decodes to exactly `{sub, role, procurement_level, iss, aud, iat, exp}` — nothing else. Any future drift fails the test. |
| AC8-D13 | Logging | `jwt.issued staff_id=… role=… level=…` on success. `jwt.verify_failed err=<error_class>` on failure. **Never log the token itself.** |
| AC8-D14 | Tests | ~15 cases: issue-cookie attributes; verify happy path; expired / wrong-sig / wrong-alg / wrong-iss / wrong-aud / missing claims / malformed; the three Depends factories (auth, role, level) with success + failure branches; claims allowlist (no `employee_id`). |

## Files this story creates / modifies

| Path | Zone | Change |
|---|---|---|
| `backend/app/auth/jwt_session.py` | 🔴 Red | **Replace stub** with real `issue_session_cookie` + add `verify_session_jwt`, `SessionClaims`, `SessionInvalid` |
| `backend/app/auth/dependencies.py` | 🔴 Red | **New** — `require_authenticated`, `require_role`, `require_level` |
| `backend/app/api/auth.py` | 🔴 Red | Update `get_session_issuer` to take `settings = Depends(get_settings)` and wrap |
| `backend/app/core/config.py` | 🟢 Green | Add `jwt_secret_key`, `jwt_ttl_hours`, `jwt_cookie_secure` |
| `backend/.env.example` | — | Uncomment + populate the JWT_* block |
| `backend/tests/conftest.py` | — | Add JWT env vars to `_env` |
| `backend/tests/test_jwt_session.py` | — | New (~9 tests) |
| `backend/tests/test_auth_dependencies.py` | — | New (~7 tests) |

## Open follow-ups

- **JWT key rotation** — out of scope per D-FD-05; will be revisited if/when
  the demo moves toward production.
- **Idle timeout** — explicitly rejected at FD-OQ-FD-07; user-explicit logout
  via AC-9 is the only deliberate session-end mechanism. The 4 h TTL handles
  the rest.
