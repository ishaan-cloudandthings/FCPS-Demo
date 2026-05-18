/**
 * Verification Callback page — implements AC-10 acceptance criteria.
 *
 * Sources:
 *   - Visual design:  docs/design/02-verification-callback.html
 *   - Rationale:      docs/design/DESIGN_RATIONALE.md §"Screen 2 — Verification Callback"
 *   - FD contract:    docs/requirements/FUNCTIONAL_DESIGN.md §7.2, §7.3
 *   - Backend API:    POST /api/auth/callback (AC-7)
 *
 * Route: `/verification/callback?code=…&state=…`
 *
 * Behaviour (DESIGN_RATIONALE.md §"Behaviour (engineer handoff)"):
 *   - Mount once. POST {code, state} to /api/auth/callback.
 *   - 200  → navigate to /vendors.
 *   - 403  → navigate to /access-denied (regardless of reason).
 *   - 400/401/502 → navigate to / with ?reason=callback_error or
 *                    ?reason=idme_unreachable (502).
 *   - Missing code/state in URL → navigate to / immediately.
 *   - 10 s hard SPA timeout via AbortController → show timeout view.
 *     The retry CTA routes back to / (NOT a re-POST — `state` is one-shot,
 *     ADR-004 D-FD-08). DESIGN_RATIONALE.md §240.
 *
 * Three internal views:
 *   - "verifying"  — spinner + bounded progress bar (0..10s)
 *   - "timeout"    — friendly retry screen (after 10s, no response)
 *   - (the success / error paths navigate away and unmount)
 */
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { AuthShellFooter } from "../components/AuthShellFooter.jsx";
import { AuthShellHeader } from "../components/AuthShellHeader.jsx";
import { SkipLink } from "../components/SkipLink.jsx";
import { ApiError, apiFetch } from "../services/apiFetch.js";
import { useAuthStore } from "../store/auth.js";

const TIMEOUT_MS = 10_000;

export function VerificationCallback() {
  useEffect(() => {
    document.title = "Verifying… | FCPS Procurement";
  }, []);

  const [params] = useSearchParams();
  const navigate = useNavigate();
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);

  const [view, setView] = useState("verifying");
  // Guard against React StrictMode running the effect twice in dev.
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const code = params.get("code");
    const state = params.get("state");

    if (!code || !state) {
      // Direct hit without OAuth params — bounce to Login.
      navigate("/", { replace: true });
      return;
    }

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);

    apiFetch("/api/auth/callback", {
      method: "POST",
      body: { code, state },
      signal: ctrl.signal,
    })
      .then((claims) => {
        // 200 → hydrate store so /vendors renders without a re-fetch on
        // landing, then navigate (FD §7.2).
        setAuthenticated(claims);
        navigate("/vendors", { replace: true });
      })
      .catch((err) => {
        if (err && err.name === "AbortError") {
          setView("timeout");
          return;
        }
        if (err instanceof ApiError) {
          if (err.status === 403) {
            // AC14-D7 — pass X-Auth-Reason via route state so AccessDenied
            // can pick the right copy variant (LEVEL_ZERO vs NOT_REGISTERED).
            const reason = err.headers?.get?.("X-Auth-Reason") ?? null;
            navigate("/access-denied", {
              replace: true,
              state: { reason },
            });
            return;
          }
          if (err.status === 502) {
            navigate("/?reason=idme_unreachable", { replace: true });
            return;
          }
          // 400 / 401 / anything else → generic banner on Login.
          navigate("/?reason=callback_error", { replace: true });
          return;
        }
        // Network/parse failure that wasn't an AbortError — show timeout
        // view so the user has a path out.
        setView("timeout");
      })
      .finally(() => {
        clearTimeout(timer);
      });

    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  }, [params, navigate, setAuthenticated]);

  return (
    <div className="flex min-h-screen flex-col">
      <SkipLink targetId="main" />
      <AuthShellHeader />
      <main
        id="main"
        role="main"
        className="flex flex-1 items-center justify-center p-6"
      >
        {view === "verifying" ? <VerifyingCard /> : <TimeoutCard />}
      </main>
      <AuthShellFooter />
    </div>
  );
}

/**
 * "Verifying your identity…" — DESIGN_RATIONALE.md §"State A".
 *
 * Accessibility:
 *   - role="status" + aria-live="polite" so SR users get one polite
 *     announcement (§290).
 *   - Spinner has aria-hidden; textual heading is the announced content.
 *   - prefers-reduced-motion handled via Tailwind's `motion-safe:` /
 *     `motion-reduce:` variants on the animated elements.
 */
function VerifyingCard() {
  return (
    <section
      role="status"
      aria-live="polite"
      className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-10 text-center shadow-lg"
    >
      <div className="relative mx-auto mb-6 flex h-[72px] w-[72px] items-center justify-center">
        <span
          aria-hidden="true"
          className="absolute -inset-1.5 rounded-full bg-[radial-gradient(circle,rgba(244,121,32,0.18)_0%,transparent_65%)]"
        />
        <Spinner />
      </div>
      <div className="mb-2 text-[0.6875rem] font-semibold uppercase tracking-[0.16em] text-brand-orange-600">
        Step 2 of 2 · Identity check
      </div>
      <h1 className="mb-2 text-[1.375rem] font-bold tracking-tight">
        Verifying your identity…
      </h1>
      <p className="text-[0.9375rem] leading-relaxed text-ink-muted">
        Just a moment while we check your FCPS procurement access.
      </p>
      <div
        aria-hidden="true"
        className="mx-auto mt-7 h-[5px] w-[180px] overflow-hidden rounded-full bg-brand-blue-50"
      >
        <div className="h-full w-full origin-left animate-slide rounded-full bg-gradient-to-r from-brand-orange-500 to-brand-orange-600 motion-reduce:opacity-50 motion-reduce:animate-none" />
      </div>
      <p
        aria-hidden="true"
        className="mt-2.5 text-xs text-ink-subtle"
      >
        Usually takes 1–3 seconds
      </p>
      <span className="visually-hidden">Verification in progress</span>
    </section>
  );
}

/**
 * "This is taking longer than expected" — DESIGN_RATIONALE.md §"State B".
 *
 * The retry CTA routes back to `/` (not a re-POST) per §240 — the OAuth
 * `state` is one-shot per ADR-004 D-FD-08, so a re-POST would 400.
 */
function TimeoutCard() {
  return (
    <section className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-10 text-center shadow-lg">
      <div className="relative mx-auto mb-6 flex h-20 w-20 items-center justify-center">
        <span
          aria-hidden="true"
          className="absolute inset-0 rounded-full bg-[radial-gradient(circle,rgba(244,121,32,0.18)_0%,rgba(244,121,32,0.08)_70%,transparent_100%)]"
        />
        <span
          aria-hidden="true"
          className="absolute inset-3 rounded-full border border-brand-orange-100 bg-brand-orange-50"
        />
        <ClockIcon className="relative z-10 h-8 w-8 text-amber-text" />
      </div>
      <div className="mb-2 text-[0.6875rem] font-semibold uppercase tracking-[0.16em] text-amber-text">
        Taking too long
      </div>
      <h1 className="mb-2 text-[1.375rem] font-bold tracking-tight">
        This is taking longer than expected
      </h1>
      <p className="mb-6 text-[0.9375rem] leading-relaxed text-ink-muted">
        We couldn&apos;t reach ID.me. Your sign-in hasn&apos;t been saved —
        please try again.
      </p>
      <Link
        to="/"
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-btn-orange px-5 py-3 text-[0.9375rem] font-semibold text-white shadow-[0_1px_0_rgba(255,255,255,0.20)_inset,0_1px_2px_rgba(184,85,16,0.40),0_6px_16px_-4px_rgba(244,121,32,0.45)] transition hover:-translate-y-px focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-brand-blue-500"
      >
        Try signing in again
      </Link>
      <Link
        to="/"
        className="mt-3 inline-block text-sm font-medium text-brand-blue-500 hover:underline focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-brand-blue-500"
      >
        Back to sign in
      </Link>
    </section>
  );
}

function Spinner() {
  return (
    <svg
      className="block h-[72px] w-[72px] motion-safe:animate-spin motion-reduce:animate-none"
      viewBox="0 0 72 72"
      fill="none"
      aria-hidden="true"
    >
      {/* Blue track */}
      <circle cx="36" cy="36" r="28" stroke="#DDE3F5" strokeWidth="5" />
      {/* Orange progress arc */}
      <circle
        cx="36"
        cy="36"
        r="28"
        stroke="#F47920"
        strokeWidth="5"
        strokeLinecap="round"
        strokeDasharray="125 70"
        transform="rotate(-90 36 36)"
      />
    </svg>
  );
}

function ClockIcon({ className }) {
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
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}
