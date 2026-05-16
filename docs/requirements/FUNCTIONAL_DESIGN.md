# Functional Design — FCPS Vendor Procurement Portal (Demo)

| Field | Value |
|---|---|
| Document | FUNCTIONAL_DESIGN.md |
| Version | 0.4 — `contact_email` removed from list responses per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md). Lives only in `VendorDetail`. |
| Date | 2026-05-16 |
| Author | C&T BA (Claude) |
| Source of truth | [REQUIREMENTS.md](./REQUIREMENTS.md) v0.5 |
| Reference docs | [../ARCHITECTURE.md](../ARCHITECTURE.md), [../DATA_MODEL.md](../DATA_MODEL.md), [../../AI_ZONES.md](../../AI_ZONES.md), [../AI_POLICY.md](../AI_POLICY.md), [../adr/](../adr/) |
| Status | v0.3 reviewed; v0.4 applies the ADR-013 cascade (OQ-08 resolved) |

---

## 1. Purpose

Translate the locked requirements in `REQUIREMENTS.md` into a concrete, build-ready
functional design: the routes, components, services, data flows, error model, and
test strategy. This document does not introduce new requirements. If something below
is not in `REQUIREMENTS.md`, it is a **design decision** — flagged in §16.

`api-spec.yaml` is the next artefact and will be derived directly from §6 (Backend
Design) and §10 (Error Model) of this document.

---

## 2. Spec Conflicts — Resolution Status

`REQUIREMENTS.md` reflects the latest call decisions (2026-05-09 + interview 2026-05-14).
The project's locked reference docs were written earlier and contain decisions that have
since been overridden. **Per `CLAUDE.md`, this document does not edit those locked
docs.** As of 2026-05-14 every conflict below has a corresponding ADR in
[`docs/adr/`](../adr/) — the *decisions* are resolved. The *doc-level cleanups* to
ARCHITECTURE.md / AI_CONTEXT.md / DATA_MODEL.md are still outstanding (see §16
follow-ups) but those are mechanical and do not block development.

| # | Locked doc | Statement in locked doc | Latest decision (REQUIREMENTS.md) | Resolution status |
|---|---|---|---|---|
| C-01 | `ARCHITECTURE.md` §8.1 | JWT TTL = 60 min, `SameSite=Strict` | TTL = 4 h (`JWT_TTL_HOURS` env), `SameSite=Lax` | ✅ Resolved — [ADR-004](../adr/ADR-004-session-cookie-and-jwt.md) |
| C-02 | `ARCHITECTURE.md` §10 env vars | `ACCESS_TOKEN_EXPIRE_MINS` | `JWT_TTL_HOURS` | ✅ Resolved — [ADR-004](../adr/ADR-004-session-cookie-and-jwt.md) |
| C-03 | `AI_CONTEXT.md` Key Business Domains 1; `ARCHITECTURE.md` §6.2 page list | "Staff Registration — self-service form", `Registration.jsx` | No registration; staff pre-loaded in Oracle | ✅ Resolved — [ADR-005](../adr/ADR-005-no-staff-registration-in-demo.md); see also REQUIREMENTS.md §1.3 out-of-scope row and §9 D-18 |
| C-04 | `ARCHITECTURE.md` §6.1 module map | `api/auth.py`, callback at `/api/auth/callback` | Discovery notes use `/verification/callback` | ✅ Resolved within this FD — backend route `/api/auth/callback` (FastAPI), SPA route `/verification/callback`. See §5 URL map + §6.1. |
| C-05 | `DATA_MODEL.md` | No `AUDIT_LOG` table | ~~`AUDIT_LOG` required (FR-13)~~ | 🚫 **Scope-removed** — [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) (2026-05-16). `AUDIT_LOG` is not built. |
| C-06 | `DATA_MODEL.md` | No `APPROVED_AT` column on `PROCUREMENT_ITEMS` | "Approved on" displayed in admin detail view (FR-15) | ✅ Decision resolved — [ADR-006](../adr/ADR-006-audit-log-and-approved-at.md). DATA_MODEL.md doc-update still pending. |
| C-07 | `DATA_MODEL.md` PROCUREMENT_ITEMS | `ITEM_NAME` (singular item) | Calls describe "Vendors" as the unit (a vendor offers items/services) | ✅ Resolved as interpretation: each row is one vendor offering. `VENDOR_NAME` is the row's display key. No schema change required for the demo. |
| C-08 | `DATA_MODEL.md` STAFF | `ACTIVE` (Y/N) column exists | Not mentioned in discovery | ✅ Resolved as design decision — `ACTIVE='N'` denies access (same UX as `IDME_VERIFIED='N'`). See §6.3 and §6.6. |

**Build kickoff posture:** Every architectural decision required to start work is now
recorded in an ADR. Outstanding work is **doc updates** to the locked reference docs
(tracked as ADR follow-ups) and **operational unblocks** (EC2 IP, 1Password access,
firewall — see REQUIREMENTS.md §10). Neither blocks code generation on
🟢 Green or 🟡 Yellow stories.

---

## 3. Conformance to AI Zones

Per `AI_ZONES.md`:

| Component | Zone | Implication for this design |
|---|---|---|
| `backend/app/auth/` (JWT internals) | 🔴 Red | Design choices in §6.4 surfaced as numbered decisions D-FD-01 … D-FD-07. Implementation must wait for human approval of each. |
| `backend/app/api/auth.py` (ID.me callback, login, logout) | 🔴 Red | Same — decisions D-FD-08 … D-FD-12 in §6.1. |
| `backend/app/services/` (`oracle_service`, `access_service`, `rbac_service`) | 🟡 Yellow | Draft provided in §6.5–6.7; developer rewrites or meaningfully edits. *`audit_service` was removed by ADR-012.* |
| `backend/app/api/procurement.py` (vendor list + detail) | 🟡 Yellow | Draft in §6.2. |
| `frontend/src/pages/` (`StaffView`, `AdminView`, `VendorDetail`, `VerificationCallback`, `AccessDenied`, `Login`) | 🟡 Yellow | Draft in §7. |
| `frontend/src/components/` (`StatusBadge`, `VendorTable`, `SearchBar`, `EmptyState`, `Header`) | 🟢 Green | AI may fully implement; developer reviews. *`BankDetailsCard` was removed by ADR-012.* |
| `backend/scripts/seed_oracle.py` (adds `APPROVED_AT` column per ADR-006) | 🟢 Green | AI writes. |
| `backend/app/schemas/` (Pydantic) | 🟢 Green | AI writes (derived from §6 + api-spec.yaml). |

**PII handling** (per `AI_POLICY.md`) applies in every zone. Wherever `FULL_NAME`,
`EMAIL`, `EMPLOYEE_ID`, `CONTACT_NAME`, or `CONTACT_EMAIL` is touched, the
implementer must confirm logging exclusions and response scoping before
generating code (see §9 and §11). *`BANK_DETAILS` is out of scope per
[ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) and is not selected,
returned, or rendered anywhere.*

---

## 4. System Context Recap

Single EC2 t3.medium running Docker Compose (Nginx, FastAPI Uvicorn, Oracle XE 21c).
React SPA served by Nginx on `:80`; FastAPI on `:8000`; Oracle internal-only on `:1521`.
Identity proved by ID.me (sandbox). Authorisation derived from Oracle `STAFF.ROLE` +
`STAFF.PROCUREMENT_LEVEL`. JWT in `HttpOnly; SameSite=Lax` cookie carries session.

```
Browser ──HTTPS (HTTP for demo)──► Nginx :80
                                    ├─ static SPA
                                    └─ /api/* ──► FastAPI :8000 ──► Oracle XE :1521
                                                                 └─► ID.me (token exchange)
```

---

## 5. Frontend ↔ Backend URL Map

Resolving conflict C-04 explicitly:

| URL | Served by | Purpose |
|---|---|---|
| `/` | Nginx (SPA) | Login page |
| `/verification/callback?code=…&state=…` | Nginx (SPA) | OAuth return page — the React component extracts `code` + `state` and POSTs them to the backend. Public URL because ID.me must redirect a browser. |
| `/vendors` | Nginx (SPA) | Staff/Admin vendor list (route guarded) |
| `/vendors/{id}` | Nginx (SPA) | Admin vendor detail (route guarded) |
| `/access-denied` | Nginx (SPA) | LEVEL 0 landing |
| `/api/auth/login` | FastAPI | Returns ID.me authorisation URL with server-generated `state` |
| `/api/auth/callback` | FastAPI | Code+state exchange; sets JWT cookie; returns `{ role, procurement_level }` |
| `/api/auth/logout` | FastAPI | Clears JWT cookie; 204 |
| `/api/auth/me` | FastAPI | Returns current session claims; used by SPA on page load |
| `/api/vendors` | FastAPI | RBAC-filtered list |
| `/api/vendors/{id}` | FastAPI | Admin-only detail (returns full record minus `BANK_DETAILS`). No audit log per ADR-012. |

**The ID.me-registered redirect URI** is the frontend page
`http(s)://<EC2_PUBLIC_IP>/verification/callback`. The backend's `/api/auth/callback`
is an internal endpoint the SPA POSTs to — ID.me never sees it.

This split keeps the SPA route stable (handles UI states like "verifying…", failure
copy, retry button) and keeps the code-exchange logic server-side as required by
`AI_CONTEXT.md` and ARCHITECTURE.md §8.1.

---

## 6. Backend Design

### 6.1 Auth router — `backend/app/api/auth.py` 🔴 Red Zone

Endpoints:

```
POST /api/auth/login            → 200 { authorize_url }
POST /api/auth/callback         → 200 { role, procurement_level }   sets cookie
POST /api/auth/logout           → 204                                  clears cookie
GET  /api/auth/me               → 200 { role, procurement_level, staff_id }
                                  401 if no/invalid cookie
```

Behaviour summary (decisions surfaced for Red Zone approval):

- **D-FD-08** `POST /api/auth/login` generates a 32-byte URL-safe `state`, stores it
  in a short-lived server-side cache (in-process dict acceptable for the demo, TTL
  10 min), and returns the full ID.me `authorize` URL. SPA performs the redirect.
  *Alternative considered:* PKCE without server state. Rejected for the demo because
  PKCE storage in the SPA conflicts with HttpOnly-cookie-only posture.
- **D-FD-09** `POST /api/auth/callback` accepts `{code, state}` JSON. Validates that
  `state` exists in the cache and has not expired; deletes it on use (one-shot).
  Mismatch or expiry → 400 with body `{"detail": "Authentication request expired. Please verify again."}`.
- **D-FD-10** Token exchange uses `requests.post(IDME_BASE_URL + "/oauth/token", …)`
  with form-encoded `client_id`, `client_secret`, `code`, `grant_type=authorization_code`,
  `redirect_uri`. Timeout 5 s. Network error → 502 `{"detail": "Identity provider unreachable."}`.
- **D-FD-11** ID token validation: verify `iss`, `aud == client_id`, `exp`, `iat`.
  Signature verification uses ID.me JWKS (cached in-process for 60 min). If validation
  fails → 401 `{"detail": "Identity verification failed."}`.
- **D-FD-12** After validation, the handler calls `access_service.decide_access(sub)`
  (see §6.6) and either sets the JWT cookie + returns `{role, procurement_level}` or
  returns 403 with the appropriate user-facing copy from FR-04.

Logout simply calls `response.delete_cookie("session", ...)` and returns 204.

`GET /api/auth/me` is consumed by the SPA on initial mount to know whether the user
is already logged in and what role to render. It is also the trigger for the session-
expiry redirect (FR-08) — a 401 from `/me` causes the SPA to redirect to
`/?reason=session_expired`.

### 6.2 Procurement router — `backend/app/api/procurement.py` 🟡 Yellow

```
GET  /api/vendors          → 200 [VendorListItem]
GET  /api/vendors/{id}     → 200 VendorDetail     (ADMIN only)
                             403 if role != ADMIN
                             404 if vendor not found
```

Both endpoints are protected by `Depends(require_authenticated)` (see §6.4). The
detail endpoint additionally depends on `Depends(require_role("ADMIN"))`.

The list endpoint always returns 200 — an empty list is a valid response and the
frontend renders the empty state. The list shape is **level-aware**: see §6.7.

The detail endpoint is a simple admin-only read. *Earlier drafts wrote an
`AUDIT_LOG` row before serialising — that posture was removed by ADR-012
along with the `audit_service` module and the entire audit-log table.*

### 6.3 Authentication / authorisation dependencies — `backend/app/auth/dependencies.py` 🔴 Red

```python
def require_authenticated(request: Request) -> SessionClaims: ...
def require_role(role: Literal["ADMIN", "STAFF"]): ...
def require_level(min_level: int): ...
```

`require_authenticated` reads the cookie, verifies the JWT signature and `exp`,
returns a typed `SessionClaims(staff_id, role, procurement_level)`. On any failure
it raises `HTTPException(401, "Session invalid or expired.")`.

`require_role` and `require_level` are factories that return dependencies which raise
403 if the claim does not match. The frontend never sees a distinction between
"missing cookie" and "expired cookie" — both surface as 401 with the same user-facing
message (`FR-08`).

### 6.4 JWT internals — `backend/app/auth/jwt.py` 🔴 Red Zone

Decisions surfaced for Red Zone approval:

- **D-FD-01** Algorithm: HS256 (matches `python-jose` default and `ARCHITECTURE.md`
  env var `JWT_ALGORITHM`). Asymmetric algorithms rejected for a single-host demo.
- **D-FD-02** Claims: `{ sub: staff_id, role, procurement_level, iat, exp, iss: "fcps-portal", aud: "fcps-portal-web" }`. `EMPLOYEE_ID` is **not** included (REQUIREMENTS D-07).
- **D-FD-03** Expiry: `exp = iat + JWT_TTL_HOURS * 3600`. Default 4. Reads env at
  startup; does not hot-reload.
- **D-FD-04** Cookie attributes: `HttpOnly`, `SameSite=Lax`, `Path=/`. `Secure=False`
  for the HTTP demo; **must flip to `True` when HTTPS is enabled** — see §16 OQ-FD-01.
- **D-FD-05** Secret rotation: out of scope for demo. `JWT_SECRET_KEY` env var only.
  Any change requires a redeploy and forces all sessions to invalidate (acceptable).
- **D-FD-06** Clock skew tolerance: 30 s when validating `exp` and `iat`.
- **D-FD-07** No refresh tokens. On expiry the user re-verifies via ID.me. This is
  the simplest correct posture for a 4-hour TTL on a demo.

### 6.5 Oracle service — `backend/app/services/oracle_service.py` 🟡 Yellow

```python
class OracleService:
    def get_staff_by_employee_id(self, employee_id: str) -> StaffRecord | None: ...
    def list_vendors(self, only_approved: bool, include_contact: bool, include_status: bool) -> list[VendorRow]: ...
    def get_vendor_by_id(self, item_id: int) -> VendorRow | None: ...
```

> *`insert_audit_log` and the `include_bank` flag were removed by
> [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md). The
> `BANK_DETAILS` column is not selected by any query.*
>
> *`list_vendors` does NOT select `CONTACT_EMAIL` — per
> [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md), email is
> only returned by `get_vendor_by_id` (admin-only detail endpoint). The
> `include_contact` flag selects `CONTACT_NAME` only.*

Parameterised queries only — `cursor.execute(sql, {"employee_id": employee_id})`.
Never f-strings into SQL. Returns plain dataclasses (`StaffRecord`, `VendorRow`); the
router/service layer maps to Pydantic response schemas (see §6.9).

`get_staff_by_employee_id` query:

```sql
SELECT STAFF_ID, EMPLOYEE_ID, ROLE, PROCUREMENT_LEVEL, IDME_VERIFIED, ACTIVE
FROM STAFF
WHERE EMPLOYEE_ID = :employee_id
```

The `IDME_VERIFIED = 'Y' AND ACTIVE = 'Y'` gate is applied in `access_service`, not
in the SQL, so the access decision can produce a precise log line (e.g. "denied:
INACTIVE" vs "denied: NOT_VERIFIED") without an extra query.

### 6.6 Access service — `backend/app/services/access_service.py` 🟡 Yellow

```python
@dataclass
class AccessDecision:
    granted: bool
    reason: Literal["GRANTED", "NOT_FOUND", "NOT_VERIFIED", "INACTIVE", "LEVEL_ZERO"]
    staff: StaffRecord | None

def decide_access(employee_id: str) -> AccessDecision: ...
```

Decision tree, evaluated in order:

1. `staff` is `None` → `NOT_FOUND`
2. `staff.IDME_VERIFIED != 'Y'` → `NOT_VERIFIED`
3. `staff.ACTIVE != 'Y'` → `INACTIVE`
4. `staff.PROCUREMENT_LEVEL == 0` → `LEVEL_ZERO`
5. otherwise → `GRANTED`

The router maps `NOT_FOUND` / `NOT_VERIFIED` / `INACTIVE` → 403 with the
"not registered" copy (FR-03 doesn't distinguish — keep it that way to avoid leaking
account-existence). `LEVEL_ZERO` → 403 with the Access Denied copy (FR-04).

### 6.7 RBAC filter — `backend/app/services/rbac_service.py` 🟡 Yellow

Single source of truth for "what columns does a role/level see":

```python
def list_query_params(role: str, level: int) -> ListQueryParams:
    if role == "ADMIN":
        return ListQueryParams(only_approved=False, include_contact=True, include_status=True)
    if role == "STAFF" and level == 2:
        return ListQueryParams(only_approved=True, include_contact=True, include_status=False)
    if role == "STAFF" and level == 1:
        return ListQueryParams(only_approved=True, include_contact=False, include_status=False)
    raise PermissionError  # LEVEL 0 never reaches here — caught in access_service
```

`oracle_service.list_vendors` honours these flags by selecting columns conditionally
and including `WHERE STATUS = 'APPROVED'` when `only_approved=True`.

> *The `include_bank` flag was removed by
> [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md). `BANK_DETAILS`
> is never queried, regardless of role.*
>
> *Per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md), the
> `include_contact` flag drives selection of `CONTACT_NAME` only. There
> is no `include_contact_email` flag; `CONTACT_EMAIL` is selected only by
> the detail endpoint (`get_vendor_by_id`).*

### 6.8 ~~Audit service~~ — **REMOVED by ADR-012**

This section previously defined `backend/app/services/audit_service.py` —
synchronous write to `AUDIT_LOG` on every `BANK_DETAILS` access, fail-closed
posture, etc. The entire service is removed by
[ADR-012](../adr/ADR-012-bank-details-out-of-scope.md): with bank-details
out of scope, there is nothing left to audit. No `audit_service` module is
built; no `AUDIT_LOG` table is created.

### 6.9 Pydantic schemas — `backend/app/schemas/` 🟢 Green

```python
# auth.py
class CallbackRequest(BaseModel):
    code: str
    state: str

class SessionResponse(BaseModel):
    role: Literal["ADMIN", "STAFF"]
    procurement_level: int = Field(ge=1, le=3)

class AuthorizeUrlResponse(BaseModel):
    authorize_url: HttpUrl

# procurement.py
class VendorListItemL1(BaseModel):
    item_id: int
    vendor_name: str
    item_name: str
    category: str

class VendorListItemL2(VendorListItemL1):
    contact_name: str | None
    # contact_email moved to VendorDetail only by ADR-013

class VendorListItemAdmin(VendorListItemL2):
    status: Literal["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED"]
    unit_price: Decimal | None
    # bank_details removed by ADR-012; contact_email moved to detail by ADR-013

class VendorDetail(VendorListItemAdmin):
    contact_email: EmailStr | None  # detail-only per ADR-013
    approved_at: date | None        # populated when status == APPROVED (requires schema add C-06)
    created_date: datetime
    updated_date: datetime
```

`GET /api/vendors` declares its response as
`list[VendorListItemL1 | VendorListItemL2 | VendorListItemAdmin]` — the actual variant
returned depends on the caller's level. OpenAPI will model this as a `oneOf`.

Empty list (no vendors / no APPROVED vendors for staff) is `[]`, status 200. The
frontend interprets emptiness; the backend never returns 204 for "no rows".

---

## 7. Frontend Design

### 7.1 Routes — React Router v6

```
/                              <Login />
/verification/callback         <VerificationCallback />
/vendors                       <ProtectedRoute><VendorList /></ProtectedRoute>
/vendors/:id                   <ProtectedRoute role="ADMIN"><VendorDetail /></ProtectedRoute>
/access-denied                 <AccessDenied />
*                              <NotFound />
```

`<VendorList />` chooses between `<StaffView />` and `<AdminView />` based on
`role` from the auth store.

### 7.2 Auth bootstrap

On every SPA mount, the root component calls `GET /api/auth/me`:

- 200 → hydrate auth store with `{ role, procurement_level, staff_id }`, render
  protected routes as available.
- 401 → set store to unauthenticated; if the current path is protected, redirect to
  `/`; preserve `?reason=session_expired` if the user was actively using the app
  (detected by checking that this 401 came mid-session, not on first paint).

`<VerificationCallback />` reads `code` and `state` from the URL, POSTs them to
`/api/auth/callback`, and on success navigates to `/vendors` (or `/access-denied`
on 403 with `reason: LEVEL_ZERO`).

### 7.3 Pages / Screen Inventory — `frontend/src/pages/` 🟡 Yellow

The demo has **six page-level components** — this is the canonical screen
inventory for the build. The list below mirrors REQUIREMENTS.md §8; both must
stay in sync. **`Registration.jsx` is explicitly NOT in this inventory** per
[ADR-005](../adr/ADR-005-no-staff-registration-in-demo.md): staff rows are
pre-loaded by `scripts/seed_oracle.py` and the portal never inserts into
`STAFF`.

| File | Route | Role / level | Purpose | Notable behaviour |
|---|---|---|---|---|
| `Login.jsx` | `/` | Anonymous | Public landing | "Verify with ID.me" CTA POSTs to `/api/auth/login`, then `window.location = response.authorize_url`. Shows banner if `?reason=session_expired`. |
| `VerificationCallback.jsx` | `/verification/callback` | Anonymous | OAuth return | Posts code+state; shows "Verifying your identity…" with a max-3 s skeleton. On 403 routes to `/access-denied` (with sub-reason) or `/` with error toast. **No infinite spinner — bounded by a 10 s frontend timeout, then user-friendly retry.** |
| `StaffView.jsx` | `/vendors` (STAFF) | LEVEL 1 / 2 | Approved-vendor list | Renders `<VendorTable variant="staff-L1" \| "staff-L2" />`, `<SearchBar />`, `<EmptyState />`. |
| `AdminView.jsx` | `/vendors` (ADMIN) | LEVEL 3 | All-status vendor list | Renders `<VendorTable variant="admin" />` with status column + status dropdown filter. |
| `VendorDetail.jsx` | `/vendors/:id` | LEVEL 3 only | Full vendor detail | Renders Item / Service card, Contact card (name + email), Metadata sidebar (vendor ID, status, approval date, created, last update). "Approved on: \<date>" line when status is APPROVED. "Back to list" link. *(`BankDetailsCard` was removed by ADR-012.)* |
| `AccessDenied.jsx` | `/access-denied` | LEVEL 0 | Friendly denial | Clean, non-alarming message + contact instruction. Single "Back to FCPS" link to log out. |

### 7.4 Components — `frontend/src/components/` 🟢 Green

- `Header.jsx` — wordmark, signed-in indicator, **Log out** link (FR-07). Visible on all
  authenticated pages.
- `StatusBadge.jsx` — coloured chip + visible text label so colour is not the sole
  signal (NFR-04 + FR-18).
- `VendorTable.jsx` — accepts a `variant` prop (`"staff-L1"`, `"staff-L2"`, `"admin"`)
  and a `rows` prop. Pure presentational; sorting and filtering done in parent.
- `SearchBar.jsx` — controlled text input with debounce (150 ms) for the client-side
  filter; emits `onChange(value)`. ARIA `role="searchbox"` + label.
- `EmptyState.jsx` — props `{ title, hint }`. Always rendered when `rows.length === 0`.
- `LoadingState.jsx` — bounded skeleton; never an indefinite spinner.

> *`BankDetailsCard.jsx` was removed by
> [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md).*

### 7.5 State — `frontend/src/store/` 🟡 Yellow

Zustand store with two slices:

- `auth`: `{ status: "loading" | "authenticated" | "unauthenticated", role, procurement_level, staff_id }`
- `vendors`: `{ items: VendorListItem[], filter: { name: string, status: Status | "ALL" }, fetchedAt }`

Selectors that combine the two (e.g. "what columns to render") live in
`store/selectors.js`.

### 7.6 API client — `frontend/src/services/` 🟢 Green

A thin `apiFetch(path, options)` wrapper:

- Always sends `credentials: "include"` so the JWT cookie travels.
- Treats 401 as a global event → triggers auth-store reset and redirect to
  `/?reason=session_expired`.
- Maps non-2xx to a typed error `{ status, detail }` consumed by the page.

### 7.7 Filter and search behaviour (FR-16)

| View | Search target | Additional filter |
|---|---|---|
| Staff L1 / L2 | Client-side substring match on `vendor_name` (case-insensitive) | none |
| Admin | Client-side substring match on `vendor_name` | Status dropdown: ALL / PENDING / UNDER_REVIEW / APPROVED / REJECTED |

Empty search results render `<EmptyState title="No results for '\<term>'." />`.
Truly empty data renders `<EmptyState title="No approved vendors found." />` for
staff and `"No vendors in the system yet."` for admin.

### 7.8 Accessibility implementation (NFR-04, WCAG 2.1 AA)

- Semantic HTML: `<header>`, `<main>`, `<nav>`, `<table>` for the vendor list with
  `<caption>` + scoped `<th>`.
- All interactive elements keyboard-reachable; visible focus ring with ≥ 3:1 contrast.
- Status badges combine an ARIA-readable text label with colour (FR-18). Colour values
  chosen with ≥ 4.5:1 contrast against badge background.
- Form-style fields (search box) have associated `<label>` elements.
- Page titles set dynamically: "Login | FCPS Procurement", "Vendors | FCPS Procurement",
  etc., for screen-reader navigation.
- Login page CTA is a `<button>` (or `<a>` if it's a direct redirect target) — never
  a `<div>` with `onClick`.
- Skip-to-main-content link before the header.

---

## 8. End-to-End Sequence Diagrams

### 8.1 Successful staff login

```
Browser     SPA(React)     FastAPI                Oracle       ID.me
   │            │              │                     │            │
   │── GET / ──►│              │                     │            │
   │            │              │                     │            │
   │            │── POST /api/auth/login ──►│        │            │
   │            │              │── generate state, cache ─────────│
   │            │◄── { authorize_url } ─────│        │            │
   │◄── 302 to authorize_url ──│            │        │            │
   │────────── ID.me login ─────────────────────────────────────►│
   │◄────── 302 to /verification/callback?code=…&state=… ────────│
   │── GET /verification/callback ►│        │        │            │
   │            │── POST /api/auth/callback {code,state} ─►       │
   │            │              │── validate state                  │
   │            │              │── exchange code ───────────────►│
   │            │              │◄── id_token ─────────────────────│
   │            │              │── decode + validate id_token       │
   │            │              │── SELECT STAFF WHERE EMPLOYEE_ID=:sub ──►│  │
   │            │              │◄── row(ACTIVE='Y', VERIFIED='Y', LEVEL=2, ROLE=STAFF) ◄┤  │
   │            │              │── access_service.decide_access → GRANTED               │
   │            │              │── jwt.sign + Set-Cookie session=…                       │
   │            │◄── 200 { role:"STAFF", procurement_level:2 } ◄────                     │
   │            │── navigate("/vendors") ────                                            │
   │            │── GET /api/vendors  (cookie sent) ──►│                                 │
   │            │              │── require_authenticated → claims OK                    │
   │            │              │── rbac_service.list_query_params(STAFF,2)              │
   │            │              │── SELECT … WHERE STATUS='APPROVED' ──►│                │
   │            │              │◄── rows ◄─────────────────────────────│                │
   │            │◄── 200 [VendorListItemL2,…] ◄────                                     │
   │◄── render StaffView ─────────│                                                      │
```

### 8.2 Admin opens vendor detail

```
Browser     SPA      FastAPI                       Oracle
   │         │          │                              │
   │── click row ─►     │                              │
   │         │── GET /api/vendors/123 ─►│              │
   │         │          │── require_role("ADMIN")      │
   │         │          │── SELECT [non-bank columns] FROM PROCUREMENT_ITEMS WHERE ITEM_ID=123 ─►│
   │         │          │◄── row (BANK_DETAILS not selected) ◄─│
   │         │◄── 200 VendorDetail ◄────│
   │◄── render VendorDetail (Item / Contact / Metadata cards) ─│
```

> *Previously this flow wrote an `AUDIT_LOG` row before responding. Removed
> by [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md).*

### 8.3 LEVEL 0 denial

```
… ID.me OK, code exchange OK, JWT NOT issued …
FastAPI: access_service → LEVEL_ZERO
FastAPI: 403 { detail: "Access denied. Your account does not have procurement clearance." }
SPA:    catches 403 on /api/auth/callback with reason=LEVEL_ZERO → navigate("/access-denied")
```

### 8.4 Session expiry mid-use

```
SPA: GET /api/vendors → 401
SPA: apiFetch wrapper resets auth store; navigate("/?reason=session_expired")
SPA: <Login /> shows banner "Your session has expired. Please verify again."
```

### 8.5 Logout

```
User clicks "Log out"
SPA: POST /api/auth/logout (cookie sent) → 204
SPA: clear auth store; navigate("/")
```

---

## 9. PII and Sensitive Data Handling

Per `AI_POLICY.md` PII rule, every implementer touching the fields below must answer
the three confirmation questions before generating code. The design decisions are:

| Field | Returned to | Logged? | Notes |
|---|---|---|---|
| `EMPLOYEE_ID` | Never returned in any API response. Used internally for Oracle lookup. | Never logged. | Map `sub → EMPLOYEE_ID` happens in `access_service`; the value does not leave the service. |
| `FULL_NAME`, `EMAIL` | Header may show first name only (e.g. "Sarah") sourced from `/api/auth/me` if the SPA needs it. **Decision D-FD-13** in §16 — not yet committed. | Never logged. | If the header line shows the name, the response of `/api/auth/me` is the only place `FULL_NAME` appears. |
| `CONTACT_NAME` | LEVEL ≥ 2 in list response; admin in detail. | Never logged. | L1 list response does not include this field at all (not just null). |
| `CONTACT_EMAIL` | **Detail endpoint only** (`GET /api/vendors/{id}`, admin-only). Never in any list response. | Never logged. | Per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md) — API responses match UI display. The detail view is the only screen that renders the email. |
| ~~`BANK_DETAILS`~~ | **Out of scope per [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md).** Not returned, not rendered, not logged. | — | The Oracle column still exists in `DATA_MODEL.md`; no application code touches it. |

Pydantic response models for L1 and L2 omit the higher-level fields entirely
(distinct classes) rather than including them with null values, to keep
over-disclosure structurally impossible.

---

## 10. Error Model

Backend error envelope (FastAPI default `{detail: string}` kept):

| HTTP | Returned when | `detail` body | Frontend rendering |
|---|---|---|---|
| 400 | OAuth `state` invalid/expired | "Authentication request expired. Please verify again." | Toast on `/` + remove `?reason=session_expired` |
| 401 | Missing/invalid/expired JWT | "Session invalid or expired." | Redirect to `/?reason=session_expired` |
| 403 (`role`) | Non-admin hits admin endpoint | "You do not have permission to view this resource." | Toast + back to `/vendors` |
| 403 (`LEVEL_ZERO`) | Access decision LEVEL 0 | "Access denied. Your account does not have procurement clearance." | `/access-denied` page |
| 403 (`NOT_REGISTERED`) | NOT_FOUND, NOT_VERIFIED, INACTIVE | "Your identity has been verified but you are not registered in the FCPS procurement system. Contact your procurement coordinator." | `/access-denied` page (same UX; no enumeration leak) |
| 404 | `/api/vendors/{id}` no row | "Vendor not found." | `<NotFound />` mini-state on detail page |
| 500 | Oracle error (query failure, connection error) | "Something went wrong. Please try again." | Toast; **stack trace never leaks**. *(The `500 on audit failure` clause was removed by ADR-012.)* |
| 502 | ID.me unreachable / token call failed | "Identity provider unreachable." | Toast on login page; retry button. |

403s carry a sub-reason in a custom header `X-Auth-Reason` so the SPA can pick the
right destination page without parsing English copy.

Stack traces and internal error codes are stripped at the FastAPI exception handler
(NFR-12). Server-side, structured logs still record the full trace.

---

## 11. Configuration Additions

Beyond what's already in `ARCHITECTURE.md` §10:

| Var | Purpose | Default |
|---|---|---|
| `JWT_TTL_HOURS` | Replaces `ACCESS_TOKEN_EXPIRE_MINS` (conflict C-02) | `4` |
| `IDME_AUTHORIZE_URL` | Full path, e.g. `${IDME_BASE_URL}/oauth/authorize` | derived |
| `IDME_TOKEN_URL` | Full path, e.g. `${IDME_BASE_URL}/oauth/token` | derived |
| `IDME_JWKS_URL` | For ID-token signature verification | derived |

Resolution C-01/C-02 (ADR-004) should drop `ACCESS_TOKEN_EXPIRE_MINS` and rename.

---

## 12. Data Model Implications (no edits to DATA_MODEL.md)

The build cannot start until DATA_MODEL.md is updated (via ADR-006) to add:

```
PROCUREMENT_ITEMS
─────────────────
+ APPROVED_AT   TIMESTAMP WITH TIME ZONE  NULL
  (set whenever STATUS transitions to 'APPROVED'; remains NULL otherwise)
```

`scripts/seed_oracle.py` will be extended to add this column and seed
plausible `APPROVED_AT` values for the 5 APPROVED rows.

> *Previously this section also specified an `AUDIT_LOG` table (LOG_ID,
> STAFF_ID, VENDOR_ID, ACCESSED_AT + two indexes). That table was removed
> by [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) along with the
> rest of the audit-logging requirement.*

---

## 13. Performance Design (NFR-01, NFR-02)

| Concern | Approach |
|---|---|
| `GET /api/vendors` p95 < 500 ms | Dataset is ~120 rows. A single indexed scan on `IDX_PROC_STATUS` plus column projection. Oracle XE on the same host, sub-10 ms expected. Headroom is for cold connection / JWT decode. |
| `GET /api/vendors/{id}` p95 < 300 ms | PK lookup. Single-row read on the indexed primary key; sub-5 ms expected on Oracle XE. *(Previous draft included an audit insert here; removed by ADR-012.)* |
| Login page < 3 s | SPA is a small Vite/CRA bundle served by Nginx from disk. Gzip enabled in Nginx. ID.me discovery URL pre-fetched. |
| Oracle XE cold start | EC2 boot script runs a "warm-up" `SELECT 1 FROM DUAL` against XE 60 s after container start. Documented in deploy README. |

No caching of vendor data on the backend — values are read fresh on every request.
With ~120 rows this is fine and avoids cache-coherency bugs.

---

## 14. Test Strategy

| Layer | Tool | Focus |
|---|---|---|
| Backend unit | Pytest | `access_service` decision tree (all 5 reasons); `rbac_service` column flags per role/level; `jwt` sign/verify. |
| Backend integration | Pytest + httpx + testcontainers Oracle | `/api/vendors` for L1, L2, ADMIN returns the right shape; `/api/vendors/{id}` returns 200 for admin, 403 for STAFF, 404 for unknown ID. |
| ID.me callback | Mocked at the `requests.post` boundary. Test happy path, expired state, invalid id_token, ID.me 5xx → 502. |
| Frontend unit | Jest + RTL | `StatusBadge` colour + text; `EmptyState` props; `apiFetch` 401 → redirect side-effect. |
| Frontend integration | RTL + MSW | StaffView L1 vs L2 column rendering; AdminView status filter; VerificationCallback success and 403→/access-denied. |
| E2E | Playwright (optional for demo) | One full happy-path admin login + detail view; one denied L0 user. |
| Accessibility | jest-axe on each page-level component | No serious or critical violations. |

Coverage gate: 80% line coverage on backend `services/` and `auth/`; no coverage gate
on frontend (pragmatic for demo).

---

## 15. Deployment Design

Unchanged from `ARCHITECTURE.md` §5. Notable specifics:

- `.github/workflows/test.yml` runs on PR: Pytest, Jest, ruff, eslint, mypy
  (strict on `app/auth/`).
- `.github/workflows/deploy.yml` runs on push to `prod`: builds React, builds backend
  image, `scp` of `docker-compose.yml` + bundles, `ssh` to run `docker compose up -d`
  and then `docker compose exec backend python scripts/seed_oracle.py` (idempotent;
  re-running is safe).
- Nginx config templates inject `EC2_PUBLIC_IP` at deploy time so the SPA's
  `IDME_REDIRECT_URI` matches what's registered in the ID.me console.

---

## 16. Open Design Items (need decisions before build)

| # | Item | Default if no decision | Who |
|---|---|---|---|
| OQ-FD-01 | When HTTPS is enabled, cookie `Secure=true`. Today's demo is HTTP; do we make the cookie env-driven `JWT_COOKIE_SECURE` so HTTPS rollout is a config flip? | Yes — env-driven, default `false`. | C&T Tech Lead |
| OQ-FD-02 | `state` cache backing store. In-process dict is fine for one Uvicorn worker. If we ever scale to multiple workers, we need a shared store (Redis) — not in demo scope. | In-process dict, single worker. Document the constraint. | C&T Tech Lead |
| OQ-FD-03 | D-FD-13: Show the user's first name in the header? Requires `GET /api/auth/me` to return name, which means PII leaves the backend. The wins are minor (friendliness). | **Do not** show name; header reads "Signed in (ADMIN)" / "Signed in". | C&T Project Lead |
| ~~OQ-FD-04~~ | ~~Audit-write failure handling.~~ **Removed by [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) — no audit service to fail.** | — |
| OQ-FD-05 | OpenAPI `oneOf` for `/api/vendors` response. Easy in spec, mildly awkward in clients. Alternative: a single union schema with optional fields. | `oneOf` — preserves the "structurally impossible to over-disclose" guarantee from §6.9. | C&T Tech Lead |
| OQ-FD-06 | Should `/api/auth/me` 401 trigger `?reason=session_expired` on **every** unauthenticated mount, or only when there was a prior session? Frontend has no durable hint either way. | Only on mid-session 401 (detected by SPA flag in session storage). On fresh page load, no banner. | C&T Tech Lead |
| OQ-FD-07 | Idle timeout for shared-school-computer concern (you opted for "Logout button" only). Confirm we are **not** adding idle timeout. | No idle timeout. | Project Lead (you) |

Red Zone decisions D-FD-01 … D-FD-12 are listed inline in §6 and require explicit
approval in writing per `AI_POLICY.md` 🔴 Red rules before any code is generated.

---

## 17. Glossary deltas vs REQUIREMENTS.md

| Term | Meaning in this doc |
|---|---|
| Vendor row | A row of `PROCUREMENT_ITEMS`. `VENDOR_NAME` is the row's display key for users. |
| Session | The JWT + its cookie. Not a server-side session — JWT only. |
| `state` cache | In-process dict mapping the OAuth `state` string to its issue time. TTL 10 min, one-shot. |

---

**Next document:** [api-spec.yaml](./api-spec.yaml) — will not be generated until this
FUNCTIONAL_DESIGN.md has been reviewed and signed off. The spec will be derived
directly from §5 (URL map), §6.1–6.2 (endpoints), §6.9 (schemas), and §10 (error
model).
