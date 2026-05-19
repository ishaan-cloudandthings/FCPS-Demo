/**
 * AccessDenied page — implements AC-14 acceptance criteria.
 *
 * Sources:
 *   - Visual design:  docs/design/05-access-denied.html
 *   - Rationale:      docs/design/DESIGN_RATIONALE.md §"Screen 5 — Access Denied"
 *   - FD contract:    docs/requirements/FUNCTIONAL_DESIGN.md §7.3, §7.8
 *   - Decisions:      docs/decision-log/AC-14-access-denied.md (AC14-D1 … AC14-D7)
 *
 * Route: `/access-denied`
 *
 * Variant selection (AC14-D1):
 *   `useLocation().state?.reason` ∈ { "LEVEL_ZERO", "NOT_REGISTERED" }
 *   No state → defaults to LEVEL_ZERO (AC14-D2).
 *
 * Back-to-Staff Procurement Portal CTA (AC14-D3):
 *   POST /api/auth/logout → navigate("/"). Always in-app, never an
 *   external jump, per user direction (supersedes design rationale's
 *   optional FRONTEND_URL).
 */
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { AuthShellFooter } from "../components/AuthShellFooter.jsx";
import { AuthShellHeader } from "../components/AuthShellHeader.jsx";
import { SkipLink } from "../components/SkipLink.jsx";
import { apiFetch } from "../services/apiFetch.js";
import { useAuthStore } from "../store/auth.js";

// ADR-015: NON_STAFF replaced LEVEL_ZERO. Copy stays in the same spirit
// (status message, non-alarming) but no longer references "procurement
// clearance" (a level-era phrase).
const COPY = {
  NON_STAFF: {
    heading: "You don't have access to this portal",
    sub:
      "Your identity is verified, but your account doesn't have access to the Staff Procurement Portal. Contact your procurement supervisor.",
  },
  NOT_REGISTERED: {
    heading: "Identity not verified",
    sub:
      "We couldn't verify your identity, so you do not have access to the portal. Contact your procurement supervisor.",
  },
};

export function AccessDenied() {
  useEffect(() => {
    document.title = "Access Denied | Staff Procurement";
  }, []);

  const location = useLocation();
  const navigate = useNavigate();
  const reset = useAuthStore((s) => s.setUnauthenticated);

  // AC14-D2 + ADR-015: default to NON_STAFF when no route state is present.
  const rawReason = location.state?.reason;
  const reason = rawReason in COPY ? rawReason : "NON_STAFF";
  const { heading, sub } = COPY[reason];

  const [busy, setBusy] = useState(false);

  async function handleBackToLogin() {
    setBusy(true);
    // POST /api/auth/logout is idempotent (AC-9): returns 204 even if
    // the session is already gone. We don't gate the navigate on the
    // response — even if logout fails, the user wants to leave this page.
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } catch {
      /* idempotent; ignore */
    }
    reset();
    navigate("/", { replace: true });
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SkipLink targetId="main" />
      <AuthShellHeader />
      <main
        id="main"
        role="main"
        className="flex flex-1 items-center justify-center p-6"
      >
        <section
          data-testid="access-denied-card"
          className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-10 text-center shadow-lg"
        >
          {/* Lock illustration — aria-hidden; heading carries meaning. */}
          <div className="relative mx-auto mb-6 flex h-20 w-20 items-center justify-center">
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full bg-[radial-gradient(circle,rgba(244,121,32,0.18)_0%,rgba(244,121,32,0.08)_70%,transparent_100%)]"
            />
            <span
              aria-hidden="true"
              className="absolute inset-3 rounded-full border border-brand-orange-100 bg-brand-orange-50"
            />
            <LockIcon className="relative z-10 h-8 w-8 text-brand-orange-600" />
          </div>
          <div className="mb-2 text-[0.6875rem] font-semibold uppercase tracking-[0.16em] text-brand-orange-700">
            Access restricted
          </div>
          <h1
            data-testid="access-denied-heading"
            className="mb-3 text-[1.625rem] font-bold leading-tight tracking-tight"
          >
            {heading}
          </h1>
          <p className="mb-6 text-[0.9375rem] leading-relaxed text-ink-muted">
            {sub}
          </p>

          {/* Contact callout — info-coloured, not alarm-coloured. */}
          <div className="mb-7 flex items-start gap-3 rounded-lg border border-brand-blue-100 bg-brand-blue-50 px-4 py-3 text-left">
            <InfoIcon className="mt-0.5 h-5 w-5 shrink-0 text-brand-blue-500" />
            <p className="m-0 text-[0.8125rem] leading-snug text-brand-blue-900">
              If you believe this is an error, contact your procurement
              coordinator.
            </p>
          </div>

          <button
            type="button"
            onClick={handleBackToLogin}
            disabled={busy}
            aria-label="Back to Staff Procurement Portal — signs you out and returns to the sign-in page"
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-btn-orange px-5 py-3 text-[0.9375rem] font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.20)_inset,0_1px_2px_rgba(184,85,16,0.40),0_6px_16px_-4px_rgba(244,121,32,0.45)] transition hover:-translate-y-px focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-brand-blue-500 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {busy ? "Signing out…" : "Back to Staff Procurement Portal"}
            {!busy && <ArrowIcon className="h-4 w-4" />}
          </button>
          <p className="mt-3 text-xs text-ink-subtle">
            Clicking this will sign you out of the portal.
          </p>
        </section>
      </main>
      <AuthShellFooter />
    </div>
  );
}

function LockIcon({ className }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      <rect x="4" y="11" width="16" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </svg>
  );
}

function InfoIcon({ className }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  );
}

function ArrowIcon({ className }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  );
}
