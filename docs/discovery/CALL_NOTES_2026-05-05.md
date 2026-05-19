# Requirements Call Notes — Staff Procurement Portal

---

## Meeting Details

| Field | Value |
|---|---|
| Date | 2026-05-05 |
| Type | Technical Discovery |
| Attendees | IT Lead, C&T Project Lead, C&T Tech Lead |
| Facilitator | C&T Tech Lead |
| Duration | 60 minutes |

---

## Context

Technical deep-dive with the IT Lead. Goal: understand the existing infrastructure,
confirm the Oracle schema, validate the ID.me integration approach, and establish what
the C&T team will build vs what Staff Procurement Portal IT will provide.

---

## Infrastructure

### EC2 Instance

- Single AWS EC2 t3.medium already provisioned and accessible.
- Ubuntu 22.04 LTS. Docker and Docker Compose installed.
- The demo will run entirely on this instance — frontend (Nginx), backend (FastAPI),
  and Oracle XE all in the same Docker Compose stack.
- Public IP assigned. SSL/TLS not required for the demo — HTTP is acceptable.
- SSH access: IT Lead will provide the key pair to C&T before development starts.

### Oracle XE

- Oracle XE 21c already running as a Docker container on the EC2 instance.
- C&T will NOT connect to the live Oracle instance during development.
  We seed our own local Docker container using `scripts/seed_oracle.py`.
- IT Lead confirmed the schema C&T needs to create: STAFF and PROCUREMENT_ITEMS tables.
  (Full schema captured in `docs/DATA_MODEL.md`.)
- oracledb thin mode confirmed — no Oracle Client installation required.
- Connection: host=`localhost`, port=`1521`, service name=`XEPDB1`. Credentials via `.env`.

### Network

- Nginx will reverse-proxy all `/api/*` requests to FastAPI on port 8000.
- React SPA served statically by Nginx on port 80.
- Oracle container accessible only within the Docker network — not exposed externally.
- ID.me callback must be a publicly reachable URL. IT Lead will whitelist the EC2 IP.

---

## ID.me Integration

### What IT Lead confirmed

- Staff Procurement Portal has an existing ID.me organisational account.
- A sandbox application already exists under that account. C&T will use sandbox
  credentials for the demo — not the production ID.me application.
- Sandbox credentials (IDME_CLIENT_ID, IDME_CLIENT_SECRET) will be shared via
  1Password before development starts. Not to be stored in the repo.
- Scopes needed: `openid email`. IT Lead confirmed these are sufficient to
  identify the user and match them against the STAFF table by email.
- Redirect URI must be registered in the ID.me developer console exactly as it will
  appear in the app. Format: `http://<EC2_PUBLIC_IP>/verification/callback`.
  C&T to confirm the exact URI; IT Lead registers it.

### Flow confirmed

1. User clicks "Verify with ID.me" on the registration page.
2. Frontend redirects to ID.me with `client_id`, `redirect_uri`, `scope`, `state`.
3. User authenticates with ID.me.
4. ID.me redirects back to `redirect_uri` with `code` and `state`.
5. Frontend passes `code` to the FastAPI backend.
6. Backend exchanges `code` for an ID token via ID.me token endpoint.
7. Backend validates the ID token, extracts `email`.
8. Backend queries Oracle STAFF table by email to get ROLE and PROCUREMENT_LEVEL.
9. Backend issues JWT with claims: `employee_id`, `role`, `procurement_level`.
10. JWT stored in httpOnly, Secure, SameSite=Strict cookie.

### Known risk

IT Lead flagged: if the redirect URI in the app does not exactly match what is
registered in the ID.me console, the OAuth flow will fail with no useful error message.
This has caught them before. Must be verified before the first end-to-end test.

---

## Oracle Schema

IT Lead reviewed and approved the schema in `docs/DATA_MODEL.md`. Specific confirmations:

- STAFF table: confirmed columns, types, constraints. PROCUREMENT_LEVEL range 0–3 is correct.
- PROCUREMENT_ITEMS table: confirmed columns. BANK_DETAILS field confirmed as sensitive —
  "that field alone is the reason we need access control."
- Seed data: C&T creates its own synthetic seed data for the demo. Real staff records
  will never be used in development or the demo environment.
- Primary keys as NUMBER GENERATED ALWAYS AS IDENTITY — confirmed Oracle XE 21c supports this.
- SCREAMING_SNAKE_CASE naming for all Oracle objects — confirmed matches Staff Procurement Portal convention.

---

## Data and Sensitive Information

| Data | Sensitivity | Handling |
|---|---|---|
| IDME_CLIENT_SECRET | Critical | 1Password only. Never in repo. |
| ORACLE_PASSWORD | High | `.env` for dev, environment variable on EC2. Never in repo. |
| JWT_SECRET_KEY | High | Same as above. |
| EC2_SSH_KEY | High | IT Lead holds original. C&T receives a copy via 1Password. |
| STAFF seed data | PII (synthetic) | Fictional names and IDs only. Never real employee data. |
| BANK_DETAILS seed data | Sensitive (synthetic) | Fictional account numbers only. |

---

## Decisions Made on This Call

- **C&T builds on local Docker Compose, deploys to the existing EC2 via GitHub Actions.**
  IT Lead does not want C&T managing the EC2 directly — deploy via SSH in CI only.
- **ID.me sandbox for the demo.** Production ID.me integration is phase 2.
- **No real staff data in the demo environment at any point.**
  Seed data will be synthetic. Confirmed by IT Lead.
- **Oracle schema managed by `seed_oracle.py`.** No migration tool — too heavyweight for a demo.
- **oracledb thin mode.** No Oracle Client needed. Confirmed as viable by IT Lead.
- **HTTP acceptable for the demo.** HTTPS is a production requirement, not a demo one.

---

## Open Questions

- [ ] Exact EC2 public IP — needed to register the ID.me redirect URI. Owner: IT Lead — by 2026-05-08.
- [ ] 1Password vault access for C&T team — needed before first ID.me integration work. Owner: IT Lead — by 2026-05-08.
- [ ] GitHub Actions SSH deploy — does Staff Procurement Portal IT firewall allow inbound SSH from GitHub Actions IPs? Owner: IT Lead — by 2026-05-10.
- [ ] Oracle XE service name on the EC2 — is it `XEPDB1` or a custom name? Owner: IT Lead — by 2026-05-08.

---

## Exact Quotes Worth Capturing

> "That BANK_DETAILS field alone is the reason we need access control. If a teacher
> can see vendor bank account numbers, we have a serious problem." — IT Lead

> "Do not touch the production Oracle instance. Not even to look at it.
> Use your own container for development." — IT Lead

> "The redirect URI mismatch has broken our ID.me integrations twice before.
> Whatever URL you put in the app, send it to me first so I can register it
> before you test." — IT Lead

---

## Next Steps

| Action | Owner | By when |
|---|---|---|
| Share EC2 public IP | IT Lead | 2026-05-08 |
| Share ID.me sandbox credentials via 1Password | IT Lead | 2026-05-08 |
| Confirm Oracle XE service name on EC2 | IT Lead | 2026-05-08 |
| Confirm GitHub Actions SSH access through Staff Procurement Portal firewall | IT Lead | 2026-05-10 |
| Register ID.me redirect URI once EC2 IP confirmed | IT Lead + C&T Tech Lead | 2026-05-12 |
| Begin `seed_oracle.py` implementation | C&T Developer | 2026-05-06 |

---

## Raw Notes

- IT Lead joined 5 minutes late. Started with a walkthrough of the EC2 console.
- Docker Compose already has a `docker-compose.yml` on the instance from a previous
  project — C&T will overwrite it with our own.
- Oracle XE container was started manually. No systemd service yet — IT Lead
  will add auto-start before the demo.
- ID.me developer console access: IT Lead owns the account. C&T does not get
  direct console access — all changes go through IT Lead.
- IT Lead was very clear: "I trust C&T to build it, but I need to control what
  goes into the ID.me console and what touches the EC2."
- C&T Tech Lead confirmed oracledb thin mode works with Oracle XE 21c — tested
  before the call.
- No load balancer, no CDN, no WAF for the demo. Raw EC2 with Nginx.
