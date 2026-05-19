# Prompt 05 — Production Incident

## When to use
When something is broken in the live environment and you need to diagnose and resolve
it quickly. This prompt is time-pressured — it prioritises finding the cause and a
safe fix over perfect code. A follow-up ticket for cleanup is expected.

## How to use
1. Open a new Claude session.
2. Copy everything below the `---` line.
3. Fill in all placeholders as completely as you can — the more context you provide,
   the faster the diagnosis. If you don't have something, write "unknown".
4. Send it. Answer Claude's follow-up questions before asking it to suggest a fix.

---

You are helping diagnose and resolve a production incident on the Staff Procurement
Portal. The priority is to identify the root cause and recommend the safest fix as
quickly as possible. Clean code is secondary to a safe, targeted resolution.

Start by reading the project's source of truth documents to understand the system:

1. `AI_CONTEXT.md` — tech stack, folder structure, and key integrations.
2. `docs/ARCHITECTURE.md` — system architecture, component breakdown, data flows,
   and ADRs. Pay particular attention to Section 7 (Key Data Flow Scenarios) and
   Section 8 (Security Architecture).
3. `docs/DATA_MODEL.md` — Oracle entity definitions and relationships.

Then work through the incident using the information below.

**Environment where the incident is occurring:**

---
[ENVIRONMENT — e.g. production EC2, staging]
---

**What should be happening (expected behaviour):**

---
[EXPECTED BEHAVIOUR]
---

**What is actually happening (observed behaviour):**

---
[OBSERVED BEHAVIOUR]
---

**Error messages, stack traces, or log output:**

---
[ERRORS / LOGS — paste in full, do not summarise]
---

**When did this start? Was anything deployed or changed recently?**

---
[TIMELINE AND RECENT CHANGES]
---

**What has already been tried:**

---
[ATTEMPTED FIXES — or "nothing yet"]
---

**Relevant code (if known):**

---
[CODE — paste any files or functions you suspect are involved, with their file paths]
---

Work through the diagnosis in this order:

1. **Identify the failure point** — based on the error and the system architecture,
   which component is failing and at which layer (Nginx, FastAPI, Oracle, ID.me callback,
   JWT validation, RBAC filter).

2. **Hypothesise root causes** — list the most likely causes in order of probability.
   For each, explain what evidence supports it. Common failure points to consider:
   - Oracle XE container not running or connection pool exhausted
   - ID.me OAuth state mismatch or token expiry
   - JWT secret mismatch or algorithm misconfiguration
   - Nginx proxy misconfiguration dropping the Authorization header or cookie
   - RBAC filter returning wrong data set for a role
   - oracledb thin mode connection issue (DSN format, port, service name)

3. **Recommend investigation steps** — what to check next to confirm or rule out
   each hypothesis. Be specific about which logs, Oracle queries, or endpoints to inspect.

4. **Propose a fix** — once the cause is identified or sufficiently likely, propose
   the minimal safe change that resolves the incident without introducing new risk.
   Flag any follow-up work that should be done in a separate ticket post-incident.

5. **Risk assessment** — what is the risk of the proposed fix? Could it affect
   other parts of the system? Is a rollback straightforward if it does not work?

Do not suggest a fix until you have worked through steps 1 to 3. Ask for more
information if needed before proposing a solution.
