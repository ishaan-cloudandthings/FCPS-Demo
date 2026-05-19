/**
 * AppHeader — authenticated in-product header.
 *
 * Distinct from `AuthShellHeader` (used on Login / Callback /
 * AccessDenied). This one shows the signed-in user's role/level + a
 * Log out button. Decisions: docs/decision-log/AC-20-frontend-foundations.md
 * (AC20-D3).
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch } from "../services/apiFetch.js";
import { useAuthStore } from "../store/auth.js";

// ADR-015 — human-readable labels for the role enum.
const ROLE_LABEL = {
  PROCUREMENT_SUPERVISOR: "Procurement Supervisor",
  REGULAR_STAFF: "Regular Staff",
};

export function AppHeader() {
  const navigate = useNavigate();
  const { role, staff_id } = useAuthStore();
  const setUnauthenticated = useAuthStore((s) => s.setUnauthenticated);

  const [busy, setBusy] = useState(false);

  async function handleLogout() {
    setBusy(true);
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } catch {
      /* idempotent (AC-9); ignore */
    }
    setUnauthenticated();
    navigate("/", { replace: true });
  }

  return (
    <header
      role="banner"
      className="flex items-center justify-between border-b border-gray-200 bg-white px-8 py-4"
    >
      <span className="flex items-center gap-2 text-sm font-semibold text-ink">
        <span
          aria-hidden="true"
          className="inline-flex h-7 w-7 items-center justify-center rounded bg-brand-blue-500 text-xs font-bold text-white"
        >
          F
        </span>
        Staff Procurement Portal
      </span>
      <div className="flex items-center gap-4">
        <span
          data-testid="user-pill"
          className="inline-flex items-center gap-2 rounded-full bg-brand-blue-50 px-3 py-1 text-xs font-medium text-brand-blue-900"
        >
          <span className="font-semibold">Signed in</span>
          <span aria-hidden="true">·</span>
          <span>{ROLE_LABEL[role] ?? role}</span>
          <span aria-hidden="true">·</span>
          <span>#{staff_id}</span>
        </span>
        <button
          type="button"
          onClick={handleLogout}
          disabled={busy}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-ink hover:border-brand-blue-300 hover:bg-brand-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {busy ? "Logging out…" : "Log out"}
        </button>
      </div>
    </header>
  );
}
