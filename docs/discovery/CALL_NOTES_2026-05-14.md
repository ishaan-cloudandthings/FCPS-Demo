# Requirements Call Notes — FCPS Procurement Portal

> BA agent prompt to use after this call:
> "Read `docs/discovery/CALL_NOTES_2026-05-14.md`, `docs/ARCHITECTURE.md`, and
> `docs/DATA_MODEL.md`. Extract the requirements, then interview me one question at
> a time to fill in anything missing. After the interview, produce
> `docs/requirements/REQUIREMENTS.md` and `docs/requirements/FUNCTIONAL_DESIGN.md`,
> then draft `docs/api-spec.yaml` covering all endpoints. Pause for my review after
> each document."

---

## Meeting Details

| Field | Value |
|---|---|
| Date | 2026-05-14 |
| Type | Requirements — Procurement Access & Role-Based Views |
| Attendees | FCPS Procurement Coordinator, FCPS IT Lead, C&T Project Lead |
| Facilitator | C&T Project Lead |
| Duration | 60 minutes |

---

## Context

FCPS needs a portal where staff can verify their identity and then access procurement
records appropriate to their role. Today everything lives in a spreadsheet that Procurement Coordinator
manually shares — there's no access control, no audit trail, and staff regularly email
her asking "is this vendor approved yet?" This portal replaces that.

The demo we're building needs to show two things clearly:
1. An admin (procurement coordinator like Procurement Coordinator) logs in and sees everything — all
   vendors, all statuses, all contact and payment details.
2. A staff member (teacher) logs in and only sees vendors that have been approved —
   nothing pending, nothing rejected, none of the sensitive vendor contact or bank details.

---

## User Journeys Discussed

### Journey: Admin views procurement records

**Who does this?**
Procurement coordinators. There are currently 2 at FCPS (Procurement Coordinator, Procurement Coordinator (secondary)).
They manage the full vendor lifecycle.

**What they want to do:**
See the complete list of all procurement items across every status. Review pending
submissions, check what's under review, confirm what's been approved or rejected.
See all vendor details including contact name, contact email, and payment/bank information.

**Steps they described:**
1. Log in (will be via ID.me in the new portal)
2. Land on a dashboard showing all procurement items — no filtering by default
3. See status badges clearly — PENDING, UNDER_REVIEW, APPROVED, REJECTED
4. Click into a record to see full detail including bank details

**What success looks like to them:**
"I should see everything. Nothing hidden from me. If I submitted a vendor last week and
it's sitting in PENDING, I need to see that."

**Edge cases or exceptions they mentioned:**
- What if a vendor has been partially approved? (Procurement Coordinator said this doesn't happen —
  it's a binary APPROVED / not-APPROVED from the committee)
- What about archived/inactive vendors? (Procurement Coordinator said out of scope for the demo —
  all records are active)

---

### Journey: Staff member views approved vendors

**Who does this?**
Teachers, facilities managers, department heads — anyone who needs to know which vendors
are cleared to work with.

**What they want to do:**
See the list of approved vendors so they know who they can engage. They don't need to
see anything in review or rejected — that's not their concern. They also should not see
vendor bank details or payment terms.

**Steps they described:**
1. Log in via ID.me
2. Land on a list — only approved vendors visible
3. Can see vendor name, category, item/service description
4. Can see contact name and email if they need to reach out (but only if they have
   sufficient procurement level — FCPS IT Lead mentioned Level 2+ for contact details)
5. Cannot see bank details under any circumstances

**What success looks like to them:**
"A teacher should be able to look up 'is Dell on the approved vendor list' and get a
yes or no with a contact person if needed. That's it."

**Edge cases or exceptions they mentioned:**
- What does a staff member with LEVEL=0 see? FCPS IT Lead said they should be denied access
  entirely — "if you have no procurement clearance, you shouldn't even be in the system."
- What if a vendor moves from APPROVED back to UNDER_REVIEW? Staff should immediately
  stop seeing it. The filter is live, not cached.

---

## What Is Out of Scope

- [ ] Vendor self-registration — vendors do not have portal access. FCPS staff submit
      vendor records internally. (Confirmed by Procurement Coordinator: "vendors don't log in, we add them")
- [ ] Approving or rejecting vendors through the portal — that workflow stays in the
      committee process for now. The portal is read-only for this demo.
- [ ] Email notifications to staff when a vendor is approved — out of scope for demo,
      possibly phase 2.
- [ ] Bulk export / CSV download of the procurement table — out of scope for demo.
- [ ] Mobile app — web browser only.

---

## Non-Functional Requirements

| NFR | What was said |
|---|---|
| Performance | "It needs to load fast — teachers check this between classes." FCPS IT Lead said < 3 seconds for the procurement list. |
| Security | ID.me verification required before any data is shown. JWT session. Bank details must never appear in a non-admin response — FCPS IT Lead was emphatic about this. |
| Compliance | FERPA doesn't directly apply here (no student data). FCPS IT policy requires all staff-facing tools to support SSO — ID.me satisfies this for the demo. |
| Accessibility | WCAG 2.1 AA minimum. Procurement Coordinator mentioned one coordinator uses a screen reader. |
| Browser support | Chrome, Firefox, Edge. No IE. Safari nice-to-have. |
| Data retention | Not discussed — flagged as open question. |
| Audit logging | FCPS IT Lead: "We need to know who looked at bank details and when." Audit log on BANK_DETAILS access is a must-have. |
| Uptime | Demo environment — no SLA required. |

---

## Integrations and External Systems

| System | Purpose | Notes |
|---|---|---|
| ID.me | Staff identity verification | Sandbox credentials available. FCPS IT Lead will share IDME_CLIENT_ID and IDME_CLIENT_SECRET. Redirect URI must be registered — confirm URL with FCPS IT Lead before dev starts. |
| Oracle XE | Staff HR data and procurement records | IT team manages the Oracle instance. For the demo we seed our own Docker container. Schema confirmed in DATA_MODEL.md. |

---

## Data and Sensitive Information

| Data type | Who owns it | PII / sensitive? | Notes |
|---|---|---|---|
| Staff records (name, email, employee ID) | FCPS HR | Yes — PII | Never logged. Employee ID used for Oracle lookup only. |
| Vendor contact name and email | Procurement team | Yes — PII | Returned only for PROCUREMENT_LEVEL >= 2 |
| Bank / payment details | Procurement team | Yes — sensitive financial | Returned only for PROCUREMENT_LEVEL = 3 (Admin). FCPS IT Lead: "This is the most sensitive field in the system." |
| Procurement item name, category, status | Procurement team | No | Safe to show to all authenticated staff with LEVEL >= 1 |

---

## Decisions Made on This Call

- **Admin = sees everything.** All statuses (PENDING, UNDER_REVIEW, APPROVED, REJECTED), all fields including CONTACT_NAME, CONTACT_EMAIL, BANK_DETAILS. Role = ADMIN in Oracle STAFF table.
- **Staff = sees APPROVED only.** No access to PENDING, UNDER_REVIEW, REJECTED items. CONTACT fields visible at LEVEL 2+. BANK_DETAILS visible at LEVEL 3 only (which in practice means only ADMIN-role users).
- **LEVEL = 0 means no access at all.** Even if ID.me verified. Access denied at the portal level.
- **Role comes from Oracle, not ID.me.** ID.me proves who you are. Oracle says what you're allowed to do. These are separate concerns.
- **The portal is read-only for this demo.** No creating, editing, or approving vendors through the UI.
- **Audit log required for BANK_DETAILS access.** Every time BANK_DETAILS is returned in a response, log: who accessed it, which item, timestamp. Do not log the value itself.

---

## Open Questions

- [ ] Data retention policy for STAFF records — how long do we keep a staff member's Oracle row after they leave FCPS? Owner: FCPS IT Lead — needed before production deploy.
- [ ] What happens if a staff member's IDME_VERIFIED goes back to 'N' mid-session (e.g. their ID.me account is suspended)? Should we invalidate the JWT? Owner: C&T Tech Lead — decision needed before auth implementation.
- [ ] Should LEVEL 2 staff see CONTACT_EMAIL for REJECTED vendors, or only APPROVED? Procurement Coordinator said "probably not — if it's rejected they don't need to contact anyone." Needs formal sign-off.
- [ ] Is there a requirement to show the date a vendor was approved? Not discussed — flagged for follow-up.

---

## Exact Quotes Worth Capturing

> "Bank details must never show up for a teacher. That's non-negotiable." — FCPS IT Lead

> "If I'm an admin I need to see everything — pending, rejected, all of it. Otherwise how do I manage the pipeline?" — Procurement Coordinator

> "Staff just need to know: is this vendor approved, and who do I call? That's the whole use case." — Procurement Coordinator

> "Level zero means you have no procurement role at all. You shouldn't even get past the login screen." — FCPS IT Lead

---

## Next Steps

| Action | Owner | By when |
|---|---|---|
| Share IDME_CLIENT_ID and IDME_CLIENT_SECRET (sandbox) | FCPS IT Lead | 2026-05-16 |
| Confirm EC2 redirect URI for ID.me registration | C&T Tech Lead | 2026-05-16 |
| Formal sign-off on LEVEL 2 access to CONTACT fields for non-APPROVED vendors | Procurement Coordinator | 2026-05-18 |
| BA agent: produce REQUIREMENTS.md, FUNCTIONAL_DESIGN.md, api-spec.yaml draft | C&T BA (Claude) | 2026-05-15 |

---

## Raw Notes

Quick notes taken during call — unstructured:

- Procurement Coordinator showed us her current Excel spreadsheet. ~120 vendors, 4 status columns
  colour-coded by hand. "This is not sustainable."
- FCPS IT Lead confirmed Oracle XE is already running on the demo EC2. The STAFF table
  has 10 seed records ready.
- Demo audience will be FCPS IT leadership and 2 procurement coordinators.
  They want to see the role separation working live — admin logs in, sees everything;
  teacher logs in, sees only approved list. That's the money shot.
- Procurement Coordinator (secondary) (second admin) won't be at the demo but Procurement Coordinator will log in as both
  roles to show the difference. Need two test accounts ready.
- No Figma, no design system specified. Procurement Coordinator said "clean and simple, nothing fancy,
  we just need it to work."
- FCPS IT Lead asked about FERPA. Confirmed no student data is in scope — this is vendor
  and staff data only.
