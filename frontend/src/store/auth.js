/**
 * Zustand auth slice — see FUNCTIONAL_DESIGN.md §7.5.
 *
 * Shape:
 *   status: "loading" | "authenticated" | "unauthenticated"
 *   role, staff_id — populated only when authenticated
 *
 * Per [ADR-015](../../../docs/adr/ADR-015-role-model-simplification.md),
 * `procurement_level` was dropped; `role` is the single authority field
 * (`PROCUREMENT_SUPERVISOR` or `REGULAR_STAFF`).
 *
 * The store is the SPA's single source of truth for "who is the current
 * user?" The hydration call lives in `useAuthBootstrap`, which calls
 * GET /api/auth/me on mount and pushes the result into here.
 */
import { create } from "zustand";

const initialState = {
  status: "loading",
  role: null,
  staff_id: null,
};

export const useAuthStore = create((set) => ({
  ...initialState,
  setAuthenticated: (claims) =>
    set({
      status: "authenticated",
      role: claims.role,
      staff_id: claims.staff_id,
    }),
  setUnauthenticated: () =>
    set({
      status: "unauthenticated",
      role: null,
      staff_id: null,
    }),
  reset: () => set(initialState),
}));
