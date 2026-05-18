/**
 * Root component — wires up routing and the auth bootstrap call.
 *
 * Screen inventory comes from FUNCTIONAL_DESIGN.md §7.3. AC-10 scope is
 * the two anonymous-shell screens; later stories fill in the rest:
 *   - VendorList   → AC-12
 *   - VendorDetail → AC-15 (admin-only)
 *   - AccessDenied → AC-11
 *   - Authenticated app layout (header w/ logout) → AC-19/20
 */
import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./components/ProtectedRoute.jsx";
import { useAuthBootstrap } from "./hooks/useAuthBootstrap.js";
import { AccessDenied } from "./pages/AccessDenied.jsx";
import { Login } from "./pages/Login.jsx";
import { VendorDetail } from "./pages/VendorDetail.jsx";
import { VendorList } from "./pages/VendorList.jsx";
import { VerificationCallback } from "./pages/VerificationCallback.jsx";

export function App() {
  useAuthBootstrap();

  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/verification/callback" element={<VerificationCallback />} />
      <Route path="/access-denied" element={<AccessDenied />} />
      <Route
        path="/vendors"
        element={
          <ProtectedRoute>
            <VendorList />
          </ProtectedRoute>
        }
      />
      <Route
        path="/vendors/:item_id"
        element={
          <ProtectedRoute>
            <VendorDetail />
          </ProtectedRoute>
        }
      />
      {/* Unknown path → land on Login. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
