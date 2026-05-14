# ADR-003 — JWT in httpOnly Cookie

| Field | Value |
|---|---|
| Status | Superseded by ADR-004 |
| Date | 2026-05-14 |
| Author | C&T BA (Claude) — extracted from ARCHITECTURE.md §11 by architecture refactor |
| Supersedes | — |
| Superseded by | ADR-004 |

## Context

Once a user has been verified by ID.me and their role resolved from Oracle
(see ADR-002), the backend issues a session credential. The choice of
*where* that credential lives in the browser determines the practical
exposure to XSS, CSRF, and token-theft attacks.

Two options were on the table:

- `localStorage` / `sessionStorage` — readable by any JavaScript on the
  page; vulnerable to XSS-based token exfiltration.
- `httpOnly` cookie — not readable from JavaScript; the browser attaches it
  automatically on same-origin requests.

C&T's prior engagement (VMS v2) established a security standard mandating
the cookie-based approach. OWASP guidance has long recommended against
storing bearer tokens in web storage for the same reason.

## Decision

> ⚠️ This decision is superseded by ADR-004. The text below is preserved for
> historical context.

JWT stored in `httpOnly`, `Secure`, `SameSite=Strict` cookie. Access token
TTL of 60 minutes, configured via the `ACCESS_TOKEN_EXPIRE_MINS` environment
variable. The token carries the user's role and `employee_id` as claims.

## Rationale

Consistent with C&T security standard (see VMS v2 ADR-005). Prevents
XSS-based token theft. `localStorage` explicitly avoided per OWASP guidance.

## Consequences

**Positive**

- Token cannot be read by injected JavaScript — XSS-based exfiltration is
  blocked at the storage layer.
- Aligns with the C&T security standard, so reviewers familiar with prior
  engagements recognise the posture immediately.
- Browser handles attachment automatically; no client-side bearer-header
  plumbing required.

**Negative**

- `SameSite=Strict` blocks the cookie on cross-site redirects, which breaks
  the post-ID.me return leg of the OAuth flow. This is the primary trigger
  for ADR-004.
- The 60-minute TTL forces re-verification mid-session for typical
  coordinator usage. Addressed in ADR-004.
- Embedding `employee_id` (PII per `DATA_MODEL.md` §7) in a long-lived
  bearer token expands the blast radius if a token is ever leaked.
  Addressed in ADR-004.

**Follow-ups required**

- All four of TTL, `SameSite`, env-var name, and the PII claim are revised
  in **ADR-004**. This ADR is retained as a historical record only.

## References

- `docs/ARCHITECTURE.md` — §8.1 (Authentication Flow), the originating doc
- `ADR-004-session-cookie-and-jwt.md` — supersedes this decision
- `docs/discovery/CALL_NOTES_2026-05-09.md` — user-journey walkthrough that
  triggered the supersession
- OWASP Cheat Sheet — "Session Management"
- C&T internal standard — VMS v2 ADR-005
