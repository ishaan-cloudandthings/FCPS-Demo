# ADR-007 — Synthetic data only; ID.me sandbox for the demo

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude), on behalf of FCPS IT Lead |
| Supersedes | — |
| Superseded by | — |

## Context

Two unconditional directives from the 2026-05-05 technical-discovery call,
both attributed to the FCPS IT Lead:

> "Do not touch the production Oracle instance. Not even to look at it. Use
> your own container for development."

> "C&T will use sandbox credentials for the demo — not the production ID.me
> application."

Together these bind the entire dev-and-demo lifecycle: no production data, no
production credentials, no production endpoints, ever.

`ARCHITECTURE.md` §8.4 mentions secrets management but does not state the
*data* policy. `AI_POLICY.md` "Confidentiality Rules" forbids real PII /
production credentials in **AI prompts**, but doesn't bind what runs in the
demo environment itself.

This ADR closes that gap.

## Decision

The following rules apply for the duration of the demo:

1. **All data in development and the demo environment is synthetic.**
   - `STAFF` records use IDs `FCPS-001`…`FCPS-010` and fictional names per
     `DATA_MODEL.md` §8.
   - `PROCUREMENT_ITEMS` rows use fictional vendor names, item descriptions,
     and routing numbers.
   - All data is generated and seeded by `scripts/seed_oracle.py`
     (see ADR-010).
2. **ID.me integration uses only the sandbox application** registered under
   FCPS's organisational ID.me account. Sandbox `client_id` / `client_secret`
   are shared via 1Password. Production ID.me is phase 2 and will require a
   separate ID.me application registration and a separate redirect-URI
   configuration.
3. **C&T does not have access to the production Oracle instance** and will not
   connect to it from dev, CI, or the demo EC2.
4. **Real FCPS staff records, real vendor records, and production credentials
   never enter**: the git repository, the demo EC2 filesystem, AI prompts,
   ChatGPT/Claude conversations, screenshots, log exports, or any C&T tooling.

## Consequences

**Positive**

- No risk of demo-data leakage onto production systems.
- Aligns cleanly with `AI_POLICY.md` confidentiality rules — synthetic data can
  safely be used in AI prompts during development, including for code review
  and test generation.
- Sandbox ID.me supports a fixed list of test users with predictable `sub`
  values, which matches the 10 synthetic STAFF rows by design.

**Negative**

- The demo cannot validate production-quality data shapes (unusual vendor
  names, very long descriptions, edge-case bank-detail formats). Accepted —
  this is a phase-2 production-readiness task, not a demo gap.
- The team must remember that "the demo cannot do X with real data" is not a
  bug.

**Follow-ups required**

- Add a one-line reference to this ADR from `ARCHITECTURE.md` §8.4
  ("Secrets Management").
- `.env.example` should mark each ID.me variable as **sandbox-only for the
  demo**.
- A short note in the deployment README explaining how to add a new test user
  (1: add a row to `seed_oracle.py`; 2: invite the corresponding sandbox
  account from the ID.me developer console, owned by FCPS IT Lead).

## References

- `docs/discovery/CALL_NOTES_2026-05-05.md` — "Data and Sensitive Information"
  table; FCPS IT Lead quotes
- `docs/requirements/REQUIREMENTS.md` — NFR-08, §6 data-and-sensitivity table
- `AI_POLICY.md` — Confidentiality Rules
- `ADR-010` — `seed_oracle.py` as schema authority
