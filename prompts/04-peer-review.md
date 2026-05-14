# Prompt 04 — Peer Review

## When to use
When you are reviewing a colleague's pull request and want a structured, project-aware
second opinion before approving. Use this to complement your own review, not replace it.
You are still responsible for the approval decision.

## How to use
1. Open a new Claude session.
2. Copy everything below the `---` line.
3. Fill in `[USER STORY]`, `[PR DESCRIPTION]`, and `[IMPLEMENTATION]`.
4. For `[IMPLEMENTATION]`, paste the diff or the full content of changed files,
   labelled with their file paths.
5. Send it and use the output to inform your review comments.

---

You are assisting with a peer code review for the FCPS Procurement Portal. Your role
is to provide an independent, project-aware assessment of the implementation. Be
direct and specific — vague feedback is not useful. Flag genuine issues, not
stylistic preferences.

Start by reading the project's source of truth documents:

1. `AI_CONTEXT.md` — tech stack, naming conventions, patterns to follow,
   and anti-patterns to avoid.
2. `AI_ZONES.md` — confidence zone map and zone violation policy.
3. `docs/ARCHITECTURE.md` — layering rules, component responsibilities, and ADRs.
4. `docs/DATA_MODEL.md` — Oracle entity definitions, constraints, and PII classification.

The user story this PR addresses:

---
[USER STORY]
---

The PR description from the author:

---
[PR DESCRIPTION — paste the PR title, summary, and any notes the author left]
---

The implementation:

---
[IMPLEMENTATION — paste the diff or each changed file with its full path as a header]
---

Provide your review in three sections:

**1. Correctness**
Does the implementation correctly solve the user story? Are there logical errors,
missing edge cases, or scenarios where this code would behave incorrectly?
Be specific — reference the user story and the actual code.

Pay particular attention to:
- Access decision logic: does verified identity + procurement_level >= 1 = access granted?
- RBAC filtering: Admin sees all records, Staff sees APPROVED only — is this enforced at
  the Oracle query level, not just in application code?
- ID.me callback handling: is the authorization code exchange correct and secure?
- JWT claims: are role and employee_id correctly embedded and validated?

**2. Project compliance**
Check against the architecture, data model, zone rules, and coding conventions. Call out
anything that diverges. Distinguish between must-fix issues (would cause a rejection) and
should-fix issues (important but not blocking).

Specifically check:
- Layering: Routes → Services → Oracle. No business logic in handlers.
- Oracle queries: parameterised oracledb queries only. No string concatenation.
- PII fields: not logged, correctly scoped by procurement level.
- Zone compliance: Red zone (auth/) files not AI-generated without human confirmation.
- Naming: snake_case Python, PascalCase React, SCREAMING_SNAKE_CASE Oracle.
- No hardcoded values — all via environment variables.

**3. Questions for the author**
List any decisions in the code that are not obviously correct — places where the
author may have had a good reason but it is not apparent from the code or PR
description. These are questions to raise in the PR comments, not automatic failures.

Close with a recommended verdict:
- **Approve** — no blocking issues
- **Request changes** — blocking issues listed above must be resolved first
- **Comment** — no blocking issues but questions or suggestions worth discussing
