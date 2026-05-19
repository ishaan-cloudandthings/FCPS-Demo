/**
 * Login page — implements AC-10 acceptance criteria.
 *
 * Sources:
 *   - Visual design:  docs/design/01-login.html
 *   - Rationale:      docs/design/DESIGN_RATIONALE.md §"Screen 1 — Login"
 *   - FD contract:    docs/requirements/FUNCTIONAL_DESIGN.md §7.3 (Login.jsx)
 *   - Backend API:    POST /api/auth/login (AC-6)
 *   - Requirements:   REQUIREMENTS.md FR-01, FR-08
 *
 * The route is `/`. A `?reason=session_expired` query parameter shows the
 * session-expired banner (REQUIREMENTS.md FR-08).
 *
 * Behaviour (DESIGN_RATIONALE.md §"Behaviour"):
 *   onClick CTA → POST /api/auth/login → window.location.assign(authorize_url)
 *
 * If the user is already authenticated (per `useAuthBootstrap`), we
 * redirect to /vendors — there's no reason to show Login to a signed-in
 * user. (FD §7.2.)
 */
import { useEffect, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";

import { AuthShellFooter } from "../components/AuthShellFooter.jsx";
import { AuthShellHeader } from "../components/AuthShellHeader.jsx";
import { SkipLink } from "../components/SkipLink.jsx";
import { ApiError, apiFetch } from "../services/apiFetch.js";
import { useAuthStore } from "../store/auth.js";

// Persona list driving the dev-only panel.
// See ADR-014 and docs/decision-log/DEV-AUTH-persona-picker.md (DEV12).
// Order matches the demo narrative: granted personas first, denied last.
// ADR-015 — three business roles + the not-registered technical denial.
const DEV_PERSONAS = [
  { key: "procurement_supervisor", label: "Procurement Supervisor", denied: false },
  { key: "regular_staff",          label: "Regular Staff",          denied: false },
  { key: "non_staff",              label: "Non-staff",              denied: true },
  { key: "not_registered", label: "Not registered", denied: true },
];

// Banner copy keyed by `?reason=…`. The session_expired text comes
// verbatim from REQUIREMENTS.md FR-08; the callback_* reasons are the
// SPA's own classification of upstream failure (see VerificationCallback).
const BANNERS = {
  session_expired: {
    title: "Your session has expired.",
    body: "Please verify again to continue.",
  },
  callback_error: {
    title: "We couldn't complete sign-in.",
    body: "Something went wrong while verifying you. Please try again.",
  },
  idme_unreachable: {
    title: "We couldn't reach ID.me.",
    body: "Their service may be temporarily unavailable. Please try again in a moment.",
  },
};

export function Login() {
  useEffect(() => {
    document.title = "Login | Staff Procurement";
  }, []);

  const [params] = useSearchParams();
  const reason = params.get("reason");
  const banner = reason ? BANNERS[reason] : null;

  // FD §7.2 — signed-in users skip the Login screen.
  const status = useAuthStore((s) => s.status);
  if (status === "authenticated") {
    return <Navigate to="/vendors" replace />;
  }

  const isReturning = reason === "session_expired";

  return (
    <div className="flex min-h-screen flex-col">
      <SkipLink targetId="main" />
      <AuthShellHeader />
      <main
        id="main"
        role="main"
        className="grid flex-1 grid-cols-1 lg:grid-cols-[5fr_7fr]"
      >
        <BrandPanel />
        <SigninPanel banner={banner} isReturning={isReturning} />
      </main>
      <AuthShellFooter />
    </div>
  );
}

/**
 * Left brand panel — DESIGN_RATIONALE.md §"Layout decisions":
 * asserts identity + value proposition. Decorative; aria-hidden so the
 * screen reader doesn't echo it before the actionable right panel.
 *
 * Note: the "Audit-logged access to sensitive fields" sub-line in the
 * original mockup was removed per ADR-012 (bank details + audit log out
 * of scope). DESIGN_RATIONALE.md §136 acknowledges this drift.
 */
function BrandPanel() {
  return (
    <aside
      aria-hidden="true"
      className="relative hidden overflow-hidden bg-brand-panel p-14 text-white lg:flex lg:flex-col lg:justify-between"
    >
      <div>
        <div className="mb-6 flex items-center gap-2 text-[0.6875rem] font-semibold uppercase tracking-[0.16em] text-brand-orange-500">
          <span className="inline-block h-0.5 w-4 rounded-full bg-brand-orange-500" />
          Staff Procurement
        </div>
        <h1 className="mb-4 max-w-md text-4xl font-bold leading-[1.12] tracking-tight">
          Approved vendors,
          <br />
          <em className="not-italic text-brand-orange-500 italic">
            one search away.
          </em>
        </h1>
        <p className="max-w-[30ch] text-[0.9375rem] leading-relaxed text-white/80">
          Find, verify, and contact the vendors Staff Procurement Portal has cleared — without
          sending a single email.
        </p>
      </div>
      <div className="flex items-center gap-3 rounded-xl border border-white/15 bg-white/10 p-3 backdrop-blur-sm">
        <ShieldIcon className="h-4 w-4 text-brand-orange-500" />
        <div className="flex flex-col gap-0.5">
          <strong className="text-sm font-semibold">
            Verified-identity access
          </strong>
          <span className="text-xs text-white/75">ID.me verification</span>
        </div>
      </div>
    </aside>
  );
}

/**
 * Right sign-in panel — single action plus optional banner.
 *
 * In `dev` environments only, also renders the persona panel below the
 * ID.me CTA. Availability is determined by probing
 * `GET /api/auth/dev-login/available` on mount — see ADR-014 and
 * DEV9 in the decision log.
 */
function SigninPanel({ banner, isReturning }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [devAvailable, setDevAvailable] = useState(false);

  // DEV9 — probe once on mount. Any non-200 (including 404 in prod) is
  // silent: no banner, no console, no log. Production builds are visually
  // identical to the ID.me-only product.
  useEffect(() => {
    let cancelled = false;
    apiFetch("/api/auth/dev-login/available")
      .then(() => {
        if (!cancelled) setDevAvailable(true);
      })
      .catch(() => {
        /* silent — see DEV9 */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleVerify() {
    setError(null);
    setSubmitting(true);
    try {
      const data = await apiFetch("/api/auth/login", { method: "POST" });
      // The CTA is intentionally NOT a hyperlink (DESIGN_RATIONALE.md §175).
      // We POST first to generate the server-side `state`, then redirect.
      window.location.assign(data.authorize_url);
    } catch (err) {
      // 503 (state cache full per AC-6) and 5xx → user-facing copy that
      // matches the design's "non-alarming" voice. We do not show the
      // raw error detail (FD §10 / AC-10 AC #5).
      const friendly =
        err instanceof ApiError && err.status === 503
          ? "Service is briefly unavailable. Please try again in a moment."
          : "We couldn't start sign-in. Please try again.";
      setError(friendly);
      setSubmitting(false);
    }
  }

  return (
    <section className="flex items-center justify-center bg-white p-10 sm:p-14">
      <div className="w-full max-w-sm">
        {banner && (
          <div
            role="alert"
            className="mb-6 flex items-start gap-3 rounded-md border-l-4 border-brand-orange-500 bg-gradient-to-b from-brand-orange-50 to-[#FFFAF1] p-3 text-sm text-amber-text"
          >
            <ClockIcon className="mt-0.5 h-4 w-4 shrink-0 text-brand-orange-600" />
            <div>
              <strong className="block font-semibold">{banner.title}</strong>
              {banner.body}
            </div>
          </div>
        )}

        <div className="mb-3 text-[0.6875rem] font-semibold uppercase tracking-[0.16em] text-brand-orange-600">
          Sign in
        </div>
        <h2 className="mb-2 text-3xl font-bold leading-tight tracking-tight">
          {isReturning ? "Welcome back" : "Welcome to the Portal"}
        </h2>
        <p className="mb-7 text-[0.9375rem] leading-relaxed text-ink-muted">
          {isReturning
            ? "Verify with ID.me to pick up where you left off."
            : "Use your verified ID.me account to continue."}
        </p>

        {/* Identity policy callout — informational (blue), not action-required. */}
        <div className="mb-7 flex items-start gap-3 rounded-lg border border-brand-blue-100 bg-brand-blue-50 px-4 py-3">
          <InfoIcon className="h-5 w-5 shrink-0 text-brand-blue-500" />
          <p className="m-0 text-[0.8125rem] leading-snug text-brand-blue-900">
            Access to the Staff Procurement Portal requires verified Staff Procurement Portal
            employee identity.
          </p>
        </div>

        <button
          type="button"
          onClick={handleVerify}
          disabled={submitting}
          aria-label="Verify with ID.me — opens id.me in this window"
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-btn-orange px-5 py-3.5 text-[0.9375rem] font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.20)_inset,0_1px_2px_rgba(184,85,16,0.40),0_8px_18px_-4px_rgba(244,121,32,0.5)] transition hover:-translate-y-px hover:shadow-[0_1px_0_rgba(255,255,255,0.25)_inset,0_1px_2px_rgba(184,85,16,0.40),0_10px_22px_-4px_rgba(244,121,32,0.55)] focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-brand-blue-500 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <ShieldIcon className="h-4 w-4" />
          {submitting ? "Redirecting…" : "Verify with ID.me"}
        </button>

        <p className="mt-4 text-center text-[0.8125rem] text-ink-subtle">
          You&apos;ll be redirected to id.me to verify, then returned here.
        </p>

        {error && (
          <p
            role="alert"
            className="mt-4 rounded-md bg-red-50 px-3 py-2 text-center text-sm text-red-700"
          >
            {error}
          </p>
        )}

        {devAvailable && <DevPersonaPanel />}
      </div>
    </section>
  );
}

/**
 * Dev-only persona panel — see ADR-014.
 *
 * Each button POSTs `/api/auth/dev-login {persona}` and reuses the same
 * outcome routing as VerificationCallback: 200 → /vendors, 403 →
 * /access-denied. The session cookie is set by the backend.
 */
function DevPersonaPanel() {
  const navigate = useNavigate();
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const [busy, setBusy] = useState(null);

  async function pick(persona) {
    setBusy(persona);
    try {
      const claims = await apiFetch("/api/auth/dev-login", {
        method: "POST",
        body: { persona },
      });
      setAuthenticated(claims);
      navigate("/vendors", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        // AC14-D7 — pass X-Auth-Reason via route state so the
        // AccessDenied page renders the correct copy variant.
        const reason = err.headers?.get?.("X-Auth-Reason") ?? null;
        navigate("/access-denied", {
          replace: true,
          state: { reason },
        });
        return;
      }
      // Any other failure — silent reset; the panel stays.
      setBusy(null);
    }
  }

  return (
    <div
      data-testid="dev-persona-panel"
      className="mt-8 border-t border-gray-200 pt-6"
    >
      <p className="mb-3 text-[0.6875rem] font-semibold uppercase tracking-[0.16em] text-ink-subtle">
        Demo mode · dev only
      </p>
      <p className="mb-3 text-xs text-ink-muted">
        Skip ID.me and sign in as:
      </p>
      <ul className="space-y-2">
        {DEV_PERSONAS.map((p) => (
          <li key={p.key}>
            <button
              type="button"
              onClick={() => pick(p.key)}
              disabled={busy !== null}
              aria-label={`Demo persona: ${p.label}`}
              className="w-full rounded-md border border-gray-300 bg-white px-4 py-2.5 text-left text-sm font-medium text-ink hover:border-brand-blue-300 hover:bg-brand-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span className="flex items-center justify-between">
                <span>{p.label}</span>
                {p.denied && (
                  <span className="rounded-full bg-orange-50 px-2 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-wider text-amber-text">
                    denied
                  </span>
                )}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---------- Inline icons (kept colocated so a designer editing this page
 * can see the full markup; we'd extract into icons/ if/when reused 3+ times). */

function ShieldIcon({ className }) {
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
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <polyline points="9 12 11 14 15 10" />
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

function ClockIcon({ className }) {
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
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}
