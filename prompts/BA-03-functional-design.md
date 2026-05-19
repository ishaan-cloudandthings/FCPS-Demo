# BA-03: Functional Design Document (FDD) Template & Prompt

> **Purpose:** This prompt guides Business Analysts in producing a comprehensive Functional Design Document that maps user journeys to system behavior, integration points, data flows, validation rules, and notification triggers.
>
> **Output:** A complete FDD living at `docs/requirements/FUNCTIONAL_DESIGN.md` that serves as the specification artefact for developers, architects, and QC.

---

## Document Naming Convention

All Functional Design Documents must follow this strict naming convention to ensure consistency and traceability:

```
<Jira Epic>_<Jira Story>_<Story Name>
```

**Format Breakdown:**
- **`<Jira Epic>`** – The epic identifier from Jira (e.g., `AC-10`, `SP-05`)
- **`<Jira Story>`** – The story/task identifier from Jira (e.g., `AC-12`, `AC-15`)
- **`<Story Name>`** – A human-readable slug of the story title (kebab-case, max 50 chars)

**Examples:**
| Epic | Story | Story Name | Full Filename |
|------|-------|-----------|---------------|
| AC-10 | AC-12 | Vendor Search & Filter | `AC-10_AC-12_Vendor-Search-Filter.docx` |
| AC-10 | AC-13 | Role-Based Access Control | `AC-10_AC-13_Role-Based-Access-Control.docx` |
| SP-05 | SP-17 | Approval Workflow | `SP-05_SP-17_Approval-Workflow.docx` |

**Rules:**
1. Use underscores `_` to separate components (Epic, Story, Name)
2. Use hyphens `-` within the Story Name for word separation (kebab-case)
3. Remove special characters, spaces, and punctuation from the story name
4. The story name should be descriptive but concise
5. Always include the `.docx` file extension
6. Save the document in the `docs/Functional_Design_Docs/` directory

**File Location Example:**
```
docs/Functional_Design_Docs/AC-10_AC-12_Vendor-Search-Filter.docx
```

---

## Document Structure Template

### Cover Page / Document Header

```
# [Project Name] – Functional Design Document

![Cloud and Things Logo](../design/c-t-logo.png)

**Version:** [X.Y]  
**Date:** [YYYY-MM-DD]  
**Author:** [Business Analyst Name]  
**Status:** [Draft | Review | Approved | In Use]

---
```

### Table of Contents

Generate a complete ToC with all major sections and subsections:
- Automatically numbering all H2 and H3 headings
- Include page breaks or section links for navigation
- Example structure:
  ```
  1. Document Overview
  2. Functional Requirements
  3. User Stories & Use Cases
  4. User Interface / UX Design
  5. System Behavior
  6. Data Requirements & Integrations
  7. Assumptions & Constraints
  8. Acceptance Criteria
  9. Version History
  ```

---

## Version History

Track all document iterations with the following table:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | [YYYY-MM-DD] | [Name] | Initial draft – sections [X, Y, Z] |
| 0.2 | [YYYY-MM-DD] | [Name] | Incorporated stakeholder feedback on [topic] |
| 1.0 | [YYYY-MM-DD] | [Name] | Approved for development sprint |
| 1.1 | [YYYY-MM-DD] | [Name] | Clarified [section] per AC-feedback |

---

## 1. Document Overview

**Purpose of this section:** Establish the "why" and "who" for this feature or system.

- **Project Title:** [e.g., "Staff Procurement Portal"]
- **Feature/Module:** [e.g., "Vendor Management System"]
- **Business Goal(s):**
  - [Goal 1: e.g., "Enable Tier 1 & 2 procurement staff to efficiently search, filter, and assess vendor qualifications without manual spreadsheet lookups"]
  - [Goal 2: ...]
- **Target Audience / User Personas:**
  - [Persona 1: e.g., "Procurement Staff (L1 & L2)" – frequency of use, pain points]
  - [Persona 2: e.g., "Administrators" – governance & audit responsibilities]
  - [Persona 3: ...]
- **Scope:**
  - **In Scope:**
    - [Feature A]
    - [Feature B]
  - **Out of Scope:**
    - [Feature C – defer to Phase 2]
    - [Feature D – business decision pending]
- **Success Metrics / KPIs:**
  - [e.g., "Time-to-vendor-search reduced from 15 min (manual) to <2 min (system)"]
  - [e.g., "User adoption: 90% of procurement staff active within 60 days"]

---

## 2. Functional Requirements

**Purpose:** Detailed, behavior-driven specification of every system feature.

For each feature or workflow, provide:

### 2.1 [Feature Name]

**Description:**  
[1–3 sentences explaining what the feature does and its business value]

**Workflow Steps:**  
1. [User action or system trigger]
2. [System processes / validation]
3. [User sees result / system sends data]
4. [Success outcome]

**Inputs:**
- Field Name | Data Type | Required | Constraints | Example
- [e.g., "Vendor Name" | String | Yes | Max 100 chars, no special chars | "Acme Corp"]
- [e.g., "Search Query" | String | Yes | Min 2 chars | "office"]

**Outputs:**
- [e.g., "Vendor List" – array of matching records with fields: ID, Name, Category, Tier, Contact Info, Compliance Status]
- [e.g., "No Results Message" – if search yields 0 matches]

**Business Rules / Logic:**
- [e.g., "Only show vendors with active status (STATUS = 'ACTIVE')"]
- [e.g., "Rank results by procurement tier (L3 > L2 > L1)"]
- [e.g., "Apply role-based filtering: Staff L1 sees only non-sensitive vendor fields"]

**Data Processing:**
- [e.g., "Search is case-insensitive and tokenized"]
- [e.g., "Results are cached for 5 minutes to reduce database load"]

---

## 3. User Stories & Use Cases

**Purpose:** Illustrate real-world actor interactions with the system.

### 3.1 [Use Case / Epic Title]

**Actor:** [e.g., Procurement Staff L1]  
**Trigger:** [e.g., "User opens the Portal and clicks 'Find Vendor'"]

**Main Flow:**
1. User enters vendor name in search box
2. System validates input (min 2 chars)
3. System queries Oracle XE for matching vendors
4. System returns paginated results (25 per page)
5. User clicks a vendor to view full profile
6. System displays vendor details: contact, tier, certifications, compliance history
7. User selects "Request Approval" to initiate procurement workflow

**Alternative Flows:**
- **No Results Found:**
  - System displays: "No vendors found. Try a different search term."
  - User can refine search or contact admin.
- **Timeout:**
  - If search takes >10s, system displays: "Search taking longer than expected. Please try again."
  - User may cancel and retry.

**Acceptance Criteria (Gherkin Format):**
```gherkin
Given a procurement staff user is logged in
When they enter "Acme" in the vendor search box
Then the system displays vendors matching "Acme" within 2 seconds
And results show Vendor Name, Tier, and Contact
And results are sorted by Tier (descending)
```

---

## 4. User Interface / UX Design

**Purpose:** Define visual layout, navigation, and interaction patterns.

- **Screen List:** Enumerate all UI screens/pages with brief descriptions
  - Screen A: [e.g., "Login" – entry point, persona picker (dev only)]
  - Screen B: [e.g., "Vendor List" – search, filter, pagination]
  - Screen C: [e.g., "Vendor Detail" – full profile, action buttons]

- **Wireframes / Mockups:**
  - Reference HTML mockups in `docs/design/[screen-name].html`
  - Include annotations for interactive elements, error states, and responsive breakpoints

- **Navigation Flow:**
  - Diagram user journey from Login → Vendor Search → Vendor Detail → Approval Workflow
  - Indicate state transitions and routing rules

- **Design Tokens & Styling:**
  - Reference `docs/design/brand.md` for color palette, typography, spacing
  - All components follow Tailwind CSS utility conventions (live in `tailwind.config.js`)

- **Accessibility Requirements:**
  - WCAG 2.1 AA compliance minimum
  - Screen reader support: all interactive elements must have semantic HTML + ARIA labels
  - Keyboard navigation: all pages must be fully navigable via Tab, Enter, Escape keys
  - Color contrast: text ≥ 4.5:1 on light backgrounds

- **Responsive Design:**
  - Mobile (≤480px), Tablet (481–1024px), Desktop (≥1025px)
  - Touch-friendly button sizes: min 44×44px

---

## 5. System Behavior

**Purpose:** Define how the system handles edge cases, errors, alerts, and performance.

### 5.1 Error Handling

| Error Type | Trigger | User Message | System Action | Logging Level |
|---|---|---|---|---|
| Validation Error | Empty/invalid search input | "Search requires at least 2 characters" | Reject submission, focus input field | INFO |
| Timeout | API call exceeds 10s | "Search taking longer. Please try again." | Cancel request, offer retry | WARN |
| Database Unavailable | Oracle XE unreachable | "System temporarily unavailable. Try again in a few minutes." | Gracefully degrade, log incident | ERROR |
| Unauthorized Access | User role < required level | "Access Denied" + reason code | Redirect to `/access-denied`, log attempt | WARN |

### 5.2 Alert & Notification Triggers

- **Success Alerts:**
  - "Vendor approval request submitted" – appears for 5s, auto-dismisses
- **Warning Alerts:**
  - "Your session will expire in 5 minutes due to inactivity" – persists until user acts
- **Error Alerts:**
  - "Failed to load vendor list. Check your connection and try again." – user must dismiss
- **Email Notifications:**
  - Sent to staff when approval request is pending admin review
  - Sent to admin when new vendor request arrives

### 5.3 Performance Expectations

- **Page Load:** ≤2s to interactive (Largest Contentful Paint)
- **Search Latency:** ≤2s for typical queries (<100 results)
- **API Response Times:**
  - GET /api/vendors/search → ≤1.5s
  - GET /api/vendors/{id} → ≤500ms
  - POST /api/approvals → ≤1s
- **Caching:**
  - Vendor list cached 5 minutes client-side
  - Oracle query results cached 1 minute server-side
- **Concurrent Users:** System designed to handle 100+ simultaneous users without degradation

---

## 6. Data Requirements & Integrations

**Purpose:** Specify data models, validation rules, and external system connections.

### 6.1 Data Model

Reference `docs/DATA_MODEL.md` for complete schema. Summary:

**VENDORS Table**
| Column | Type | Required | Constraints | Sample Value |
|--------|------|----------|-------------|--------------|
| vendor_id | INT | Yes | PK | 12345 |
| vendor_name | VARCHAR(100) | Yes | Unique, case-insensitive | "Acme Corp" |
| tier_level | INT | Yes | 1–3 (L1=3, L2=2, L3=1) | 2 |
| status | VARCHAR(20) | Yes | 'ACTIVE', 'INACTIVE', 'PENDING' | "ACTIVE" |
| created_date | DATE | Yes | Auto-populated on INSERT | 2026-01-15 |

**APPROVALS Table**
| Column | Type | Required | Constraints | Sample Value |
|--------|------|----------|-------------|--------------|
| approval_id | INT | Yes | PK | 67890 |
| vendor_id | INT | Yes | FK → VENDORS | 12345 |
| requested_by | VARCHAR(50) | Yes | User email | "staff@example.com" |
| approval_status | VARCHAR(20) | Yes | 'PENDING', 'APPROVED', 'REJECTED' | "PENDING" |

### 6.2 Validation Rules

- **Vendor Name:**
  - Required, non-empty, max 100 characters
  - No leading/trailing whitespace
  - Allowed: alphanumeric, spaces, hyphens, apostrophes
  - Denied: special characters, SQL keywords
- **Tier Level:**
  - Must be an integer: 1, 2, or 3
  - Immutable after initial assignment (business rule)
- **Status:**
  - Enum: 'ACTIVE', 'INACTIVE', 'PENDING'
  - Default: 'PENDING' on creation
  - Transition rules: PENDING → ACTIVE (admin), ACTIVE → INACTIVE (admin only)

### 6.3 Integrations

**ID.me (OAuth 2.0 / OpenID Connect)**
- **Purpose:** User authentication and identity verification
- **Endpoint:** `https://idp.sandbox.id.me/authorize` (sandbox) → production redirects to `https://idp.id.me/authorize`
- **Response Fields:** `sub` (unique ID), `email`, `email_verified`, `given_name`, `family_name`
- **Callback URL:** `http://localhost:5173/verification/callback` (dev), `https://procure.example.com/verification/callback` (prod)
- **Error Handling:** If ID.me unreachable, display "Identity verification unavailable. Try again later."

**Oracle XE (SQL Database)**
- **Host:** `localhost:1521` (dev), RDS endpoint (prod)
- **Database:** `XEPDB1`
- **Connection:** Via `oracledb` Python driver (backend → Oracle)
- **Queries:**
  - SELECT vendors by search term, tier, status
  - INSERT vendor requests
  - UPDATE approval workflow state
- **Transaction Isolation:** Read Committed (default)

**JWT Token Management**
- **Token Format:** HS256-signed JWT issued by backend
- **Payload:**
  ```json
  {
    "sub": "user@example.com",
    "role": "STAFF|ADMIN",
    "procurement_level": 1|2|3,
    "exp": 1704067200
  }
  ```
- **Lifespan:** 8 hours
- **Storage:** HttpOnly, Secure cookie (dev uses non-secure for localhost)

---

## 7. Assumptions & Constraints

**Purpose:** Document technical limits, dependencies, and compliance requirements.

### 7.1 Technical Assumptions

- Users have modern browsers supporting ES2020+ (Chrome, Firefox, Safari, Edge)
- Backend services (FastAPI, Oracle) are accessible and healthy before user requests arrive
- Network latency is <500ms (typical for local/regional connections)
- Oracle XE is properly indexed on `vendor_name` and `status` columns

### 7.2 External Dependencies

- **ID.me Sandbox/Production:** Must remain operational for authentication
- **Oracle XE Container:** Must be running and seeded with test data
- **Nginx Reverse Proxy:** Routes `/api/*` to FastAPI and `/*` to Vite dev server (dev) or built React app (prod)
- **Email Service:** Required for approval notifications (not yet implemented; assumed available)

### 7.3 Constraints & Limitations

- **Browser Support:** IE11 not supported (uses ES2020 syntax)
- **Concurrent Users:** Tested up to 100; untested beyond that
- **Data Volume:** Vendor list limited to 10,000 records (performance expectations assume <100 search results)
- **Session Duration:** 8-hour expiration; no "remember me" functionality
- **Rate Limiting:** Not enforced (assumed controlled by firewall/WAF in production)

### 7.4 Regulatory & Compliance

- **Data Privacy (FERPA / State):** Procurement data is non-student PII; logs must not expose full email addresses in debug output
- **Accessibility (WCAG 2.1 AA):** All screens must pass automated + manual accessibility audits
- **Audit Trail:** All vendor approvals must log: who requested, when, what action, outcome (stored in `approval_audit` table)

---

## 8. Acceptance Criteria

**Purpose:** Define conditions and QA testing benchmarks for feature completion and sign-off.

### 8.1 Functional Acceptance Criteria

All criteria below must pass **and** be verified by QA before sign-off.

#### AC-1: Vendor Search

```gherkin
Given a logged-in Staff user is on the Vendor List page
When they enter "Acme" in the search box and press Enter
Then the system returns vendors matching "Acme" within 2 seconds
And displays Vendor Name, Tier Level, and Contact Email
And results are sorted by Tier (L3 → L2 → L1)
And the page shows "Results: X–Y of Z"
And pagination controls are visible for >25 results
```

#### AC-2: Role-Based Filtering

```gherkin
Given a Staff L1 user searches for vendors
Then the system filters to show only non-sensitive fields (excludes Contract History, Pricing)
And when an Admin searches
Then all fields are visible
```

#### AC-3: Error Handling – Empty Search

```gherkin
Given a user enters fewer than 2 characters in the search box
When they press Enter
Then the system displays "Search requires at least 2 characters"
And the search box retains focus
And no API call is made
```

#### AC-4: Timeout Handling

```gherkin
Given a search query takes >10 seconds to complete
When the timeout is reached
Then the system displays "Search taking longer. Please try again."
And the request is cancelled
And the user can immediately retry
```

### 8.2 Non-Functional Acceptance Criteria

#### AC-5: Performance

- Search latency: **≤2 seconds** for typical queries (95th percentile)
- Page load (Largest Contentful Paint): **≤2 seconds**
- API response times:
  - `GET /api/vendors/search` → **≤1.5s**
  - `GET /api/vendors/{id}` → **≤500ms**

#### AC-6: Accessibility (WCAG 2.1 AA)

- All form inputs have associated labels visible or via ARIA
- Button text is descriptive (no "Click Here")
- Color is not the only indicator of state (e.g., error text is red + has an icon)
- Text contrast ≥ 4.5:1 on light backgrounds
- Keyboard navigation: Tab order is logical, no keyboard traps

#### AC-7: Security

- All API endpoints require valid JWT token
- Unauthorized users (role mismatch) receive 403 Forbidden
- Passwords are never logged or included in error messages
- HTTPS enforced in production (mixed content warnings must not appear)

### 8.3 QA Test Plan Outline

| Scenario | Test Case | Expected Result | Status |
|----------|-----------|-----------------|--------|
| Happy Path | Search for existing vendor | Results returned in <2s, sorted by tier | ✓ |
| Empty Search | Enter <2 chars | Error message, no API call | ✓ |
| No Results | Search for non-existent vendor | "No vendors found" message | ✓ |
| Timeout | Simulate slow API | Timeout message after 10s | ✓ |
| Pagination | Click "Next" on 50 results | Display items 26–50 | ✓ |
| Mobile | View on iPhone 12 | Layout responsive, touch targets ≥44px | ✓ |
| Keyboard Nav | Tab through form | All interactive elements reachable | ✓ |
| Unauthorized | Access without valid JWT | Redirect to `/access-denied` | ✓ |

---

## Sign-Off & Approval

**Document Owner:** [Business Analyst Name]  
**Reviewed By:** [Architect Name, QC Lead]  
**Approved By:** [Product Owner / Tech Lead]  

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Business Analyst | | | |
| Architect | | | |
| QC Lead | | | |
| Product Owner | | | |

---

## Appendix: References

- **Data Model:** `docs/DATA_MODEL.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **AI Zones:** `docs/AI_ZONES.md`
- **Design Rationale:** `docs/design/DESIGN_RATIONALE.md`
- **Brand Guide:** `docs/design/brand.md`
- **UI Mockups:** `docs/design/` (HTML files)
- **ADRs (Architecture Decision Records):** `docs/adr/`
- **Project Issues:** [Jira/Linear project link]

---

**Document Status:** [Draft | Review | Approved | In Use]  
**Last Updated:** [YYYY-MM-DD]
