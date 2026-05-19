# Prompt 03 — Validate Before PR

## When to use
When you believe a user story is complete and are about to raise a pull request.
Run this before opening the PR — not after. It is your final self-check.

## How to use
1. Open a new Claude session. Do not use the same session you built in — a fresh
   context gives a more honest review.
2. Copy everything below the `---` line.
3. Fill in `[USER STORY]` and `[IMPLEMENTATION]`.
4. For `[IMPLEMENTATION]`, paste the full content of every file you created or
   modified, clearly labelled with the file path.
5. Send it. Do not ask Claude to fix anything in the same message — let it
   complete the review first.

---

You are conducting a pre-PR validation of a completed user story implementation
for the Staff Procurement Portal. Your role is reviewer, not author. Be thorough
and direct — flag everything that would cause a rejection or introduce a bug, no
matter how small.

Start by reading the project's source of truth documents:

1. `AI_CONTEXT.md` — tech stack, naming conventions, patterns to follow,
   anti-patterns to avoid.
2. `AI_ZONES.md` — confidence zone map. A zone misclassification is an automatic
   rejection regardless of code quality.
3. `docs/ARCHITECTURE.md` — layering rules, component responsibilities, data flows,
   and Architecture Decision Records.
4. `docs/DATA_MODEL.md` — Oracle entity definitions, constraints, and PII classification.

The user story being validated:

---
[USER STORY]
---

The implementation to review:

---
[IMPLEMENTATION — paste each file with its full path as a header, e.g.
### backend/app/api/staff.py
(file contents here)

### backend/app/services/oracle_service.py
(file contents here)
]
---

Review against every item in this checklist. For each item, state Pass, Fail, or
Not Applicable with a brief explanation:

**Architecture**
- [ ] No business logic in route handlers — all logic is in the service layer
- [ ] No direct Oracle queries from route handlers — always through the service layer
- [ ] Layering is correct: Routes → Services → Oracle
- [ ] All FastAPI dependencies injected via `Depends()`, not instantiated inline

**Architecture conformance**
- [ ] Every endpoint is consistent with the component breakdown in `docs/ARCHITECTURE.md`
- [ ] Auth flow (if touched) follows the ID.me → Oracle → JWT sequence from Section 7.1
- [ ] RBAC filtering matches the role/access rules in Section 8.2
- [ ] Any new ADR-worthy decision has been flagged for documentation

**Data model conformance**
- [ ] All Oracle interactions use the tables and columns defined in `docs/DATA_MODEL.md`
- [ ] No columns, tables, or relationships invented that are not in the data model
- [ ] Oracle constraints and enumerations are respected (CHK_ROLE, CHK_STATUS, etc.)
- [ ] All Oracle queries use parameterised `oracledb` queries — no raw SQL concatenation

**Zone compliance**
- [ ] Every file is correctly classified against `AI_ZONES.md`
- [ ] For any Red zone file: confirm that all decisions were explicitly surfaced as
      questions and confirmed by the human before code was generated. If no decision
      log exists, this is a failure.
- [ ] Yellow zone code is a draft suitable for meaningful developer editing, not final
- [ ] For any code touching PII fields: confirm that logging protection, response
      scoping, and access control decisions were explicitly confirmed before generation

**Code quality**
- [ ] All Python functions have type hints on parameters and return values
- [ ] Naming follows project conventions (snake_case Python, PascalCase React, kebab-case routes,
      SCREAMING_SNAKE_CASE Oracle tables/columns)
- [ ] No hardcoded credentials, API keys, secrets, or environment-specific values
- [ ] No `print()` statements — structured logger (`from app.utils.logging import logger`) used
- [ ] No raw SQL string concatenation — parameterised oracledb queries only
- [ ] No inline styles in JSX
- [ ] No class-based React components

**PII handling**
- [ ] PII fields (EMPLOYEE_ID, FULL_NAME, EMAIL, CONTACT_NAME, CONTACT_EMAIL, BANK_DETAILS)
      do not appear in log statements
- [ ] PII is not returned in list-level API responses where it should be excluded
- [ ] CONTACT_NAME/CONTACT_EMAIL only returned for PROCUREMENT_LEVEL >= 2
- [ ] BANK_DETAILS only returned for PROCUREMENT_LEVEL = 3 (Admin)
- [ ] Any new PII fields are identified and classified

**Tests**
- [ ] Tests exist for every new function or component
- [ ] Happy path covered
- [ ] At least two failure or edge cases covered per unit
- [ ] Tests do not call real external services — ID.me and Oracle calls are mocked

**Summary**
After completing the checklist, provide a summary verdict:
- **PASS** — ready to PR with no changes required
- **PASS WITH NOTES** — ready to PR but minor improvements recommended
- **FAIL** — changes required before this PR should be raised

List every Fail item with the specific file, line or section, and what needs to change.
