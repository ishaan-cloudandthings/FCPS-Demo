/**
 * VendorList — placeholder for AC-12.
 *
 * AC-10 needs the route to exist so VerificationCallback can navigate to
 * `/vendors` on a successful login. Full design + RBAC variants are in
 * docs/design/03-vendor-list.html and
 * docs/design/DESIGN_RATIONALE.md §"Screen 3 — Vendor List".
 */
import { useEffect } from "react";

import { useAuthStore } from "../store/auth.js";

export function VendorList() {
  useEffect(() => {
    document.title = "Vendors | FCPS Procurement";
  }, []);

  const { role, procurement_level, staff_id } = useAuthStore();

  return (
    <main role="main" className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">Vendor list (placeholder)</h1>
      <p className="mt-2 text-ink-muted">
        Signed in as staff #{staff_id} · role {role} · level{" "}
        {procurement_level}
      </p>
      <p className="mt-6 text-xs text-ink-subtle">
        Placeholder — full screen ships with AC-12.
      </p>
    </main>
  );
}
