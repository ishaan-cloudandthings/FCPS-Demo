# Requirements — FCPS Vendor Procurement Portal (Demo)

| Field | Value |
|---|---|
| Document | REQUIREMENTS.md |
| Version | 0.5 — OQ-08 resolved per ADR-013 |
| Date | 2026-05-16 |
| Author | C&T BA (Claude) |
| Source calls | 2026-04-28, 2026-05-05, 2026-05-09 + 2026-05-16 design review + architect review |
| Status | v0.4 reviewed; v0.5 closes OQ-08 — `contact_email` removed from L2/Admin list responses per ADR-013. Now lives only in `VendorDetail`. |
| Changelog | v0.1 → v0.2 (Staff Registration scope-out, ADR-005) → v0.3 (bank + audit scope-out, ADR-012) → v0.4 (consistency cleanup) → v0.5 (OQ-08 resolved, ADR-013) |

---

## 1. Purpose and Scope

### 1.1 Purpose

Replace the shared Excel spreadsheet that the FCPS Procurement Coordinators use today
with a small, internal, read-only web portal so that FCPS staff (teachers, department
heads) can self-serve answers to the question *"Is this vendor on the approved list,
and who do I contact?"* without emailing the Procurement Coordinator. The portal
uses ID.me to verify FCPS-employee identity and a level-based RBAC model on Oracle
to gate what each user sees.

> **Scope note (2026-05-16):** an earlier framing of this purpose emphasised
> protecting `BANK_DETAILS` and auditing every access to it. Both are now out of
> scope for the demo per
> [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md). The motivating
> spreadsheet-replacement story remains; the financial-data protection story
> moves to phase 2.

This document is the demo-build scope. Production rollout is phase 2.

### 1.2 In Scope (Demo)

- ID.me identity verification of FCPS staff (sandbox application)
- Role-based, level-based access control (`ADMIN` vs `STAFF`; `PROCUREMENT_LEVEL` 0–3)
- Read-only vendor list and detail views
- Single-tenant deployment to one existing AWS EC2 (t3.medium) running Docker Compose
- Synthetic seed data only — no real FCPS employee or vendor records

### 1.3 Out of Scope (Demo)

| Item | Source |
|---|---|
| Vendor self-service login | 2026-04-28 |
| **Staff self-service registration** — STAFF rows are pre-loaded via `scripts/seed_oracle.py` (synthetic data). The ID.me callback only **looks up** existing STAFF rows; it never creates them. | **ADR-005** (2026-05-14) |
| **Bank details (`PROCUREMENT_ITEMS.BANK_DETAILS`)** — not rendered on any screen, not returned in any API response, not RBAC-filtered. The column stays in the Oracle schema as dead-but-present. | **ADR-012** (2026-05-16) |
| **Audit logging (`AUDIT_LOG` table) and the `audit_service` backend** — was created to record bank-detail access; with bank access out of scope, the audit log is too. | **ADR-012** (2026-05-16) |
| Approval workflow inside the portal (committee decisions stay offline) | 2026-04-28 |
| Creating or editing vendor records via the UI | 2026-04-28 |
| Any student data (FERPA) | 2026-04-28 |
| Mobile / native app | 2026-04-28 |
| Email notifications | 2026-04-28 (possibly phase 2) |
| Server-side search | 2026-05-09 |
| Pagination | 2026-05-09 |
| HTTPS / TLS termination | 2026-05-05 (production requirement, not demo) |
| Real Oracle connection in development | 2026-05-05 |
| ~~Out-of-hours BANK_DETAILS alerting~~ | Subsumed by ADR-012 (no bank_details → nothing to alert on) |
| ~~Audit log history view in detail view~~ | Subsumed by ADR-012 (no audit log) |
| ~~AUDIT_LOG retention / purge job~~ | Subsumed by ADR-012 (no audit log) |

---

## 2. Stakeholders and User Roles

### 2.1 Stakeholders

| Stakeholder | Interest |
|---|---|
| FCPS Procurement Coordinator (primary) | Daily user; owns vendor data; primary requestor |
| FCPS Procurement Coordinator (secondary) | Same access; second daily user |
| FCPS IT Lead | Owns EC2, Oracle XE, ID.me developer console; gatekeeper on infra and identity |
| FCPS Deputy Superintendent | Possible demo audience |
| C&T Project Lead | Delivery accountability |
| C&T Tech Lead | Architecture, ID.me integration, Oracle seed |
| C&T Developer | Implementation |

### 2.2 User Roles and Access Levels

Authorisation is the combination of `ROLE` and `PROCUREMENT_LEVEL`, both stored in the
Oracle `STAFF` table and surfaced as JWT claims after ID.me verification.

| ROLE | PROCUREMENT_LEVEL | Description | Vendor list view | Vendor detail view |
|---|---|---|---|---|
| (any) | 0 | No procurement clearance | **Access Denied screen** | n/a |
| STAFF | 1 | General staff, basic | APPROVED only; columns: Name, Category, Description | Not available |
| STAFF | 2 | General staff with contact visibility | APPROVED only; adds Contact Name column (list page renders name only — email shown on detail view, admin-only) | Not available |
| ADMIN | 3 | Procurement coordinator | All vendors regardless of status, with status badges | Full record (excluding `BANK_DETAILS` per ADR-012): name, category, description, contact name + email, unit price, status, `APPROVED_AT`, created / updated dates |

**Locked by interview 2026-05-14 + 2026-05-16 design review + ADR-013
(architect review):** LEVEL 1 and LEVEL 2 staff both see APPROVED vendors
only. LEVEL 2's only difference from LEVEL 1 is that the **Contact Name**
column is visible (on screen and in the API response). `contact_email` is
**not** returned at L2 — it lives only in the admin-only `VendorDetail`
response per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md).

---

## 3. User Journeys

### 3.1 Journey — Staff first-time access (LEVEL ≥ 1)

1. User opens portal URL → React SPA login page loads (< 3 s).
2. User clicks **Verify with ID.me** → redirect to ID.me with `client_id`,
   `redirect_uri`, `state`, `scope=openid email`.
3. User completes ID.me login → ID.me redirects to
   `/verification/callback?code=…&state=…`.
4. FastAPI exchanges `code` for an ID token, validates the token, extracts the
   ID.me subject (`sub`) and email.
5. Backend looks up `STAFF` by `EMPLOYEE_ID = sub`. Access decision per
   FUNCTIONAL_DESIGN.md §6.6 (`access_service`):
   - No row → **403 + `X-Auth-Reason: NOT_REGISTERED`** → SPA routes to
     `/access-denied`.
   - `IDME_VERIFIED != 'Y'` → same 403 + `NOT_REGISTERED` → `/access-denied`.
   - `ACTIVE != 'Y'` → same 403 + `NOT_REGISTERED` → `/access-denied`.
     *(Same response for all three to prevent account-existence enumeration.)*
6. Level check:
   - `PROCUREMENT_LEVEL = 0` → **403 + `X-Auth-Reason: LEVEL_ZERO`** →
     `/access-denied` (see 3.3).
   - `PROCUREMENT_LEVEL ≥ 1` → continue.
7. Backend issues JWT with claims `{ role, procurement_level, staff_id }`,
   sets it as `HttpOnly; SameSite=Lax` cookie (TTL 4 h), redirects to `/vendors`.
8. `/vendors` view loads — APPROVED vendors only, columns gated by level.
9. User filters list client-side by typing into the search box (matches Vendor
   Name only). No match → "No results for '…'.".

### 3.2 Journey — Admin (procurement coordinator) daily use

1. Login flow identical to 3.1, JWT issued with `role=ADMIN`,
   `procurement_level=3`.
2. `/vendors` loads with **all** vendors regardless of status, plus status badges
   (PENDING amber, UNDER_REVIEW blue, APPROVED green, REJECTED red).
3. Filter bar: client-side search by Vendor Name + optional status dropdown.
4. Click a row → `/vendors/{id}` detail view, full record returned
   (excluding `BANK_DETAILS` per ADR-012).
5. Detail view shows **Approved on: \<date>** when status is APPROVED
   (locked 2026-05-14; implies a small `DATA_MODEL.md` addition — see §11).

### 3.3 Journey — Access Denied (LEVEL 0 and NOT_REGISTERED)

The Access Denied screen serves two distinct denial cases. Same page, same
visual treatment, different copy driven by the `X-Auth-Reason` response
header.

**Case A — `LEVEL_ZERO` (user exists, no procurement clearance):**

1. ID.me verification succeeds.
2. STAFF row found with `PROCUREMENT_LEVEL = 0`.
3. Backend returns **403 + `X-Auth-Reason: LEVEL_ZERO`** with body
   `{"detail": "Access denied. Your account does not have procurement clearance."}`.
4. React shows the **Access Denied** screen with the LEVEL_ZERO copy variant:
   *"You don't have access to this portal."*

**Case B — `NOT_REGISTERED` (user not found / not verified / not active):**

1. ID.me verification succeeds.
2. STAFF lookup fails for one of: no row, `IDME_VERIFIED='N'`, or
   `ACTIVE='N'`.
3. Backend returns **403 + `X-Auth-Reason: NOT_REGISTERED`** with body
   `{"detail": "Your identity has been verified but you are not registered in the FCPS procurement system. Contact your procurement coordinator."}`.
4. React shows the **Access Denied** screen with the NOT_REGISTERED copy
   variant: *"We can't sign you in."*

Both variants share: clean, friendly, not an error page; contact line
*"If you believe this is an error, contact your procurement coordinator."*;
**Back to FCPS** CTA that clears the cookie via `POST /api/auth/logout`.

### 3.4 Journey — Logout (added by interview 2026-05-14)

1. Header (visible on every authenticated page) shows a **Log out** link.
2. Clicking it calls `POST /api/auth/logout`, which clears the JWT cookie and
   returns 204.
3. React redirects to `/`.

### 3.5 Journey — Session expiry

1. JWT cookie expires (default 4 h, configurable via `JWT_TTL_HOURS`).
2. Next API call returns 401.
3. React redirects to `/?reason=session_expired` with message
   *"Your session has expired. Please verify again."*

---

## 4. Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-01 | The portal SHALL authenticate users exclusively via ID.me OAuth in any non-`dev` environment. No username/password fields are present. **In `dev` environments only**, a hardcoded persona endpoint (`POST /api/auth/dev-login`) is permitted for demo and smoke-testing — scoped supersession per [ADR-014](../adr/ADR-014-demo-persona-login-dev-only.md); the endpoint is not registered when `ENVIRONMENT != dev` and FR-01 stands unmodified outside dev. | 2026-04-28, 2026-05-05, ADR-014 (2026-05-18) |
| FR-02 | The backend SHALL exchange the ID.me authorisation code for an ID token server-side, never on the client. | 2026-05-05 |
| FR-03 | The backend SHALL map the ID.me `sub` claim to `STAFF.EMPLOYEE_ID`. Access is granted only if a matching `STAFF` row exists **and** `IDME_VERIFIED = 'Y'` **and** `ACTIVE = 'Y'`. Any failure of these checks returns 403 with `X-Auth-Reason: NOT_REGISTERED` (single response for all three to avoid account-existence enumeration). | 2026-05-05, 2026-05-09, FUNCTIONAL_DESIGN.md §6.6 |
| FR-04 | The backend SHALL deny access (403, Access Denied screen) to any user with `PROCUREMENT_LEVEL = 0`. | 2026-05-09 |
| FR-05 | The backend SHALL issue a JWT with claims `{ role, procurement_level, staff_id }` set as an `HttpOnly; SameSite=Lax` cookie. `EMPLOYEE_ID` MUST NOT appear in the JWT. | 2026-05-09 |
| FR-06 | JWT TTL SHALL default to 4 hours and SHALL be configurable via the `JWT_TTL_HOURS` environment variable. | 2026-05-09 |
| FR-07 | The portal SHALL provide a Log out link in the header on every authenticated page. `POST /api/auth/logout` clears the JWT cookie and returns 204. | Interview 2026-05-14 |
| FR-08 | The portal SHALL redirect to `/?reason=session_expired` on any 401 from the API. | 2026-05-09 |
| FR-09 | `GET /api/vendors` SHALL return APPROVED vendors only for any user with `ROLE = STAFF` (regardless of LEVEL 1 or 2). | 2026-05-09, Interview 2026-05-14 |
| FR-10 | `GET /api/vendors` SHALL return all vendors regardless of status for `ROLE = ADMIN`. | 2026-05-09 |
| FR-11 | Response fields SHALL be gated by role/level, separated by endpoint: **`GET /api/vendors` (list)** — LEVEL 1 receives `{item_id, vendor_name, item_name, category}`; LEVEL 2 additionally receives `{contact_name}`; LEVEL 3 (admin) additionally receives `{status, unit_price}`. **`GET /api/vendors/{id}` (detail, admin-only)** — full record per the list-admin shape **plus** `{contact_email, approved_at, created_date, updated_date}`. `contact_email` is returned **only** on the detail endpoint (ADR-013). `BANK_DETAILS` is NOT returned at any level on any endpoint (ADR-012). | 2026-05-09, Interview 2026-05-14, ADR-012, ADR-013 |
| FR-12 | `GET /api/vendors/{id}` SHALL be available only to `ROLE = ADMIN` and SHALL return the full vendor record (excluding `BANK_DETAILS`, per ADR-012). STAFF users SHALL receive 403. | 2026-05-09, ADR-012 |
| ~~FR-13~~ | ~~Audit logging on `BANK_DETAILS` access.~~ **Removed by ADR-012 (2026-05-16).** | — |
| ~~FR-14~~ | ~~"Not on file" placeholder for null `BANK_DETAILS`.~~ **Removed by ADR-012 (2026-05-16).** | — |
| FR-15 | The detail view SHALL display the vendor's approval date when status is APPROVED, formatted as a calendar date. | Interview 2026-05-14 |
| FR-16 | The STAFF vendor list SHALL provide a client-side search filter matching on Vendor Name. The ADMIN vendor list SHALL additionally provide a Status dropdown filter. No server-side search endpoint exists in the demo. | 2026-05-09 |
| FR-17 | The list views SHALL render an empty state message — never a blank table and never an infinite loading spinner. Empty state copy: "No approved vendors found." or "No results for '\<term>'." | 2026-05-09 |
| FR-18 | Vendor status SHALL be displayed using colour-coded badges (PENDING amber, UNDER_REVIEW blue, APPROVED green, REJECTED red) AND a text label, so status is never communicated by colour alone (accessibility). | 2026-05-09, NFR-04 |
| FR-19 | The portal SHALL NOT surface the `STAFF` table in any UI. STAFF records are used only for authorisation decisions. | 2026-05-09 |
| FR-20 | All sensitive secrets (`IDME_CLIENT_SECRET`, `ORACLE_PASSWORD`, `JWT_SECRET_KEY`) SHALL be supplied via environment variables. None SHALL appear in the repository. | 2026-05-05, CLAUDE.md |

---

## 5. Non-Functional Requirements

| ID | Category | Requirement | Source |
|---|---|---|---|
| NFR-01 | Performance | Login page first paint < 3 s on a Chromium-class browser on a standard school workstation. | 2026-05-09 |
| NFR-02 | Performance | `GET /api/vendors` p95 < 500 ms; `GET /api/vendors/{id}` p95 < 300 ms; Access Denied screen < 2 s. Dataset assumption: ~120 vendors, ~40 APPROVED. | Interview 2026-05-14 |
| NFR-03 | Browser support | Latest two stable versions of Chrome, Edge, Firefox, and Safari. | Interview 2026-05-14 |
| NFR-04 | Accessibility | WCAG 2.1 Level AA. Specifically: keyboard navigable; colour contrast ≥ 4.5:1 for normal text; semantic HTML and ARIA labels; logo `alt` text; status badges paired with text labels (see FR-18). | Interview 2026-05-14 |
| NFR-05 | Security | ID.me verification is mandatory before any vendor data is returned. No anonymous endpoints under `/api/vendors`. | 2026-04-28, 2026-05-05 |
| NFR-06 | Security | JWT is stored in an `HttpOnly; SameSite=Lax` cookie. Never in `localStorage` or `sessionStorage`. | 2026-05-09 |
| ~~NFR-07~~ | ~~Security — BANK_DETAILS RBAC + audit + visual distinction.~~ **Removed by ADR-012 (2026-05-16).** | — |
| NFR-08 | Compliance | No real FCPS staff or vendor data in development or demo environments. Synthetic seed only. | 2026-05-05 |
| NFR-09 | Compliance | No student data (FERPA scope confirmed empty). | 2026-04-28 |
| ~~NFR-10~~ | ~~Audit log retention.~~ **Removed by ADR-012 (2026-05-16).** | — |
| NFR-11 | UX — empty state | Every list view defines an empty state. No blank tables. | 2026-05-09 |
| NFR-12 | UX — error messaging | 403 messages are user-friendly. Stack traces and internal codes MUST NOT leak to the browser. | 2026-05-09 |
| ~~NFR-13~~ | ~~UX — sensitive (BANK_DETAILS) display.~~ **Removed by ADR-012 (2026-05-16).** | — |
| NFR-14 | Infrastructure | Demo runs on a single existing AWS EC2 t3.medium with Docker Compose (Nginx, FastAPI, Oracle XE 21c). HTTP acceptable for demo. | 2026-05-05 |
| NFR-15 | Deployability | Deployment via GitHub Actions over SSH to the EC2. C&T does not manage EC2 directly. | 2026-05-05 |
| NFR-16 | Data integrity | Oracle schema managed by `scripts/seed_oracle.py`. No migration tooling. | 2026-05-05 |
| NFR-17 | Identity infra | `oracledb` thin mode — no Oracle Client install required. | 2026-05-05 |
| NFR-18 | Observability | The backend SHALL log auth decisions (verify, deny, level-deny) without logging PII values. | Derived from 2026-05-09 |

---

## 6. Data and Sensitivity

| Data | Sensitivity | Handling |
|---|---|---|
| `IDME_CLIENT_SECRET` | Critical | 1Password only; never in repo |
| `JWT_SECRET_KEY` | High | Env var; never in repo |
| `ORACLE_PASSWORD` | High | Env var; never in repo |
| `EC2_SSH_KEY` | High | 1Password copy from FCPS IT Lead |
| `STAFF` seed data | PII (synthetic) | Fictional names and IDs only |
| ~~`PROCUREMENT_ITEMS.BANK_DETAILS`~~ | — | **Out of scope per ADR-012 (2026-05-16).** Column remains in Oracle schema (DATA_MODEL.md untouched) but is not selected, returned, or rendered. |
| `PROCUREMENT_ITEMS.CONTACT_NAME` | Moderate | LEVEL 2+ only (list + detail) |
| `PROCUREMENT_ITEMS.CONTACT_EMAIL` | Moderate / PII | **Admin-only, detail view only** (ADR-013). Not returned by any list endpoint. |
| `EMPLOYEE_ID` | Internal | Oracle lookup only; never in JWT or any API response |

Oracle objects use `SCREAMING_SNAKE_CASE`. Primary keys are
`NUMBER GENERATED ALWAYS AS IDENTITY`.

---

## 7. Integrations and External Systems

| System | Purpose | Owner | Notes |
|---|---|---|---|
| ID.me (sandbox) | Staff identity verification | FCPS IT Lead | Sandbox `client_id`/`client_secret` via 1Password. Scopes: `openid email`. Redirect URI must be registered before first test. |
| Oracle XE 21c | `STAFF`, `PROCUREMENT_ITEMS` | C&T (dev container); FCPS IT Lead (EC2) | `localhost:1521/XEPDB1` in dev. `oracledb` thin mode. No real data ever. *(`AUDIT_LOG` was previously planned; removed by ADR-012.)* |
| AWS EC2 | Demo host | FCPS IT Lead | t3.medium, Ubuntu 22.04, Docker + Compose preinstalled. SSH key via 1Password. |
| GitHub Actions | CI/CD | C&T | Build, test, deploy over SSH. Subject to FCPS firewall confirmation. |
| Nginx | Static SPA + reverse proxy | C&T | Serves SPA on :80; proxies `/api/*` to FastAPI :8000. |

---

## 8. Screen Inventory (Demo)

| Path | Role | Description |
|---|---|---|
| `/` | Anonymous | Login page. Single CTA: **Verify with ID.me**. Wordmark + explanatory sentence. |
| `/verification/callback` | Anonymous | ID.me OAuth callback. No UI — exchanges code, sets cookie, redirects. |
| `/vendors` | STAFF (LEVEL 1) | Vendor table: Name, Category, Description. Search bar. Empty state. |
| `/vendors` | STAFF (LEVEL 2) | Vendor table: Name, Category, Description, Contact Name. Search bar. Empty state. (`contact_email` is not returned by the list endpoint at L2 per ADR-013 — it lives only in the admin-only detail response.) |
| `/vendors` | ADMIN (LEVEL 3) | Vendor table: Name, Category, Description, Contact Name, Status badge. Search bar + Status dropdown. Row click navigates to detail. (No bank-details column — ADR-012.) |
| `/vendors/{id}` | ADMIN only | Full vendor detail: Item / Service card, Contact card (name + email), Metadata sidebar (vendor ID, status, approval date, created, last update). **Approved on** shown when status = APPROVED. "Back to list" link. (No bank-details card — ADR-012.) |
| `/access-denied` | LEVEL 0 **and** NOT_REGISTERED (anonymous-on-denial) | Friendly denial page with two copy variants driven by `X-Auth-Reason` header (`LEVEL_ZERO` vs `NOT_REGISTERED`). Same visual treatment. Contact line + **Back to FCPS** CTA that logs the user out. Not an error page. |

---

## 9. Decisions Locked

| # | Decision | Date / source |
|---|---|---|
| D-01 | Read-only portal for the demo. No create/edit/delete. | 2026-04-28 |
| D-02 | ID.me is the only identity provider in any non-`dev` environment. In `dev` only, [ADR-014](../adr/ADR-014-demo-persona-login-dev-only.md) permits a hardcoded persona endpoint for the demo. | 2026-04-28; ADR-014 (2026-05-18) |
| D-03 | Two roles, four levels (0–3). | 2026-04-28, 2026-05-09 |
| ~~D-04~~ | ~~`BANK_DETAILS` LEVEL 3 only; audit-logged.~~ **Removed by ADR-012 (2026-05-16).** | — |
| D-05 | JWT in `HttpOnly; SameSite=Lax` cookie (Lax supersedes the earlier Strict in 2026-05-05). | 2026-05-09 |
| D-06 | JWT TTL 4 h, `JWT_TTL_HOURS` env override. | 2026-05-09 |
| D-07 | `EMPLOYEE_ID` NOT in JWT; `staff_id` is. | 2026-05-09 |
| D-08 | Client-side search only; no pagination. | 2026-05-09 |
| D-09 | Synthetic data only; no real FCPS data ever. | 2026-05-05 |
| D-10 | Deploy via GitHub Actions over SSH. HTTP for demo, HTTPS phase 2. | 2026-05-05 |
| D-11 | LEVEL 1 and LEVEL 2 both see APPROVED vendors only. | Interview 2026-05-14 |
| D-12 | Explicit Log out link + `POST /api/auth/logout`. | Interview 2026-05-14 |
| D-13 | Performance targets: `/api/vendors` p95 < 500 ms; detail p95 < 300 ms; login < 3 s. | Interview 2026-05-14 |
| D-14 | Browser support: latest 2 stable of Chrome, Edge, Firefox, Safari. | Interview 2026-05-14 |
| D-15 | Accessibility: WCAG 2.1 AA. | Interview 2026-05-14 |
| ~~D-16~~ | ~~AUDIT_LOG retention indefinite for the demo.~~ **Removed by ADR-012 (2026-05-16).** | — |
| D-17 | Approved date shown on admin detail view. *(The "audit log history NOT shown in detail view" clause is moot under ADR-012 — there is no audit log.)* | Interview 2026-05-14, ADR-012 |
| D-18 | Staff self-service registration is out of scope for the demo. STAFF rows are pre-loaded by `scripts/seed_oracle.py`; the ID.me callback only looks up existing rows. Supersedes the "Staff Registration" domain in `AI_CONTEXT.md`. | ADR-005 (2026-05-14) |
| D-19 | Bank details (`PROCUREMENT_ITEMS.BANK_DETAILS`) and audit logging (`AUDIT_LOG` table + `audit_service`) are out of scope for the demo. The Oracle column remains in DATA_MODEL.md but is not selected, returned, or rendered. Application code does not write any audit rows. | ADR-012 (2026-05-16) |
| D-20 | API responses match UI display. `contact_email` is returned only by the admin-only `GET /api/vendors/{id}` endpoint and lives only in the `VendorDetail` schema. The L2 + Admin list endpoints return `contact_name` only. | ADR-013 (2026-05-16) |

---

## 10. Open Questions (still unresolved)

| # | Question | Owner | Needed by |
|---|---|---|---|
| OQ-01 | EC2 public IP — needed to register ID.me redirect URI | FCPS IT Lead | Before first ID.me test |
| OQ-02 | 1Password vault access for C&T team | FCPS IT Lead | Before ID.me integration work starts |
| OQ-03 | GitHub Actions inbound SSH through FCPS firewall | FCPS IT Lead | Before deploy work |
| OQ-04 | Oracle XE service name on the demo EC2 (assumed `XEPDB1`) | FCPS IT Lead | Before deploy work |
| OQ-05 | FCPS logo asset for the login page | FCPS IT Lead | Before demo; placeholder acceptable |
| OQ-06 | Rough number of staff users (load planning) | Procurement Coordinator | Already satisfied informally by ~120 vendors / 2 admins / TBD staff — not blocking |
| OQ-07 | FCPS data governance policy applicable to vendor financial data | FCPS IT Lead | Before phase 2; not blocking demo (less urgent under ADR-012 since no financial data is handled) |
| ~~OQ-08~~ | ~~Should `GET /api/vendors` drop `contact_email` from the LEVEL 2 response?~~ **Resolved 2026-05-16 by [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md):** yes — dropped from L2 and Admin list responses; `contact_email` now lives only in `VendorDetail`. See D-20. | — | Closed |

---

## 11. Implications for `DATA_MODEL.md` (flagged, not edited)

`CLAUDE.md` forbids modifying `docs/DATA_MODEL.md` without explicit instruction.
The following requirements imply schema additions that the data-model author should
confirm before build:

1. **`PROCUREMENT_ITEMS.APPROVED_AT TIMESTAMP NULL`** — required to satisfy FR-15 /
   D-17 (show approval date on admin detail view). Set when status transitions to
   APPROVED. Authorised by [ADR-006](../adr/ADR-006-audit-log-and-approved-at.md)
   (APPROVED_AT portion still in force).
2. ~~**`AUDIT_LOG` table**~~ — **Removed by [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) (2026-05-16).**
   No audit table is created or seeded.
3. **`PROCUREMENT_ITEMS.BANK_DETAILS` column** stays in `DATA_MODEL.md` as a
   dead-but-present column. The demo code does not select, return, or render
   it. A future ADR may drop the column from the schema; for the demo we
   leave the spec untouched.

---

## 12. Glossary

| Term | Meaning |
|---|---|
| ADMIN | `ROLE = 'ADMIN'`, always paired with `PROCUREMENT_LEVEL = 3`. The two procurement coordinators. |
| STAFF | `ROLE = 'STAFF'`, `PROCUREMENT_LEVEL` 0–2. Teachers, department heads, anyone with FCPS staff identity. |
| PROCUREMENT_LEVEL | Integer 0–3 stored on `STAFF`. 0 = no access; 1 = approved-only basic; 2 = approved-only + contact name; 3 = admin (all statuses + detail view). |
| IDME_VERIFIED | Y/N flag on `STAFF`. Must be `Y` for the user to be allowed in even after ID.me OAuth succeeds. |
| Sandbox (ID.me) | Non-production ID.me application. Used for the demo. Production app is phase 2. |

---

**Next document:** [FUNCTIONAL_DESIGN.md](./FUNCTIONAL_DESIGN.md) — will not be
generated until this REQUIREMENTS.md has been reviewed and signed off.
