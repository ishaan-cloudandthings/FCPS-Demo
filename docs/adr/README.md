# Architecture Decision Records — Staff Procurement Portal

This folder records every architectural decision made for the Staff Procurement
Portal. `docs/ARCHITECTURE.md` §11 now points here.

## Numbering

All ADRs (ADR-001 onwards) live in this folder as standalone files. The
inline ADR-001…ADR-003 entries that previously sat in `docs/ARCHITECTURE.md`
§11 have been extracted here; §11 is now a pointer to this index.

## Index

| ID | Title | Status | Key references |
|----|-------|--------|----------------|
| [ADR-001](ADR-001-ec2-docker-compose-over-serverless.md) | EC2 + Docker Compose over Serverless | Accepted | `ARCHITECTURE.md` §2, §5 |
| [ADR-002](ADR-002-role-sourced-from-oracle.md) | Role Sourced from Oracle, Not ID.me | Accepted | `ARCHITECTURE.md` §8.2; ADR-009 |
| [ADR-003](ADR-003-jwt-in-httponly-cookie.md) | JWT in `httpOnly` Cookie | Superseded by ADR-004 | `ARCHITECTURE.md` §8.1 |
| [ADR-004](ADR-004-session-cookie-and-jwt.md) | Session cookie and JWT reconciliation | Accepted (supersedes ADR-003) | 2026-05-09 call |
| [ADR-005](ADR-005-no-staff-registration-in-demo.md) | Staff Registration out of scope for the demo | Accepted | 2026-04-28 + 2026-05-09 |
| [ADR-006](ADR-006-audit-log-and-approved-at.md) | Add `AUDIT_LOG` table and `PROCUREMENT_ITEMS.APPROVED_AT` | Partial — `AUDIT_LOG` superseded by ADR-012; `APPROVED_AT` remains | 2026-05-09 call |
| [ADR-007](ADR-007-synthetic-data-and-idme-sandbox.md) | Synthetic data only; ID.me sandbox for demo | Accepted | 2026-05-05 call |
| [ADR-008](ADR-008-http-for-demo.md) | HTTP for the demo; HTTPS deferred to phase 2 | Accepted | 2026-05-05 call |
| [ADR-009](ADR-009-idme-sub-mapping.md) | ID.me `sub` mapped to `STAFF.EMPLOYEE_ID` | Accepted | 2026-05-09 call |
| [ADR-010](ADR-010-no-migration-tool.md) | No DB migration tool; `seed_oracle.py` is schema authority | Accepted | 2026-05-05 call |
| [ADR-011](ADR-011-client-side-search-no-pagination.md) | Client-side search; no pagination | Accepted | 2026-05-09 call |
| [ADR-012](ADR-012-bank-details-out-of-scope.md) | Bank details and audit logging out of scope for the demo | Accepted (supersedes ADR-006 `AUDIT_LOG` portion) | 2026-05-16 design review |
| [ADR-013](ADR-013-api-responses-match-ui-display.md) | API responses match UI display — `contact_email` moved to detail-only | Accepted (resolves OQ-08) | 2026-05-16 architect review |
| [ADR-014](ADR-014-demo-persona-login-dev-only.md) | Demo persona login for `dev` environments only | Accepted | 2026-05-18; scoped supersession of FR-01 inside dev only |
| [ADR-015](ADR-015-role-model-simplification.md) | Role model simplification — 3 roles (`PROCUREMENT_SUPERVISOR`, `REGULAR_STAFF`, `NON_STAFF`); `PROCUREMENT_LEVEL` dropped | Accepted (supersedes D-03) | 2026-05-19 |

## ADR template

Each ADR contains: a metadata table (status, date, supersedes, etc.),
**Context**, **Decision**, **Rationale**, **Consequences** (positive / negative /
follow-ups), and **References**. Where an ADR contradicts a paragraph in
`ARCHITECTURE.md`, `AI_CONTEXT.md`, or `DATA_MODEL.md`, the contradiction is
called out explicitly under follow-ups.
