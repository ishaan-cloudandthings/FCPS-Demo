# AI_POLICY.md — Rules of Engagement for AI Tool Usage

This document defines the rules of engagement for AI tool usage on the Staff Procurement
Portal. Governance conversations reference this document — not anyone's opinion. Any deviation
from these rules requires explicit sign-off from the project lead and a documented ADR.

---

## Approved AI Tools

| Tool           | Approved Use                                                   |
|----------------|----------------------------------------------------------------|
| Claude         | Requirements analysis, architecture review, documentation      |
| Claude Code    | Code generation, refactoring, test writing, PR review          |

No other AI tools are approved for use on this project without written sign-off from the
project lead.

---

## Confidence Zone Rules

Zone classifications are defined in `AI_ZONES.md`. The rules for each zone are:

### 🟢 Green — AI Writes, Developer Reviews

- AI may generate the full implementation
- Developer must read and understand every block before the PR is opened
- Developer must be able to explain what the code does without referring back to the AI chat
- One reviewer required
- Comprehension Declaration must be completed in the PR template

### 🟡 Yellow — AI Drafts, Developer Meaningfully Edits

- AI may produce a draft
- Developer must rewrite or meaningfully edit the draft — not accept it wholesale
- Developer must walk a senior through the logic live before the PR is approved
- Two reviewers required
- No AI-only explanations accepted during review — the developer must explain it in their
  own words
- Comprehension Declaration must be completed in the PR template

### 🔴 Red — AI Proposes, Human Approves, AI Writes

- AI does not generate code speculatively. It first surfaces every decision as explicit
  questions covering security approach, failure behaviour, edge cases, and non-obvious
  trade-offs.
- Human must approve all decisions on record before AI writes a single line.
- AI writes the implementation based solely on the confirmed decisions — no deviation.
- The developer must be able to explain every block as if they wrote it themselves.
- Security review required before merge
- Architect sign-off required
- Comprehension Declaration must be completed in the PR template

---

## What "Comprehension" Means Operationally

A developer has demonstrated comprehension when they can answer all three of the following
questions in plain English, without referring back to the AI chat or the code itself:

1. **What does this code do?** — A clear, non-technical description of the behaviour
2. **Why was this approach chosen?** — The reasoning behind the implementation decision
3. **What breaks if it fails?** — The downstream impact of a failure in this code

If a developer cannot answer these questions, the code is not ready for review.

---

## PR Requirements for AI-Assisted Code

Every PR that contains AI-assisted code must include:

- **Comprehension Declaration** — All three questions answered. Non-optional.
- **Zone classification** — Explicit declaration of the zone(s) covered by the PR.
- **Zone compliance confirmation** — Confirmation that zone rules were followed.

A PR opened without a completed Comprehension Declaration must be rejected by the reviewer,
regardless of code quality or test results.

---

## Confidentiality Rules

The following must never appear in AI prompts, chat history, or AI tool inputs:

- Real staff data, PII, or personally identifiable information of any kind
- Production credentials, API keys, JWT secrets, ID.me secrets, or Oracle passwords
- Any data classified as confidential under Staff Procurement Portal or C&T data classification policy

When in doubt, anonymise or replace with dummy values before using in a prompt.

---

## Incident Accountability Clause

The named owner of a module is accountable for any production incident in that module,
regardless of whether AI generated the code. Accepting AI-generated code without
understanding it is not a defence — it is the root cause.

When a production incident occurs:

1. The module owner is the first point of contact
2. The post-incident review will include a Comprehension Declaration audit for the relevant PR
3. If the Comprehension Declaration was incomplete or false, this is treated as a governance
   failure, not just a technical one

---

## Governance Theatre Risk

This policy only works if it is held to under delivery pressure. The following are never
acceptable under any circumstances:

- Skipping the Comprehension Declaration to ship faster
- Approving a PR the reviewer cannot explain
- Reclassifying a Red or Yellow zone file as Green to avoid review overhead
- Using unapproved AI tools because they are faster
