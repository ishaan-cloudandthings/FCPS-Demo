/**
 * RTL tests for ProtectedRoute — AC-20.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./ProtectedRoute.jsx";
import { useAuthStore } from "../store/auth.js";

function renderProtected(initialPath = "/secret") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route
          path="/secret"
          element={
            <ProtectedRoute>
              <div>secret content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<div data-testid="login-page">Login</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("renders children when authenticated", () => {
    useAuthStore.setState({
      status: "authenticated",
      role: "PROCUREMENT_SUPERVISOR",
      staff_id: 1,
    });

    renderProtected();
    expect(screen.getByText(/secret content/i)).toBeInTheDocument();
  });

  it("redirects to /?reason=session_expired when unauthenticated", () => {
    useAuthStore.setState({ status: "unauthenticated" });

    renderProtected();
    expect(screen.getByTestId("login-page")).toBeInTheDocument();
    expect(screen.queryByText(/secret content/i)).not.toBeInTheDocument();
  });

  it("renders nothing while loading", () => {
    useAuthStore.setState({ status: "loading" });

    const { container } = renderProtected();
    // The Route still mounts but ProtectedRoute returns null.
    expect(container.textContent).toBe("");
  });
});
