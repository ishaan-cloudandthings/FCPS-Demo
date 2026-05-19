/**
 * Auth bootstrap hook — implements FUNCTIONAL_DESIGN.md §7.2.
 *
 * On SPA mount, call GET /api/auth/me:
 *   - 200 → hydrate the auth store with {role, staff_id}.
 *   - 401 → mark unauthenticated; the page-level routing decides whether
 *           the current URL is allowed for an anonymous user.
 *
 * Designed to run exactly once at the App root. Pages should NOT call
 * /me again on their own mounts — they read from the store.
 */
import { useEffect } from "react";

import { ApiError, apiFetch } from "../services/apiFetch.js";
import { useAuthStore } from "../store/auth.js";

export function useAuthBootstrap() {
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const setUnauthenticated = useAuthStore((s) => s.setUnauthenticated);

  useEffect(() => {
    let cancelled = false;
    apiFetch("/api/auth/me")
      .then((claims) => {
        if (cancelled) return;
        setAuthenticated(claims);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          setUnauthenticated();
        } else {
          // Network / 5xx — treat as unauthenticated for routing purposes;
          // the Login screen is a safe place to land. We deliberately do
          // NOT surface this as a banner — first-paint network blips are
          // common and the user hasn't done anything yet.
          setUnauthenticated();
        }
      });
    return () => {
      cancelled = true;
    };
  }, [setAuthenticated, setUnauthenticated]);
}
