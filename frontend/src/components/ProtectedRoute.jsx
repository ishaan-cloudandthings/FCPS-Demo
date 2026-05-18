/**
 * ProtectedRoute — gates routes that require an authenticated session.
 *
 * Decisions: docs/decision-log/AC-20-frontend-foundations.md (AC20-D1, D2).
 *
 * Status semantics (from store/auth.js):
 *   - "loading"          → render nothing (bootstrap in-flight).
 *   - "unauthenticated"  → redirect to "/?reason=session_expired".
 *   - "authenticated"    → render children.
 *
 * The `level` prop is reserved for AC-17 (real RBAC). It has no effect
 * today. TODO(AC-17): consult `level` and `claims.procurement_level`.
 */
import { Navigate } from "react-router-dom";

import { useAuthStore } from "../store/auth.js";

export function ProtectedRoute({ children, level }) {  // eslint-disable-line no-unused-vars
  const status = useAuthStore((s) => s.status);

  if (status === "loading") {
    return null;
  }
  if (status === "unauthenticated") {
    return <Navigate to="/?reason=session_expired" replace />;
  }
  // TODO(AC-17): if (level && claims.procurement_level < level) redirect to /access-denied.
  return children;
}
