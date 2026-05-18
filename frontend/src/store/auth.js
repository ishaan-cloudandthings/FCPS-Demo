/**
 * Zustand auth slice — see FUNCTIONAL_DESIGN.md §7.5.
 *
 * Shape:
 *   status: "loading" | "authenticated" | "unauthenticated"
 *   role, procurement_level, staff_id — populated only when authenticated
 *
 * The store is the SPA's single source of truth for "who is the current
 * user?" The hydration call lives in `useAuthBootstrap`, which calls
 * GET /api/auth/me on mount and pushes the result into here.
 */
import { create } from "zustand";

const initialState = {
  status: "loading",
  role: null,
  procurement_level: null,
  staff_id: null,
};

export const useAuthStore = create((set) => ({
  ...initialState,
  setAuthenticated: (claims) =>
    set({
      status: "authenticated",
      role: claims.role,
      procurement_level: claims.procurement_level,
      staff_id: claims.staff_id,
    }),
  setUnauthenticated: () =>
    set({
      status: "unauthenticated",
      role: null,
      procurement_level: null,
      staff_id: null,
    }),
  reset: () => set(initialState),
}));
