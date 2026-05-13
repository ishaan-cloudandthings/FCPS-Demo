# AI_CONTEXT.md — FCPS Procurement Portal

> **Read this file before every AI session.** This is the single source of truth for the
> FCPS Procurement Portal project. All AI tools (Claude, Claude Code) reference this file.
> Tool-specific files (CLAUDE.md) are thin wrappers that point here.

---

## Project Identity

| Field          | Value                                                          |
|----------------|----------------------------------------------------------------|
| Project        | Fairfax County Public Schools — Procurement Access Portal      |
| Client         | Fairfax County Public Schools (FCPS)                          |
| Build Type     | Greenfield demo build                                          |
| GitHub Repo    | github.com/Cloud-and-Things/fcps-procurement-portal           |
| Framework      | C&T AI-Driven SDLC Framework v1.0                             |

---

## Tech Stack

| Layer              | Technology                                      |
|--------------------|-------------------------------------------------|
| Frontend           | React (functional components + hooks)           |
| Backend            | Python 3.11+ / FastAPI                          |
| Database           | Oracle XE 21c (Docker)                          |
| Oracle Driver      | oracledb (thin mode — no Oracle Client needed)  |
| Auth               | JWT (python-jose) + ID.me OAuth 2.0             |
| Identity           | ID.me (OAuth 2.0 / OpenID Connect)              |
| Web Server         | Nginx (reverse proxy + React static serving)    |
| Containerisation   | Docker / Docker Compose                         |
| Infrastructure     | AWS EC2 (t3.medium)                             |
| CI/CD              | GitHub Actions                                  |
| Testing            | Pytest (backend), Jest + React Testing Library  |

---

## Folder Structure

```
fcps-procurement-portal/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI route handlers (one file per domain)
│   │   ├── auth/            # 🔴 RED ZONE — JWT, ID.me callback, session
│   │   ├── core/            # Config, Oracle session, dependencies
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic layer
│   │   └── utils/           # Shared utilities
│   ├── scripts/
│   │   └── seed_oracle.py   # Oracle table creation + demo data seeding
│   ├── tests/               # Pytest test suite
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable React components
│   │   ├── pages/           # Page-level components
│   │   │   ├── Registration.jsx
│   │   │   ├── VerificationCallback.jsx
│   │   │   ├── AdminView.jsx
│   │   │   └── StaffView.jsx
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API client
│   │   ├── store/           # State management
│   │   └── utils/
│   └── public/
├── docs/
│   ├── ARCHITECTURE.md      # System architecture
│   ├── DATA_MODEL.md        # Oracle data model
│   ├── AI_POLICY.md         # AI tool usage rules
│   └── adr/                 # Architecture Decision Records
├── nginx/
│   └── nginx.conf
├── .github/
│   └── workflows/
│       ├── test.yml          # PR → test branch pipeline
│       └── deploy.yml        # prod branch → EC2 deploy pipeline
├── docker-compose.yml
├── AI_CONTEXT.md
├── AI_ZONES.md
├── CLAUDE.md
└── .env.example
```

---

## Naming Conventions

| Context                    | Convention          | Example                          |
|----------------------------|---------------------|----------------------------------|
| Python files               | snake_case          | `oracle_service.py`              |
| Python functions/variables | snake_case          | `get_staff_by_employee_id()`     |
| Python classes             | PascalCase          | `OracleService`                  |
| FastAPI route paths        | kebab-case          | `/staff-lookup/{employee_id}`    |
| React components           | PascalCase          | `AdminView`                      |
| React files                | PascalCase          | `AdminView.jsx`                  |
| CSS / style files          | kebab-case          | `admin-view.css`                 |
| Environment variables      | SCREAMING_SNAKE_CASE| `IDME_CLIENT_SECRET`             |
| Oracle tables              | SCREAMING_SNAKE_CASE| `STAFF`, `PROCUREMENT_ITEMS`     |
| Oracle columns             | SCREAMING_SNAKE_CASE| `EMPLOYEE_ID`, `CREATED_DATE`    |

---

## Patterns to Follow

- **Layered architecture**: Routes → Services → Oracle. No business logic in route handlers.
  No direct Oracle queries from routes.
- **Dependency injection**: Use FastAPI's `Depends()` for Oracle sessions, auth, and service
  injection.
- **Pydantic schemas**: All request and response bodies must have explicit Pydantic models.
  No raw dicts in or out of endpoints.
- **Functional React**: All components must be functional with hooks. No class components.
- **Explicit typing**: All Python functions must have type hints on parameters and return values.
- **Environment config**: All configuration via environment variables using `pydantic-settings`.
  No hardcoded values anywhere.
- **oracledb thin mode**: No Oracle Client installation required. Use `oracledb.connect()` with
  thin mode only.

---

## Anti-Patterns to Avoid

- ❌ Business logic in FastAPI route handlers — put it in `services/`
- ❌ Direct Oracle queries from routes — always go through the service layer
- ❌ Hardcoded credentials, API keys, or secrets anywhere in code
- ❌ `print()` for logging — use the project logger (`from app.utils.logging import logger`)
- ❌ Raw SQL strings — use parameterised queries with oracledb only
- ❌ Class-based React components
- ❌ Inline styles in JSX
- ❌ Skipping zone classification before writing code
- ❌ Real staff data, PII, or production credentials in AI prompts

---

## Key Business Domains

1. **Staff Registration** — Self-service registration with name, work email, and employee ID
2. **Identity Verification** — ID.me OAuth 2.0 flow; verified status stored per user
3. **Oracle HR Lookup** — Query STAFF table by employee ID; return role and procurement level
4. **Access Decision** — Verified identity + procurement level ≥ 1 = access granted
5. **RBAC** — Admin sees all procurement records; Staff sees approved records only

---

## Key Integrations

| Integration   | Purpose                                              | Zone      |
|---------------|------------------------------------------------------|-----------|
| ID.me         | Staff identity verification via OAuth 2.0            | 🔴 Red    |
| Oracle XE     | Staff HR data and procurement records                | 🟡 Yellow |
| AWS EC2       | Application hosting (FastAPI + React + Oracle XE)    | 🟡 Yellow |
| GitHub Actions| CI/CD — test pipeline on PR, deploy on prod merge    | 🟡 Yellow |

Env vars for each integration are defined in `.env.example`.
