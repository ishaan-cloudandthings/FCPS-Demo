# CLAUDE.md

> **Read `AI_CONTEXT.md` first.** This file is a thin wrapper for Claude Code. All project context
> lives in `AI_CONTEXT.md`. Update context there — not here.

---

## Project Context

See [`AI_CONTEXT.md`](./AI_CONTEXT.md) for:

- Tech stack (React + FastAPI + Oracle XE + ID.me + AWS EC2)
- Folder structure and naming conventions
- Patterns to follow and anti-patterns to avoid
- Key business domains and integrations

---

## Claude Code Flags

**`docs/` is reference-only.**
Do not modify `ARCHITECTURE.md` or `DATA_MODEL.md` without an explicit instruction to do so.
These are specification artefacts — read them, don't change them.

**Confidence zones apply.**
Before generating code, check `AI_ZONES.md` to confirm the zone for the file or module being
worked on:
- 🔴 Red (`backend/app/auth/`, ID.me callback, JWT handling) — surface every decision as
  explicit questions and wait for human confirmation on each one before generating any code.
- 🟡 Yellow (`backend/app/services/`, API handlers, Oracle lookup, Docker, Nginx, CI/CD) —
  draft code for the developer to meaningfully edit. Flag any logic that requires a human decision.
- 🟢 Green (schemas, seed scripts, tests, components, utilities) — write fully. Developer
  reviews for correctness.

**No credentials in responses.**
Never generate code with hardcoded API keys, secrets, or credentials. Always reference
environment variables as defined in `.env.example`.

**Ask before refactoring across modules.**
Multi-file refactors touching more than one domain should be confirmed before execution.
