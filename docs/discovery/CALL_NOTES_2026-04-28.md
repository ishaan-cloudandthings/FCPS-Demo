# Requirements Call Notes — Staff Procurement Portal

> BA agent prompt after this call:
> "Read all files in `docs/discovery/` in date order. Build a picture of what has been
> agreed across all calls. Interview me one question at a time to fill in gaps. Then
> produce `docs/requirements/REQUIREMENTS.md`."

---

## Meeting Details

| Field | Value |
|---|---|
| Date | 2026-04-28 |
| Type | Initial Discovery |
| Attendees | Procurement Coordinator, C&T Project Lead |
| Facilitator | C&T Project Lead |
| Duration | 45 minutes |

---

## Context

First call with Staff Procurement Portal. No technical details discussed — purely understanding the
business problem and what a successful outcome looks like. IT Lead was
not available and will join the technical call next week.

---

## User Journeys Discussed

### Journey: Current state — what Procurement Coordinator does today

**Who does this?**
The two procurement coordinators.

**What they do today:**
Maintain a shared Excel spreadsheet with all vendor records. When a teacher wants
to know if a vendor is approved, they email Procurement Coordinator. Procurement Coordinator checks the spreadsheet and
replies. On a busy week she gets 15–20 of these emails.

When a new vendor is submitted for consideration, Procurement Coordinator adds them to the spreadsheet
manually, the committee reviews offline, and Procurement Coordinator updates the status. There is no
audit trail for who changed what or when.

**The pain:**
- No self-service — every query comes to Procurement Coordinator
- No access control — anyone Procurement Coordinator shares the file with sees everything, including
  bank details
- No verification that the person asking is actually an employee
- No audit log on who accessed sensitive vendor financial information

**What success looks like:**
"Teachers can look up approved vendors themselves without emailing me. And I can
control who sees the sensitive stuff."

---

### Journey: What the portal needs to do (high level)

Procurement Coordinator described two types of users:

**Procurement coordinators (her team):**
Need to see the full picture — every vendor regardless of status, all contact and
payment details. Currently 2 people. Likely to stay small.

**General staff (teachers, department heads, etc.):**
Just need to know: is this vendor on the approved list? If yes, who do I contact?
They don't need to know what's pending, what's been rejected, or any payment info.

The portal needs to show each type of user the right slice of data — automatically,
based on who they are.

**Identity:**
Procurement Coordinator mentioned that Staff Procurement Portal already uses ID.me for some HR processes. She wants
staff to verify through ID.me before they can access any data. "If they're not
a real employee, they shouldn't see anything."

---

## What Is Out of Scope

- [ ] Vendors logging into the portal — this is an internal staff tool only
- [ ] The approval workflow — committee decisions happen offline, outside this system
- [ ] Editing or creating vendor records through the portal — read-only for this demo
- [ ] Any student data — confirmed explicitly, this is vendor/staff data only
- [ ] Mobile app — browser only
- [ ] Email notifications — possibly phase 2

---

## Non-Functional Requirements

| NFR | What was said |
|---|---|
| Performance | Not discussed — flagged for follow-up |
| Security | ID.me verification required. Sensitive fields (bank details) must not be visible to general staff under any circumstances. |
| Compliance | Procurement Coordinator mentioned FERPA briefly but confirmed no student data is in scope. IT policy requires SSO-compatible auth — ID.me satisfies this. |
| Accessibility | Not discussed — flagged for follow-up |
| Browser support | Not discussed — flagged for follow-up |
| Data retention | Not discussed — flagged for follow-up |
| Audit logging | Procurement Coordinator mentioned wanting to know "who's been looking at our vendor payment info." Audit trail is a requirement. |

---

## Integrations and External Systems

| System | Purpose | Notes |
|---|---|---|
| ID.me | Staff identity verification | Procurement Coordinator confirmed Staff Procurement Portal already has an account. IT Lead will handle the technical setup. |
| Oracle | Staff and vendor data | IT Lead manages the Oracle instance. Procurement Coordinator wasn't sure of the details — deferred to technical call. |

---

## Decisions Made on This Call

- **The portal is read-only for the demo.** No creating or editing vendors through the UI.
- **ID.me is the identity provider.** Not negotiable — Staff Procurement Portal IT policy.
- **Two distinct views are needed.** Admin (procurement coordinator) sees everything. Staff sees approved vendors only.
- **Sensitive vendor financial data must be access-controlled.** Bank details are not for general staff.
- **This is a demo build.** The goal is to show the concept to Staff Procurement Portal leadership — not a production system yet.

---

## Open Questions

- [ ] How many staff members will use this? Rough number for load planning — Owner: Procurement Coordinator — needed before NFR call
- [ ] Are there more than two procurement levels, or is it just admin vs staff? — Owner: IT Lead — needed before technical call
- [ ] What browser does Staff Procurement Portal IT standardise on? — Owner: IT Lead — needed before design starts
- [ ] What does the committee approval process look like? (Out of scope for portal but useful context) — Owner: Procurement Coordinator — informal
- [ ] Are there any data governance policies that apply to vendor financial data? — Owner: IT Lead — needed before build starts

---

## Exact Quotes Worth Capturing

> "I spend half my day answering emails from teachers asking if a vendor is on the list.
> That should not be my job." — Procurement Coordinator

> "The problem isn't just the emails. It's that I have to share the whole spreadsheet
> to answer one question, and that spreadsheet has bank account numbers in it." — Procurement Coordinator

> "If they're a real employee with procurement clearance, they should be able to
> see what they need. If they're not, they get nothing." — Procurement Coordinator

---

## Next Steps

| Action | Owner | By when |
|---|---|---|
| Schedule technical discovery call with IT Lead | C&T Project Lead | 2026-04-30 |
| Procurement Coordinator to confirm approximate number of staff users | Procurement Coordinator | 2026-05-02 |
| C&T to prepare technical questions list for IT Lead call | C&T Tech Lead | 2026-05-03 |

---

## Raw Notes

- Procurement Coordinator has been at Staff Procurement Portal 8 years. Knows the vendor data inside out.
- The Excel spreadsheet has ~120 vendors. Roughly 40 are APPROVED.
- Committee meets monthly to review PENDING and UNDER_REVIEW vendors.
- Procurement Coordinator (secondary) (second coordinator) does the same job as Procurement Coordinator — both need full access.
- Demo audience: Staff Procurement Portal IT leadership and the two coordinators. Possibly the Deputy
  Superintendent. Procurement Coordinator said "if it impresses IT Lead, it impresses everyone."
- Procurement Coordinator explicitly does NOT want anything "fancy" — "we don't need animations or
  dashboards. We need a list that works."
- C&T confirmed this is a greenfield demo build — not migrating from an existing system.
