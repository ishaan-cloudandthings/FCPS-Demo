---
name: sit-test-plan
description: Produce a System Integration Test plan and pytest scripts that exercise a full sprint's stories against the FCPS Docker Compose stack, including all integration points (ID.me sandbox, Oracle XE, JWT). Used by the QC agent at the end of each sprint.
---

# Skill: SIT Test Plan — FCPS Procurement Portal

## When to use this

Sprint code is deployed to the Docker Compose stack (or EC2 staging). You need a SIT plan that proves the integrated system meets the sprint goal, exercises all integration points, and produces a defects list with classifications.

## Environment setup before running SIT

```bash
# Start the full stack
docker compose up --build -d

# Seed Oracle tables and demo data
docker compose exec backend python scripts/seed_oracle.py

# Verify Oracle is healthy
docker compose exec backend python -c "import oracledb; c = oracledb.connect(dsn='...'); print('OK')"

# Verify backend is up
curl -s http://localhost:8000/docs | head -5
```

## SIT plan output

`docs/qa/sit-plan-sprint-N.md`:

```markdown
# SIT Plan — Sprint N

## Sprint goal
<one sentence>

## Scope
Stories: FCPS-...

## Environment
- URL: http://localhost:80 (dev) or https://<ec2-ip> (staging)
- Oracle XE: seeded via seed_oracle.py (see data/seed_staff.json for synthetic users)
- ID.me: sandbox credentials from .env (IDME_CLIENT_ID, IDME_CLIENT_SECRET)
- JWT: JWT_SECRET_KEY from .env

## Entry criteria
- [ ] docker compose up --build succeeds with no errors
- [ ] seed_oracle.py completes successfully
- [ ] All unit tests pass in CI (pytest -q)
- [ ] Smoke: GET /docs returns 200

## Defect classification
- Critical — auth bypass, data loss, Oracle down, PII leak
- High — primary flow broken (registration, login, procurement access)
- Medium — edge-case validation gap, minor RBAC issue
- Low — cosmetic, copy error

## Test scenarios
[One section per story — see template below]

## Exit criteria
- [ ] Zero Critical / High open
- [ ] All scenarios executed
- [ ] Tech Lead signs off
```

## Test scenario template

```markdown
### FCPS-<N> — <Story title>

**Pre-conditions:**
- Oracle seeded: <which seed record(s)>
- Auth state: <unauthenticated / authenticated as STAFF / authenticated as ADMIN>

**Steps:**
1. ...
2. ...

**Expected:**
- HTTP status: <code>
- Response body: <key fields>
- Oracle state: <what changed in the DB>
- Cookie: <if JWT issued — assert httpOnly, Secure, SameSite=Strict>

**Integration points exercised:**
- [ ] Oracle STAFF table
- [ ] Oracle PROCUREMENT_ITEMS table
- [ ] ID.me OAuth (sandbox)
- [ ] JWT issuance / validation
- [ ] Nginx proxy

**Negative cases:**
- <bad input / wrong role / wrong level> → expect <error status + message>

**Data file:** `tests/sit/sprint_N/data/<story-slug>.json`
```

## FCPS-specific test scenarios to always include

| Scenario | What it proves |
|---|---|
| FCPS-010 (Evans, LEVEL=0) attempts access | Access denied correctly |
| Unverified staff (IDME_VERIFIED='N') attempts access | Access denied correctly |
| INACTIVE staff (ACTIVE='N') attempts access | Access denied correctly |
| Staff (LEVEL=1) requests procurement list | Only APPROVED items returned; no CONTACT/BANK fields |
| Staff (LEVEL=2) requests procurement list | APPROVED items + CONTACT fields; no BANK_DETAILS |
| Admin (LEVEL=3) requests procurement list | All statuses + all fields including BANK_DETAILS |
| Admin requests single item | BANK_DETAILS present |
| Staff requests single item | BANK_DETAILS absent |

## Pytest layout

```
tests/sit/sprint_N/
├── conftest.py          # base_url fixture, Oracle seed helper, httpx client, JWT factory
├── test_registration.py
├── test_auth_flow.py
├── test_access_decision.py
├── test_procurement.py
└── data/                # synthetic data (no real EMPLOYEE_IDs or personal details)
```

Run:
```bash
pytest tests/sit/sprint_N/ \
       --base-url http://localhost:80 \
       --html=reports/sit-sprint-N.html \
       --self-contained-html
```

## Post-run: post results to Jira

For each story, post a comment:
- Pass/Fail per scenario.
- Defects found (with severity and steps to reproduce).
- Link to the HTML report.

## Refuse-and-flag

- SIT plan using real staff EMPLOYEE_IDs or real personal details. Refuse; use seed data names only.
- Exit criteria marked green with open Critical defects. Refuse.
- Asked to skip the Oracle seed step. Refuse — tests are invalid without known data state.
