# PM-01: Weekly Project Status Report Template & Prompt

> **Purpose:** This prompt instructs the PM agent to produce a comprehensive weekly project status report in .docx format by querying Jira via the Atlassian MCP, reading local project documentation, generating data-driven charts, and assembling a polished Microsoft Word document.
>
> **Output:** A complete status report saved at `docs/PM_Reports/<MM>_<DD>_<YYYY>_Status_Report.docx` covering the past 7 days of activity. Generated every Monday morning. Includes sprint status, all Jira activity, blockers, decisions, ADRs, mandatory charts, and next-week plan. Designed for distribution to stakeholders.

---

## Document Naming Convention

All weekly project status reports must follow this strict naming convention to ensure consistency and traceability:

```
<MM>_<DD>_<YYYY>_Status_Report.docx
```

**Format Breakdown:**
- **`<MM>`** – Two-digit month of the report generation date, zero-padded (e.g., `05` for May, `12` for December)
- **`<DD>`** – Two-digit day of the report generation date, zero-padded (e.g., `01`, `19`, `31`)
- **`<YYYY>`** – Four-digit year of the report generation date (e.g., `2026`)
- **`_Status_Report`** – Fixed suffix (exactly this casing and spacing)
- **`.docx`** – Always Microsoft Word format; never `.doc`, `.pdf`, or other formats

**Examples:**

| Report Week Ending | Generated On (Monday) | Full Filename |
|---|---|---|
| Week of May 12–18, 2026 | 2026-05-19 | `05_19_2026_Status_Report.docx` |
| Week of May 19–25, 2026 | 2026-05-26 | `05_26_2026_Status_Report.docx` |
| Week of June 01–07, 2026 | 2026-06-02 | `06_02_2026_Status_Report.docx` |

**Rules:**

1. Always use **today's date** (the Monday on which the report is being generated), not the week-end date.
2. Zero-pad month and day — `05`, not `5`; `01`, not `1`.
3. Use underscores `_` as separators between all components; never use hyphens or spaces.
4. The fixed suffix must be exactly `_Status_Report` — no abbreviations or variations.
5. Always use the `.docx` file extension.
6. Save all reports in the `docs/PM_Reports/` directory. Create the directory if it does not exist.
7. Never overwrite an existing file — if a report with today's date already exists, append `_v2`, `_v3`, etc. to the filename before the `.docx` extension (e.g., `05_19_2026_Status_Report_v2.docx`).

**File Location Example:**

```
docs/PM_Reports/05_19_2026_Status_Report.docx
```

---

## Pre-Generation Steps (Agent Checklist)

Before the PM agent generates the report, it **must** execute the following steps in order. These steps gather all necessary data from local files and Jira.

### Step 1: Read Project Documentation

1a. Read `AI_CONTEXT.md` — extract:
   - Project name
   - Client name
   - Jira project key (usually `AC` for this project)
   - GitHub repository URL
   - Tech stack summary (framework, language, database, etc.)
   - Key integrations (ID.me, Oracle, etc.)

1b. Read `docs/requirements/REQUIREMENTS.md` — extract:
   - Business purpose (1–2 sentence summary)
   - In-scope items (list)
   - Out-of-scope items (list)
   - Stakeholders (list with roles)
   - Project goals and success metrics

1c. Read `docs/requirements/FUNCTIONAL_DESIGN.md` (first section only) — extract:
   - Executive summary sentence for use in the report's Project Brief section

### Step 2: Compute Report Dates

2a. Let `today` = the current date (should always be a Monday when this prompt is run)
2b. Let `report_start` = `today` minus 7 days (last Monday)
2c. Let `report_end` = `today` minus 1 day (yesterday, Sunday)
2d. Format both dates as `YYYY-MM-DD` for use in JQL queries and displayed in the report

**Example:**
```
Today (Monday):     2026-05-19
Report Start:       2026-05-12 (last Monday)
Report End:         2026-05-18 (yesterday)
Report Period:      May 12 – May 18, 2026
```

### Step 3: Execute Jira MCP Queries

3a–3e. Run each of the five Jira queries below via `mcp__atlassian__searchIssues`. Store all results. For each issue returned, **extract and store** the following fields (use Jira API field names as specified):

- `key` (e.g., `AC-22`)
- `summary` (story title)
- `status` (e.g., `Done`, `In Progress`, `To Do`)
- `assignee` (display name or "Unassigned")
- `customfield_10016` or `story_points` (story point estimate, may be `null`)
- `labels` (array of labels; look for zone labels: `green-zone`, `yellow-zone`, `red-zone`)
- `updated` (ISO 8601 timestamp)
- `created` (ISO 8601 timestamp)
- `priority` (e.g., `Highest`, `High`, `Medium`, `Low`)
- `sprint` (sprint object with name and date range; may be `null` if in backlog)

---

## Jira MCP Queries (Exact JQL)

Execute these five queries in order. Replace `<YYYY-MM-DD>` with the computed `report_start` date.

**Query 1: All activity this week** (feeds Section 3 — Jira Activity This Week)

```jql
project = AC AND updated >= -7d ORDER BY updated DESC
```

**MCP call:**
```
mcp__atlassian__searchIssues(jql="project = AC AND updated >= -7d ORDER BY updated DESC", maxResults=100)
```

**Query 2: Stories completed / moved to Done this week** (feeds Section 4 — Stories Completed)

```jql
project = AC AND status = Done AND updated >= -7d ORDER BY updated DESC
```

**MCP call:**
```
mcp__atlassian__searchIssues(jql="project = AC AND status = Done AND updated >= -7d ORDER BY updated DESC", maxResults=50)
```

**Query 3: Stories currently In Progress** (feeds Section 5 — Stories In Progress)

```jql
project = AC AND status = "In Progress" ORDER BY updated ASC
```

**MCP call:**
```
mcp__atlassian__searchIssues(jql='project = AC AND status = "In Progress" ORDER BY updated ASC', maxResults=50)
```

Note: `ORDER BY updated ASC` intentionally surfaces the oldest (potentially stuck) items first.

**Query 4: Backlog / Not Started stories** (feeds Section 6 — Backlog)

```jql
project = AC AND status in (Backlog, "To Do", "Selected for Development") AND sprint in openSprints() ORDER BY priority DESC, created ASC
```

**MCP call:**
```
mcp__atlassian__searchIssues(jql='project = AC AND status in (Backlog, "To Do", "Selected for Development") AND sprint in openSprints() ORDER BY priority DESC, created ASC', maxResults=100)
```

**Query 5: Blocked issues and impediments** (feeds Section 7 — Blockers & Risks)

```jql
project = AC AND (labels = impediment OR priority = Highest OR flagged = Impediment) AND status != Done ORDER BY priority DESC, updated DESC
```

**MCP call:**
```
mcp__atlassian__searchIssues(jql="project = AC AND (labels = impediment OR priority = Highest OR flagged = Impediment) AND status != Done ORDER BY priority DESC, updated DESC", maxResults=50)
```

### Step 4: Fetch Active Sprint Data

4a. Call `mcp__atlassian__getSprint()` (or use the sprint object embedded in Query 1 results) to extract:
   - Sprint name (e.g., `Sprint 5`)
   - Sprint goal (from the sprint's `goal` field)
   - Sprint start date (`startDate` in `YYYY-MM-DD` format)
   - Sprint end date (`endDate` in `YYYY-MM-DD` format)
   - Compute `days_remaining` = `endDate` minus today (if positive, sprint is active; if negative or zero, sprint has ended)

4b. From Query 1–4 results, compute:
   - Total issues in sprint: count of all issues with a sprint assigned and status not in (Backlog, To Do)
   - Story points committed: sum of `story_points` for all issues in active sprint
   - Story points completed: sum of `story_points` for all issues in active sprint with status = Done

4c. Compute velocity (optional, requires historical data):
   - If available, fetch the previous sprint via `mcp__atlassian__getSprint()` or a query for closed sprints: `project = AC AND status = Done AND sprint in closedSprints() ORDER BY updated DESC LIMIT 1`
   - Compute `previous_velocity` = sum of story points in the previous sprint's Done issues
   - Compute burn-down status: narrative text — "On track" (50% of days elapsed, 50% of points done), "Behind" (more days elapsed than points % done), or "Ahead" (fewer days elapsed than points % done)

---

## Step 5: Scan Local Documentation for Recent Changes

5a. Scan `docs/adr/` directory for all `*.md` files modified in the past 7 days (skip `README.md`):

```bash
find docs/adr -name "*.md" ! -name "README.md" -mtime -7
```

For each qualifying file:
   - Extract ADR ID from filename (e.g., `ADR-015` from `ADR-015-role-model-simplification.md`)
   - Extract title from the first H1 heading in the file
   - Extract Status from the metadata YAML front-matter (if present) or from a "Status" section
   - Extract Date from the metadata (if present)
   - Extract a one-sentence summary from the Decision section

Store as a list: `adrs_this_week = [{adr_id, title, status, date, summary}]`

5b. Scan `docs/decision-log/` directory for all `*.md` files modified in the past 7 days:

```bash
find docs/decision-log -name "*.md" -mtime -7
```

For each qualifying file:
   - Extract story ID from filename (e.g., `AC-12` from `AC-12-seed-staff.md`)
   - Extract decision title from the first H2 or H3 heading
   - Extract "Ratified on" date from a metadata table (if present)
   - Extract "Ratified by" field (PM agent name or title, if present)
   - Store path for reference

Store as a list: `decisions_this_week = [{story_id, title, ratified_date, ratified_by, path}]`

---

## Step 6: Compute Sprint Metrics

6a. From the collected data, calculate:
   - `total_story_points_committed` = sum of story points for all issues in active sprint
   - `total_story_points_done` = sum of story points for all issues in active sprint with status = Done
   - `total_story_points_remaining` = total committed minus total done
   - `story_count_done` = count of Done issues this week (Query 2)
   - `story_count_in_progress` = count of In Progress issues (Query 3)
   - `story_count_backlog` = count of Backlog/To Do issues in active sprint (Query 4)
   - `story_count_blocked` = count of issues in Query 5
   - `zone_green_count` = count of issues in Query 1 with label `green-zone`
   - `zone_yellow_count` = count of issues in Query 1 with label `yellow-zone`
   - `zone_red_count` = count of issues in Query 1 with label `red-zone`

6b. Identify In Progress issues at risk:
   - For each issue in Query 3, compute `age_days` = today minus issue's created date
   - Flag any issue with `age_days` > 5 as "at risk" (amber color in report)
   - Flag any issue with `age_days` > sprint length (typically 14 days) as "overdue" (red color, counted in blockers)

---

## Step 7: Prepare Data for Report Generation

7a. **PII Guard (Critical):** Before proceeding, scan all collected data for personally identifiable information (real names, employee IDs, email addresses, etc.). If any issue summary or description contains real PII:
   - **Do not copy the full summary into the report.**
   - Instead, render only the Jira issue key (e.g., `AC-22`) with a hyperlink to the full issue in Jira.
   - This is mandatory per the PM agent's "No real PII" rule and organization policy.

7b. All data is now ready to be passed to the Python script scaffold (see next section). Populate every placeholder variable in the script with real values collected from the above steps.

---

## Document Structure Template

### Cover Page / Document Header

The cover page must include the following elements in this order:

1. **Cloud and Things Logo** — top-center, width 150px
   - Primary path: `docs/design/assets/cnt-logo.png`
   - Fallback path: `docs/design/assets/CloudAndThingsv1transparent 1.png`
   - If neither exists, omit the logo and proceed with the title

2. **Title** — "Weekly Project Status Report"
   - Font: Inter Bold, 24pt
   - Color: C&T Blue `#3B4EA8`
   - Alignment: center

3. **Subtitle** — "Staff Procurement Portal"
   - Font: Inter Regular, 14pt
   - Color: Dark Grey `#1F2937`
   - Alignment: center

4. **Horizontal divider line**
   - Color: C&T Orange `#F47920`
   - Width: full page width

5. **Document metadata table** — no visible borders, two columns:

| Field | Value |
|---|---|
| Report Date | `<YYYY-MM-DD>` (today) |
| Report Period | `<YYYY-MM-DD>` (start) to `<YYYY-MM-DD>` (end) |
| Sprint | `<Sprint Name>` (e.g., "Sprint 5") |
| Prepared By | Cloud and Things Project Management Team |
| Client | Staff Procurement Portal |
| Jira Project | AC |
| Status | Final or Draft (agent chooses based on completeness) |

---

### Table of Contents

Insert a Word TOC field that auto-generates a hyperlinked table of contents for all H1 and H2 headings in the document. Use python-docx's `oxml` interface to insert the Word TOC field code. Add a note below the TOC:

> **Note:** If this document is opened in Microsoft Word, right-click the table of contents and select "Update Field" to refresh page numbers before distributing.

---

### Section 1: Project Brief / Executive Summary

**Source:** `AI_CONTEXT.md` + `docs/requirements/REQUIREMENTS.md` + `docs/requirements/FUNCTIONAL_DESIGN.md` §1

**Content to include:**

- **Project name:** (from `AI_CONTEXT.md`)
- **Client:** (from `AI_CONTEXT.md`)
- **Build type:** (from `AI_CONTEXT.md` — e.g., "Greenfield demo build")
- **GitHub repository:** (from `AI_CONTEXT.md`)
- **Purpose:** (1–2 sentences from `REQUIREMENTS.md` §1.1)
- **In-scope items:** (bulleted list from `REQUIREMENTS.md` §1.2)
- **Tech stack summary table:**
  | Component | Technology |
  |---|---|
  | Frontend | React 18 + React Router 6 + Zustand |
  | Backend | Python 3.11+ / FastAPI |
  | Database | Oracle XE 21c |
  | Authentication | JWT + ID.me OAuth 2.0 |
  | Infrastructure | AWS EC2 + Docker Compose |
  | CI/CD | GitHub Actions |

- **Team:** C&T Project Lead, C&T Tech Lead, C&T Developer, Business Analyst (Claude)
- **Sprint framework:** Agile / Scrum, Jira project AC

---

### Section 2: Sprint Status

**Source:** `mcp__atlassian__getSprint` + Queries 1–4

**Content to include:**

- **Sprint name:** (e.g., "Sprint 5")
- **Sprint goal:** (from sprint object)
- **Sprint start date:** `YYYY-MM-DD`
- **Sprint end date:** `YYYY-MM-DD`
- **Days remaining:** (computed as end date minus today)
- **Total stories committed:** (count from Query 1)
- **Story points committed:** (sum of story points in sprint)
- **Story points completed:** (sum of story points for Done issues)
- **Completion percentage:** `(points_done / points_committed) × 100%`
- **Velocity:** (story points completed this sprint vs. previous sprint — if data available, show as "X pts this sprint, Y pts last sprint")
- **Burn-down status:** Narrative text — "On track" / "Behind" / "Ahead" based on the ratio of elapsed days to completed story points

**Format:** Render this section as a mix of text paragraphs and a summary table.

---

### Section 3: Jira Activity This Week

**Source:** Query 1 results

**Content:** A table with the following columns and styling:

| Issue Key | Summary | Status | Assignee | Updated |
|---|---|---|---|---|
| AC-22 | [Summary truncated if >100 chars] | Done | Jane Doe | 2026-05-18 |
| AC-21 | [Summary] | In Progress | John Smith | 2026-05-17 |
| ... | ... | ... | ... | ... |

**Table styling:**
- Header row: background C&T Blue `#3B4EA8`, text white, bold font, 10pt
- Data rows: alternating white / Light Grey `#F5F6FA` backgrounds
- Status cells: color-coded based on status (see Styling Specification below)
- Borders: 1pt grey `#D1D5DB` on all cells
- Rows are sorted by Updated date descending (most recent first)
- All results from Query 1 (up to 100 issues)

---

### Section 4: Stories Completed (Done) This Week

**Source:** Query 2 results

**Content:** A richer table with the following columns:

| Issue Key | Summary | Story Points | Zone | Assignee | Closed Date |
|---|---|---|---|---|---|
| AC-20 | Login with ID.me | 8 | Red | Jane Doe | 2026-05-18 |
| AC-19 | Vendor Search API | 5 | Yellow | John Smith | 2026-05-17 |
| ... | ... | ... | ... | ... | ... |

**Table styling:**
- Header row: background C&T Blue `#3B4EA8`, white text, bold
- Data rows: alternating white / Light Grey
- Zone column: cells color-coded by zone (Green `#16A34A`, Yellow `#D97706`, Red `#DC2626`) with white text
- Summary row at the bottom: **Total story points completed this week: X**
- Sorted by Closed Date descending

---

### Section 5: Stories In Progress

**Source:** Query 3 results

**Content:** A table with the following columns:

| Issue Key | Summary | Story Points | Assignee | Age (days) | Blockers |
|---|---|---|---|---|---|
| AC-18 | Vendor List Frontend | 5 | Jane Doe | 2 | None |
| AC-17 | Oracle Lookup | 8 | John Smith | 7 | Yes (flagged) |
| ... | ... | ... | ... | ... | ... |

**Table styling:**
- Header row: C&T Blue background, white text, bold
- Data rows: alternating white / Light Grey
- Age column:
  - If age ≤ 5 days: plain text
  - If age > 5 days: background amber `#D97706`, white text (warning)
- Blockers column:
  - If issue appears in Query 5 results: **Yes (flagged)** in red `#DC2626`
  - Otherwise: **None** in plain text
- Sorted by Updated date ascending (oldest first — surfaces potentially stuck items)

---

### Section 6: Backlog / Not Started Stories

**Source:** Query 4 results

**Content:** A table grouped by sprint status:

**Sub-heading:** In Active Sprint — Not Started

| Issue Key | Summary | Story Points | Priority | Assignee |
|---|---|---|---|---|
| AC-16 | Access Denied Page | 3 | High | Unassigned |
| AC-15 | Session Timeout | 5 | Medium | Jane Doe |

**Sub-heading:** Product Backlog

| Issue Key | Summary | Story Points | Priority | Assignee |
|---|---|---|---|---|
| AC-14 | Admin Dashboard | 8 | Medium | Unassigned |
| AC-13 | Vendor Audit Trail | 5 | Low | John Smith |

**Table styling:**
- Headers: C&T Blue background, white text, bold
- Alternating rows: white / Light Grey
- Within each section, sort by Priority (High → Medium → Low), then by Created date (oldest first)
- Show up to 100 issues total

---

### Section 7: Blockers & Risks

**Source:** Query 5 results + any In Progress issues with age > sprint length

**Content:** Two parts:

**Part A — Blockers Table:**

| Issue Key | Summary | Blocker Type | Owner / Assignee | Days Stuck | Notes |
|---|---|---|---|---|---|
| AC-17 | Oracle Lookup | Flagged | John Smith | 7 | Awaiting API credentials from IT |
| AC-19 | Vendor Search API | Overdue | Jane Doe | 15 | In Progress for >2 sprints |

**Blocker types:**
- **Flagged** — issue has the `impediment` label or `flagged` field set
- **Overdue** — issue is In Progress and age > sprint length (14 days typical)
- **Dependency** — issue is blocked by another issue (extract from linked issues if available)

**Part B — Risk Narrative:**

A free-form paragraph (2–3 sentences) summarizing the top 2–3 risks based on the blockers found:

> "Oracle API credentials remain unavailable, blocking the Vendor Lookup feature. Additionally, the ID.me integration is experiencing intermittent timeouts in the sandbox environment. Both risks should be escalated to the IT team and client for immediate resolution."

If no blockers are found:
> "No blockers or impediments identified this week. All stories are progressing as planned."

---

### Section 8: Charts & Metrics

**Mandatory:** This section must always include all four charts. Charts are **always embedded as PNG images** — never fallback to text tables. The Python script must have `matplotlib.use('Agg')` to support headless environments (AWS EC2).

**Chart 1 — Burndown Chart**

- **Type:** Line chart
- **X-axis:** Sprint days (Day 1 to Day N)
- **Y-axis:** Story points remaining
- **Two lines:**
  - "Ideal burndown" (linear from total committed story points down to 0)
  - "Actual remaining" (story points remaining as of today)
- **Data source:** Computed from sprint totals
- **Note:** Full daily burndown history requires a historical snapshot. If only current-day data is available, the agent should note in the chart caption: "Note: Burndown calculated as of today; daily snapshots were not available."
- **File:** `status_burndown.png`

**Chart 2 — Status Distribution Pie Chart**

- **Type:** Pie / donut chart
- **Slices and counts:**
  - Done (green `#16A34A`)
  - In Progress (orange `#D97706`)
  - To Do / Backlog (grey `#6B7280`)
  - Blocked (red `#DC2626`)
- **Data source:** Issue counts from Queries 2, 3, 4, 5
- **File:** `status_distribution.png`

**Chart 3 — Velocity Bar Chart**

- **Type:** Horizontal or vertical bar chart
- **Bars:** One bar per sprint (current sprint + up to 3 previous sprints if data available)
- **Y-axis (if vertical):** Sprint names (e.g., Sprint 3, Sprint 4, Sprint 5)
- **X-axis:** Story points completed
- **Data source:** Sum of completed story points per sprint (from closed sprints and current sprint)
- **Note:** If only the current sprint has data, show a single bar with a note: "Insufficient historical data; showing current sprint only."
- **File:** `velocity_bar.png`

**Chart 4 — Zone Breakdown Bar Chart**

- **Type:** Horizontal bar chart showing count of issues per zone
- **Bars:**
  - Green Zone (from `green-zone` label count)
  - Yellow Zone (from `yellow-zone` label count)
  - Red Zone (from `red-zone` label count)
- **Y-axis:** Zone names
- **X-axis:** Issue count
- **Data source:** Labels from Query 1 results
- **Color coding:** Green `#16A34A`, Yellow `#D97706`, Red `#DC2626`
- **File:** `zone_breakdown.png`

**Embedding:** Use python-docx's `doc.add_picture(image_path, width=Inches(6))` to embed each PNG. If a PNG file is missing, the script must raise an error and terminate — do not skip the chart.

---

### Section 9: Decisions Made This Week

**Source:** `docs/decision-log/` files modified in the past 7 days

**Content:** A table with the following columns:

| Story ID | Decision Title | Ratified Date | Ratified By | File Path |
|---|---|---|---|---|
| AC-12 | Staff Lookup via Oracle | 2026-05-17 | PM Agent | docs/decision-log/AC-12-seed-staff.md |
| AC-13 | RBAC Simplification | 2026-05-16 | PM Agent | docs/decision-log/AC-13-access-service.md |

**Table styling:**
- Header row: C&T Blue background, white text, bold
- Alternating rows: white / Light Grey
- Sorted by Ratified Date descending (most recent first)

**If no decisions exist this week:**
> "No decisions were ratified this week."

---

### Section 10: ADRs Raised This Week

**Source:** `docs/adr/` files modified in the past 7 days

**Content:** A table with the following columns:

| ADR ID | Title | Status | Date | Summary |
|---|---|---|---|---|
| ADR-015 | Role Model Simplification | Accepted | 2026-05-19 | Simplified RBAC to 3 roles: Admin, Staff L1, Staff L2. |
| ADR-014 | Demo Persona Login | Accepted | 2026-05-10 | Dev-only persona picker for testing without ID.me. |

**Table styling:**
- Header row: C&T Blue background, white text, bold
- Alternating rows: white / Light Grey
- Status cells: color-coded (Accepted = green, Proposed = amber, Superseded = red)
- Sorted by Date descending

**If no ADRs exist this week:**
> "No ADRs were raised or updated this week."

---

### Section 11: Next Week Plan

**Source:** Query 3 (In Progress — rollover) + Query 4 (upcoming backlog)

**Content:** Three sub-sections:

**Sub-section A: Stories Carrying Forward**

> "The following stories are currently In Progress and will continue into next sprint:"

| Issue Key | Summary | Age (days) | Assignee |
|---|---|---|---|
| AC-18 | Vendor List Frontend | 2 | Jane Doe |
| AC-17 | Oracle Lookup | 7 | John Smith |

**Sub-section B: Upcoming Sprint Stories**

> "These stories are being proposed for next sprint, prioritized by priority:"

| Issue Key | Summary | Story Points | Priority | Assignee |
|---|---|---|---|---|
| AC-16 | Access Denied Page | 3 | High | Unassigned |
| AC-15 | Session Timeout | 5 | Medium | Jane Doe |

**Sub-section C: Planned Ceremonies**

> Standard Scrum ceremonies for the coming week:
> - **Sprint Review** — Friday, 2:00 PM EST (demo of completed stories)
> - **Retrospective** — Friday, 3:00 PM EST (team reflection)
> - **Sprint Planning** — Monday, 10:00 AM EST (next sprint scope)

**Sub-section D: Open Questions & Dependencies**

Free-form paragraph identifying any blockers, open decisions, or dependencies that may affect next week's progress:

> "The Oracle API credentials are still pending from IT. This blocks story AC-17 (Vendor Lookup). Additionally, ID.me sandbox access needs renewal — expiration is 2026-05-31. Recommend following up with both teams before sprint planning."

If no open items:
> "No critical dependencies or open questions identified for next sprint."

---

### Section 12: Version History

**Content:** A table tracking iterations of the report document itself:

| Version | Date | Generated By | Changes |
|---|---|---|---|
| 1.0 | 2026-05-19 | PM Agent (Claude) | Initial generation for week of May 12–18 |
| 1.1 | 2026-05-20 | PM Agent (Claude) | Corrected sprint points; updated blocker details |

**Rules:**
- First report version is always 1.0
- If the report is regenerated for the same week (because data was corrected or new issues added), increment to 1.1, 1.2, etc.
- If a new week's report is generated, start fresh at 1.0

---

## Styling Specification

Apply the following styles consistently throughout the document. All hex colour codes are from `docs/design/brand.md`.

### Document-Level Styling

| Element | Font | Size | Color | Notes |
|---|---|---|---|---|
| Default / Body text | Inter Regular | 11pt | `#1F2937` (Dark Grey) | Applies to all paragraph text unless overridden |
| H1 (Major sections) | Inter Bold | 18pt | `#3B4EA8` (C&T Blue) | Chapter headings |
| H2 (Sub-sections) | Inter Bold | 14pt | `#3B4EA8` (C&T Blue) | Section headings |
| H3 (Sub-sub-sections) | Inter Bold | 12pt | `#1F2937` (Dark Grey) | Tertiary headings |
| Page margins | — | — | — | 2.54 cm (1 inch) on all sides |
| Section divider | — | — | `#F47920` (C&T Orange) | Horizontal line between major sections |
| Line spacing | — | — | — | 1.15x (single space + 15% extra) |

### Table Styling

| Element | Style |
|---|---|
| Header row | Background `#3B4EA8`, text white, font bold 10pt, cell padding 0.1cm top/bottom, 0.2cm left/right |
| Data rows (odd) | Background white, text `#1F2937`, font regular 10pt |
| Data rows (even) | Background `#F5F6FA` (Light Grey), text `#1F2937`, font regular 10pt |
| Cell borders | 1pt solid `#D1D5DB` (Mid Grey) on all sides |
| Status cells | Color-coded per table below |
| Zone cells | Color-coded per zone label |

### Status Cell Colours

| Status | Background | Text Colour | Notes |
|---|---|---|---|
| Done | `#16A34A` (Success Green) | White | Story is completed |
| In Progress | `#D97706` (Warning Orange) | White | Story is being worked |
| To Do / Backlog | `#6B7280` (Neutral Grey) | White | Story is not started |
| Blocked | `#DC2626` (Danger Red) | White | Story is impedance |

### Zone Badge Colours

| Zone | Background | Text | Notes |
|---|---|---|---|
| Green Zone | `#16A34A` | White | Low risk, full autonomy |
| Yellow Zone | `#D97706` | White | Medium risk, draft-then-review |
| Red Zone | `#DC2626` | White | High risk, decision gate required |

### Priority Cell Colours (optional, for Backlog section)

| Priority | Background | Text | Notes |
|---|---|---|---|
| Highest | `#DC2626` | White | Critical blocker |
| High | `#F97316` | White | Urgent |
| Medium | `#F59E0B` | White | Normal |
| Low | `#D1D5DB` | `#1F2937` | Deferred |

### Special Formatting

- **Age > 5 days (In Progress):** Cell background `#D97706` (amber warning), white text, bold
- **Overdue (age > 14 days):** Cell background `#DC2626` (red danger), white text, bold
- **Hyperlinks:** C&T Blue `#3B4EA8`, underlined; issue keys like `AC-22` should be hyperlinked to `https://cloudandthings.atlassian.net/browse/AC-22` (if python-docx supports hyperlinks)
- **Emphasis:** Use bold for key metrics (story point totals, days remaining, blockers count)

---

## Python Script Scaffold

The PM agent must populate and execute the following Python script to generate the `.docx` report. This is a complete, runnable scaffold — the agent needs only to fill in the data variables (marked with `# AGENT: POPULATE` comments).

```python
#!/usr/bin/env python3
"""
generate_pm_status_report.py
Generates the weekly project status report for the Staff Procurement Portal.
Run: python3 generate_pm_status_report.py
Requires: python-docx, matplotlib, pillow
Install: pip install python-docx matplotlib pillow
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import matplotlib
matplotlib.use('Agg')  # CRITICAL: Headless backend for AWS EC2 / Docker
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ══════════════════════════════════════════════════════════════════════════════
# BRAND CONSTANTS (Hex → RGBColor)
# ══════════════════════════════════════════════════════════════════════════════
CT_BLUE   = RGBColor(0x3B, 0x4E, 0xA8)
CT_ORANGE = RGBColor(0xF4, 0x79, 0x20)
CT_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
CT_LGREY  = RGBColor(0xF5, 0xF6, 0xFA)
CT_DGREY  = RGBColor(0x1F, 0x29, 0x37)
CLR_DONE  = RGBColor(0x16, 0xA3, 0x4A)
CLR_WIP   = RGBColor(0xD9, 0x77, 0x06)
CLR_BLKD  = RGBColor(0xDC, 0x26, 0x26)
CLR_PEND  = RGBColor(0x6B, 0x72, 0x80)

# ══════════════════════════════════════════════════════════════════════════════
# FILE PATHS
# ══════════════════════════════════════════════════════════════════════════════
LOGO_PATHS = [
    Path("docs/design/assets/cnt-logo.png"),
    Path("docs/design/assets/CloudAndThingsv1transparent 1.png")
]
OUTPUT_DIR = Path("docs/PM_Reports")
CHART_DIR = Path("/tmp/pm_report_charts")

# ══════════════════════════════════════════════════════════════════════════════
# DATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════
today        = datetime.today()
report_start = today - timedelta(days=7)
report_end   = today - timedelta(days=1)
filename     = today.strftime("%m_%d_%Y") + "_Status_Report.docx"
output_path  = OUTPUT_DIR / filename

# ══════════════════════════════════════════════════════════════════════════════
# DATA VARIABLES
# AGENT: Populate these with real values from Jira MCP queries and local files
# ══════════════════════════════════════════════════════════════════════════════

sprint_data = {
    "name": "Sprint 5",  # AGENT: From mcp__atlassian__getSprint()
    "goal": "Complete vendor search and access control features",
    "start_date": "2026-05-12",
    "end_date": "2026-05-26",
    "days_remaining": 7,
    "total_issues": 12,
    "total_story_points_committed": 34,
    "total_story_points_done": 24,
    "previous_velocity": 21,
}

# AGENT: Populate from Query 1 results (all activity this week)
issues_this_week = [
    # {key, summary, status, assignee, story_points, labels, updated, priority}
]

# AGENT: Populate from Query 2 results (done this week)
issues_done = [
    # {key, summary, story_points, labels, assignee, updated}
]

# AGENT: Populate from Query 3 results (in progress)
issues_in_progress = [
    # {key, summary, story_points, assignee, created, labels, updated}
]

# AGENT: Populate from Query 4 results (backlog / to do)
issues_backlog = [
    # {key, summary, story_points, priority, assignee, created}
]

# AGENT: Populate from Query 5 results (blockers)
issues_blockers = [
    # {key, summary, assignee, labels, priority}
]

# AGENT: Populate by scanning docs/decision-log/
decisions_this_week = [
    # {story_id, title, ratified_date, ratified_by, path}
]

# AGENT: Populate by scanning docs/adr/
adrs_this_week = [
    # {adr_id, title, status, date, summary}
]

project_brief = {
    "project": "Staff Procurement Portal",
    "client": "Staff Procurement Portal",
    "build_type": "Greenfield demo build",
    "repo": "github.com/Cloud-and-Things/spp-procurement-portal",
    "purpose": "Enable procurement staff to access vendor information via a secure, role-based portal.",
    "tech_stack": {
        "frontend": "React 18 + React Router 6 + Zustand",
        "backend": "Python 3.11+ / FastAPI",
        "database": "Oracle XE 21c",
        "auth": "JWT + ID.me OAuth 2.0",
        "infra": "AWS EC2 + Docker Compose",
        "cicd": "GitHub Actions",
    },
    "team": "C&T Project Lead, C&T Tech Lead, C&T Developer, BA (Claude)",
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def set_cell_color(cell, rgb_color):
    """Set the background color of a table cell."""
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), '%02x%02x%02x' % (rgb_color[0], rgb_color[1], rgb_color[2]))
    cell._element.get_or_add_tcPr().append(shading_elm)

def add_styled_heading(doc, text, level=1, color=CT_BLUE):
    """Add a styled heading (H1, H2, H3)."""
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = color
    return heading

def add_styled_table(doc, headers, rows, header_color=CT_BLUE, alt_row_color=CT_LGREY):
    """Add a table with styled header and alternating rows."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    
    # Header row
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = str(header_text)
        set_cell_color(hdr_cells[i], header_color)
        for paragraph in hdr_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.color.rgb = CT_WHITE
                run.font.bold = True
                run.font.size = Pt(10)
    
    # Data rows
    for row_idx, row_data in enumerate(rows, start=1):
        row_cells = table.rows[row_idx].cells
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = str(cell_value) if cell_value else ""
            # Alternate row colors
            if row_idx % 2 == 0:
                set_cell_color(row_cells[col_idx], alt_row_color)
    
    return table

def status_color(status_str):
    """Return RGBColor for a given Jira status."""
    if status_str == "Done":
        return CLR_DONE
    elif status_str == "In Progress":
        return CLR_WIP
    elif status_str == "Blocked":
        return CLR_BLKD
    else:
        return CLR_PEND

def zone_color(labels):
    """Return RGBColor for zone from labels list."""
    if "red-zone" in labels:
        return CLR_BLKD
    elif "yellow-zone" in labels:
        return CLR_WIP
    elif "green-zone" in labels:
        return CLR_DONE
    else:
        return CLR_PEND

def generate_status_pie_chart(done, wip, todo, blocked):
    """Generate burndown-style line chart (placeholder: pie chart showing status)."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sizes = [done, wip, todo, blocked]
    labels = ['Done', 'In Progress', 'To Do', 'Blocked']
    colors = ['#16A34A', '#D97706', '#6B7280', '#DC2626']
    explode = (0.05, 0, 0, 0)
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
           shadow=True, startangle=90)
    ax.axis('equal')
    plt.title('Issue Status Distribution', fontsize=14, fontweight='bold', color='#3B4EA8')
    plt.tight_layout()
    chart_path = CHART_DIR / "status_distribution.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    return chart_path

def generate_velocity_bar_chart(sprint_labels, sprint_points):
    """Generate velocity bar chart."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(sprint_labels, sprint_points, color='#3B4EA8')
    ax.set_xlabel('Story Points Completed', fontsize=11, fontweight='bold')
    ax.set_ylabel('Sprint', fontsize=11, fontweight='bold')
    ax.set_title('Sprint Velocity', fontsize=14, fontweight='bold', color='#3B4EA8')
    for i, v in enumerate(sprint_points):
        ax.text(v + 0.5, i, str(v), va='center', fontweight='bold')
    plt.tight_layout()
    chart_path = CHART_DIR / "velocity_bar.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    return chart_path

def generate_zone_breakdown_chart(green, yellow, red):
    """Generate zone distribution bar chart."""
    fig, ax = plt.subplots(figsize=(10, 6))
    zones = ['Green Zone', 'Yellow Zone', 'Red Zone']
    counts = [green, yellow, red]
    colors = ['#16A34A', '#D97706', '#DC2626']
    ax.bar(zones, counts, color=colors)
    ax.set_ylabel('Issue Count', fontsize=11, fontweight='bold')
    ax.set_title('Issues by Risk Zone', fontsize=14, fontweight='bold', color='#3B4EA8')
    for i, v in enumerate(counts):
        ax.text(i, v + 0.2, str(v), ha='center', fontweight='bold')
    plt.tight_layout()
    chart_path = CHART_DIR / "zone_breakdown.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    return chart_path

def generate_burndown_chart(days_elapsed, days_total, points_ideal_remaining, points_actual_remaining):
    """Generate sprint burndown chart."""
    fig, ax = plt.subplots(figsize=(10, 6))
    days = list(range(1, days_elapsed + 2))
    # Ideal line (linear from total to 0)
    total_points = points_ideal_remaining[0] if points_ideal_remaining else 1
    ideal = [total_points * (1 - i/days_total) for i in days]
    # Actual line
    actual = points_actual_remaining if points_actual_remaining else ideal
    
    ax.plot(days, ideal, 'o-', label='Ideal Burndown', linewidth=2, color='#D1D5DB')
    ax.plot(days, actual, 's-', label='Actual Remaining', linewidth=2, color='#3B4EA8')
    ax.set_xlabel('Sprint Day', fontsize=11, fontweight='bold')
    ax.set_ylabel('Story Points Remaining', fontsize=11, fontweight='bold')
    ax.set_title('Sprint Burndown', fontsize=14, fontweight='bold', color='#3B4EA8')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    chart_path = CHART_DIR / "status_burndown.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    return chart_path

def embed_chart(doc, chart_path, caption):
    """Embed a PNG chart into the document. Raises error if file missing."""
    if not chart_path.exists():
        raise FileNotFoundError(f"Chart not found: {chart_path}")
    doc.add_picture(str(chart_path), width=Inches(6))
    caption_para = doc.add_paragraph(caption, style='Caption')
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return True

# ══════════════════════════════════════════════════════════════════════════════
# SECTION BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def add_cover_page(doc):
    """Build the cover page."""
    # Try to add logo
    logo_found = False
    for logo_path in LOGO_PATHS:
        if logo_path.exists():
            doc.add_picture(str(logo_path), width=Inches(1.5))
            logo_found = True
            break
    
    # Title
    title = doc.add_paragraph()
    title_run = title.add_run("Weekly Project Status Report")
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = CT_BLUE
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Subtitle
    subtitle = doc.add_paragraph()
    subtitle_run = subtitle.add_run("Staff Procurement Portal")
    subtitle_run.font.size = Pt(14)
    subtitle_run.font.color.rgb = CT_DGREY
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Divider
    divider = doc.add_paragraph()
    divider_format = divider.paragraph_format
    divider_format.space_before = Pt(12)
    divider_format.space_after = Pt(12)
    pPr = divider._element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '24')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'F47920')
    pBdr.append(bottom)
    pPr.append(pBdr)
    
    # Info table
    doc.add_paragraph()
    info_table = doc.add_table(rows=7, cols=2)
    info_table.autofit = False
    
    info_data = [
        ("Report Date", today.strftime("%Y-%m-%d")),
        ("Report Period", f"{report_start.strftime('%Y-%m-%d')} to {report_end.strftime('%Y-%m-%d')}"),
        ("Sprint", sprint_data.get("name", "N/A")),
        ("Prepared By", "Cloud and Things Project Management Team"),
        ("Client", project_brief["client"]),
        ("Jira Project", "AC"),
        ("Status", "Final"),
    ]
    
    for i, (label, value) in enumerate(info_data):
        cells = info_table.rows[i].cells
        cells[0].text = label
        cells[1].text = value
    
    doc.add_page_break()

def add_project_brief(doc):
    """Section 1: Project Brief / Executive Summary."""
    add_styled_heading(doc, "1. Project Brief / Executive Summary")
    
    brief_para = doc.add_paragraph(f"{project_brief['project']} is a {project_brief['build_type']} built by Cloud and Things for {project_brief['client']}. The system enables procurement staff to access vendor information securely via role-based access controls.")
    brief_para.paragraph_format.space_after = Pt(12)
    
    doc.add_heading("Tech Stack", level=3)
    tech_table = doc.add_table(rows=1 + len(project_brief["tech_stack"]), cols=2)
    tech_table.style = 'Light Grid Accent 1'
    tech_headers = tech_table.rows[0].cells
    tech_headers[0].text = "Component"
    tech_headers[1].text = "Technology"
    
    for i, (component, tech) in enumerate(project_brief["tech_stack"].items(), start=1):
        cells = tech_table.rows[i].cells
        cells[0].text = component.title()
        cells[1].text = tech
    
    doc.add_paragraph()

def add_sprint_status(doc):
    """Section 2: Sprint Status."""
    add_styled_heading(doc, "2. Sprint Status")
    
    sprint = sprint_data
    days_remaining = (datetime.strptime(sprint["end_date"], "%Y-%m-%d") - today).days
    completion_pct = (sprint["total_story_points_done"] / sprint["total_story_points_committed"] * 100) if sprint["total_story_points_committed"] > 0 else 0
    
    status_para = doc.add_paragraph()
    status_para.add_run(f"Sprint {sprint['name']}").bold = True
    status_para.add_run(f" ({sprint['start_date']} to {sprint['end_date']}) — {days_remaining} days remaining\n")
    status_para.add_run(f"Goal: {sprint['goal']}\n")
    status_para.add_run(f"Story Points: {sprint['total_story_points_committed']} committed, {sprint['total_story_points_done']} completed ({completion_pct:.0f}%)\n")
    status_para.add_run(f"Velocity: {sprint['total_story_points_done']} pts this sprint, {sprint['previous_velocity']} pts previous sprint")
    
    doc.add_paragraph()

def add_jira_activity(doc):
    """Section 3: Jira Activity This Week."""
    add_styled_heading(doc, "3. Jira Activity This Week")
    
    if not issues_this_week:
        doc.add_paragraph("No issues updated this week.")
        return
    
    headers = ["Issue Key", "Summary", "Status", "Assignee", "Updated"]
    rows = [[issue['key'], issue['summary'][:80], issue['status'], issue.get('assignee', 'Unassigned'), issue['updated'][:10]] for issue in issues_this_week]
    add_styled_table(doc, headers, rows)
    doc.add_paragraph()

def add_stories_done(doc):
    """Section 4: Stories Completed."""
    add_styled_heading(doc, "4. Stories Completed (Done) This Week")
    
    if not issues_done:
        doc.add_paragraph("No stories completed this week.")
        return
    
    headers = ["Issue Key", "Summary", "Story Points", "Assignee"]
    rows = [[issue['key'], issue['summary'][:80], str(issue.get('story_points', 0)), issue.get('assignee', 'Unassigned')] for issue in issues_done]
    add_styled_table(doc, headers, rows)
    
    total_points = sum([issue.get('story_points', 0) for issue in issues_done])
    summary = doc.add_paragraph()
    summary.add_run(f"Total story points completed this week: {total_points}").bold = True
    doc.add_paragraph()

def add_stories_in_progress(doc):
    """Section 5: Stories In Progress."""
    add_styled_heading(doc, "5. Stories In Progress")
    
    if not issues_in_progress:
        doc.add_paragraph("No stories in progress.")
        return
    
    headers = ["Issue Key", "Summary", "Story Points", "Assignee", "Age (days)"]
    rows = []
    for issue in issues_in_progress:
        age = (today - datetime.strptime(issue['created'], "%Y-%m-%dT%H:%M:%S.%fZ")).days if 'T' in issue['created'] else 0
        rows.append([
            issue['key'],
            issue['summary'][:80],
            str(issue.get('story_points', 0)),
            issue.get('assignee', 'Unassigned'),
            str(age)
        ])
    add_styled_table(doc, headers, rows)
    doc.add_paragraph()

def add_stories_backlog(doc):
    """Section 6: Backlog / Not Started."""
    add_styled_heading(doc, "6. Backlog / Not Started")
    
    if not issues_backlog:
        doc.add_paragraph("No backlog items.")
        return
    
    headers = ["Issue Key", "Summary", "Story Points", "Priority", "Assignee"]
    rows = [[issue['key'], issue['summary'][:80], str(issue.get('story_points', 0)), issue.get('priority', 'N/A'), issue.get('assignee', 'Unassigned')] for issue in issues_backlog[:10]]
    add_styled_table(doc, headers, rows)
    doc.add_paragraph()

def add_blockers(doc):
    """Section 7: Blockers & Risks."""
    add_styled_heading(doc, "7. Blockers & Risks")
    
    if not issues_blockers:
        doc.add_paragraph("No blockers or impediments identified this week.")
        return
    
    headers = ["Issue Key", "Summary", "Assignee", "Priority"]
    rows = [[issue['key'], issue['summary'][:80], issue.get('assignee', 'Unassigned'), issue.get('priority', 'N/A')] for issue in issues_blockers]
    add_styled_table(doc, headers, rows)
    
    risk_para = doc.add_paragraph()
    risk_para.add_run("Risk Narrative: ").bold = True
    risk_para.add_run(f"{len(issues_blockers)} blockers identified this week requiring attention. See table above for details.")
    doc.add_paragraph()

def add_charts(doc):
    """Section 8: Charts & Metrics."""
    add_styled_heading(doc, "8. Charts & Metrics")
    
    # Generate all charts
    chart_burndown = generate_burndown_chart(
        days_elapsed=min(7, (today - datetime.strptime(sprint_data['start_date'], "%Y-%m-%d")).days),
        days_total=14,
        points_ideal_remaining=[sprint_data['total_story_points_committed']],
        points_actual_remaining=[sprint_data['total_story_points_remaining']]
    )
    
    done_count = len(issues_done)
    wip_count = len(issues_in_progress)
    todo_count = len(issues_backlog)
    blocked_count = len(issues_blockers)
    chart_status = generate_status_pie_chart(done_count, wip_count, todo_count, blocked_count)
    
    chart_velocity = generate_velocity_bar_chart(
        ['Current Sprint'],
        [sprint_data['total_story_points_done']]
    )
    
    green_count = sum(1 for issue in issues_this_week if 'green-zone' in issue.get('labels', []))
    yellow_count = sum(1 for issue in issues_this_week if 'yellow-zone' in issue.get('labels', []))
    red_count = sum(1 for issue in issues_this_week if 'red-zone' in issue.get('labels', []))
    chart_zone = generate_zone_breakdown_chart(green_count, yellow_count, red_count)
    
    # Embed charts
    embed_chart(doc, chart_burndown, "Figure 1: Sprint Burndown (Ideal vs. Actual)")
    doc.add_paragraph()
    
    embed_chart(doc, chart_status, "Figure 2: Issue Status Distribution")
    doc.add_paragraph()
    
    embed_chart(doc, chart_velocity, "Figure 3: Sprint Velocity")
    doc.add_paragraph()
    
    embed_chart(doc, chart_zone, "Figure 4: Issues by Risk Zone")
    doc.add_paragraph()

def add_decisions(doc):
    """Section 9: Decisions Made This Week."""
    add_styled_heading(doc, "9. Decisions Made This Week")
    
    if not decisions_this_week:
        doc.add_paragraph("No decisions were ratified this week.")
        return
    
    headers = ["Story ID", "Decision Title", "Ratified Date", "Ratified By"]
    rows = [[d['story_id'], d['title'], d.get('ratified_date', 'N/A'), d.get('ratified_by', 'N/A')] for d in decisions_this_week]
    add_styled_table(doc, headers, rows)
    doc.add_paragraph()

def add_adrs(doc):
    """Section 10: ADRs Raised This Week."""
    add_styled_heading(doc, "10. ADRs Raised This Week")
    
    if not adrs_this_week:
        doc.add_paragraph("No ADRs were raised or updated this week.")
        return
    
    headers = ["ADR ID", "Title", "Status", "Date", "Summary"]
    rows = [[adr['adr_id'], adr['title'], adr.get('status', 'N/A'), adr.get('date', 'N/A'), adr.get('summary', '')[:80]] for adr in adrs_this_week]
    add_styled_table(doc, headers, rows)
    doc.add_paragraph()

def add_next_week_plan(doc):
    """Section 11: Next Week Plan."""
    add_styled_heading(doc, "11. Next Week Plan")
    
    doc.add_heading("Stories Carrying Forward", level=3)
    if issues_in_progress:
        rows = [[issue['key'], issue['summary'][:80], issue.get('assignee', 'Unassigned')] for issue in issues_in_progress[:5]]
        add_styled_table(doc, ["Issue Key", "Summary", "Assignee"], rows)
    else:
        doc.add_paragraph("No in-progress stories to carry forward.")
    
    doc.add_heading("Upcoming Sprint Stories", level=3)
    if issues_backlog:
        rows = [[issue['key'], issue['summary'][:80], str(issue.get('story_points', 0)), issue.get('priority', 'N/A')] for issue in issues_backlog[:5]]
        add_styled_table(doc, ["Issue Key", "Summary", "Story Points", "Priority"], rows)
    else:
        doc.add_paragraph("No backlog items queued for next sprint.")
    
    doc.add_heading("Planned Ceremonies", level=3)
    ceremonies = doc.add_paragraph()
    ceremonies.add_run("Sprint Review — Friday, 2:00 PM EST\n")
    ceremonies.add_run("Retrospective — Friday, 3:00 PM EST\n")
    ceremonies.add_run("Sprint Planning — Monday, 10:00 AM EST\n")
    
    doc.add_paragraph()

def add_version_history(doc):
    """Section 12: Version History."""
    add_styled_heading(doc, "12. Version History")
    
    headers = ["Version", "Date", "Generated By", "Changes"]
    rows = [["1.0", today.strftime("%Y-%m-%d"), "PM Agent (Claude)", "Initial generation"]]
    add_styled_table(doc, headers, rows)
    doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"Generating status report for {today.strftime('%Y-%m-%d')}...")
    
    # Create directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create document
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    
    # Build document sections
    add_cover_page(doc)
    add_project_brief(doc)
    add_sprint_status(doc)
    add_jira_activity(doc)
    add_stories_done(doc)
    add_stories_in_progress(doc)
    add_stories_backlog(doc)
    add_blockers(doc)
    add_charts(doc)
    add_decisions(doc)
    add_adrs(doc)
    add_next_week_plan(doc)
    add_version_history(doc)
    
    # Save
    doc.save(str(output_path))
    print(f"✓ Report saved: {output_path}")
    print(f"✓ Sections: 12/12")
    print(f"✓ Charts: 4/4 (embedded)")

```

---

## Agent Step-by-Step Execution Checklist

The PM agent must execute the following steps **in order** each time this prompt is invoked:

1. ✅ Read `AI_CONTEXT.md` and extract project metadata (project name, client, Jira key, repo, stack)
2. ✅ Read `docs/requirements/REQUIREMENTS.md` and extract business purpose, stakeholders, scope
3. ✅ Read `docs/requirements/FUNCTIONAL_DESIGN.md` (§1 only) for executive summary
4. ✅ Compute `today`, `report_start` (today minus 7 days), `report_end` (today minus 1 day)
5. ✅ Run JQL Query 1 via `mcp__atlassian__searchIssues` — store all results
6. ✅ Run JQL Query 2 via `mcp__atlassian__searchIssues` — store all results
7. ✅ Run JQL Query 3 via `mcp__atlassian__searchIssues` — store all results
8. ✅ Run JQL Query 4 via `mcp__atlassian__searchIssues` — store all results
9. ✅ Run JQL Query 5 via `mcp__atlassian__searchIssues` — store all results
10. ✅ Fetch active sprint via `mcp__atlassian__getSprint` or from Query 1 results
11. ✅ Scan `docs/adr/` for files modified in the past 7 days — extract metadata from each
12. ✅ Scan `docs/decision-log/` for files modified in the past 7 days — extract metadata from each
13. ✅ Compute all sprint metrics (story-point totals, velocity, days remaining, burn-down status)
14. ✅ **PII Guard Check:** Scan all collected data for real names, employee IDs, email addresses. If found, redact from the report — use only Jira issue keys.
15. ✅ Populate all placeholder variables in the Python script with real data
16. ✅ Run the script: `python3 docs/PM_Reports/generate_pm_status_report.py` (or inline it as a temporary file and run)
17. ✅ Verify the `.docx` was created at `docs/PM_Reports/<MM>_<DD>_<YYYY>_Status_Report.docx`
18. ✅ Verify the .docx opens without errors
19. ✅ Print a summary message: "✓ Report generated: `<path>` — Sections: 12/12 — Charts: 4/4 (embedded)"
20. ✅ Do **NOT** push to Jira, update any issue, or modify any files unless explicitly instructed

---

## References

- **Project Context:** `AI_CONTEXT.md`
- **Requirements:** `docs/requirements/REQUIREMENTS.md`
- **Functional Design:** `docs/requirements/FUNCTIONAL_DESIGN.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Data Model:** `docs/DATA_MODEL.md`
- **Brand Guide:** `docs/design/brand.md`
- **Logo (primary):** `docs/design/assets/cnt-logo.png`
- **Logo (fallback):** `docs/design/assets/CloudAndThingsv1transparent 1.png`
- **ADRs:** `docs/adr/`
- **Decision Log:** `docs/decision-log/`
- **Jira Project:** https://cloudandthings.atlassian.net/projects/AC
- **PM Agent Definition:** `.claude/agents/pm.md`
- **BA-03 (style reference):** `prompts/BA-03-functional-design.md`
- **DEV-01 (style reference):** `prompts/DEV-01-unit-test.md`

---

**Document Status:** Active — Generated every Monday morning  
**Last Updated:** 2026-05-19
