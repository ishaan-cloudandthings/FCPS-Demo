/**
 * RTL tests for AppHeader — AC-20.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AppHeader } from "./AppHeader.jsx";
import { useAuthStore } from "../store/auth.js";

function renderHeader() {
  useAuthStore.setState({
    status: "authenticated",
    role: "PROCUREMENT_SUPERVISOR",
    staff_id: 42,
  });
  return render(
    <MemoryRouter initialEntries={["/vendors"]}>
      <Routes>
        <Route path="/vendors" element={<AppHeader />} />
        <Route path="/" element={<div data-testid="login-page">Login</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AppHeader", () => {
  it("renders the brand wordmark and user pill", () => {
    renderHeader();
    expect(
      screen.getByText(/Staff Procurement Portal/i),
    ).toBeInTheDocument();
    const pill = screen.getByTestId("user-pill");
    expect(pill).toHaveTextContent(/procurement supervisor/i);
    expect(pill).toHaveTextContent(/#42/);
  });

  it("renders a Log out button", () => {
    renderHeader();
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();
  });

  it("clicking Log out POSTs /api/auth/logout, resets store, navigates to /", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("", { status: 204 }));
    globalThis.fetch = fetchMock;

    renderHeader();
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/auth/logout",
        expect.objectContaining({ method: "POST", credentials: "include" }),
      );
    });
    expect(await screen.findByTestId("login-page")).toBeInTheDocument();
    expect(useAuthStore.getState().status).toBe("unauthenticated");
  });
});
