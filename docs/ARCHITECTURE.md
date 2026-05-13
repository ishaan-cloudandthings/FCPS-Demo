# ARCHITECTURE.md — FCPS Procurement Portal

> **Reference document.** Do not modify without explicit instruction and a corresponding ADR.
> All implementation must conform to the patterns described here.

**Version:** 1.0
**Date:** May 2026
**Owner:** Cloud & Things (C&T)
**Stack:** React · FastAPI · Oracle XE · ID.me · AWS EC2

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Style](#2-architecture-style)
3. [C4 Model — Context](#3-c4-model--context)
4. [C4 Model — Containers](#4-c4-model--containers)
5. [AWS Infrastructure](#5-aws-infrastructure)
6. [Component Breakdown](#6-component-breakdown)
7. [Data Flow — Key Scenarios](#7-data-flow--key-scenarios)
8. [Security Architecture](#8-security-architecture)
9. [Local Development Setup](#9-local-development-setup)
10. [Environment Configuration](#10-environment-configuration)
11. [Architecture Decision Records](#11-architecture-decision-records)

---

## 1. System Overview

The FCPS Procurement Portal allows Fairfax County Public Schools staff to self-register,
verify their identity via ID.me, and access procurement data appropriate to their role.
Admins (procurement coordinators) see all records. Staff (teachers) see approved records only.

The system integrates two external sources of truth:
- **ID.me** — proves who the user is
- **Oracle** — proves what the user is allowed to do

---

## 2. Architecture Style

**Containerised, API-First, Layered.**

| Principle         | Decision                                                                    |
|-------------------|-----------------------------------------------------------------------------|
| Deployment        | Single AWS EC2 instance running Docker Compose                              |
| Backend pattern   | Layered: Routes → Services → Oracle. No business logic in route handlers.   |
| Frontend pattern  | React SPA served by Nginx; communicates via REST API only                   |
| Auth              | ID.me OAuth 2.0 for identity; JWT for session; role sourced from Oracle     |
| Configuration     | All config via environment variables; no hardcoded values                   |
| Oracle access     | oracledb thin mode; no Oracle Client installation required                  |

---

## 3. C4 Model — Context

```
┌──────────────────────────────────────────────────────────────────────┐
│                   FCPS Procurement Portal                            │
│                                                                      │
│  ┌─────────────┐   HTTPS    ┌──────────────────────────────────┐    │
│  │  FCPS Staff │ ─────────► │  React SPA (Nginx on EC2)        │    │
│  │  / Admin    │            └──────────────┬───────────────────┘    │
│  └─────────────┘                           │ REST API               │
│                              ┌─────────────▼───────────────────┐    │
│                              │  FastAPI Backend (EC2 Docker)   │    │
│                              └──────┬─────────────┬────────────┘    │
│                                     │             │                  │
│                          ┌──────────▼──┐   ┌──────▼──────────┐     │
│                          │  Oracle XE  │   │     ID.me        │     │
│                          │  (Docker)   │   │  (OAuth 2.0)     │     │
│                          └─────────────┘   └─────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. C4 Model — Containers

### 4.1 Frontend — React SPA

| Property   | Value                                              |
|------------|----------------------------------------------------|
| Technology | React 18 (functional components + hooks)           |
| State      | Zustand (global), React Hook Form (forms)          |
| Routing    | React Router v6                                    |
| Hosting    | Nginx on EC2 (port 80)                             |
| Auth       | JWT stored in httpOnly cookie (set by backend)     |
| Styling    | CSS Modules                                        |
| Testing    | Jest + React Testing Library                       |

### 4.2 Backend — FastAPI

| Property   | Value                                              |
|------------|----------------------------------------------------|
| Technology | Python 3.11+ / FastAPI                             |
| Runtime    | Uvicorn (Docker on EC2, port 8000)                 |
| Oracle     | oracledb (thin mode, synchronous)                  |
| Validation | Pydantic v2                                        |
| Auth       | python-jose (JWT) + ID.me OAuth 2.0                |
| Testing    | Pytest + httpx                                     |

**Internal layer order (strictly enforced):**

```
HTTP Request
    │
    ▼
app/api/          ← Route handlers only. No business logic.
    │               Calls service layer via FastAPI Depends().
    ▼
app/services/     ← All business logic lives here.
    │               Oracle lookup, access decision, RBAC filter.
    ▼
Oracle XE         ← Parameterised queries via oracledb only.
```

### 4.3 Database — Oracle XE

| Property   | Value                                              |
|------------|----------------------------------------------------|
| Engine     | Oracle XE 21c                                     |
| Hosting    | Docker container on EC2                            |
| Access     | FastAPI container via Docker network               |
| Driver     | oracledb (Python, thin mode)                       |
| Schema     | See `docs/DATA_MODEL.md`                           |

### 4.4 Identity — ID.me

| Property   | Value                                              |
|------------|----------------------------------------------------|
| Protocol   | OAuth 2.0 / OpenID Connect                         |
| Flow       | Authorization Code Flow                            |
| Callback   | `{FRONTEND_URL}/verification/callback`             |
| Scopes     | `openid email`                                     |
| Zone       | 🔴 Red                                             |

---

## 5. AWS Infrastructure

```
┌───────────────────────────────────────────┐
│  AWS EC2 — t3.medium                      │
│                                           │
│  ┌────────────┐   ┌──────────────────┐    │
│  │  Nginx     │   │  FastAPI         │    │
│  │  :80       ├──►│  (Uvicorn) :8000 │    │
│  └────────────┘   └────────┬─────────┘    │
│                            │              │
│                   ┌────────▼─────────┐    │
│                   │  Oracle XE       │    │
│                   │  :1521           │    │
│                   └──────────────────┘    │
│                                           │
│  GitHub Actions → SSH deploy on merge     │
└───────────────────────────────────────────┘

External:
  - ID.me (OAuth 2.0 authorization server)
  - GitHub Actions (CI/CD runner)
```

### Environments

| Environment | Purpose                          | Oracle       |
|-------------|----------------------------------|--------------|
| `dev`       | Local development (Docker)       | Docker XE    |
| `prod`      | Live demo on EC2                 | Docker XE    |

---

## 6. Component Breakdown

### 6.1 Backend Module Map

```
backend/
├── app/
│   ├── api/                    # 🟡 Yellow — Route handlers (thin, no logic)
│   │   ├── auth.py             # 🔴 RED — ID.me callback, login, logout
│   │   ├── staff.py            # Staff registration and status
│   │   ├── procurement.py      # Procurement data (role-filtered)
│   │   └── verification.py     # Verification status endpoints
│   │
│   ├── auth/                   # 🔴 RED — JWT internals. AI proposes, human approves.
│   │   ├── jwt.py              # Token issuance, validation
│   │   └── dependencies.py     # FastAPI Depends() for auth injection
│   │
│   ├── core/
│   │   ├── config.py           # 🟢 Pydantic Settings — env var loading
│   │   ├── database.py         # 🟢 Oracle connection factory (oracledb thin)
│   │   └── dependencies.py     # 🟢 Shared FastAPI Depends()
│   │
│   ├── schemas/                # 🟢 Green — Pydantic request/response schemas
│   │   ├── staff.py
│   │   ├── procurement.py
│   │   └── auth.py
│   │
│   ├── services/               # 🟡 Yellow — All business logic
│   │   ├── oracle_service.py   # Oracle STAFF + PROCUREMENT_ITEMS queries
│   │   ├── access_service.py   # Access decision logic
│   │   └── rbac_service.py     # Role-based data filtering
│   │
│   └── utils/                  # 🟢 Green — Shared helpers
│       └── logging.py          # Structured logger
│
├── scripts/
│   └── seed_oracle.py          # 🟢 Table creation + demo data seeding
├── tests/                      # 🟢 Green — Pytest test suite
└── main.py
```

### 6.2 Frontend Module Map

```
frontend/src/
├── components/                 # 🟢 Green — Reusable UI components
│   ├── StatusBadge.jsx
│   ├── ProcurementTable.jsx
│   └── layout/
│
├── pages/                      # 🟡 Yellow — Page-level components
│   ├── Registration.jsx        # Staff self-registration form
│   ├── VerificationCallback.jsx# ID.me OAuth return handler
│   ├── AdminView.jsx           # All procurement records
│   └── StaffView.jsx           # Approved records only
│
├── hooks/                      # 🟡 Yellow — Custom hooks
├── services/                   # 🟢 Green — API client
├── store/                      # 🟡 Yellow — Zustand stores
└── utils/                      # 🟢 Green — Shared utilities
```

---

## 7. Data Flow — Key Scenarios

### 7.1 Staff Registration and ID.me Verification

```
Staff (Browser)          Nginx/React           FastAPI              ID.me       Oracle
     │                       │                    │                   │            │
     │── Register form ──────►│                    │                   │            │
     │                       │── POST /staff ─────►│                   │            │
     │                       │                    │── INSERT staff ───────────────►│
     │◄── Redirect to ID.me ─────────────────────│                   │            │
     │────────────────────────────────────────────────────────────────►│            │
     │◄── Auth code ──────────────────────────────────────────────────│            │
     │── GET /callback?code= ─►│                    │                   │            │
     │                       │── GET /auth/callback►│                   │            │
     │                       │                    │── Exchange code ──►│            │
     │                       │                    │◄── ID token ───────│            │
     │                       │                    │── SELECT STAFF ───────────────►│
     │                       │                    │◄── role + level ───────────────│
     │                       │                    │── Issue JWT with role           │
     │◄── Access granted/denied ─────────────────│                   │            │
```

### 7.2 Procurement Data Access (RBAC)

```
Staff/Admin (Browser)        FastAPI                    Oracle
     │                          │                          │
     │── GET /procurement ──────►│                          │
     │                          │── Validate JWT           │
     │                          │── Extract role           │
     │                          │                          │
     │   [Admin]                │── SELECT * FROM          │
     │                          │   PROCUREMENT_ITEMS ────►│
     │                          │◄── all records ──────────│
     │                          │                          │
     │   [Staff]                │── SELECT * FROM          │
     │                          │   PROCUREMENT_ITEMS      │
     │                          │   WHERE STATUS='APPROVED'►│
     │                          │◄── approved only ────────│
     │◄── role-filtered data ───│                          │
```

---

## 8. Security Architecture

> ID.me OAuth callback and JWT handling are 🔴 **Red Zone**. AI surfaces every decision as
> explicit questions, waits for human approval, then writes. Security review and architect
> sign-off required before merge.

### 8.1 Authentication Flow

- Staff redirected to ID.me for identity verification.
- ID.me returns authorization code to the FastAPI callback endpoint.
- FastAPI exchanges code for ID token, validates it, then queries Oracle for role.
- JWT issued with role and employee_id claims.
- JWT stored in `httpOnly`, `Secure`, `SameSite=Strict` cookie.
- Access token TTL: 60 minutes.

### 8.2 Authorisation

| Role    | Access                                           |
|---------|--------------------------------------------------|
| `ADMIN` | All PROCUREMENT_ITEMS regardless of status       |
| `STAFF` | PROCUREMENT_ITEMS where STATUS = 'APPROVED' only |

Role is sourced from Oracle STAFF table — not from ID.me. ID.me proves identity only.

### 8.3 PII Handling

PII fields (employee name, email, employee ID) must never appear in logs. See
`docs/DATA_MODEL.md` PII Classification section for the full list.

### 8.4 Secrets Management

All secrets stored in environment variables. Loaded via `pydantic-settings` at startup.
Never hardcoded. See `.env.example` for the full list.

---

## 9. Local Development Setup

```bash
# 1. Clone the repo
git clone github.com/Cloud-and-Things/fcps-procurement-portal
cd fcps-procurement-portal

# 2. Copy env template and fill in values
cp .env.example .env

# 3. Start all services
docker compose up --build

# 4. Seed Oracle tables and demo data
docker compose exec backend python scripts/seed_oracle.py

# 5. Access
#   Frontend: http://localhost:80
#   API docs: http://localhost:8000/docs
```

---

## 10. Environment Configuration

All configuration loaded via `pydantic-settings` (`app/core/config.py`). Full variable list
in `.env.example`.

| Group       | Variables                                                               |
|-------------|-------------------------------------------------------------------------|
| ID.me       | `IDME_CLIENT_ID`, `IDME_CLIENT_SECRET`, `IDME_REDIRECT_URI`, `IDME_BASE_URL` |
| Oracle      | `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE_NAME`, `ORACLE_USER`, `ORACLE_PASSWORD` |
| JWT         | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINS`          |
| App         | `ENVIRONMENT`, `FRONTEND_URL`, `ALLOWED_ORIGINS`                        |
| Deploy      | `EC2_HOST`, `EC2_SSH_KEY`                                               |

---

## 11. Architecture Decision Records

### ADR-001 — EC2 + Docker Compose over Serverless

**Decision:** Deploy on a single EC2 t3.medium running Docker Compose rather than
Lambda + RDS.

**Rationale:**
- Oracle XE cannot run on Lambda. A container-based host is required.
- Demo context favours simplicity — one instance, one compose file, one SSH deploy.
- EC2 allows ID.me OAuth callback on a stable public URL without API Gateway complexity.

**Production recommendation:** RDS Oracle SE2, ECS Fargate, S3 + CloudFront, ALB.

---

### ADR-002 — Role Sourced from Oracle, Not ID.me

**Decision:** The user's role (Admin or Staff) is read from the Oracle STAFF table after
ID.me verification. ID.me is used for identity only.

**Rationale:**
- FCPS HR data lives in Oracle. Oracle is the authoritative source for role and clearance.
- Embedding role in ID.me claims would require FCPS to manage claims — out of scope.
- Separation of concerns: ID.me answers "who are you?", Oracle answers "what can you do?".

---

### ADR-003 — JWT in httpOnly Cookie

**Decision:** JWT stored in httpOnly, Secure, SameSite=Strict cookie.

**Rationale:** Consistent with C&T security standard (see VMS v2 ADR-005). Prevents
XSS-based token theft. localStorage explicitly avoided per OWASP guidance.
