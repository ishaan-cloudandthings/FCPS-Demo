# ADR-010 — No DB migration tool; `seed_oracle.py` is the schema authority

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude), on behalf of C&T Tech Lead |
| Supersedes | — |
| Superseded by | — |

## Context

2026-05-05 call, "Decisions Made on This Call":

> "Oracle schema managed by `seed_oracle.py`. No migration tool — too
> heavyweight for a demo."

The demo runs on a single Oracle XE 21c container that is re-seeded per
deployment. There is no production-grade schema-evolution requirement during
the demo period: data is synthetic, the schema is small, and there are no
existing rows to preserve.

`ARCHITECTURE.md` mentions `scripts/seed_oracle.py` in §6.1 and §9 but does
not state that this is the *only* place schema is defined. Without a clear
authority, contributors might add Alembic / Liquibase / a `migrations/`
folder and create two competing sources of truth.

## Decision

- For the demo, all Oracle DDL (table creation, columns, constraints, indexes)
  lives in **`scripts/seed_oracle.py`** and only there.
- The script is **idempotent**: it can be run multiple times safely. Approach:
  `DROP TABLE IF EXISTS … CASCADE CONSTRAINTS` followed by `CREATE TABLE …`,
  wrapped in transaction control so a failed run leaves no half-state.
- The script also seeds the synthetic demo data (see ADR-007), so the file
  has two roles for the demo: schema definition + data seed.
- **No** Alembic, Liquibase, Flyway, or `migrations/` folder is introduced.
- **`docs/DATA_MODEL.md` is the human-readable contract**;
  `scripts/seed_oracle.py` is the machine source of truth. The two must agree.
  Discrepancies are bugs.
- For phase 2, a migration tool will be selected (ADR) and the seed script
  will be downgraded to "demo data only".

## Consequences

**Positive**

- One file, one place to look, one place to change for the demo.
- Trivial to reset the demo: `docker compose exec backend python scripts/seed_oracle.py`.
- Aligned with `ARCHITECTURE.md` §9 local-development workflow.
- No tool installation, no migration history table, no rollback semantics.

**Negative**

- Any schema change (e.g. ADR-006's `AUDIT_LOG` + `APPROVED_AT`) requires
  editing the script directly.
- No reproducible audit trail of schema changes beyond `git log` and
  `git blame` on `seed_oracle.py`.
- Re-running the seed destroys any data that has accumulated since the last
  seed. Accepted for the demo because **all data is synthetic and**
  **regeneratable**.

**Follow-ups required**

- Add a header comment to `scripts/seed_oracle.py`:

  ```python
  """
  Demo schema authority — see docs/adr/ADR-010.
  Mirrors docs/DATA_MODEL.md exactly. Discrepancies are bugs.
  """
  ```

- Phase-2 ADR: choose a migration tool before any production data is loaded.

## References

- `docs/discovery/CALL_NOTES_2026-05-05.md` — "Decisions Made on This Call"
- `docs/requirements/REQUIREMENTS.md` — NFR-16
- `docs/requirements/FUNCTIONAL_DESIGN.md` — §12 (data-model implications)
- `ADR-006` — `AUDIT_LOG` + `APPROVED_AT` (the next schema change applied via
  this script)
- `ADR-007` — synthetic data only
