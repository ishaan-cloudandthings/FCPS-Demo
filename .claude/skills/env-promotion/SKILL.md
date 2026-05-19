---
name: env-promotion
description: Produce or update the environment-promotion playbook (dev → staging → prod), governance CI pipeline, and incident runbook for the Staff Procurement Portal (Docker Compose + EC2). Used by the Administrator agent.
---

# Skill: Environment Promotion — Staff Procurement Portal

## When to use this

The project is approaching its first production deploy, or you need to update the promotion gates after a learning from staging.

## Outputs

| File | Purpose |
|---|---|
| `docs/ENV_SETUP.md` | How to provision each environment from scratch |
| `docs/PROMOTION.md` | Exact steps for each promotion |
| `docs/INCIDENT_RUNBOOK.md` | What to do when production breaks |
| `docs/DEVSECOPS.md` | Secrets, supply chain, SAST/DAST cadence, threat model |
| `docs/SECRETS.md` | Secret-handling policy |
| `.github/workflows/governance.yml` | CI gate enforcing per-PR governance rules |
| `.github/workflows/deploy-staging.yml` | EC2 deploy to staging |
| `.github/workflows/deploy-prod.yml` | EC2 deploy to prod (with human approval gate) |

## Promotion gates

### dev → staging
- Governance CI green on the merged PR.
- Unit-test coverage >= 80%.
- Linters clean (ruff, eslint, yamllint).
- gitleaks clean.
- pip-audit / npm audit: no Critical/High.
- bandit / CodeQL: no Critical/High.
- For changes to `backend/app/auth/**`: `red-zone-architect-approved` label + `Decision-trail:` comment on PR.

### staging → UAT (manual)
- docker compose up on EC2 succeeds with no errors.
- seed_oracle.py completes on staging Oracle.
- SIT exit criteria met (zero Critical/High open).
- Regression suite green.
- Sprint stories have QC sign-off comments in Jira.

### UAT → prod (manual + 4-eyes)
- Written client UAT sign-off captured in `docs/uat/uat-sign-off-sprint-N.md`.
- INCIDENT_RUNBOOK.md updated for any new failure modes.
- On-call developer named in the release note.
- Release tag created (`v<major>.<minor>.<patch>`).
- Two named approvers click the deploy workflow's "Approve" button.

## Staff Procurement Portal rollback procedure

**Application rollback:**
```bash
# Redeploy previous tag via GitHub Actions
gh workflow run deploy-prod.yml -f rollback_to=<previous-sha>
```

**Oracle data rollback:**
- There are no migration scripts — Oracle schema is managed by `seed_oracle.py`.
- If a schema change was deployed, restore from the pre-deploy Oracle snapshot (if taken) or re-seed from scratch.
- Always take an Oracle export before any schema-changing deploy: `docker compose exec db exp ORACLE_USER/ORACLE_PASSWORD file=/tmp/pre-deploy.dmp`

## Staff Procurement Portal DevSecOps notes

- **Secrets:** IDME_CLIENT_SECRET, ORACLE_PASSWORD, JWT_SECRET_KEY, EC2_SSH_KEY — never in repo. Use environment variables; manage real values in AWS Secrets Manager for staging/prod, `.env` for dev only.
- **Supply chain:** Dependabot weekly, `pip-audit`, `npm audit` on each PR.
- **SAST:** bandit (Python) and CodeQL on each PR.
- **Dynamic analysis:** OWASP ZAP weekly against staging EC2.
- **PII:** EMPLOYEE_ID, FULL_NAME, EMAIL in STAFF table — encrypted at rest on EC2 EBS, encrypted in transit via HTTPS. Never logged. Audit log for any access to CONTACT_NAME/CONTACT_EMAIL/BANK_DETAILS.
- **ID.me secrets:** IDME_CLIENT_SECRET and IDME_REDIRECT_URI must match exactly between `.env` and ID.me developer console. Any mismatch causes a complete auth failure.

## Governance CI gates (governance.yml)

1. PR template completeness: Comprehension Declaration >= 100 chars.
2. Zone label present on PR.
3. Pytest + coverage >= 80%.
4. Linters: ruff, eslint, yamllint.
5. Secrets scan: gitleaks.
6. Dependency scan: pip-audit, npm audit.
7. SAST: bandit, CodeQL.
8. Red-zone path guard: changes to `backend/app/auth/**` require `red-zone-architect-approved` label and `Decision-trail:` comment.

## Refuse-and-flag

- Asked to disable a gate "just for this deploy". Refuse. Suggest a documented, time-boxed waiver.
- Asked to put a real secret into a repo file. Refuse. Show the env-var pattern.
- Asked to promote to prod without UAT sign-off. Refuse. List the missing artefact.
- Asked to skip Oracle export before a schema-changing deploy. Flag strongly.
