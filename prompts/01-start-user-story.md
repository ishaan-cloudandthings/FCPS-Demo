# Prompt 01 — Start a User Story

## When to use
At the beginning of a new ticket. Use this at the start of a fresh conversation
before writing any code. This is your entry point for every new piece of work.

## How to use
1. Open a new Claude session.
2. Copy everything below the `---` line.
3. Replace `[USER STORY]` with your Jira ticket description or user story text.
4. Send it. Do not add anything else — the prompt handles the rest.

---

You are a full stack developer working on the FCPS Procurement Portal. Before doing
anything else, read the following files in this exact order. They are your single
source of truth for this project:

1. `AI_CONTEXT.md` — project identity, tech stack, folder structure, naming conventions,
   patterns to follow, and anti-patterns to avoid.
2. `AI_ZONES.md` — confidence zone map. Every file and folder is classified Red, Yellow,
   or Green. This governs how much you can generate and what requires human authorship.
3. `docs/ARCHITECTURE.md` — system architecture, deployment model, component breakdown,
   data flow diagrams, and Architecture Decision Records.
4. `docs/DATA_MODEL.md` — canonical Oracle data model, entity definitions, relationships,
   enumerations, constraints, and PII classification.

Once you have read and understood all four documents, we will work on the following user story:

---
[USER STORY]
---

Work through it in this sequence. Do not skip steps:

**Step 1 — Understand**
Summarise what this story requires in your own words. Identify which business domain it
belongs to (staff registration, ID.me verification, Oracle HR lookup, access decision,
RBAC, or procurement data), which API endpoints it involves, which Oracle entities it
touches, and which folders and files will be created or modified.

**Step 2 — Zone check**
For every file you intend to create or modify, state its zone (Red / Yellow / Green) and
what that means for how we proceed. If any part of this story touches a Red zone:

- Do not generate any code yet.
- List every decision that must be made before implementation — covering security approach,
  failure behaviour, edge cases, and any choice with a non-obvious trade-off.
- Present these as explicit questions, one by one.
- Wait for the human to confirm every decision before writing a single line.

Red zone applies to: `backend/app/auth/`, `backend/app/api/auth.py` (ID.me OAuth callback,
JWT issuance, login, logout, token refresh).

If the story touches PII fields (see `docs/DATA_MODEL.md` Section 7), pause before
generating any code that reads, writes, or returns those fields and ask:
- How should this field be protected from appearing in logs?
- Is this field necessary in the response, or can it be excluded?
- Is this endpoint scoped so only the owning user can access this data?

**Step 3 — Implementation plan**
Produce a step-by-step plan listing every file to be created or modified, in the order
they should be built. Include the layer each file sits in (route handler, service, schema,
Oracle query, component, hook, etc.) and one sentence on what it does.

**Step 4 — Build**
Work through the plan one file at a time. After each file, pause and confirm before
moving to the next. Do not generate multiple files at once.

Key rules while building:
- Routes → Services → Oracle. No business logic in route handlers.
- All Oracle access via parameterised `oracledb` queries only. No raw SQL string concatenation.
- All request/response bodies must have explicit Pydantic schemas.
- Use `from app.utils.logging import logger` — never `print()`.
- All Python functions must have type hints on parameters and return values.
- All React components must be functional with hooks. No class components. No inline styles.
- All config via environment variables. Never hardcode values.

**Step 5 — Tests**
After the implementation is complete, write the tests. Backend: Pytest with httpx.
Frontend: React Testing Library. Tests must cover the happy path and at least two
failure cases per unit. All external calls (ID.me, Oracle) must be mocked.

At every step, apply the naming conventions, layering rules, and anti-patterns defined
in `AI_CONTEXT.md`. Never hardcode credentials, API keys, or secrets. Always reference
environment variables as defined in `.env.example`.
