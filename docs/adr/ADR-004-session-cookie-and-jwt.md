# ADR-004 — Session cookie and JWT reconciliation

| Field | Value |
|---|---|
| Status | Accepted — supersedes ADR-003 (in `ARCHITECTURE.md` §11) |
| Date | 2026-05-14 |
| Author | C&T BA (Claude), on behalf of C&T Tech Lead |
| Supersedes | ADR-003 on TTL, SameSite, claim name, and env-var name |
| Superseded by | — |

## Context

`ARCHITECTURE.md` §8.1 and ADR-003 (in §11) describe the session as:

- JWT TTL **60 minutes**
- Cookie **`httpOnly, Secure, SameSite=Strict`**
- Env var **`ACCESS_TOKEN_EXPIRE_MINS`**
- JWT claim includes **`employee_id`**

The 2026-05-09 user-journey walkthrough call superseded several of these
decisions during the user-journey design and access-control review:

- A 60-minute TTL would force coordinators to re-verify mid-morning. **4 hours** matches a coordinator's typical sitting at the portal.
- `SameSite=Strict` would prevent the cookie from being attached on the post-ID.me cross-site redirect that initiates the session, breaking the OAuth flow on first sign-in. **`SameSite=Lax`** is the practical choice for an OAuth-driven login.
- The TTL should be tunable for demo flexibility. **`JWT_TTL_HOURS`** replaces `ACCESS_TOKEN_EXPIRE_MINS`.
- `EMPLOYEE_ID` is classified as PII in `DATA_MODEL.md` §7. It should not appear in a long-lived bearer token. The internal `STAFF_ID` (Oracle PK) is sufficient for backend lookups.

Demo runs on HTTP (see ADR-008), so the `Secure` flag must be **env-driven**
to permit cookies over plain HTTP for the demo while keeping the production
upgrade a config flip.

## Decision

The JWT session implementation will use:

| Attribute | Value |
|---|---|
| Algorithm | HS256 |
| TTL | 4 hours, configurable via `JWT_TTL_HOURS` (env) |
| Claims | `sub=staff_id, role, procurement_level, iat, exp, iss=fcps-portal, aud=fcps-portal-web` |
| Cookie name | `session` |
| Cookie attributes | `HttpOnly; SameSite=Lax; Path=/` |
| `Secure` flag | env-driven (`JWT_COOKIE_SECURE`, default `false`); flips to `true` when HTTPS is enabled (see ADR-008) |
| Clock skew tolerance | 30 seconds |
| Refresh tokens | Out of scope. On expiry the user re-verifies via ID.me. |

## Consequences

**Positive**

- A single authoritative source for cookie + JWT decisions, referenced by
  `FUNCTIONAL_DESIGN.md` §6.3–6.4 and the OpenAPI spec.
- Predictable behaviour across Chrome / Edge / Firefox / Safari (the supported
  matrix per `REQUIREMENTS.md` NFR-03).
- No PII (`EMPLOYEE_ID`, name, email) embedded in any bearer credential.

**Negative**

- `ARCHITECTURE.md` §4.1, §8.1, §10 (env-var list), and §11 ADR-003 are now
  stale and must be updated.
- `Secure=false` for the demo means the cookie is observable on the wire if
  HTTP traffic is intercepted. Mitigated by: short TTL (4 h), synthetic data
  only (ADR-007), HTTP for demo only (ADR-008).

**Follow-ups required (none break code, all break docs)**

- Update `ARCHITECTURE.md` §4.1 — note SameSite + cookie name + TTL.
- Update `ARCHITECTURE.md` §8.1 — supersede the JWT cookie paragraph.
- Update `ARCHITECTURE.md` §10 — rename `ACCESS_TOKEN_EXPIRE_MINS` → `JWT_TTL_HOURS`; add `JWT_COOKIE_SECURE`, `JWT_ISSUER`, `JWT_AUDIENCE`.
- Update `ARCHITECTURE.md` §11 ADR-003 — mark **Superseded by ADR-004**.
- Update `.env.example` to reflect the new env-var names.

## References

- `docs/discovery/CALL_NOTES_2026-05-09.md` — "Decisions Made on This Call"
- `docs/requirements/REQUIREMENTS.md` — FR-05, FR-06, NFR-06, D-05, D-06, D-07
- `docs/requirements/FUNCTIONAL_DESIGN.md` — §6.3, §6.4 (decisions D-FD-01…D-FD-07)
- `docs/requirements/api-spec.yaml` — `cookieAuth` security scheme
- `ADR-008` — HTTP for the demo (the `Secure=false` rationale)
