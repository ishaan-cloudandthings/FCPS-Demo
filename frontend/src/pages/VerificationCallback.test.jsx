/**
 * RTL tests for VerificationCallback.jsx — covers AC-10 acceptance
 * criteria: success → /vendors, 403 LEVEL_ZERO → /access-denied, 10 s
 * timeout → retry screen (never an infinite spinner).
 */
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

import { VerificationCallback } from "./VerificationCallback.jsx";

/**
 * Test stub that exposes the route-state `reason` via a data-testid so we
 * can assert AC14-D7 threading without pulling AccessDenied into these
 * tests.
 */
function AccessDeniedStub() {
  const location = useLocation();
  return (
    <div>
      <span>Access Denied page</span>
      <span data-testid="route-reason">{location.state?.reason ?? "none"}</span>
    </div>
  );
}

function renderCallback(search = "?code=abc&state=xyz") {
  return render(
    <MemoryRouter initialEntries={[`/verification/callback${search}`]}>
      <Routes>
        <Route path="/verification/callback" element={<VerificationCallback />} />
        <Route path="/vendors" element={<div>Vendors page</div>} />
        <Route path="/access-denied" element={<AccessDeniedStub />} />
        <Route path="/" element={<div data-testid="login">Login page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("VerificationCallback", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the verifying card on mount", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => new Promise(() => {}), // never resolves — keep us in verifying view
    );
    renderCallback();
    expect(
      await screen.findByRole("heading", {
        name: /verifying your identity/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/usually takes 1.3 seconds/i)).toBeInTheDocument();
  });

  it("navigates to /vendors on a 200 callback response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ role: "STAFF", procurement_level: 2, staff_id: 42 }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    renderCallback();
    expect(await screen.findByText(/vendors page/i)).toBeInTheDocument();
  });

  it("navigates to /access-denied on a 403 callback response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Access denied." }), {
        status: 403,
        headers: {
          "Content-Type": "application/json",
          "X-Auth-Reason": "LEVEL_ZERO",
        },
      }),
    );
    renderCallback();
    expect(await screen.findByText(/access denied page/i)).toBeInTheDocument();
    // AC14-D7 — X-Auth-Reason from the 403 must be threaded via route state.
    expect(screen.getByTestId("route-reason")).toHaveTextContent("LEVEL_ZERO");
  });

  it("bounces to / when code/state are missing", async () => {
    renderCallback("");
    expect(await screen.findByTestId("login")).toBeInTheDocument();
  });

  it("shows the timeout view after the 10 s hard timeout", async () => {
    // Mock fetch so it only resolves AFTER abort — i.e. it stays pending
    // for the entire 10 s window, then the AbortController triggers an
    // AbortError.
    vi.spyOn(globalThis, "fetch").mockImplementation(
      (_url, init) =>
        new Promise((_resolve, reject) => {
          init.signal.addEventListener("abort", () => {
            const err = new Error("Aborted");
            err.name = "AbortError";
            reject(err);
          });
        }),
    );

    renderCallback();
    expect(
      await screen.findByRole("heading", {
        name: /verifying your identity/i,
      }),
    ).toBeInTheDocument();

    // Advance past the 10 s SPA timeout.
    await vi.advanceTimersByTimeAsync(10_001);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", {
          name: /taking longer than expected/i,
        }),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole("link", { name: /try signing in again/i }),
    ).toBeInTheDocument();
  });
});
