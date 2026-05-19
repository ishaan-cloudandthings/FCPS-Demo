# Prompt 02 — Resume a User Story

## When to use
When you are mid-way through a user story and need to continue in a new Claude session.
Use this instead of starting from scratch — it re-establishes the project context and
picks up where you left off without repeating the full onboarding.

## How to use
1. Open a new Claude session.
2. Copy everything below the `---` line.
3. Fill in all four placeholders: `[USER STORY]`, `[COMPLETED SO FAR]`,
   `[WHAT REMAINS]`, and `[BLOCKERS OR DECISIONS NEEDED]`.
4. Attach or paste any files already written if you want Claude to review them.
5. Send it.

---

You are a full stack developer resuming work on a user story mid-session for the
Staff Procurement Portal. Before continuing, read the following files to re-establish
project context:

1. `AI_CONTEXT.md` — tech stack, folder structure, naming conventions, patterns,
   and anti-patterns.
2. `AI_ZONES.md` — confidence zone map. Governs what can be generated and what
   must be human-authored.
3. `docs/ARCHITECTURE.md` — system architecture, component breakdown, and ADRs.
4. `docs/DATA_MODEL.md` — canonical Oracle data model and entity definitions.

We are working on this user story:

---
[USER STORY]
---

Here is what has been completed so far:

---
[COMPLETED SO FAR — list files created, decisions made, and any deviations from the
original plan and the reason for them]
---

Here is what still needs to be done:

---
[WHAT REMAINS — list remaining files or steps from the implementation plan]
---

Any blockers or decisions that need to be resolved before continuing:

---
[BLOCKERS OR DECISIONS NEEDED — or write "none" if there are none]
---

Review the completed work against the project context files, then continue with what
remains. Apply the same rules as if this were a fresh session — naming conventions,
zone compliance, layering rules, and Oracle query conventions.

If you spot any issues in the completed work while reviewing it, flag them before
proceeding rather than building on top of a problem.
