# Design Rationale — Staff Procurement Portal

| Field | Value |
|---|---|
| Document | DESIGN_RATIONALE.md (consolidated) |
| Date | 2026-05-16 |
| Author | C&T BA (Claude) |
| Spec sources | [REQUIREMENTS.md](../requirements/REQUIREMENTS.md), [FUNCTIONAL_DESIGN.md](../requirements/FUNCTIONAL_DESIGN.md), [brand.md](./brand.md) |
| Mockups | `docs/design/01-login.html` … `docs/design/06-access-denied.html` |
| Status | Living document — appended as each screen is designed and reviewed |

This is the single design rationale for every page-level component in the
Staff Procurement Portal demo. The **Shared design language** section
covers patterns and tokens used across all screens — read it first. Each
per-screen section below references it rather than repeating it.

---

## Shared design language

### Brand tokens

Defined in [`brand.md`](./brand.md). Used here:

- **C&T Blue `#3B4EA8`** — structural colour (header, brand panel, focus rings, info callouts).
- **C&T Orange `#F47920`** — accent and action colour (CTA fill, brand chip, eyebrow text, italic wordmark accent, status indicators).
- **Surface `#F5F6FA`** — page background base.
- **Inter** typeface — `400` body, `500` UI labels, `600` strong, `700` headings, `700 italic` for the "Things"-style accent words.

Colour discipline: **Blue carries structure. Orange carries action.** Each
screen uses orange in at most five clearly-scoped places so it stays loud where
it matters (the CTA).

### Shared layout components

#### Browser-chrome frame

Every screen mockup sits inside a "browser frame" (URL bar + traffic-light
dots). Purely a review affordance — each mockup reads as a finished artefact,
not a wireframe.

#### Header (dark)

- C&T Blue vertical gradient (`#3B4EA8` → `#2D3D8A`)
- Fine 2 px orange under-rule
  (`linear-gradient(90deg, transparent, #F47920, transparent)`)
- **Left:** brand chip (orange tile with white "F" monogram) + portal wordmark.
  The chip is a placeholder for the Staff Procurement Portal logo asset (REQUIREMENTS.md OQ-05);
  it slots in at the same dimensions once the asset arrives.
- **Right, anonymous pages:** "Built by Cloud & Things" text-only attribution.
- **Right, authenticated pages:** user pill (`Signed in · ROLE · LEVEL`)
  + Log out button with icon.

> **Why no logo in the dark header?** The C&T logo file has a light-grey
> cloud interior + blue "Cloud" wordmark that both lose contrast on dark
> backgrounds. Earlier drafts wrapped the logo in a white pill — visually
> sticker-y. Dropped in favour of text-only attribution; the **real logo
> lives in the light footer**, where it reads cleanly.

#### Footer (light)

- White background, 1 px border-top.
- **Left:** `© Staff Procurement Portal · Procurement Portal demo`
- **Right:** `Built by` + real Cloud & Things logo image at 22 px height.

#### Ambient page background

Subtle radial gradients (faint blue from top-left + faint orange from
bottom-right) layered over the C&T Surface grey. Below the conscious-noticing
threshold; communicates "this product is intentionally designed".

#### Primary CTA

- Linear gradient `#F47920` → `#DA660D`
- 1 px white inset highlight + branded soft shadow
- Hover: 1 px translateY lift + larger shadow
- Active: returns to baseline
- Focus: 3 px C&T Blue outline, 2 px offset

### Accessibility patterns (every screen)

- **Skip-to-main-content** link as the first focusable element.
- **Semantic landmarks** — `<header role="banner">`, `<main role="main">`,
  `<footer role="contentinfo">`.
- **Real `<button>` / real `<a>`** — never `<div onClick>` (FD §7.8).
- **Visible focus rings** on every interactive element, contrast ≥ 3:1.
- **Page titles** set dynamically (FD §7.8): `Login | Staff Procurement`,
  `Verifying… | Staff Procurement`, `Vendors | Staff Procurement`, etc.
- **`prefers-reduced-motion`** respected — spinners and progress bars halt.
- **Colour never the sole signal** (FR-18 / NFR-04) — pairs with a text label
  or icon shape everywhere it's used to convey state.

### Sample data discipline

All vendor names, contact names, and emails in the mockups are **synthetic**
per [ADR-007](../adr/ADR-007-synthetic-data-and-idme-sandbox.md). Vendor
names mirror the categories from `DATA_MODEL.md` §8 but are not real
suppliers.

### Open follow-ups that apply everywhere

- **Staff Procurement Portal logo asset** (REQUIREMENTS.md OQ-05) — replaces the orange "F" brand
  chip in the header once provided.
- **`jest-axe` accessibility audit** once the React components are built
  (FUNCTIONAL_DESIGN.md §14).

---

## Screen 1 — Login

**File:** [`01-login.html`](./01-login.html)
**Route:** `/` and `/?reason=session_expired`
**Spec sources:** REQUIREMENTS.md §3.1 + §8; FUNCTIONAL_DESIGN.md §7.3 (Login.jsx)
**Component zone:** 🟡 Yellow

### Goals

1. Make the only action on this screen ("Verify with ID.me") completely
   unambiguous. There is nothing else to do here.
2. Set the expectation that this is an *internal Staff Procurement Portal tool* with
   verified-identity access — so a teacher who lands here understands why
   they're being routed through ID.me.
3. Handle the session-expired return path without alarming the user
   (REQUIREMENTS.md FR-08; 2026-05-09 IT Lead quote: *"I don't want teachers
   staring at a spinning wheel"*).

### Layout decisions

- **Split-panel canvas (5fr / 7fr).** Left brand panel asserts identity and
  value proposition. Right sign-in panel holds the single action. Stacks
  vertically below 900 px so the action remains tappable on a school
  workstation in a side-by-side window.
- **Brand panel content** — short, confident copy ("Approved vendors, *one
  search away.*" with the second line in italic C&T Orange — picks up the
  "Things" italic wordmark style from `brand.md`) plus a trust pill at the
  bottom that names ID.me verification. *(Earlier drafts also mentioned
  audit-logged access; the audit story was removed by
  [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md).)*
- **Decorative grid + concentric ring** on the brand panel — subtle visual
  texture so the colour panel feels designed, not empty.
- **Three vertical blocks in the sign-in panel:** eyebrow ("Sign in") +
  headline ("Welcome to the Portal"), short value prop, an identity-policy
  callout, then the CTA. Each answers a question: *what is this? why am I
  here? how do I get in?*
- **Identity callout is a soft-blue tinted box** with an info icon and a
  one-line policy statement. Blue (not orange) because it is informational,
  not action-required.
- **No username / password fields, ever** — FR-01 / FR-20 says ID.me is the
  only identity provider. Putting a "username" field on screen even greyed
  out would invite confusion about what to type.

### The session-expired variant

The HTML stacks two states: `/` (default) and `/?reason=session_expired`.
In production this is one screen with a query parameter; for design review
they're shown side-by-side.

- **Soft-orange banner** with a clock icon at the top of the sign-in panel.
  Attention-coloured, not error-coloured. 2026-05-09 IT Lead quote drives
  this — *"If someone is denied, they shouldn't feel like they crashed the
  system"* applies equally to a routine session expiry.
- Banner copy reuses REQUIREMENTS.md FR-08 wording exactly:
  *"Your session has expired. Please verify again."*
- `role="alert"` so a screen reader announces the banner when the page loads.

### Behaviour (engineer handoff)

```js
onClick: // "Verify with ID.me"
  POST /api/auth/login
  → { authorize_url }
  → window.location.assign(authorize_url)
```

The CTA is **not** a hyperlink. It triggers an API call first (to generate
the server-side `state`), then redirects. A bare `<a href="…">` would lose
that step.

`?reason=session_expired` is the only query-param the page reads. Any other
value or no value renders the default state.

### What I left out (and why)

- **No marketing copy.** This is an internal staff tool. 2026-04-28
  Coordinator quote: *"we don't need anything fancy"*.
- **No "Forgot password"** — there is no password (FR-01).
- **No "Help" link** — the Access Denied screen carries the contact
  instruction (FR-04); a teacher who can't get past Login just needs to
  verify.

---

## Screen 2 — Verification Callback

**File:** [`02-verification-callback.html`](./02-verification-callback.html)
**Route:** `/verification/callback?code=…&state=…`
**Spec sources:** FUNCTIONAL_DESIGN.md §7.2 + §7.3 (VerificationCallback.jsx); FD §10 error model
**Component zone:** 🟡 Yellow

### Goals

1. Show the user that *something is happening* the moment ID.me redirects
   back. Without feedback the screen looks broken in the 1–3 s the backend
   takes to exchange the code, validate the ID token, and look up Oracle.
2. Honour the FD §7.3 / §7.4 constraint: **bounded** loading state, **never**
   an infinite spinner.
3. Give the user a way out if the network actually fails.

### Two states

#### State A — "Verifying your identity…" (0 to 10 s)

- **Dual-colour spinner** — blue track with a partial orange arc rotating
  over it, plus a soft orange halo behind. Both brand colours in their
  structural / accent roles.
- **"Step 2 of 2 · Identity check" eyebrow** — gives the user a sense of
  *where they are* in the sign-in flow.
- **Headline** *"Verifying your identity…"* in plain English. The ellipsis
  signals progress.
- **Sub** sets the expectation that there's both an identity check (ID.me)
  and an access check (Oracle STAFF lookup) happening.
- **Bounded progress bar** beneath the sub — orange gradient on a blue-50
  track, fills 0 → 100 % over 3 s and stays. Label underneath: *"Usually
  takes 1–3 seconds"*. The bar visualises the expectation; the label states
  it. If the bar finishes and the page is still there, the user knows
  something is unusual *before* the 10 s hard timeout fires.

#### State B — "Taking longer than expected" (after 10 s)

- **Soft orange halo + inset disc + clock icon** — bespoke "delay" visual,
  not a generic warning sign.
- **Headline** intentionally non-blaming: *"This is taking longer than
  expected"* — doesn't say "error", "failed", or "denied".
- **Sub** is honest about state: *"Your sign-in hasn't been saved"* —
  important so the user doesn't wonder if they're half-logged-in.
- **Primary CTA "Try signing in again"** + secondary **"Back to sign in"**
  link. Two paths to the same exit on purpose: keyboard tab reaches the
  button first; mouse scanners notice the link.

### Why the retry goes back to Login (not POST callback again)

Per [ADR-004](../adr/ADR-004-session-cookie-and-jwt.md) D-FD-08, the OAuth
`state` is **one-shot** — the cache entry is deleted on first lookup.
Retrying `POST /api/auth/callback` with the same `code` + `state` would 400
with *"Authentication request expired"*. The retry deliberately routes back
to `/` so the user can start a fresh OAuth flow with a fresh `state`.

### Where the other error paths go

Most failure modes route away before this component renders:

| Failure | Detected when | User lands |
|---|---|---|
| 400 — `state` invalid / expired | callback POST returns 400 | `/` with toast |
| 401 — ID-token validation failed | callback POST returns 401 | `/` with toast |
| 403 — `NON_STAFF` | 403 + `X-Auth-Reason: NON_STAFF` | `/access-denied` |
| 403 — `NOT_REGISTERED` | 403 + `X-Auth-Reason: NOT_REGISTERED` | `/access-denied` |
| 502 — ID.me unreachable | callback POST returns 502 | `/` with toast |
| Network failure / no response in 10 s | SPA `AbortController` | **State B** |

State B is specifically the "no answer at all" case.

### Behaviour (engineer handoff)

```js
useEffect(() => {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 10_000);
  const { code, state } = parseSearch();
  if (!code || !state) {
    navigate("/", { state: { reason: "missing_oauth_params" } });
    return;
  }
  apiFetch("/api/auth/callback", { method: "POST", signal: ctrl.signal,
    body: JSON.stringify({ code, state }) })
    .then(handleResponse)
    .catch(err => {
      if (err.name === "AbortError") setView("timeout");
      else navigate("/", { state: { reason: "callback_error" } });
    })
    .finally(() => clearTimeout(timer));
}, []);
```

- The component is mounted **once**. No retry-with-backoff loop.
- "Try signing in again" calls `navigate("/")`, not a retry POST.

### Accessibility (NFR-04)

- **`role="status"` + `aria-live="polite"`** on the verifying card.
- **Spinner has `aria-hidden="true"`** — the textual heading is the announced
  content. SR users hear *"Verifying your identity… Just a moment while we
  check your staff procurement access"* once.
- **`prefers-reduced-motion`** disables both spinner rotation and progress
  slide.

### Open follow-up

Confirm the 10 s SPA timeout sits cleanly outside the 5 s server-side ID.me
token-exchange timeout (FD §6.1 D-FD-10). If the backend timeout ever
increases, this SPA value must track.

---

## Screen 3 — Vendor List (unified for STAFF and ADMIN)

**File:** [`03-vendor-list.html`](./03-vendor-list.html)
**Route:** `/vendors` (single route; React picks the right `<VendorList />` rendering by role)
**Spec sources:** REQUIREMENTS.md §3.1 + §3.2 + §8; FUNCTIONAL_DESIGN.md §7.1, §7.3, §7.7
**Component zone:** 🟡 Yellow

> **One screen, RBAC-driven data filter.** The vendor list is a single
> component. The backend's `rbac_service` (FD §6.7) decides what rows and
> columns the user receives; the frontend renders whatever it gets. Staff
> sees only APPROVED rows with role-appropriate columns; admin sees every
> status with the extra Status · row-drill-in columns. The page
> heading, lead, and toolbar adapt by role but the underlying layout,
> typography, and component vocabulary are identical.

### Goals

1. Make finding a vendor by name take less than 3 seconds — for both
   teachers (LEVEL 1 / 2) and procurement coordinators (LEVEL 3).
2. Make the LEVEL 1 → LEVEL 2 → ADMIN column expansion visually obvious so
   the RBAC posture (FR-09 … FR-13) is inspectable in the demo.
3. Replace the coordinator's email-driven workflow (2026-04-28 call:
   *"I spend half my day answering emails…"*) — admin sees every vendor +
   status on one screen, with one-click status filtering.
4. **Keep contact email off the list page entirely** — neither rendered in
   the UI nor returned by the list endpoint. Email lives only in the
   admin-only `VendorDetail` response per
   [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md):
   *"API responses match UI display."*
   *(Earlier drafts also discussed keeping bank-details off the list +
   tightening an audit-log story; both are out of scope per
   [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md).)*
5. Communicate "empty list" clearly so users never see a blank table
   (FR-17, NFR-11).

### Four variants in the file

1. **Staff · LEVEL 1** — 3 columns: Vendor · Category · Item/Service.
   No row-click. Lead reads *"Approved vendors cleared for staff procurement."*
2. **Staff · LEVEL 2** — 4 columns: + Contact name. Otherwise identical to
   L1. Lead reads *"Approved vendors with contact details for Staff Procurement Portal
   procurement."* (Per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md),
   `contact_email` is **not** returned by the list endpoint at L2 — email
   lives only in the admin-only detail response.)
3. **Admin** — 6 columns: + Status · row-chevron. Rows clickable. Toolbar
   gains the **status filter** dropdown. Lead reads *"Every vendor across
   every status. Clicking a row opens the detail view."*
4. **No search matches** — search input populated with "zyxx", table area
   replaced by an empty state. Shape is identical regardless of role.

### What adapts by role

| Element | Staff L1 | Staff L2 | Admin |
|---|---|---|---|
| Page heading (`h1`) | "Vendors" | "Vendors" | "Vendors" |
| Page lead copy | approved-only | approved + contact | every-status |
| Count pill | `5 approved vendors` | `5 approved vendors` | `12 vendors` (or `N of 12 matching`) |
| Status filter | absent | absent | present |
| Columns | 3 | 4 | 6 |
| Contact column | absent | **name only** | **name only** |
| Status badge column | absent | absent | present |
| Row clickable | no | no | yes (vendor name `<a>` → detail) |
| `contact_email` | **list does not return or render** — detail-only per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md) | | |
| Bank details | **out of scope** per [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) — never shown, never returned | | |

Everything else — header, footer, search input, table-card chrome, category
pills, ambient background — is **identical** across roles. The component
vocabulary is one design system, not two.

### Why the layout converges

In an earlier draft, the staff and admin views were two separate screens
with different page titles ("Approved Vendors" vs "All Vendors") and
slightly different table densities. Consolidating into one screen does
three useful things:

1. **One mental model.** Coordinators who occasionally borrow a teacher's
   workstation aren't relearning a layout. Teachers promoted to LEVEL 2 see
   the same screen with one new column, not a redesigned page.
2. **One component implementation.** FD §7.4 already specifies a single
   `<VendorTable variant="staff-L1" | "staff-L2" | "admin" />`. The page
   matches.
3. **Honest UX.** Staff aren't told "you're using the *staff* view" — they
   just see vendors. Admin sees more because their auth claims unlock more.

### Authenticated header pattern (used here and onwards)

- **User pill** on the right of the header: small orange-gradient avatar
  dot + "Signed in" + role tag ("Staff · L1" / "Staff · L2" / "Admin · L3").
  The user pill is **decorative** — REQUIREMENTS.md doesn't show the user's
  name (FD OQ-FD-03 defaulted to "no name in header" to keep PII off-screen).
- **Log out button** to the right of the pill — outlined-on-dark, icon-led.
  Calls `POST /api/auth/logout` per FR-07.

### Table design

- **Light-blue tinted header row** (`--blue-50`), uppercase tracked-out
  column labels in deep blue — reads as structural, doesn't compete with row
  content.
- **Category column** uses small coloured-dot pills: Technology blue,
  Furniture purple, Facilities green, Supplies amber, Services red. The dot
  + label pairing means colour is never the sole signal (FR-18 / NFR-04).
- **Contact column** (L2 + admin) shows the contact's **name only**. The
  email is **not** in the list endpoint's API response either, per
  [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md) — *"API
  responses match UI display."* Email lives only in the admin-only
  `VendorDetail` schema. Keeps the list compact, avoids long email strings
  causing column reflow, and ensures L2 staff cannot inspect email values
  via browser devtools.
- **No per-vendor avatars or logos.** An earlier draft used coloured
  letter-tile avatars on each row. Removed because (a) we don't have real
  vendor logos in scope, (b) the letters were noise — the vendor name is
  already the primary identifier, and (c) it made the table feel more like
  a "people directory" than a "lookup tool".

### Status badges (admin only)

Pill design — small text-with-coloured-dot, never colour alone (FR-18 /
NFR-04). Brand colour roles:

- `APPROVED` — green-50 bg / green-700 text / green-500 dot
- `PENDING` — gray-50 / gray-700 / gray-500 (intentionally neutral —
  "awaiting action" reads as informational, not urgent)
- `UNDER_REVIEW` — amber-50 / amber-700 / amber-500
- `REJECTED` — red-50 / red-700 / red-500

Every badge meets WCAG 2.1 AA (≥ 4.5:1 for small text). Dots are
decorative; the text label is the announced content. The dropdown filter
reuses the same dots so the filter and the table speak the same language.

### Status filter (admin only)

- **Trigger button** styled like the search input — same height, border,
  shadow, and focus-glow — so the toolbar reads as a single control group.
  "Status:" eyebrow label + selected value + caret.
- **Selected-value visual** shows a coloured dot + status name when
  filtered — the user can see the active filter without opening the menu.
- **Open state** (CSS in file; not rendered in any of the 4 variants): a
  popover beneath the button with 5 options (All / Pending / Under review /
  Approved / Rejected), each with a matching dot. Selected option has a
  blue tinted background + check icon.
- **ARIA** — `aria-haspopup="listbox"`, `aria-expanded`, `role="listbox"`,
  `role="option"`, `aria-selected`.

**Engineer note:** the mockup hand-rolls the listbox for visual fidelity,
but the React implementation should use a tested combobox/listbox library
(e.g. Headless UI `Listbox`) to get focus management, arrow-key navigation,
Escape-to-close, and click-outside dismissal for free. Don't reinvent these
behaviours.

### Bank details — fully out of scope (ADR-012)

`BANK_DETAILS` is no longer part of the product. The column remains in the
Oracle schema (DATA_MODEL.md, locked) but the application code does not
select, return, or render it. No screen shows bank-account information; no
endpoint returns it; the `AUDIT_LOG` table that used to record bank access
is not created.

This earlier section described a "list page doesn't show bank, detail page
does, audit fires on detail" posture. All three claims are no longer
operative — see
[ADR-012](../adr/ADR-012-bank-details-out-of-scope.md) for the rationale
and the full follow-up list.

### Row interaction (admin only)

- **Vendor name is a real `<a>` to `/vendors/{id}`** — primary focusable.
  Tab moves through vendor links row by row; Enter navigates.
- **Whole-row hover** changes background + shifts the chevron right + tints
  it C&T Blue — communicates "this row is clickable".
- **Whole-row click** in production is a JS enhancement that activates the
  vendor link. Not a requirement for a11y because the link itself is
  keyboard reachable.
- **Chevron column** at the right end — reinforces drill-in without taking
  real horizontal space. `aria-hidden`; the link text is announced.

For STAFF variants, the vendor name is **plain text** in the same font weight
and colour as the admin variant's link — but it's not interactive, because
the detail view is admin-only (FR-12). The visual treatment converges; the
behaviour differs.

### Empty / filtered counts

- Staff L1/L2: `5 approved vendors` (white pill on the heading row)
- Admin default: `12 vendors`
- Filter / search active: `N of 12 matching` (number switches to the matching
  count, total stays for context)
- No matches (variant 4): empty state — soft blue radial halo behind a small
  white tile holding the magnifier icon. Copy: *"No results for '\<term>'."*
  + hint to retry.

### Behaviour (engineer handoff)

- Search debounce: **150 ms** (FD §7.4 SearchBar).
- Filter: **client-side substring match** on `vendor_name`, case-insensitive
  (FD §7.7 / [ADR-011](../adr/ADR-011-client-side-search-no-pagination.md)).
- Status filter (admin only): also client-side.
- Column visibility driven by `procurement_level` + `role` from the auth
  store; no role-conditional API calls.
- The data comes from `GET /api/vendors`, which is already RBAC-filtered by
  the backend — the SPA does not re-filter for level / role / status.
- Row click (admin only) → `navigate(\`/vendors/${item_id}\`)`.

### Accessibility

- `<table>` with **visually-hidden `<caption>`** describing scope (changes
  per variant — caption text adapts when filter is applied).
- **`<th scope="col">`** on every column header. Admin's last "actions"
  header has `<span class="visually-hidden">Open</span>` so SR users hear
  "Open" for the chevron column.
- **`<label for>`** paired with `<input type="search">` (label visually
  hidden, read by screen readers).
- **Focus-within** highlights the table row + 2 px C&T Blue outline for
  keyboard navigation.
- Status badges + category pills always pair the colour dot with a text
  label.
- Focus ring on every interactive element ≥ 3:1 contrast.

### What's left out (and why)

- **No bank-details column.** Out of scope per [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md).
- **No email column** — and `contact_email` is **not** in the list-endpoint
  response either, per [ADR-013](../adr/ADR-013-api-responses-match-ui-display.md).
  Email is rendered (and returned) only by the admin-only detail view.
- **No bulk actions.** Read-only portal (D-01).
- **No multi-status filter** (e.g. "Pending OR Under review"). FD §7.7
  specifies a single dropdown.
- **No date columns** in the list. Approval date is in the detail view
  (FR-15).
- **No unit-price column.** Available in the detail view; would clutter the
  list.
- **No sortable columns.** FR-16 specifies search + filter only.
- **No row-click for STAFF.** Detail view is admin-only (FR-12).

### Open follow-up

- Once the production dataset exceeds ~500 rows, revisit the no-pagination
  posture per [ADR-011](../adr/ADR-011-client-side-search-no-pagination.md).

---

## Screen 4 — Vendor Detail

**File:** [`04-vendor-detail.html`](./04-vendor-detail.html)
**Route:** `/vendors/:id` — **admin only** (FR-12)
**Spec sources:** REQUIREMENTS.md §3.2 + §8; FUNCTIONAL_DESIGN.md §7.3 (VendorDetail.jsx), §6.2
**Component zone:** 🟡 Yellow
**Scope note:** Bank-details rendering and audit logging were removed from
this page by [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md). An
earlier draft of this section described a prominent orange Bank Details card
with an "Audit row written" footnote; both are gone.

### Goals

1. Be the deep-read view for one vendor — contact email, unit price,
   approval timestamp, and metadata that don't appear in the list (Screen 3).
2. Make the approval-date display obvious when the vendor is APPROVED
   (FR-15).
3. Stay simple. With bank-details gone, the page becomes three plain
   cards + a metadata sidebar — no special-case styling.

### Two variants in the file

1. **Approved vendor, full data** — Dell Technologies, status APPROVED,
   `approved_at = 2026-03-14`. Demonstrates the green status badge and the
   approval-date pill on the heading row.
2. **Pending vendor** — STEM Lab Solutions, status PENDING, no
   `approved_at`. Demonstrates the pending grey badge and the
   *"— pending approval"* placeholder in the metadata sidebar's "Approved"
   row.

### Layout decisions

- **Back link as first focusable element in `<main>`** — small blue text +
  left arrow. Returns to `/vendors`. Single Tab-stop above the heading.
- **Heading block** — three lines vertically:
  1. **Meta line**: Category pill + Status badge + (if APPROVED)
     approval-date pill with a green tick icon. The approval-date pill is
     on the same row as the badge so the relationship between `status` and
     `approved_at` is visible without scrolling.
  2. **Vendor name** — 2 rem h1, tight letter-spacing.
  3. **Item description** — single-line lead in muted text.
- **Two-column grid below the heading** (`2fr / 1fr`, stacks below 880 px):
  - **Left (main, 2/3):** Item / Service card → Contact card. *(An
    earlier draft included a third Bank Details card here; removed by
    ADR-012.)*
  - **Right (sidebar, 1/3):** Metadata card — Vendor ID, status, approval
    date, created, last update.

### Cards

All three cards (Item / Service, Contact, Metadata) share the same
treatment: white background, 1 px grey border, soft shadow, 12 px radius.
A `card-head` strip with a blue-700 uppercase tracked eyebrow
("ITEM / SERVICE", "CONTACT", "METADATA"). Below the head, a `<dl>`
definition list in a `grid-template-columns: max-content 1fr` grid —
labels in muted grey, values in body text. Consistent rhythm across all
three cards.

The metadata `dl` uses `code` style for the numeric ID and reuses the
status badge component for the status row. Reusing components keeps the
detail page's vocabulary identical to the list page's.

### Status + approval-date display (FR-15)

The "Approved on Mar 14, 2026" pill appears **only when status is APPROVED**.
For PENDING / UNDER_REVIEW / REJECTED it is replaced by the placeholder
*"— pending approval"* in the metadata sidebar's "Approved" row. The pill
sits next to the status badge in the heading meta line so the date is
visible in the same eye-fixation as the status.

### Behaviour (engineer handoff)

```js
// Route guard: ProtectedRoute role="PROCUREMENT_SUPERVISOR"
// On mount:
GET /api/vendors/:id   // returns VendorDetail
  → 200 → render
  → 403 (X-Auth-Reason: ROLE_FORBIDDEN) → navigate("/vendors") with toast
  → 404 → render inline 404 mini-state on this page
  → 500 → toast "Something went wrong. Please try again."
```

- Date formatting: `Intl.DateTimeFormat(undefined, { dateStyle: "medium" })`.
  In production we may want to fix the locale to `en-US` for Staff Procurement Portal.
- Money formatting: `Intl.NumberFormat("en-US", { style: "currency", currency: "USD" })`.
- *No audit-log side effect.* The detail endpoint is a simple read.

### Accessibility

- Each card section uses `<section aria-labelledby="t-…">` with the eyebrow
  carrying the matching `id`, so SR users navigate by region.
- `<dl>` semantics make label / value pairs readable.
- Status badges and category pills pair colour with text (FR-18 / NFR-04).
- Back-link is a real `<a>` with a visible focus ring (3 px C&T Blue).
- Page title (FD §7.8): `<Vendor Name> | Staff Procurement` —
  e.g. `Dell Technologies | Staff Procurement`.

### What's left out (and why)

- **No Bank Details card** — bank-details handling is out of scope per
  [ADR-012](../adr/ADR-012-bank-details-out-of-scope.md).
- **No audit-log footnote** — same ADR. No audit row is written; nothing to
  surface on screen.
- **No edit / approve / reject controls.** Read-only portal (D-01); the
  committee workflow happens offline.
- **No vendor history / audit-access viewer.** Out of demo scope
  (REQUIREMENTS.md §10; D-17). Moot anyway under ADR-012.
- **No related items.** The schema is one row = one vendor offering
  (DATA_MODEL.md §4.2). A future "all items by this vendor" view would need
  a different schema.
- **No print-friendly view.** PDF export is phase 2.

### Open follow-up

- Once `APPROVED_AT` is in `DATA_MODEL.md` (ADR-006 follow-up — still
  required and in force per ADR-012), confirm the date format used in the
  seed data matches `dateStyle: "medium"` rendering.

## Screen 5 — Access Denied

**File:** [`05-access-denied.html`](./05-access-denied.html)
**Route:** `/access-denied`
**Spec sources:** REQUIREMENTS.md §3.3 + §4 FR-04 + §8; FUNCTIONAL_DESIGN.md §6.6, §7.3 (AccessDenied.jsx), §10 error model
**Component zone:** 🟡 Yellow

### Goals

1. Tell the user they're denied — clearly and without making them feel
   they broke something. The 2026-05-09 IT Lead quote drives the whole
   page: *"If someone is denied, they shouldn't feel like they crashed the
   system. It should just say: you don't have access, here's who to call."*
2. Give exactly one next step: contact your procurement coordinator, and
   if you can't / don't want to, leave the portal.
3. Don't leak information about *why* one user is denied versus another —
   distinct copy per `X-Auth-Reason` is OK (per REQUIREMENTS.md journey
   §3.3 and §3.1 step 5), but the page treatment is identical so the user
   isn't told the architecture of the access decision tree.

### Two variants in the file

Both rendered with the same visual structure. The only difference is the
heading + sub copy, driven by the `X-Auth-Reason` response header that the
SPA reads from `POST /api/auth/callback`:

1. **`NON_STAFF`** — user exists in `STAFF`, but `PROCUREMENT_LEVEL = 0`.
   Heading: *"You don't have access to this portal."* Sub: *"Your Staff Procurement Portal
   identity is verified, but your account doesn't have the procurement
   clearance needed to view vendor records."*
2. **`NOT_REGISTERED`** — covers `NOT_FOUND` + `IDME_VERIFIED='N'` +
   `ACTIVE='N'` (combined into one bucket on purpose, per FD §6.6 — no
   account-existence enumeration leak). Heading: *"Identity not verified."*
   Sub: *"We couldn't verify your identity, so you do not have access to
   the portal. Contact your procurement supervisor."*

The two headings are deliberately phrased differently: NON_STAFF is a
*permissions* problem ("you can't go in here"); NOT_REGISTERED is an
*identity-system* problem ("we don't have a record of you"). A user who's
been promoted to LEVEL ≥ 1 but hasn't been re-seeded would see the
NOT_REGISTERED variant — phrasing that one as "no clearance" would be
misleading.

### Why the header is the Login-style header (not the authenticated one)

The user has technically gone through ID.me verification, so a cookie may
or may not be set when they land here. But they haven't gained access to
the product, so showing a user pill that says *"Signed in · Staff · L0"*
on the header would be misleading and a little cruel.

The header instead matches the Login screen: brand wordmark on the left,
plain "Built by Cloud & Things" attribution on the right. No user pill,
no Log out button. The "Back to Staff Procurement Portal" CTA inside the card handles the
logout flow.

### Layout decisions

- **Centred 480 px card** on the same ambient-gradient + dotted-grid
  surface used by VerificationCallback. Reinforces "system state" rather
  than "in-product page".
- **Soft amber lock illustration** — orange radial halo + inset white
  disc + lock icon in `--orange-600`. Same illustration family as the
  VerificationCallback timeout state. The lock metaphor reads as
  "restricted" not "broken"; the soft palette reads as informational not
  alarming.
- **Eyebrow "ACCESS RESTRICTED"** in tracked-uppercase orange-700 above
  the heading — sets the tonality before the user reads the heading.
- **Heading + sub paragraph** sized smaller than the Login headline
  (1.625 rem vs 1.875 rem). The user is reading a status message, not
  being asked to take an action.
- **Contact callout** — soft-blue tinted box with an info icon. Reuses the
  identity-callout component from Login (same blue tones, same border
  radius). The contact-your-coordinator text is the most useful sentence
  on the page; the blue box gives it visible weight without alarm.
- **Primary CTA "Back to Staff Procurement Portal"** with a forward-arrow icon — same gradient
  orange button used everywhere else, but the arrow signals "you're going
  somewhere" rather than "you're submitting a form".
- **Hint line under the CTA** — *"Clicking this will sign you out of the
  portal."* — small grey text. Tells the user what the button actually
  does before they click it, instead of surprising them with an unexpected
  logout.

### Behaviour (engineer handoff)

Clicking "Back to Staff Procurement Portal":

1. `POST /api/auth/logout` — clears the `session` cookie (idempotent).
2. Browser navigates to the configured staff landing page (e.g.
   `https://www.spp.edu`). For the demo the destination is the
   `?FRONTEND_URL` config var; production should point at Staff Procurement Portal's own
   portal.

The Access Denied page does **not** read any data from the API. The
copy variant is selected on mount based on a `reason` value passed via
route state (set by `VerificationCallback` after parsing
`X-Auth-Reason`). Refreshing the page without that state shows the
NON_STAFF copy as the safe default.

### Accessibility

- **Skip-to-main-content** link as the first focusable element.
- **Semantic landmarks** — `<header role="banner">`, `<main role="main">`,
  `<footer role="contentinfo">`. The card itself is inside `<main>`.
- **`role="alert"` is intentionally NOT used** on the heading — this isn't
  a dynamic alert, it's the page's primary content. Screen readers
  announce the heading naturally via document order.
- **The lock icon is `aria-hidden`**; the heading and sub paragraph carry
  the meaning.
- **`aria-label` on the CTA** spells out the destination explicitly:
  *"Back to Staff Procurement Portal — signs you out and returns to the Staff Procurement Portal site"*. Screen
  reader users know what's about to happen before activating.
- **Contrast** — heading on white ≥ 16:1; sub-paragraph muted-grey ≥ 7:1;
  blue-tinted callout text ≥ 9:1 against its background.
- **Page title** (FD §7.8): `Access Denied | Staff Procurement`.

### What's left out (and why)

- **No support / help-desk email or phone number on screen.** The contact
  instruction is intentionally vague ("contact your procurement
  coordinator") because the actual contact details aren't in spec scope
  (REQUIREMENTS.md §10 — data governance / help-desk routing is a
  phase-2 question). Once Staff Procurement Portal provides a contact, we either inline the
  name + email or turn the contact-your-coordinator line into a mailto
  link.
- **No "try a different account" affordance.** ID.me sessions persist on
  their side; sending the user back through `/` to try again would re-use
  the same ID.me identity and produce the same denial. Better to send
  them away.
- **No retry button.** Same reason — there's no scenario where retrying
  the same flow yields a different result. Their access was decided
  server-side.
- **No specific error code or technical detail.** NFR-12 forbids leaking
  internals; the user-facing copy is enough for the user, and the
  `X-Auth-Reason` header is enough for the SPA.

### Open follow-up

- Once Staff Procurement Portal confirms a help-desk contact (REQUIREMENTS.md §10 OQ-07), wire
  it into the callout — either as plain text ("contact \<name\> at
  \<email\>") or a `mailto:` link. The component already has space for it
  in the current callout block.

---

## All screens complete

The five page-level components for the demo:

1. [Login](./01-login.html) (anonymous)
2. [Verification Callback](./02-verification-callback.html) (anonymous)
3. [Vendor List](./03-vendor-list.html) (Staff L1 / L2 / Admin — RBAC-driven)
4. [Vendor Detail](./04-vendor-detail.html) (Admin only)
5. [Access Denied](./05-access-denied.html) (LEVEL 0 / NOT_REGISTERED)

Behaviour and accessibility decisions are fully documented above. The
React implementation (FUNCTIONAL_DESIGN.md §7) can take these mockups as
visual specs and the corresponding Jira stories (AC-10, AC-14, AC-20–22)
as the work units.
