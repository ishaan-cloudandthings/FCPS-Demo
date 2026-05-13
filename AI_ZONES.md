# AI_ZONES.md — Confidence Zone Map

This file maps every module and folder in the FCPS Procurement Portal to a Green, Yellow,
or Red AI confidence zone. Zone classification determines how much AI autonomy is permitted
and what review is required before merge.

See `docs/AI_POLICY.md` for the full zone definitions and governance rules.

---

## Zone Summary

| Zone          | AI Role                                                        | Required Before Merge                                                                      |
|---------------|----------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| 🔴 **Red**   | AI surfaces every decision as explicit questions, waits for human approval, then writes. | Human approves all decisions on record. Security review + architect sign-off. Two reviewers. |
| 🟡 **Yellow** | AI drafts. Developer rewrites or edits meaningfully.          | Live walk-through with senior. Two reviewers. No AI-only explanations accepted.            |
| 🟢 **Green** | AI writes. Developer reviews for correctness.                  | Developer can explain every block. One reviewer. Comprehension Declaration complete.       |

---

## 🔴 Red Zone — AI Proposes, Human Approves, AI Writes

In Red Zone, AI does not generate code speculatively. The sequence is:

1. **AI reads the relevant spec documents** and understands what needs to be built.
2. **AI surfaces every decision** that must be made before implementation — presented as
   explicit questions covering security approach, failure behaviour, edge cases, and any
   choice with a non-obvious trade-off.
3. **Human approves every decision on record.** AI does not proceed until all decisions
   are confirmed.
4. **AI writes the code** based solely on the confirmed decisions. No deviation.
5. **Human reviews** with security review and architect sign-off before merge.

| Path                                      | Reason                                                          |
|-------------------------------------------|-----------------------------------------------------------------|
| `backend/app/auth/`                       | JWT issuance, session management, token validation              |
| `backend/app/api/auth.py`                 | ID.me OAuth callback, login, logout, token refresh              |

---

## 🟡 Yellow Zone — AI Drafts, Developer Meaningfully Edits

| Path                                      | Reason                                                          |
|-------------------------------------------|-----------------------------------------------------------------|
| `backend/app/services/`                   | All business logic — Oracle lookup, access decision, RBAC filter|
| `backend/app/api/staff.py`                | Staff registration and status endpoints                         |
| `backend/app/api/procurement.py`          | Procurement data endpoints (role-filtered)                      |
| `backend/app/api/verification.py`         | ID.me verification status endpoints                             |
| `frontend/src/pages/`                     | Page-level components with business logic                       |
| `frontend/src/store/`                     | State management                                                |
| `frontend/src/hooks/`                     | Custom hooks with non-trivial logic                             |
| `docker-compose.yml`, `Dockerfile`        | Container and infrastructure configuration                      |
| `nginx/nginx.conf`                        | Reverse proxy and static file serving config                    |
| `.github/workflows/`                      | CI/CD pipelines — review carefully before merge                 |

---

## 🟢 Green Zone — AI Writes, Developer Reviews

| Path                                      | Reason                                                          |
|-------------------------------------------|-----------------------------------------------------------------|
| `backend/app/schemas/`                    | Pydantic request/response schemas                               |
| `backend/app/core/config.py`              | Pydantic settings / env var loading                             |
| `backend/app/core/database.py`            | Oracle connection factory (oracledb thin mode)                  |
| `backend/app/utils/`                      | Shared utility functions and structured logger                  |
| `backend/scripts/seed_oracle.py`          | Oracle table creation and demo data seeding                     |
| `backend/tests/`                          | Pytest unit and integration tests                               |
| `frontend/src/components/`               | Reusable UI components (forms, buttons, tables, status badges)  |
| `frontend/src/services/`                  | API client                                                      |
| `frontend/src/utils/`                     | Frontend utility functions                                      |

---

## Zone Violation Policy

- A PR that misclassifies a Red zone file as Yellow or Green **must be rejected** regardless
  of code quality.
- A Red zone PR where decisions were not explicitly approved by the human before code
  generation **must be rejected**.
- If you are unsure which zone applies, **default to the higher zone** (more restrictive).
- Zone reclassification requires a documented ADR in `docs/adr/`.

## PII Handling Rule (applies across all zones)

PII handling is not a zone classification — it is a rule that applies everywhere. When writing
any code that reads, writes, logs, or returns PII fields (see `docs/DATA_MODEL.md` PII section),
AI must pause before generating and explicitly confirm with the human:

- How will this field be protected from appearing in logs?
- Is this field needed in the response, or can it be excluded?
- Is the endpoint scoped so only the owning user can access this data?

This applies in Yellow and Green zones as well as Red.
