---
name: unit-testing
description: Write unit tests that map 1:1 with a story's acceptance criteria. Pytest + httpx for backend (FastAPI/oracledb), Jest + React Testing Library for frontend. Used by the Developer agent after writing the implementation.
---

# Skill: Unit Testing — Staff Procurement Portal

## When to use this

You've just implemented a story and need tests that (a) cover each acceptance criterion, (b) catch the obvious edge cases, (c) hit the 80% line-coverage target on the new code.

## Backend (pytest + httpx)

- Tests under `backend/tests/` mirroring the source path: `backend/tests/api/test_<resource>.py`, `backend/tests/services/test_<service>.py`.
- Use the `conftest.py` fixtures: `client` (httpx TestClient), `oracle_mock` (mock Oracle connection), `test_staff` (synthetic staff data).
- One test function per scenario in the story's AC, plus one per edge case (empty input, wrong type, unauthenticated, unauthorised, access denied by procurement level).
- **Mock Oracle — never hit the real Oracle XE container in unit tests.** Use `unittest.mock.patch` or `pytest-mock` to mock `oracledb.connect()` and cursor responses.
- **Mock ID.me — never hit the real ID.me OAuth server.** Use `respx` or `pytest-httpx` to mock the token exchange endpoint.
- Assert on response status code + body shape (Pydantic model dump, not raw dict).
- Run: `pytest --cov=app/<path> --cov-report=term-missing` and confirm >= 80%.

## Example backend test pattern (Oracle mock)

```python
from unittest.mock import MagicMock, patch

def test_get_procurement_as_admin(client, mock_jwt_admin):
    mock_row = (1, "Laptops", "Dell", "Technology", "APPROVED", 999.99, "Jane Smith", "jane@vendor.com", None)
    with patch("app.core.database.get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [mock_row]
        mock_cursor.description = [("ITEM_ID",), ("ITEM_NAME",), ...]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        response = client.get("/procurement", cookies={"access_token": mock_jwt_admin})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["item_name"] == "Laptops"
```

## Key test scenarios per domain

| Domain | Happy path | Failure cases |
|---|---|---|
| Staff registration | POST /staff returns 201, row in Oracle | Duplicate email 409; missing field 422 |
| ID.me callback | Code exchange succeeds, JWT cookie set | Invalid code 400; Oracle lookup fails 500 |
| Access decision | Level 1 + verified = 200 | Level 0 = 403; unverified = 403; inactive = 403 |
| RBAC filter | Admin gets all statuses; Staff gets APPROVED only | Staff cannot see PENDING/REJECTED |
| PII gating | Level 2+ gets CONTACT fields; Level 3 gets BANK_DETAILS | Level 1 response omits those fields |

## Frontend (Jest + RTL)

- Tests in `frontend/src/__tests__/<Component>.test.jsx` or co-located as `<Component>.test.jsx`.
- Render with React Testing Library. Query by role/label, not by class or test ID.
- Cover: happy path render, error state, loading state, empty state, keyboard interaction.
- Mock the API client (axios instance or fetch) — never hit the real backend.
- Snapshot tests advisory only — don't rely on them as primary assertions.

## Output

After writing tests:
1. Run: `pytest -q backend/tests/` — must pass.
2. Run coverage: `pytest --cov=app` — confirm >= 80% on new code.
3. Run frontend: `npm test -- --watchAll=false` — must pass.
4. Print: how many tests added, which ACs each maps to, current coverage.

## Refuse-and-flag

- Asked to skip tests "just this once". Refuse and explain DoD.
- Asked to mock business logic instead of testing it. Refuse — mock the boundary (Oracle, ID.me), not the unit.
- Asked to lower the coverage gate. Refuse and surface to Tech Lead.
- Asked to write tests that hit the real Oracle container or real ID.me. Refuse — use mocks.
