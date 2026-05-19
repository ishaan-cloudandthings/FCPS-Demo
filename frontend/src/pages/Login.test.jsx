/**
 * RTL tests for Login.jsx — covers AC-10 acceptance criteria:
 *   - Default state: "Verify with ID.me" CTA visible + one-line explanation.
 *   - Returning after session expiry: banner reads
 *     "Your session has expired. Please verify again." (REQUIREMENTS.md FR-08).
 *   - CTA triggers POST /api/auth/login then window.location redirect.
 *
 * Yellow-Zone story — these are the smoke tests. A developer doing
 * meaningful edits will extend coverage.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { Login } from "./Login.jsx";
import { useAuthStore } from "../store/auth.js";

function renderLogin(initialPath = "/") {
  // Force unauthenticated so the page doesn't redirect to /vendors.
  useAuthStore.setState({ status: "unauthenticated" });
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Login />
    </MemoryRouter>,
  );
}

describe("Login", () => {
  it("renders the single 'Verify with ID.me' CTA and the explanation hint", () => {
    renderLogin();
    expect(
      screen.getByRole("button", { name: /verify with id\.me/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/redirected to id\.me to verify/i),
    ).toBeInTheDocument();
  });

  it("shows the session-expired banner on /?reason=session_expired", () => {
    renderLogin("/?reason=session_expired");
    const banner = screen.getByRole("alert");
    expect(banner).toHaveTextContent(/your session has expired/i);
    expect(banner).toHaveTextContent(/please verify again/i);
  });

  it("POSTs /api/auth/login and redirects on click", async () => {
    // Mock the network and the window navigation.
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ authorize_url: "https://api.id.me/oauth/authorize?x=1" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const assignMock = vi.fn();
    // jsdom's window.location is read-only; replace it with a stub.
    const originalLocation = window.location;
    delete window.location;
    window.location = { ...originalLocation, assign: assignMock };

    renderLogin();
    await userEvent.click(
      screen.getByRole("button", { name: /verify with id\.me/i }),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/auth/login",
        expect.objectContaining({ method: "POST", credentials: "include" }),
      );
      expect(assignMock).toHaveBeenCalledWith(
        "https://api.id.me/oauth/authorize?x=1",
      );
    });

    window.location = originalLocation;
  });

  // -------------------------------------------------------------------------
  // ADR-014 / DEV9 — dev persona panel
  // -------------------------------------------------------------------------

  it("renders the persona panel when the dev-login probe returns 200", async () => {
    globalThis.fetch = vi.fn().mockImplementation((url) => {
      if (typeof url === "string" && url.endsWith("/api/auth/dev-login/available")) {
        return Promise.resolve(
          new Response(JSON.stringify({ available: true }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }
      return Promise.reject(new Error(`unexpected url ${url}`));
    });

    renderLogin();
    expect(
      await screen.findByTestId("dev-persona-panel"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /demo persona: procurement supervisor/i }),
    ).toBeInTheDocument();
  });

  it("does NOT render the persona panel when the probe returns 404", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response("", { status: 404 }),
    );

    renderLogin();
    // Give the probe a chance to resolve.
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /verify with id\.me/i }),
      ).toBeInTheDocument();
    });
    expect(screen.queryByTestId("dev-persona-panel")).not.toBeInTheDocument();
  });

  it("clicking Admin POSTs dev-login and navigates to /vendors", async () => {
    useAuthStore.setState({ status: "unauthenticated" });

    const fetchMock = vi.fn().mockImplementation((url, init) => {
      if (typeof url === "string" && url.endsWith("/api/auth/dev-login/available")) {
        return Promise.resolve(
          new Response(JSON.stringify({ available: true }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }
      if (
        typeof url === "string" &&
        url.endsWith("/api/auth/dev-login") &&
        init?.method === "POST"
      ) {
        return Promise.resolve(
          new Response(
            JSON.stringify({ role: "ADMIN", procurement_level: 3, staff_id: 1 }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        );
      }
      return Promise.reject(new Error(`unexpected url ${url}`));
    });
    globalThis.fetch = fetchMock;

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/vendors" element={<div>Vendors page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    const adminButton = await screen.findByRole("button", {
      name: /demo persona: procurement supervisor/i,
    });
    await userEvent.click(adminButton);

    expect(await screen.findByText(/vendors page/i)).toBeInTheDocument();
    // Verify the POST was made with the right body.
    const postCall = fetchMock.mock.calls.find(
      ([url, init]) =>
        typeof url === "string" &&
        url.endsWith("/api/auth/dev-login") &&
        init?.method === "POST",
    );
    expect(postCall).toBeDefined();
    expect(JSON.parse(postCall[1].body)).toEqual({ persona: "procurement_supervisor" });
  });
});
