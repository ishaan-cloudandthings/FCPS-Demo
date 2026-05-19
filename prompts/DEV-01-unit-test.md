# DEV-01: Unit Test Plan (UTP) Spreadsheet Template & Prompt

> **Purpose:** This prompt guides Developers in creating a comprehensive Unit Test Plan spreadsheet that documents all test cases, preconditions, dependencies, test steps, expected results, and execution status for a given user story.
>
> **Output:** A complete UTP spreadsheet (.xlsx) saved at `docs/Unit_test_Docs/` following the naming convention `<Epic num>_<Story Num>_UTP_<Story_Name>.xlsx` that serves as the test execution artefact for QA, developers, and stakeholders.

---

## Document Naming Convention

All Unit Test Plan spreadsheets must follow this strict naming convention to ensure consistency and traceability:

```
<Epic num>_<Story Num>_UTP_<Story_Name>.xlsx
```

**Format Breakdown:**
- **`<Epic num>`** – The epic number from Jira (e.g., `AC-10`, `SP-05`)
- **`<Story Num>`** – The story/task number from Jira (e.g., `AC-12`, `AC-15`)
- **`UTP`** – Unit Test Plan (fixed prefix)
- **`<Story_Name>`** – A human-readable slug of the story title (PascalCase, max 50 chars)

**Examples:**
| Epic | Story | Story Name | Full Filename |
|------|-------|-----------|---------------|
| AC-10 | AC-12 | VendorSearchFilter | `AC-10_AC-12_UTP_VendorSearchFilter.xlsx` |
| AC-10 | AC-13 | RoleBasedAccessControl | `AC-10_AC-13_UTP_RoleBasedAccessControl.xlsx` |
| SP-05 | SP-17 | ApprovalWorkflow | `SP-05_SP-17_UTP_ApprovalWorkflow.xlsx` |

**Rules:**
1. Use underscores `_` to separate components (Epic, Story, UTP, Name)
2. Use PascalCase for the story name (no hyphens or spaces)
3. Remove special characters and punctuation from the story name
4. Always include the `.xlsx` file extension
5. Save the spreadsheet in the `docs/Unit_test_Docs/` directory

**File Location Example:**
```
docs/Unit_test_Docs/AC-10_AC-12_UTP_VendorSearchFilter.xlsx
```

---

## Spreadsheet Structure & Layout

### Sheet 1: Cover Page / Document Header

Create a title section at the top of the spreadsheet with the following information:

```
┌─────────────────────────────────────────────────────────┐
│  [Cloud and Things Logo - embedded or linked image]    │
├─────────────────────────────────────────────────────────┤
│  UNIT TEST PLAN                                        │
│  <Project Name> – <Feature/Module Name>               │
├─────────────────────────────────────────────────────────┤
│  Epic ID:              [AC-10]                          │
│  Story ID:             [AC-12]                          │
│  Story Title:          [Vendor Search & Filter]         │
│  Version:              [X.Y]                            │
│  Date Created:         [YYYY-MM-DD]                     │
│  Test Executed By:     [Developer/QA Name]             │
│  Test Executed Date:   [YYYY-MM-DD]                     │
│  Status:               [Draft | In Review | Ready]      │
└─────────────────────────────────────────────────────────┘
```

**Styling:**
- Use header cells with bold text and light gray background
- Include the C&T logo at the top (embedded image or URL reference)
- Leave adequate white space for readability
- Use consistent fonts (recommended: Arial, 11pt for body, 14pt for headers)

---

### Version History Section

Include a version tracking table below the document header:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | [YYYY-MM-DD] | [Name] | Initial test plan draft |
| 0.2 | [YYYY-MM-DD] | [Name] | Added edge case tests |
| 1.0 | [YYYY-MM-DD] | [Name] | Approved for execution |
| 1.1 | [YYYY-MM-DD] | [Name] | Updated post-execution notes |

**Columns:**
- **Version** – Semantic versioning (0.1, 1.0, 1.1, etc.)
- **Date** – Date of version update
- **Author** – Name of person making changes
- **Changes** – Brief description of what changed

---

### Precondition & Dependencies Section

Before the test cases table, include sections for setup information:

```
PRECONDITION
┌─────────────────────────────────────────────────────────┐
│ • User is logged in with valid credentials              │
│ • Oracle XE database is running and seeded with data    │
│ • Backend FastAPI server is running on localhost:8000   │
│ • Frontend Vite dev server is running on localhost:5173 │
│ • Network connectivity to ID.me sandbox is available    │
└─────────────────────────────────────────────────────────┘

DEPENDENCIES
┌─────────────────────────────────────────────────────────┐
│ • AC-10_AC-11_UTP_UserAuthentication.xlsx (must pass)  │
│ • Oracle VENDORS table populated with test data         │
│ • ID.me sandbox credentials configured in .env          │
│ • Nginx reverse proxy configured (dev mode)             │
└─────────────────────────────────────────────────────────┘

ENVIRONMENT DETAILS
┌─────────────────────────────────────────────────────────┐
│ • Browser: Chrome/Firefox (latest version)              │
│ • OS: macOS/Linux/Windows                               │
│ • Python Version: 3.11+                                 │
│ • Node Version: 16+                                     │
│ • Test Framework: Pytest (backend), Jest (frontend)     │
└─────────────────────────────────────────────────────────┘
```

---

### Test Cases Table (Main Content)

Create a detailed table with the following columns. Use **Sheet 1** for the header info and **Sheet 2** (or same sheet below header) for the test cases table:

#### Column Definitions

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| **Test Case#** | Integer | Yes | Unique test case identifier (TC-001, TC-002, etc.) | TC-001 |
| **Test Title** | String | Yes | Concise, descriptive title of the test | "Search with valid vendor name" |
| **Test Summary** | String | Yes | 1–2 sentence overview of what is being tested | "Verifies that vendor search returns matching results when user enters a valid vendor name" |
| **Test Steps** | String (multi-line) | Yes | Numbered steps to execute the test (1. 2. 3. ... format) | See detailed example below |
| **Test Data** | String | Yes | Input data needed for the test (values, payloads, etc.) | "Search term: 'Acme'" |
| **Expected Results** | String | Yes | What should happen after test execution | "System displays vendors matching 'Acme' within 2 seconds, sorted by tier" |
| **Actual Results** | String | No | What actually happened (filled during execution) | "✓ Vendors displayed in <1.5s, correctly sorted" |
| **Test Status** | Enum | No | Result of test execution | Pass / Fail / Blocked / Not Executed |
| **Notes** | String | No | Additional observations, defects, or comments | "Test executed on Chrome 120. Minor UI delay on first load." |
| **Precondition** | String | No | Specific setup needed for this test | "User must be logged in with Staff L1 role" |
| **Dependencies** | String | No | Other test cases or resources this test depends on | "Depends on: TC-001 (successful login)" |

---

## Detailed Test Case Examples

### Example 1: Happy Path Test

```
Test Case#:     TC-001
Test Title:     Search for existing vendor with valid input
Test Summary:   Verifies that vendor search returns matching results 
                when user enters a valid vendor name with minimum 
                2 characters.

Test Steps:
1. Navigate to the Vendor List page
2. Locate the search input field
3. Enter "Acme" in the search box
4. Click the "Search" button (or press Enter)
5. Wait for results to load
6. Verify results are displayed
7. Verify results are sorted by tier (L3 → L2 → L1)
8. Verify pagination controls are visible if >25 results

Test Data:
- Search Term: "Acme"
- Expected Result Count: 3–5 vendors
- User Role: Staff L1

Expected Results:
- Results returned within 2 seconds
- Vendors matching "Acme" displayed in table
- Each row shows: Vendor Name, Tier, Contact Email
- Results sorted by Tier (descending: L3 → L2 → L1)
- Pagination shows "Results: X–Y of Z"
- No error messages displayed

Precondition:
- User is logged in with valid Staff L1 credentials
- Oracle database is seeded with test vendor data

Dependencies:
- AC-10_AC-10_UTP_UserAuthentication.xlsx must pass (login test)
```

---

### Example 2: Negative Test (Error Handling)

```
Test Case#:     TC-003
Test Title:     Search with insufficient input characters
Test Summary:   Verifies that the system rejects search queries with 
                fewer than 2 characters and displays appropriate error.

Test Steps:
1. Navigate to the Vendor List page
2. Enter "A" (single character) in the search box
3. Click the "Search" button
4. Observe system response
5. Verify no API call is made
6. Verify error message is displayed

Test Data:
- Search Term: "A" (1 character)
- User Role: Staff L1

Expected Results:
- Error message: "Search requires at least 2 characters"
- Search box retains focus (for accessibility)
- No vendor results displayed
- No API call to /api/vendors/search endpoint
- Error message persists until user clears input

Precondition:
- User is logged in with valid credentials

Dependencies:
- None (independent test)
```

---

### Example 3: Integration Test

```
Test Case#:     TC-008
Test Title:     Role-based vendor filtering for Staff L1
Test Summary:   Verifies that Staff L1 users see only non-sensitive 
                fields and cannot access restricted data.

Test Steps:
1. Log in as Staff L1 user (use dev persona picker)
2. Navigate to Vendor List page
3. Search for a vendor with sensitive data (e.g., "Acme")
4. Click on vendor detail to open profile
5. Verify sensitive fields are hidden or masked
6. Check that visible fields match L1 permissions
7. Attempt to access restricted field via API (Chrome DevTools)
8. Verify 403 Forbidden response

Test Data:
- User: staff-l1@example.com (dev persona)
- Vendor: ID 12345 (Acme Corp with contracts & pricing)
- API Endpoint: GET /api/vendors/12345

Expected Results:
- Visible Fields (L1 can see): Name, Tier, Contact, Compliance Status
- Hidden Fields (L1 cannot see): Contract History, Pricing, Internal Notes
- API call returns only permitted fields
- Attempt to access restricted field returns 403 status
- No console errors or security warnings

Precondition:
- User is logged in as Staff L1
- Vendor record exists with sensitive data

Dependencies:
- AC-10_AC-10_UTP_RoleBasedAccessControl.xlsx (RBAC setup)
- Test data must include vendors with contracts
```

---

## Spreadsheet Formatting & Styling

### Cell Formatting

**Header Row (Row 1):**
- Background Color: Dark Blue (#003366) or corporate C&T color
- Text Color: White
- Font: Bold Arial 11pt
- Row Height: 25px

**Cover Page Section (Rows 1–20):**
- Merge cells as needed for title and logo
- Use light gray (#F0F0F0) background for label cells
- Use white background for value cells
- Font: Arial 11pt (regular for values, bold for labels)

**Test Cases Table Header (Row with column titles):**
- Background Color: Light Gray (#E0E0E0) or corporate secondary color
- Font: Bold Arial 11pt
- Borders: 1pt black border on all sides

**Test Cases Data Rows:**
- Alternating row colors: White and light blue (#F5F5F5) for readability
- Font: Arial 10pt
- Borders: 1pt gray border on all sides
- Word wrap enabled for multi-line cells (Test Steps, Test Data, etc.)
- Minimum row height: 30px (adjust as needed for content)

**Status Column Color Coding:**
- **Pass** – Green background (#90EE90) with black text
- **Fail** – Red background (#FF6B6B) with white text
- **Blocked** – Yellow background (#FFD700) with black text
- **Not Executed** – Gray background (#CCCCCC) with black text

### Column Widths

| Column | Width |
|--------|-------|
| Test Case# | 12 |
| Test Title | 25 |
| Test Summary | 35 |
| Test Steps | 45 |
| Test Data | 20 |
| Expected Results | 35 |
| Actual Results | 35 |
| Test Status | 12 |
| Notes | 25 |
| Precondition | 30 |
| Dependencies | 30 |

---

## Spreadsheet Organization

### Single Sheet Layout (Recommended for smaller test plans)

```
Rows 1–3:    Cloud & Things Logo (merged cells)
Rows 4–8:    Document Header (Epic, Story, Version, etc.)
Rows 9–12:   Version History Table
Rows 13–16:  Precondition & Dependencies Sections
Row 17:      (Blank separator)
Row 18:      Test Cases Table Header (column titles)
Rows 19+:    Test Cases (data rows)
```

### Multiple Sheet Layout (Recommended for larger test plans)

**Sheet 1: Cover & Metadata**
- Logo, title, version history, preconditions, dependencies

**Sheet 2: Test Cases (Happy Path)**
- All positive test cases (TC-001 to TC-005)

**Sheet 3: Test Cases (Negative/Edge Cases)**
- All error handling and boundary tests (TC-006 to TC-012)

**Sheet 4: Test Cases (Integration)**
- All integration and role-based tests (TC-013+)

**Sheet 5: Test Summary/Dashboard**
- Summary statistics: Total Tests, Passed, Failed, Blocked, Pass Rate %

---

## Test Summary / Dashboard (Optional Sheet)

For larger test plans, create a summary sheet with:

```
UNIT TEST EXECUTION SUMMARY
┌─────────────────────────────────────────────────────────┐
│ Epic ID:                 AC-10                          │
│ Story ID:                AC-12                          │
│ Story Title:             Vendor Search & Filter         │
│ Test Executed By:        [Name]                         │
│ Test Executed Date:      [YYYY-MM-DD]                   │
│ Total Test Cases:        12                             │
│ Passed:                  11 (91.7%)                      │
│ Failed:                  1  (8.3%)                       │
│ Blocked:                 0  (0%)                         │
│ Not Executed:            0  (0%)                         │
│ Overall Status:          ⚠️  CONDITIONAL PASS           │
│ Failed Tests:            TC-008 (Timeout edge case)     │
└─────────────────────────────────────────────────────────┘

CHARTS (Optional):
- Pie Chart: Test Result Distribution (Pass/Fail/Blocked)
- Bar Chart: Test Count by Category (Happy Path, Negative, Integration)
- Timeline: Test Execution Progress
```

---

## Test Data Management

### Test Data Best Practices

1. **Seed Data Location:** Reference data in `backend/scripts/seed_test_data.sql`
2. **Test User Accounts:**
   - Staff L1: `staff-l1@example.com` / password: `DevTestPass123`
   - Staff L2: `staff-l2@example.com` / password: `DevTestPass123`
   - Admin: `admin@example.com` / password: `DevTestPass123`
3. **Test Vendors:** Use IDs 10001–10010 (reserved for testing, never in production)
4. **Isolation:** Each test should clean up after itself (DELETE test records, reset state)

### Test Data Table (Optional Separate Sheet)

| Variable Name | Data Type | Sample Value | Purpose |
|---------------|-----------|--------------|---------|
| VENDOR_NAME | String | "Acme Corp" | Used in search tests |
| VENDOR_ID | Integer | 10001 | Used in detail/update tests |
| SEARCH_TERM_SHORT | String | "A" | Edge case: 1 char (should fail) |
| USER_STAFF_L1 | String | "staff-l1@example.com" | Role-based filtering test |
| USER_ADMIN | String | "admin@example.com" | Admin-only operations test |

---

## Execution Instructions

### Before Test Execution

1. **Verify Preconditions:**
   - [ ] All services running (FastAPI, Oracle, Vite)
   - [ ] Test database seeded with sample data
   - [ ] Test user accounts created
   - [ ] Network connectivity verified

2. **Prepare Spreadsheet:**
   - [ ] Open UTP spreadsheet in Excel/Google Sheets
   - [ ] Clear any "Actual Results" from previous runs
   - [ ] Reset "Test Status" column to blank
   - [ ] Verify "Test Executed By" name is current

3. **Set Up Environment:**
   - [ ] Browser dev tools open (F12) for API/console monitoring
   - [ ] Terminal open to monitor backend logs
   - [ ] Fresh browser session (clear cache)

### During Test Execution

1. **Execute Each Test Case:**
   - Follow test steps exactly as written
   - Record actual results in "Actual Results" column
   - Take screenshots of unexpected behavior
   - Note timing if performance-critical

2. **Update Test Status:**
   - Mark **Pass** if actual results match expected
   - Mark **Fail** if any deviation occurs
   - Mark **Blocked** if preconditions not met
   - Mark **Not Executed** if test was skipped

3. **Document Issues:**
   - If **Fail**, note the exact discrepancy in "Notes" column
   - Include error messages, stack traces, timing data
   - Create linked Jira bug if critical
   - Link to screenshot attachment (if applicable)

### After Test Execution

1. **Review & Sign-Off:**
   - [ ] Re-verify all failed tests (rule out false failures)
   - [ ] Calculate overall pass rate
   - [ ] Update "Test Executed Date" to today
   - [ ] Add summary notes to cover page

2. **Archive & Report:**
   - [ ] Save spreadsheet with final results
   - [ ] Export summary to stakeholders
   - [ ] Update Jira story with test results
   - [ ] Move UTP to completed tests folder (if using version control)

---

## Sign-Off & Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer (Test Author) | | | |
| QA Lead (Reviewer) | | | |
| Tech Lead (Approver) | | | |

---

## References

- **Story Details:** [Link to Jira story]
- **Functional Design:** `docs/requirements/FUNCTIONAL_DESIGN.md`
- **API Specification:** `docs/api/openapi.yaml`
- **Test Framework Docs:** Pytest & Jest documentation
- **Test Data:** `backend/scripts/seed_test_data.sql`
- **Related UTPs:** [Link to dependent test plans]

---

**Document Status:** [Draft | Ready for Execution | Execution In Progress | Complete]  
**Last Updated:** [YYYY-MM-DD]
