/**
 * AccessDenied — placeholder for AC-11.
 *
 * AC-10 needs the route to exist so VerificationCallback's `navigate` can
 * land somewhere on a 403 response. Full design is in
 * docs/design/05-access-denied.html and
 * docs/design/DESIGN_RATIONALE.md §"Screen 5 — Access Denied".
 */
import { useEffect } from "react";

import { AuthShellFooter } from "../components/AuthShellFooter.jsx";
import { AuthShellHeader } from "../components/AuthShellHeader.jsx";
import { SkipLink } from "../components/SkipLink.jsx";

export function AccessDenied() {
  useEffect(() => {
    document.title = "Access denied | FCPS Procurement";
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <SkipLink targetId="main" />
      <AuthShellHeader />
      <main
        id="main"
        role="main"
        className="flex flex-1 items-center justify-center p-6"
      >
        <section className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-10 text-center shadow-lg">
          <h1 className="mb-2 text-2xl font-bold tracking-tight">
            Access denied
          </h1>
          <p className="text-ink-muted">
            Your identity was verified, but your account does not have
            procurement clearance. Contact your procurement coordinator.
          </p>
          <p className="mt-6 text-xs text-ink-subtle">
            Placeholder — full screen ships with AC-11.
          </p>
        </section>
      </main>
      <AuthShellFooter />
    </div>
  );
}
