# Requirements — FCPS Vendor Procurement Portal (Demo)

| Field | Value |
|---|---|
| Document | REQUIREMENTS.md |
| Version | 0.2 — scope clarification (Staff Registration explicitly out) |
| Date | 2026-05-14 |
| Author | C&T BA (Claude) |
| Source calls | 2026-04-28, 2026-05-05, 2026-05-09 |
| Status | v0.1 reviewed; v0.2 adds explicit out-of-scope row + decision for Staff Registration (per ADR-005) |

---

## 1. Purpose and Scope

### 1.1 Purpose

Replace the shared Excel spreadsheet that the FCPS Procurement Coordinators use today
with a small, internal, read-only web portal so that FCPS staff (teachers, department
heads) can self-serve answers to the question *"Is this vendor on the approved list,
and who do I contact?"* without emailing the Procurement Coordinator, while sensitive
vendor financial data (`BANK_DETAILS`) remains visible only to procurement
coordinators and every access to it is auditable.

This document is the demo-build scope. Production rollout is phase 2.

### 1.2 In Scope (Demo)

- ID.me identity verification of FCPS staff (sandbox application)
- Role-based, level-based access control (`ADMIN` vs `STAFF`; `PROCUREMENT_LEVEL` 0–3)
- Read-only vendor list and detail views
- Audit logging of every `BANK_DETAILS` access
- Single-tenant deployment to one existing AWS EC2 (t3.medium) running Docker Compose
- Synthetic seed data only — no real FCPS employee or vendor records

### 1.3 Out of Scope (Demo)

| Item | Source |
|---|---|
| Vendor self-service login | 2026-04-28 |
| **Staff self-service registration** — STAFF rows are pre-loaded via `scripts/seed_oracle.py` (synthetic data). The ID.me callback only **looks up** existing STAFF rows; it never creates them. | **ADR-005** (2026-05-14) |
| Approval workflow inside the portal (committee decisions stay offline) | 2026-04-28 |
| Creating or editing vendor records via the UI | 2026-04-28 |
| Any student data (FERPA) | 2026-04-28 |
| Mobile / native app | 2026-04-28 |
| Email notifications | 2026-04-28 (possibly phase 2) |
| Server-side search | 2026-05-09 |
| Pagination | 2026-05-09 |
| HTTPS / TLS termination | 2026-05-05 (production requirement, not demo) |
| Real Oracle connection in development | 2026-05-05 |
| Out-of-hours BANK_DETAILS alerting | 2026-05-09 (phase 2) |
| Audit log history view in detail view | Interview 2026-05-14 |
| AUDIT_LOG retention / purge job | Interview 2026-05-14 (indefinite for demo) |

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

| ROLE | PROCUREMENT_LEVEL | Description | Vendor list view | Vendor detail view | BANK_DETAILS |
|---|---|---|---|---|---|
| (any) | 0 | No procurement clearance | **Access Denied screen** | n/a | Never |
| STAFF | 1 | General staff, basic | APPROVED only; columns: Name, Category, Description | Not available | Never |
| STAFF | 2 | General staff with contact visibility | APPROVED only; columns: Name, Category, Description, Contact Name, Contact Email | Not available | Never |
| ADMIN | 3 | Procurement coordinator | All vendors regardless of status, with status badges | Full record, all columns | Visible + audit-logged on every access |

**Locked by interview 2026-05-14:** LEVEL 1 and LEVEL 2 staff both see APPROVED
vendors only. LEVEL 2's only difference from LEVEL 1 is that the Contact Name and
Contact Email columns are present.

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
5. Backend looks up `STAFF` by `EMPLOYEE_ID = sub` AND `IDME_VERIFIED = 'Y'`.
   - No row → **403** "Your identity has been verified but you are not registered
     in the FCPS procurement system. Contact your procurement coordinator."
   - `IDME_VERIFIED = 'N'` → same 403.
6. Level check:
   - `PROCUREMENT_LEVEL = 0` → **Access Denied screen** (see 3.3).
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
4. Click a row → `/vendors/{id}` detail view, full record returned including
   `BANK_DETAILS`.
5. Backend writes an `AUDIT_LOG` row on every detail fetch that returns
   `BANK_DETAILS`: `(STAFF_ID, VENDOR_ID, ACCESSED_AT)`. The value itself is
   never logged.
6. Detail view shows `BANK_DETAILS` in a visually distinct bordered card with
   muted background; if `NULL`, display **"Not on file"** (not blank).
7. Detail view shows **Approved on: \<date>** when status is APPROVED
   (locked 2026-05-14; implies a small `DATA_MODEL.md` addition — see §11).

### 3.3 Journey — Access Denied (LEVEL 0)

1. ID.me verification succeeds.
2. STAFF row found with `PROCUREMENT_LEVEL = 0`.
3. Backend returns 403 with body
   `{"detail": "Access denied. Your account does not have procurement clearance."}`.
4. React shows a dedicated **Access Denied** screen — clean, friendly, not an
   error page. Includes the contact line:
   *"If you believe this is an error, contact your procurement coordinator."*

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
| FR-01 | The portal SHALL authenticate users exclusively via ID.me OAuth. No username/password fields are present. | 2026-04-28, 2026-05-05 |
| FR-02 | The backend SHALL exchange the ID.me authorisation code for an ID token server-side, never on the client. | 2026-05-05 |
| FR-03 | The backend SHALL map the ID.me `sub` claim to `STAFF.EMPLOYEE_ID` and reject any user not present in `STAFF` with `IDME_VERIFIED = 'Y'`. | 2026-05-05, 2026-05-09 |
| FR-04 | The backend SHALL deny access (403, Access Denied screen) to any user with `PROCUREMENT_LEVEL = 0`. | 2026-05-09 |
| FR-05 | The backend SHALL issue a JWT with claims `{ role, procurement_level, staff_id }` set as an `HttpOnly; SameSite=Lax` cookie. `EMPLOYEE_ID` MUST NOT appear in the JWT. | 2026-05-09 |
| FR-06 | JWT TTL SHALL default to 4 hours and SHALL be configurable via the `JWT_TTL_HOURS` environment variable. | 2026-05-09 |
| FR-07 | The portal SHALL provide a Log out link in the header on every authenticated page. `POST /api/auth/logout` clears the JWT cookie and returns 204. | Interview 2026-05-14 |
| FR-08 | The portal SHALL redirect to `/?reason=session_expired` on any 401 from the API. | 2026-05-09 |
| FR-09 | `GET /api/vendors` SHALL return APPROVED vendors only for any user with `ROLE = STAFF` (regardless of LEVEL 1 or 2). | 2026-05-09, Interview 2026-05-14 |
| FR-10 | `GET /api/vendors` SHALL return all vendors regardless of status for `ROLE = ADMIN`. | 2026-05-09 |
| FR-11 | Response fields SHALL be gated by level: LEVEL 1 receives `{name, category, description}`; LEVEL 2 additionally receives `{contact_name, contact_email}`; LEVEL 3 receives the full record including `bank_details` and `status`. | 2026-05-09, Interview 2026-05-14 |
| FR-12 | `GET /api/vendors/{id}` SHALL be available only to `ROLE = ADMIN` and SHALL return the full vendor record. STAFF users SHALL receive 403. | 2026-05-09 |
| FR-13 | On every successful `GET /api/vendors/{id}` response that includes `BANK_DETAILS`, the backend SHALL write an `AUDIT_LOG` row containing `{STAFF_ID, VENDOR_ID, ACCESSED_AT}`. The `BANK_DETAILS` value MUST NEVER be written to AUDIT_LOG or to application logs. | 2026-05-09 |
| FR-14 | When `BANK_DETAILS` is `NULL`, the detail view SHALL display "Not on file" — never a blank field. | 2026-05-09 |
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
| NFR-07 | Security | `BANK_DETAILS` returned only to `PROCUREMENT_LEVEL = 3`. Audit-logged on every access. Visually distinct in the UI. | 2026-05-09 |
| NFR-08 | Compliance | No real FCPS staff or vendor data in development or demo environments. Synthetic seed only. | 2026-05-05 |
| NFR-09 | Compliance | No student data (FERPA scope confirmed empty). | 2026-04-28 |
| NFR-10 | Audit | AUDIT_LOG retention is indefinite for the demo. No purge job. Phase 2 will revisit with FCPS data governance. | Interview 2026-05-14 |
| NFR-11 | UX — empty state | Every list view defines an empty state. No blank tables. | 2026-05-09 |
| NFR-12 | UX — error messaging | 403 messages are user-friendly. Stack traces and internal codes MUST NOT leak to the browser. | 2026-05-09 |
| NFR-13 | UX — sensitive display | `BANK_DETAILS` rendered in a bordered card with muted background to signal sensitivity. | 2026-05-09 |
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
| `PROCUREMENT_ITEMS.BANK_DETAILS` | Sensitive (synthetic) | LEVEL 3 only; audit-logged; never written to logs |
| `PROCUREMENT_ITEMS.CONTACT_NAME` / `.CONTACT_EMAIL` | Moderate | LEVEL 2+ only |
| `AUDIT_LOG.ACCESSED_AT` | Internal | UTC timestamp, demo-only retention indefinite |
| `EMPLOYEE_ID` | Internal | Oracle lookup only; never in JWT or any API response |

Oracle objects use `SCREAMING_SNAKE_CASE`. Primary keys are
`NUMBER GENERATED ALWAYS AS IDENTITY`.

---

## 7. Integrations and External Systems

| System | Purpose | Owner | Notes |
|---|---|---|---|
| ID.me (sandbox) | Staff identity verification | FCPS IT Lead | Sandbox `client_id`/`client_secret` via 1Password. Scopes: `openid email`. Redirect URI must be registered before first test. |
| Oracle XE 21c | STAFF, PROCUREMENT_ITEMS, AUDIT_LOG | C&T (dev container); FCPS IT Lead (EC2) | `localhost:1521/XEPDB1` in dev. `oracledb` thin mode. No real data ever. |
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
| `/vendors` | STAFF (LEVEL 2) | Vendor table: Name, Category, Description, Contact Name, Contact Email. Search bar. Empty state. |
| `/vendors` | ADMIN (LEVEL 3) | Vendor table: all columns including Status badge and Bank Details. Search bar + Status dropdown. Row click navigates to detail. |
| `/vendors/{id}` | ADMIN only | Full vendor detail card. `BANK_DETAILS` in bordered card. **Approved on** shown when status = APPROVED. "Back to list" link. |
| Access Denied screen | LEVEL 0 | Friendly message + contact instruction. Not an error page. |

---

## 9. Decisions Locked

| # | Decision | Date / source |
|---|---|---|
| D-01 | Read-only portal for the demo. No create/edit/delete. | 2026-04-28 |
| D-02 | ID.me is the only identity provider. | 2026-04-28 |
| D-03 | Two roles, four levels (0–3). | 2026-04-28, 2026-05-09 |
| D-04 | `BANK_DETAILS` LEVEL 3 only; audit-logged. | 2026-05-09 |
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
| D-16 | AUDIT_LOG retention indefinite for the demo. | Interview 2026-05-14 |
| D-17 | Approved date shown on admin detail view. Audit log history NOT shown in detail view for the demo. | Interview 2026-05-14 |
| D-18 | Staff self-service registration is out of scope for the demo. STAFF rows are pre-loaded by `scripts/seed_oracle.py`; the ID.me callback only looks up existing rows. Supersedes the "Staff Registration" domain in `AI_CONTEXT.md`. | ADR-005 (2026-05-14) |

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
| OQ-07 | FCPS data governance policy applicable to vendor financial data | FCPS IT Lead | Before phase 2; not blocking demo |

---

## 11. Implications for `DATA_MODEL.md` (flagged, not edited)

`CLAUDE.md` forbids modifying `docs/DATA_MODEL.md` without explicit instruction.
The following requirements imply schema additions that the data-model author should
confirm before build:

1. **`PROCUREMENT_ITEMS.APPROVED_AT TIMESTAMP NULL`** — required to satisfy FR-15 /
   D-17 (show approval date on admin detail view). Set when status transitions to
   APPROVED. Alternative: a more general `LAST_STATUS_CHANGE_AT` if FCPS wants
   the change date for any status — not required by the current demo scope.
2. **`AUDIT_LOG` table** — confirmed in 2026-05-09 to be added to
   `scripts/seed_oracle.py`. Columns: `LOG_ID` (PK, identity), `STAFF_ID` (FK),
   `VENDOR_ID` (FK), `ACCESSED_AT` (TIMESTAMP). Already aligned with FR-13.

**Action:** Project Lead to authorise the `APPROVED_AT` addition (or substitute)
before FUNCTIONAL_DESIGN.md commits to the field on the detail view.

---

## 12. Glossary

| Term | Meaning |
|---|---|
| ADMIN | `ROLE = 'ADMIN'`, always paired with `PROCUREMENT_LEVEL = 3`. The two procurement coordinators. |
| STAFF | `ROLE = 'STAFF'`, `PROCUREMENT_LEVEL` 0–2. Teachers, department heads, anyone with FCPS staff identity. |
| PROCUREMENT_LEVEL | Integer 0–3 stored on `STAFF`. 0 = no access; 1 = approved-only basic; 2 = approved-only + contact; 3 = full + bank + audit. |
| IDME_VERIFIED | Y/N flag on `STAFF`. Must be `Y` for the user to be allowed in even after ID.me OAuth succeeds. |
| AUDIT_LOG | Oracle table written on every `BANK_DETAILS` access. Stores `STAFF_ID`, `VENDOR_ID`, `ACCESSED_AT` only — never the value. |
| Sandbox (ID.me) | Non-production ID.me application. Used for the demo. Production app is phase 2. |

---

**Next document:** [FUNCTIONAL_DESIGN.md](./FUNCTIONAL_DESIGN.md) — will not be
generated until this REQUIREMENTS.md has been reviewed and signed off.
