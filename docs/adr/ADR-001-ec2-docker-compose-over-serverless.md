# ADR-001 — EC2 + Docker Compose over Serverless

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude) — extracted from ARCHITECTURE.md §11 by architecture refactor |
| Supersedes | — |
| Superseded by | — |

## Context

The FCPS Procurement Portal demo needs a hosting target that can run the full
stack — React SPA, FastAPI backend, and Oracle XE — as a coherent unit and
expose a stable public URL for the ID.me OAuth callback.

A serverless option (AWS Lambda + RDS) was considered. Two constraints made
that unworkable for this engagement:

- **Oracle XE is the database of record for the demo** and cannot be hosted
  on Lambda. A container-based host is required to run the Oracle XE 21c
  image alongside the application services.
- **ID.me's OAuth flow requires a stable, publicly reachable callback URL.**
  Achieving that on Lambda would require API Gateway, custom-domain
  configuration, and the associated IAM/cert plumbing — overhead that exceeds
  the demo's scope.

The team also wanted a single deployment artefact that a developer could
reproduce locally with one command (`docker compose up`), so dev and demo
environments stay structurally identical.

## Decision

Deploy the FCPS Procurement Portal on a single AWS EC2 instance (`t3.medium`)
running Docker Compose. The compose file orchestrates three containers —
Nginx + React, FastAPI (Uvicorn), and Oracle XE — on a shared Docker network.
GitHub Actions performs an SSH-based deploy on merge to `main`.

## Rationale

- Oracle XE cannot run on Lambda. A container-based host is required.
- Demo context favours simplicity — one instance, one compose file, one SSH
  deploy.
- EC2 allows ID.me OAuth callback on a stable public URL without API Gateway
  complexity.

## Consequences

**Positive**

- Single deployment artefact: the same `docker-compose.yml` runs locally and
  on the demo EC2, removing dev/prod drift as a class of bug.
- Stable callback URL for ID.me is trivial — a single EC2 public DNS entry.
- No managed-service learning curve for the demo team; standard Docker +
  SSH skills suffice.

**Negative**

- Single point of failure: the EC2 instance is unreplicated. Acceptable for a
  demo, not for production.
- Oracle XE in a container is **not** a production database posture; it has
  resource limits and is not patched on a managed cadence.
- Scaling is vertical only. Acceptable for ≤10 demo users.

**Follow-ups required**

- For any phase-2 production rollout, revisit with: RDS Oracle SE2, ECS
  Fargate (or EKS), S3 + CloudFront for the SPA, ALB in front of the API,
  and a managed certificate. This is recorded as a "production
  recommendation" in `ARCHITECTURE.md` and is **not** scoped for the demo.

## References

- `docs/ARCHITECTURE.md` — §2 (Architecture Style), §5 (AWS Infrastructure),
  the originating doc
- `docs/discovery/CALL_NOTES_2026-04-28.md` — initial scoping
- `docs/discovery/CALL_NOTES_2026-05-05.md` — technical discovery
- `ADR-008` — HTTP for the demo (related deployment-posture decision)
- `ADR-010` — `seed_oracle.py` as schema authority (no migration tooling on
  the container)
