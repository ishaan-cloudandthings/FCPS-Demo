---
name: functional-design
description: Produce a Functional Design document that maps user journeys to system behaviour, integration points, data flows, validation rules, and notification triggers. Used by the BA agent after the requirements interview is complete. Output lives at docs/requirements/FUNCTIONAL_DESIGN.md.
---

# Skill: Functional Design

## When to use this

The requirements interview is complete and you need to translate it into a structured Functional Design that developers, designers, and QC will all read.

## Output structure (`docs/requirements/FUNCTIONAL_DESIGN.md`)

```markdown
# Functional Design — <Project>

## 1. Overview
One paragraph. The product purpose, the personas, the high-level value.

## 2. Personas
| Persona | Goals | Permissions |
| --- | --- | --- |
| … | … | … |

## 3. User Journeys
For each top-level journey:

### 3.<n>. <Journey name>
- **Trigger.**
- **Pre-conditions.**
- **Steps.** (Numbered. Each step: actor → action → system response.)
- **Validation rules.** (Field-level + cross-field.)
- **Integration points.** (Which external service is called, when, with what payload, what response is expected, how failure is handled.)
- **Notifications.** (Which channel, which template, who receives.)
- **Audit log entries.**
- **Post-conditions.**
- **Open questions.**

## 4. System-wide rules
Roles & permissions. Session/auth rules. Data retention. Audit obligations. Error-handling philosophy.

## 5. Non-functional requirements
- Performance (specific targets).
- Security (specific obligations, e.g. POPIA, GDPR).
- Compliance (named regulations).
- Accessibility (WCAG 2.1 AA target).
- Internationalisation.
- Browser/device support matrix.

## 6. Open questions (project-wide)
Anything you weren't told.
```

## Rules

- Specific, not general. "The form rejects email addresses without `@`" not "validates input properly".
- Integration points are named: SES, Google Address Validation, Postgres, etc. — never "the email service".
- NFRs as numbers: "p95 < 500 ms" not "fast".
- Every journey has at least one error path documented.
- Open Questions list is mandatory. If empty, flag suspicion.
