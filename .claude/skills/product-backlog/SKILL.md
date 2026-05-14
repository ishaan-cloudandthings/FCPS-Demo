---
name: product-backlog
description: Build and groom a Product Backlog from a Functional Design or ARCHITECTURE.md. Produces a Markdown snapshot at docs/planning/product-backlog.md and creates epics + stories in Jira via the Atlassian MCP. Use when the PM agent needs to seed or refresh the backlog.
---

# Skill: Product Backlog — FCPS Procurement Portal

## When to use this

You have a Functional Design document (or the existing ARCHITECTURE.md) and need to convert it into a tracked, prioritised, zone-labelled Product Backlog in Jira plus a Markdown snapshot in the repo.

## Inputs

- `docs/requirements/FUNCTIONAL_DESIGN.md` (or `docs/ARCHITECTURE.md` if FD not yet produced)
- `AI_ZONES.md`
- `docs/DATA_MODEL.md`

## Steps

1. **Read the Functional Design.** Cluster user journeys into themes (= epics). For FCPS: Staff Registration, Identity Verification, Oracle HR Lookup, Access Decision, RBAC / Procurement Data.
2. **For each theme**, list candidate user stories following the story-writing skill template.
3. **Order by priority** using MoSCoW plus dependency order. Registration must precede verification; verification must precede access decision.
4. **Print the proposed backlog** to the chat. Wait for explicit confirmation.
5. **Write the Markdown snapshot** to `docs/planning/product-backlog.md`.
6. **Create Jira epics and stories** using the Atlassian MCP. Project key: `FCPS`. Search for existing issues first to avoid duplicates.
7. **Print issue keys** back to the chat.

## FCPS story dependency order (enforce this sequence)

```
Sprint 0 / Foundation
  └── BA: requirements interview + api-spec.yaml draft

Sprint 1: Core plumbing
  ├── Staff Registration (Green) — POST /staff
  ├── Oracle DB connection + seed script (Green)
  └── JWT + session infrastructure (Red — decision gate first)

Sprint 2: Identity
  ├── ID.me OAuth initiation (Amber)
  └── ID.me callback + IDME_VERIFIED update (Red — decision gate first)

Sprint 3: Access + Data
  ├── Access decision logic (Amber)
  ├── Procurement list endpoint with RBAC filter (Amber)
  └── PII field gating by procurement level (Amber)

Sprint 4: Frontend
  ├── Registration page (Green)
  ├── Verification callback page (Green)
  ├── Admin view (Amber)
  └── Staff view (Amber)

Sprint 5: QA + Deploy
  ├── SIT plan + scripts (Green)
  ├── CI governance pipeline (Amber)
  └── EC2 deployment + runbook (Amber)
```

## Zone inference guide

| Story area | Zone |
|---|---|
| `backend/app/auth/`, auth.py callback | Red |
| `backend/app/services/`, API handlers | Amber |
| `frontend/src/pages/` | Amber |
| `backend/app/schemas/`, `backend/app/utils/` | Green |
| `backend/scripts/seed_oracle.py` | Green |
| `backend/tests/`, `frontend/src/__tests__/` | Green |

## Refuse-and-flag

- No Functional Design exists and user wants full backlog: produce a draft from ARCHITECTURE.md but flag it as unconfirmed.
- Story estimated > 13 SP with no decomposition: flag for splitting before adding to a sprint.
