# ADR-008 — HTTP for the demo; HTTPS deferred to phase 2

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-05-14 |
| Author | C&T BA (Claude), on behalf of FCPS IT Lead |
| Supersedes | — |
| Superseded by | — |

## Context

2026-05-05 call, "Infrastructure / EC2 Instance":

> "Public IP assigned. SSL/TLS not required for the demo — HTTP is acceptable.
> HTTPS is a production requirement, not a demo one."

The demo runs on a single EC2 t3.medium with a public IP — no domain name, no
ACM certificate, no ALB or CloudFront. Nginx terminates HTTP on port 80 and
proxies `/api/*` to FastAPI on port 8000.

ID.me's OAuth callback can target an `http://` URL only when the application is
registered as a sandbox/non-production app (see ADR-007). Production ID.me
rejects non-HTTPS redirect URIs.

`ARCHITECTURE.md` §8.1 currently says the JWT cookie is `Secure` — but
`Secure` cookies cannot be set over plain HTTP, which would silently break the
demo. This ADR resolves that conflict.

## Decision

- **The demo runs on HTTP only.** No TLS termination on the EC2 for the demo.
- **Cookie `Secure` flag is environment-driven** via `JWT_COOKIE_SECURE`,
  defaulting to `false`. For the demo it is left at `false`; for phase 2 it
  flips to `true` with no code change. (See ADR-004.)
- **The ID.me sandbox application has the HTTP redirect URI registered**
  exactly as `http://<EC2_PUBLIC_IP>/verification/callback`. Production will
  register an HTTPS redirect URI under a different ID.me application.
- **HTTPS is a phase-2 production blocker.** The termination strategy
  (ALB + ACM vs Nginx-on-instance with Let's Encrypt) is a phase-2 ADR.

## Consequences

**Positive**

- Eliminates demo-time complexity: no domain name, no certificate provisioning,
  no certificate-rotation automation, no ALB.
- Faster onboarding for the demo audience — they hit an IP and a portal opens.

**Negative**

- Cookies are observable in transit if the HTTP traffic is intercepted on the
  same network. Mitigated by:
  - Short JWT TTL (4 h — ADR-004)
  - No production data or credentials (ADR-007)
  - Demo is short-lived (single audience showcase)
- Some browsers may show a "Not secure" warning that distracts demo viewers.
  Accepted; FCPS IT Lead is aware.

**Follow-ups required**

- Update `ARCHITECTURE.md` §8.1 to note that `Secure` is env-driven and
  disabled for the demo (this also resolves the conflict captured by ADR-004).
- Add `JWT_COOKIE_SECURE=false` to `.env.example` with a comment marking the
  env-driven nature.
- Phase 2 ADR: choose HTTPS termination strategy.

## References

- `docs/discovery/CALL_NOTES_2026-05-05.md` — "Decisions Made on This Call"
- `docs/requirements/REQUIREMENTS.md` NFR-14
- `docs/requirements/FUNCTIONAL_DESIGN.md` OQ-FD-01
- `ADR-004` — Session cookie and JWT reconciliation
- `ADR-007` — Synthetic data + ID.me sandbox
