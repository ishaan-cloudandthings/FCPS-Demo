# Demo in-memory vendor fallback

| Field | Value |
|---|---|
| Topic | `/api/vendors*` serves in-memory data when Oracle is unreachable in `dev` |
| Zones | 🟢 Green (`backend/app/services/demo_vendor_data.py`, `backend/app/core/database.py`) + 🟡 Yellow (`backend/app/api/procurement.py`) |
| Ratified on | 2026-05-19 |
| Ratified by | C&T Project Lead |
| Status | Ratified |
| Related | [demo-zero-config-boot.md](./demo-zero-config-boot.md), [AC-11](./AC-11-oracle-staff-lookup.md), [AC-16](./AC-16-procurement-queries.md), [AC-18](./AC-18-procurement-router.md), [AC-19](./AC-19-seed-procurement-items.md) |

## Context

After the [zero-config boot](./demo-zero-config-boot.md) work, the demo
boots without a `.env` file and the persona panel renders out of the
box. But clicking a granted persona lands on `/vendors`, which fetches
`GET /api/vendors`, which couldn't connect to Oracle (because Oracle
XE isn't running locally) — the SPA showed *"Service temporarily
unavailable"* instead of a vendor table.

The demo arc is "every user sees everything → voila, RBAC narrows it"
(per the deliberate AC-17 skip). That arc requires *something* to be
visible on `/vendors` from a fresh clone. Standing up Oracle XE in
Docker before the client demo is exactly the kind of in-front-of-the-
client step we've been removing.

## Decision

Add a **dev-only** in-memory fallback for both procurement endpoints:

- `GET /api/vendors` serves a hardcoded 15-row list when Oracle is
  unreachable AND `ENVIRONMENT=dev`.
- `GET /api/vendors/{id}` does the same — looks up by `item_id` in the
  same set, 404 when missing.

The fallback is **strictly** gated to `dev`. In any non-dev environment,
Oracle being unreachable still maps to 503 (the AC-18 / AC-13 contract).

The fallback data is the **same** 15 rows the AC-19 seed inserts into
Oracle, sourced from a single canonical module — they cannot drift.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| DEMO-VENDOR-1 | Connection-time fallback | `app/core/database.py:get_oracle_connection` catches `oracledb.DatabaseError` at `connect()` time. In dev, it yields `None` instead of raising; handlers detect `None` and serve demo data. In non-dev, it wraps as `OracleUnavailable` so handlers can return 503. |
| DEMO-VENDOR-2 | Query-time fallback | The procurement router catches `OracleUnavailable` raised from `list_vendors` / `get_vendor_by_id`. In dev, it serves demo data. In non-dev, it returns 503 (existing AC-13/AC-18 behaviour). |
| DEMO-VENDOR-3 | Hard environment gate | Both fallback paths check `settings.environment == "dev"` before substituting demo data. There is no env flag that flips this on outside dev. |
| DEMO-VENDOR-4 | Single source of truth | The 15-row data lives in `app/services/demo_vendor_data.py:VENDOR_SEED_ENTRIES`. `scripts/seed_oracle.py:_PROCUREMENT_SEED` is now a derived view of the same entries (wrapped to the Oracle INSERT shape). Editing one updates both. |
| DEMO-VENDOR-5 | Data shape | `DEMO_VENDOR_ROWS: list[VendorRow]` is also derived; item_ids are `1..15` matching the Oracle IDENTITY assignment order. Detail variant exposed by `get_demo_vendor_by_id(item_id)` which re-tags as `admin_detail`. |
| DEMO-VENDOR-6 | Logging | Every fallback path emits `procurement.list count=… DEMO_FALLBACK source=…` (or `procurement.detail …`) at INFO. `DEMO_FALLBACK` is grep-friendly for prod-leak detection (mirrors `DEMO_BOOT` and `DEV_AUTH_USED` discipline). |
| DEMO-VENDOR-7 | Tests | Existing "503 on OracleUnavailable" tests were renamed and split into: (a) `falls_back_to_demo_in_dev_on_oracle_unavailable` — query-time fallback; (b) `falls_back_to_demo_when_connection_is_none_in_dev` — connection-time fallback; (c) `503_when_oracle_unavailable_in_non_dev` — non-dev 503 path with explicit `environment="staging"` Settings override. |
| DEMO-VENDOR-8 | When real Oracle returns | When Oracle XE is later wired up via docker-compose, the fallback automatically yields to the real connection. No code change needed. The fallback is a graceful degradation, not a hardcoded short-circuit. |

## Trade-offs

**Positive**

- Zero-step demo: the vendor table renders from `git clone` + `uvicorn` + `npm run dev`.
- The AC-17 demo arc ("everyone sees everything → RBAC narrows it") works
  without Oracle.
- Seed data and demo data can't drift — they share a source.
- Non-dev environments are completely unaffected: 503 still 503.

**Negative**

- An extra ~250 lines of code (data + fallback paths + tests) carrying
  vendor data that's logically *test* data. Acceptable trade for a
  pure demo build; the data lives behind an env gate so it doesn't
  taint the prod posture.
- Two code paths in the procurement handlers (Oracle vs in-memory).
  Tests cover both, but a future contributor must remember the
  fallback exists when modifying procurement.

## Rollback path

When Oracle XE is wired up in docker-compose AND the demo programme
wraps:

1. Delete `app/services/demo_vendor_data.py`.
2. Restore the inline `_PROCUREMENT_SEED` in `scripts/seed_oracle.py`
   (or move it back if you'd rather keep the canonical source).
3. Remove the `if connection is None` and `if _is_dev(settings)` branches
   in `app/api/procurement.py`.
4. Remove the `if settings.environment == "dev"` branch in
   `app/core/database.py:get_oracle_connection`.
5. Delete tests `_falls_back_to_demo_*` and `_returns_404_when_demo_item_missing_in_dev`.
6. Grep production logs for `DEMO_FALLBACK` — any hit is a finding.

## Files this decision creates / modifies

| Path | Change |
|---|---|
| `backend/app/services/demo_vendor_data.py` | New — 15-row canonical data + `DEMO_VENDOR_ROWS` + `get_demo_vendor_by_id` |
| `backend/scripts/seed_oracle.py` | `_PROCUREMENT_SEED` now derives from `VENDOR_SEED_ENTRIES` |
| `backend/app/core/database.py` | `get_oracle_connection` handles connect failure: yields `None` in dev, raises `OracleUnavailable` otherwise |
| `backend/app/api/procurement.py` | Both endpoints handle `connection is None` and `OracleUnavailable` paths |
| `backend/tests/test_procurement_api.py` | 4 new tests (fallback paths + non-dev 503 path); 2 existing renamed |
| `docs/decision-log/demo-inmem-vendor-fallback.md` | This file |
