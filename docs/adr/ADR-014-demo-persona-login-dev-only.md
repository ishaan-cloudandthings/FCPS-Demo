# ADR-014 — Demo persona login for `dev` environments only

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-18 |
| Author | C&T Project Lead |
| Supersedes | — |
| Superseded by | — |
| Related | ADR-007 (ID.me sandbox), [REQUIREMENTS.md FR-01](../requirements/REQUIREMENTS.md), [D-02](../requirements/REQUIREMENTS.md) |

## Context

[ADR-007](./ADR-007-synthetic-data-and-idme-sandbox.md) constrains the demo
to the ID.me **sandbox** application. That account is shared via 1Password
and must be set up before login works end-to-end. For the duration of the
build (and during stakeholder showings) C&T may need to:

1. Smoke-test the SPA without an ID.me sandbox account configured.
2. Click through all five UI variants (ADMIN/L3, STAFF/L2, STAFF/L1,
   LEVEL_0 denied, NOT_REGISTERED denied) inside one screen-share, without
   incurring the ~10 s ID.me round-trip per persona.
3. Continue UI work on stories AC-11 / AC-12 / AC-15 before the access
   service (AC-13) and Oracle seed (AC-14) are wired up — those are the
   only things that would otherwise let the real `/api/auth/callback`
   complete a session.

`REQUIREMENTS.md` **FR-01** ("The portal SHALL authenticate users
exclusively via ID.me OAuth") and `D-02` ("ID.me is the only identity
provider") together forbid any alternative auth path in production. The
question is whether we may have a **dev-only** path that bypasses ID.me
without contradicting FR-01.

The alternative — multiple ID.me sandbox accounts plus a real Oracle seed
plus waiting for AC-13/14 — is the right answer for the formal walkthrough
but not for daily build work or for the persona-swap moments inside a
stakeholder demo.

## Decision

A new authentication route, `POST /api/auth/dev-login`, is added with the
following constraints:

1. **Scope.** The route exists **only** when the backend's `ENVIRONMENT`
   env var equals `dev`. It is the sole supported alternative to the
   ID.me flow, and only inside dev environments.

2. **Defence in depth — two independent env gates.**
   - **Boot-time:** `main.py` only calls
     `app.include_router(dev_auth.router)` when
     `settings.environment == "dev"`. In any other environment the route
     is not registered at all; FastAPI returns the same 404 it returns
     for any unknown path.
   - **Request-time:** every handler in `dev_auth.py` re-reads
     `settings.environment` on each call and raises `HTTPException(404)`
     if it is not `dev`. The 404 is **indistinguishable from "endpoint
     does not exist"** — no 403, no "forbidden in this environment", no
     enumeration of the dev surface.

3. **Persona table.** Five hardcoded personas:

   | Persona key       | Response | Session claims |
   |---|---|---|
   | `admin_l3`        | 200 + Set-Cookie | `{staff_id: 1, role: "ADMIN", procurement_level: 3}` |
   | `staff_l2`        | 200 + Set-Cookie | `{staff_id: 2, role: "STAFF", procurement_level: 2}` |
   | `staff_l1`        | 200 + Set-Cookie | `{staff_id: 3, role: "STAFF", procurement_level: 1}` |
   | `level_zero`      | 403 + `X-Auth-Reason: LEVEL_ZERO` | — |
   | `not_registered`  | 403 + `X-Auth-Reason: NOT_REGISTERED` | — |

   Bodies match the real `/api/auth/callback` denial responses byte-for-byte
   (`FUNCTIONAL_DESIGN.md` §10).

4. **Same session machinery as `/callback`.** The granted personas mint
   their cookie via the existing `Depends(get_session_issuer)` →
   `issue_session_cookie`. Cookie attributes (HttpOnly, SameSite=Lax,
   Secure-from-env, TTL) and JWT claims are **identical** to those issued
   by `/callback`. There is no second JWT format.

5. **Probe endpoint.** `GET /api/auth/dev-login/available` returns
   `200 {"available": true}` in dev and 404 elsewhere. The SPA renders
   the persona panel only on a 200; on any other response it renders
   nothing (no error banner, no log noise) so a production SPA build is
   visually identical to the ID.me-only product.

6. **No persistent state, no migration, no Oracle.** Personas are static
   constants. They do **not** map to STAFF rows, do **not** require seed
   data, and are unaffected by ADR-009 (`sub` → `EMPLOYEE_ID`).

7. **Logging.** Every call logs
   `dev_auth.login persona=<key> outcome=<granted|denied>` at INFO with the
   literal token `DEV_AUTH_USED` so any prod log aggregation can alert on
   the presence of that string. The session JWT itself is never logged
   (AC8-D13 stands).

8. **No frontend env flag.** The SPA does not read its own environment.
   It probes the backend on every Login mount. There is no path by which
   the SPA can think it is in demo mode while the backend disagrees.

## Rationale

- **Why a dev-only endpoint rather than a CLI?** A persona-swap during a
  live stakeholder demo needs to be one click — not a context switch to
  a terminal. A CLI still has its place (smoke-testing without a browser)
  but is not the primary mechanism.

- **Why not gate by a separate `DEV_FEATURES_ENABLED` flag?** Adding a
  new flag widens the surface for accidental enablement. Reusing the
  existing `ENVIRONMENT` value keeps the gate at the same scope as every
  other dev/prod distinction in the codebase.

- **Why 404 instead of 403 in non-dev?** 403 leaks the existence of the
  route ("there is a thing here you may not access"). 404 is honest:
  outside dev, there is literally no such endpoint.

- **Why reuse `issue_session_cookie` instead of writing a parallel
  minter?** A second JWT format is two attack surfaces. The dev path
  produces the *same* cookie as the real path; if the real cookie
  semantics change, the dev path inherits the change for free.

- **Why does FR-01 still stand?** FR-01 says the *portal* authenticates
  via ID.me. The dev endpoint is not part of the portal as deployed — it
  literally does not exist in production builds. The supersession is
  scoped to environments, not to the requirement itself.

## Consequences

**Positive**

- Demo and dev work no longer blocked on ID.me sandbox + AC-13 + AC-14.
- Persona swap inside a stakeholder demo is a single click.
- No new JWT format, no new cookie semantics, no new test surface for
  the session contract — all of that reuses AC-8.

**Negative**

- A backdoor exists in the codebase, even if compiled out in prod. Any
  future security review must understand and validate the env-gate.
- Three places now need to stay in sync: `dev_auth.py` router, the
  Login.jsx panel, and this ADR. A drift between them is a silent risk.
- Anyone with deploy access can flip `ENVIRONMENT=dev` and re-enable
  the panel. Deploy permissions and `.env` provenance are now
  load-bearing for the auth model.

**Follow-ups**

- **Kill criteria** (mandatory):
  1. Remove `backend/app/api/dev_auth.py`, its schema entries, its
     tests, and the Login.jsx persona panel when **either** of the
     following is true:
     - The demo programme has wrapped and no further stakeholder
       showings are scheduled.
     - Any environment other than the local-dev / demo EC2 box is
       being provisioned (staging, UAT, prod).
  2. Architect signoff is required to delete the env-gate **without**
     removing the code. Default is to remove the code.
- A grep for `DEV_AUTH_USED` in production logs SHALL alert. If that
  string ever appears in a non-dev environment's logs, treat as a
  security incident.

## References

- [REQUIREMENTS.md FR-01, FR-20, D-02](../requirements/REQUIREMENTS.md)
- [ADR-007 — Synthetic data and ID.me sandbox](./ADR-007-synthetic-data-and-idme-sandbox.md)
- [ADR-008 — HTTP for the demo](./ADR-008-http-for-demo.md)
- [decision-log/DEV-AUTH-persona-picker.md](../decision-log/DEV-AUTH-persona-picker.md) — code-level decisions DEV1…DEV13
