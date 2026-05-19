# Demo zero-config boot — built-in demo defaults

| Field | Value |
|---|---|
| Topic | Backend `Settings` boot posture for the demo build |
| Zone | 🔴 Red (`backend/app/core/config.py`, `backend/main.py`) |
| Ratified on | 2026-05-19 |
| Ratified by | C&T Project Lead |
| Status | Ratified |

## Context

The demo build is run live in front of clients. Steps like *"generate
a JWT secret"* or *"copy .env.example to .env"* are friction the
stakeholder shouldn't see. The persona panel is the headline feature
of the demo arc (per ADR-014); it must render from a fresh `git clone`
with zero manual setup.

Until now, `Settings` declared every required field with
`Field(min_length=...)` and **no default**, so the backend refused to
boot without either a `.env` file or environment variables.

A side effect of the prior posture: someone committed a real-looking
JWT signing key into `backend/.env.example` to make the demo work.
That file is the public template; a real secret in there is a leak
even if the demo build never deploys.

## Decision

`Settings` now ships **built-in demo defaults** for every required
field. The backend boots without `.env` or any environment variables
when `ENVIRONMENT=dev` (the default). The defaults are clearly named
`_DEMO_*` constants in `config.py`.

A `model_validator` enforces the only hard rule: **any environment
other than `"dev"` is forbidden from booting with any demo sentinel
in place**. Promoting this build outside dev requires real env vars
or it will refuse to start.

## Decisions

| # | Decision | Ratified value |
|---|---|---|
| DEMO-1 | What gets a default | `idme_client_id`, `idme_client_secret`, `idme_issuer`, all `idme_*_url`, `jwt_secret_key`, `oracle_user`, `oracle_password`. URLs default to the real ID.me sandbox endpoints + `localhost:1521` for Oracle. Credentials default to obviously-synthetic sentinels (`spp_demo_user`, `spp_demo_password`, etc.). |
| DEMO-2 | JWT demo secret | `_DEMO_JWT_SECRET` is a 64-char `str` that satisfies `min_length=32`. It is intentionally **not** the output of `secrets.token_urlsafe(48)` — its hardcoded content (`spp-demo-only-jwt-secret-…`) is part of the audit trail. |
| DEMO-3 | Non-dev guard | `Settings._refuse_demo_defaults_outside_dev` raises `ValueError` at construction time when `ENVIRONMENT != "dev"` and any `_DEMO_*` sentinel is still in place. Boot fails loudly with the list of leaked fields. |
| DEMO-4 | Operator visibility | `main.py` calls `Settings.is_using_demo_jwt_secret()` and logs a `DEMO_BOOT` WARNING when true. The warning makes any tail-log inspection obvious. |
| DEMO-5 | `.env.example` posture | Reset to an empty template (no values, only documentation). The real demo secret lives in `config.py` `_DEMO_*` constants — not in the template file. |
| DEMO-6 | `.gitignore` | Root `.gitignore` added; `.env`, `backend/.env`, and the `.local` variants are blocked. The template `.env.example` stays tracked. |
| DEMO-7 | Tests | Backend test fixtures (`conftest.py`) continue to set `JWT_SECRET_KEY` etc. via monkeypatch — those override the defaults exactly the same way as a real env var would. No test changes required. |

## Why this is OK for the demo build

- AI_CONTEXT.md flags the project as `Build Type: Greenfield demo build`.
- ADR-007 commits the entire build to synthetic data + ID.me sandbox.
- The demo JWT secret only ever signs cookies that authenticate
  synthetic personas against synthetic data. It signs nothing of value.
- The non-dev guard means the same code is **incapable** of booting
  with this posture against any environment other than `dev` — there
  is no "I forgot to set the env var" failure mode.

## Why this is not OK to ship to production

- A static, public JWT secret signs forgeable sessions for anyone who
  reads the source.
- That's exactly why DEMO-3 exists: setting `ENVIRONMENT=prod` (or
  `staging`, or anything else) with the defaults in place is a hard
  boot failure, not a silent fallback.

## Rollback path

When the demo programme wraps or any non-dev deployment is on the
table:

1. Set `ENVIRONMENT` to the target environment via env var. The
   `model_validator` will refuse to boot until real values are
   provided.
2. Replace each `_DEMO_*` constant with a `Field(min_length=...)` (no
   default) — the old posture — *and* remove `_refuse_demo_defaults_outside_dev`.
3. Audit any deployment for the literal string `DEMO_BOOT` in logs;
   any hit is a finding.

## Files this decision creates / modifies

| Path | Change |
|---|---|
| `backend/app/core/config.py` | Built-in `_DEMO_*` constants + `model_validator` + `is_using_demo_jwt_secret()` |
| `backend/main.py` | `DEMO_BOOT` warning when the demo JWT secret is in force |
| `backend/.env.example` | Reset to empty template; documentation only |
| `.gitignore` | New (root) — `.env` and friends gitignored |
| `docs/decision-log/demo-zero-config-boot.md` | This file |
