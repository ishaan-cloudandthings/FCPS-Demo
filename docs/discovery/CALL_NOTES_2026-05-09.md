# Requirements Call Notes — Staff Procurement Portal

> BA agent prompt to use after this call:
> "Read all files in `docs/discovery/` in date order. Build a picture of what has been
> agreed across all calls. Interview me one question at a time to fill in gaps. Then
> produce `docs/requirements/REQUIREMENTS.md` and `docs/requirements/FUNCTIONAL_DESIGN.md`."

---

## Meeting Details

| Field | Value |
|---|---|
| Date | 2026-05-09 |
| Type | User Journey Walkthrough |
| Attendees | Procurement Coordinator, IT Lead, C&T Project Lead, C&T Tech Lead |
| Facilitator | C&T Tech Lead |
| Duration | 75 minutes |

---

## Context

Third call. Technical setup confirmed on the May 5 call. This session focuses on
walking through every user-facing interaction step by step — what the user sees,
what the system does, and what success and failure look like at each point.
Two journeys covered in full: staff member first-time access, and admin daily use.

---

## User Journeys Discussed

### Journey 1: Staff member — first-time access

**Who does this?**
A teacher or department head logging in to check the approved vendor list.
Likely not technically sophisticated. May be doing this from a shared school computer.

**Step-by-step walkthrough:**

| Step | What user does | What system does | Success state | Failure state |
|---|---|---|---|---|
| 1 | Navigates to portal URL | Serves React SPA login page | Login page loads in < 3 s | Blank page — check Nginx/EC2 |
| 2 | Clicks "Verify with ID.me" | Redirects to ID.me with `client_id`, `redirect_uri`, `state`, `scope=openid` | ID.me login page appears | OAuth error — check client_id and redirect_uri registration |
| 3 | Completes ID.me login | ID.me redirects back to `/auth/callback?code=...&state=...` | Callback received by FastAPI | `state` mismatch → 400 |
| 4 | FastAPI exchanges code for token | POST to ID.me `/token` endpoint with `client_id`, `client_secret`, `code`, `redirect_uri` | Access token + `sub` (ID.me subject) returned | 401 from ID.me — secret wrong or code expired |
| 5 | FastAPI looks up staff in Oracle | `SELECT * FROM STAFF WHERE EMPLOYEE_ID = :employee_id AND IDME_VERIFIED = 'Y'` | Row found, PROCUREMENT_LEVEL and ROLE returned | No row → 403 "not recognised" |
| 6 | LEVEL check | Backend evaluates `PROCUREMENT_LEVEL` | LEVEL >= 1: continue | LEVEL = 0: 403 "no procurement clearance" |
| 7 | JWT issued | FastAPI signs JWT with `role`, `employee_id`, `procurement_level` claims; sets `HttpOnly` cookie | Cookie set, redirect to `/vendors` | JWT sign failure — check JWT_SECRET env var |
| 8 | Staff view loads | React fetches `/api/vendors` with cookie | Returns APPROVED vendors only, no BANK_DETAILS, CONTACT fields gated by level | Empty list if no vendors are APPROVED |
| 9 | Staff searches for a vendor | Frontend filters displayed list by name | Matching vendor rows highlighted | No match → "No approved vendors found matching your search" |

**What success looks like:**
"A teacher types 'Dell' into the search box and sees the Dell row with the category
and contact name. They didn't need to email anyone." — Procurement Coordinator

**Edge cases discussed:**
- What if the teacher has an ID.me account but is NOT in the Oracle STAFF table?
  → 403 with message "Your identity has been verified but you are not registered in
  the staff procurement system. Contact your procurement coordinator."
- What if the teacher's ID.me account is verified but IDME_VERIFIED = 'N' in Oracle?
  → 403 — same message as above. The flag must match.
- What if no vendors are APPROVED yet?
  → Empty state message. Not an error. "Under no circumstances should a loading spinner
  loop forever." — IT Lead

---

### Journey 2: Admin (procurement coordinator) — daily use

**Who does this?**
The two procurement coordinators. This is their primary tool once the portal replaces
the spreadsheet.

**Step-by-step walkthrough:**

| Step | What user does | What system does | Success state | Failure state |
|---|---|---|---|---|
| 1 | Same login flow via ID.me | Same as Journey 1 steps 1–7 | JWT issued with ROLE = ADMIN, PROCUREMENT_LEVEL = 3 | Same failure modes as Journey 1 |
| 2 | Admin dashboard loads | React fetches `/api/vendors` — backend returns ALL vendors regardless of status | All vendors visible with STATUS badges | If ROLE check fails and only APPROVED shown → critical bug |
| 3 | Coordinator scans the list | Frontend shows status badges: PENDING (amber), UNDER_REVIEW (blue), APPROVED (green), REJECTED (red) | All four statuses visible | Missing status badge — check frontend badge component |
| 4 | Coordinator clicks a vendor row | React fetches `/api/vendors/{id}` | Full detail returned including CONTACT_NAME, CONTACT_EMAIL, BANK_DETAILS | 403 — check JWT role claim |
| 5 | BANK_DETAILS viewed | Backend returns BANK_DETAILS, writes audit log entry | Audit record created: staff_id, vendor_id, timestamp (no BANK_DETAILS value logged) | Audit log not written → compliance failure |
| 6 | Coordinator reviews pending vendor | Sees PENDING status badge on vendor row | Vendor visible in list | Vendor not visible → access filter bug |

**What success looks like:**
"I log in, I see everything, I can click into any vendor and see their bank details if I
need to. And if anyone asks who's been looking at that data, we have a record." — Procurement Coordinator

**Edge cases discussed:**
- Can an admin see their own Oracle STAFF row through the portal?
  → No. The portal only exposes the PROCUREMENT_ITEMS table. STAFF records are never
  surfaced in any UI.
- What if BANK_DETAILS is NULL for a vendor?
  → Show "Not on file" in the detail view. Do not show a blank field.
- What if an admin's session expires mid-use?
  → JWT cookie expiry triggers a redirect back to the login page. The JWT should have
  a reasonably short TTL — IT Lead suggested 4 hours for the demo.

---

### Journey 3: Access denied — LEVEL 0 staff

**Who does this?**
An employee who has been set up in Oracle with PROCUREMENT_LEVEL = 0. This means
they have no procurement role. They have a valid ID.me account and are in the STAFF
table, but they are not cleared for the portal.

**Step-by-step walkthrough:**

1. Staff completes ID.me verification successfully.
2. FastAPI looks up Oracle row — found, but `PROCUREMENT_LEVEL = 0`.
3. Backend returns 403 with body: `{"detail": "Access denied. Your account does not have procurement clearance."}`.
4. React shows a dedicated "Access Denied" screen — not a generic error page.
5. Screen includes a contact line: "If you believe this is an error, contact your procurement coordinator."

**IT Lead note:** "The denied screen should be clean and not scary. We don't want
staff thinking they've broken something."

---

## Screen Requirements Finalised This Call

### Login page (`/`)
- Single CTA button: "Verify with ID.me"
- Staff Procurement Portal logo or wordmark (C&T to source from IT Lead — pending)
- No username/password fields — ID.me only
- Brief explanatory sentence: "Access to the Staff Procurement Portal requires
  verified employee identity."

### Staff vendor list (`/vendors` — ROLE = STAFF)
- Table columns: Vendor Name | Category | Item / Service Description | Contact Name (L2+) | Contact Email (L2+)
- No status column (all shown are APPROVED)
- Search / filter bar at top — client-side filter on Vendor Name
- No pagination required for demo (~40 approved vendors max)
- Empty state: "No approved vendors found." or "No results for '[search term]'."

### Admin vendor list (`/vendors` — ROLE = ADMIN)
- Same table as staff view PLUS: Status column, Bank Details column
- Status column shows coloured badges
- Row click navigates to detail view
- Filter bar — client-side on Vendor Name, with optional Status dropdown filter

### Admin vendor detail (`/vendors/{id}` — ROLE = ADMIN)
- Full record: all columns from PROCUREMENT_ITEMS
- BANK_DETAILS shown in a highlighted/bordered card (visually distinct)
- "Back to list" navigation
- Timestamp of last status change if available (open question — see below)

### Access denied page
- Clean, simple message
- Not an error page — friendly tone
- Contact instruction for staff

---

## Non-Functional Requirements (additions to May 5 call)

| NFR | What was said |
|---|---|
| JWT TTL | 4 hours for demo. Configurable via env var `JWT_TTL_HOURS`. |
| Session expiry UX | On expiry, redirect to login page with query param `?reason=session_expired`. Show brief message: "Your session has expired. Please verify again." |
| Empty state | Every list view must have a defined empty state. No blank tables. |
| Error messaging | 403 messages must be user-friendly. Do not expose internal error codes or stack traces to the browser. |
| BANK_DETAILS display | Visually distinct in the detail view — bordered card, muted background. Makes clear this is sensitive data. |
| Audit log content | Log: `STAFF_ID`, `VENDOR_ID`, `ACCESSED_AT` (UTC timestamp). Never log the `BANK_DETAILS` value itself. Table: `AUDIT_LOG`. |

---

## Integrations and External Systems

No new integrations added. Confirmed from May 5:
- ID.me sandbox credentials will be shared by IT Lead by 2026-05-16.
- Oracle STAFF table has 10 seed records including at least 1 ADMIN and 2 STAFF with varying PROCUREMENT_LEVEL values.
- C&T Tech Lead to confirm EC2 redirect URI before dev starts.

---

## Data and Sensitive Information

Refinements agreed on this call:

| Data type | Rule confirmed |
|---|---|
| BANK_DETAILS | Returned only for PROCUREMENT_LEVEL = 3. Visually highlighted in UI. Audit-logged on every access. Never logged to application logs. |
| CONTACT_NAME / CONTACT_EMAIL | Returned in API response only for PROCUREMENT_LEVEL >= 2. Not shown in list view for LEVEL 1 staff — columns simply absent. |
| STAFF table | Never surfaced in UI. Used only internally for auth decisions. |
| EMPLOYEE_ID | Used for Oracle lookup only. Not in JWT. Not in any API response. |

---

## Decisions Made on This Call

- **JWT claims:** `role` (ADMIN or STAFF), `procurement_level` (0–3), `staff_id` (Oracle primary key). `employee_id` NOT in JWT.
- **HttpOnly cookie for JWT.** No localStorage. SameSite=Lax.
- **ID.me `sub` mapped to `EMPLOYEE_ID` in Oracle.** The mapping is confirmed — `EMPLOYEE_ID` in the STAFF table stores the ID.me subject identifier.
- **AUDIT_LOG table required.** Schema: `LOG_ID` (PK), `STAFF_ID` (FK → STAFF), `VENDOR_ID` (FK → PROCUREMENT_ITEMS), `ACCESSED_AT` (TIMESTAMP). To be added to `seed_oracle.py`.
- **JWT TTL: 4 hours.** Configurable via `JWT_TTL_HOURS` env var.
- **Client-side search only.** No server-side search endpoint for the demo.
- **No pagination.** ~40 approved vendors and ~120 total — fits on one page.
- **Staff Procurement Portal logo:** IT Lead to provide asset. Placeholder acceptable for demo if not received.

---

## Open Questions

- [ ] Is there a requirement to show the date a vendor was approved? Procurement Coordinator said "that would be useful" but did not commit. Owner: Procurement Coordinator — sign-off needed before detail view is built.
- [ ] Should the admin detail view show the full AUDIT_LOG history for that vendor (who accessed it and when)? IT Lead said "interesting idea" — not confirmed for demo scope. Owner: IT Lead — decision needed before Sprint 3.
- [ ] Staff Procurement Portal logo asset — where does C&T source this? Owner: IT Lead — to provide file by 2026-05-16.
- [ ] Should LEVEL 2 staff see CONTACT_EMAIL for REJECTED vendors? (Carried from May 14 call — still no formal sign-off.) Owner: Procurement Coordinator.

---

## Exact Quotes Worth Capturing

> "I don't want teachers staring at a spinning wheel. Either it works or it tells them
> something went wrong. No mystery." — IT Lead

> "The bank details box should look important — not just another field. People need to
> know that's sensitive." — Procurement Coordinator

> "If someone is denied, they shouldn't feel like they crashed the system. It should
> just say: you don't have access, here's who to call." — IT Lead

> "The admin view needs to show everything in one place. I don't want to click around
> to find out what's pending." — Procurement Coordinator

---

## Next Steps

| Action | Owner | By when |
|---|---|---|
| Add AUDIT_LOG to `seed_oracle.py` schema | C&T Tech Lead | 2026-05-12 |
| Confirm JWT claims list with C&T Tech Lead | C&T Tech Lead | 2026-05-12 |
| Sign off on vendor approval date display in detail view | Procurement Coordinator | 2026-05-12 |
| Provide Staff Procurement Portal logo asset | IT Lead | 2026-05-16 |
| BA agent: read all discovery docs and produce REQUIREMENTS.md + FUNCTIONAL_DESIGN.md | C&T BA (Claude) | 2026-05-15 |

---

## Raw Notes

- C&T Tech Lead screenshared a rough wireframe of the staff view. Procurement Coordinator
  approved the column layout immediately — "yes, exactly that, nothing more."
- Discussion about whether to show vendor phone number in the staff view. Staff Procurement
  Coordinator said coordinators don't always have phone on file — email is sufficient.
  Phone column dropped from requirements.
- IT Lead asked whether the audit log should email an alert when BANK_DETAILS is
  accessed outside business hours. C&T Project Lead noted this as out of scope for the
  demo but flagged as a phase 2 consideration.
- Confirmed the Oracle STAFF seed will have:
  - 1 ADMIN user (PROCUREMENT_LEVEL = 3, ROLE = 'ADMIN')
  - 2 STAFF users at PROCUREMENT_LEVEL = 2 (can see contact details)
  - 2 STAFF users at PROCUREMENT_LEVEL = 1 (cannot see contact details)
  - 1 STAFF user at PROCUREMENT_LEVEL = 0 (access denied)
- IT Lead confirmed Oracle XE is running on the demo EC2 and responsive.
  No schema changes needed beyond adding AUDIT_LOG table.
