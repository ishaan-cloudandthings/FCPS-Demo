/**
 * RTL tests for AccessDenied.jsx — AC-14.
 *
 * Maps to decisions in `docs/decision-log/AC-14-access-denied.md`:
 *   - AC14-D1 — variant selection by route state.
 *   - AC14-D2 — default to NON_STAFF when no state.
 *   - AC14-D3 — "Back to Staff Procurement Portal" posts logout and navigates to "/".
 *   - AC14-D5 — accessibility: SkipLink, main landmark.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AccessDenied } from "./AccessDenied.jsx";

function renderAt(reason) {
  // `MemoryRouter` lets us seed `useLocation().state` via `initialEntries`
  // with an array of location objects.
  const entries = [
    reason === undefined
      ? "/access-denied"
      : { pathname: "/access-denied", state: { reason } },
  ];
  return render(
    <MemoryRouter initialEntries={entries}>
      <Routes>
        <Route path="/access-denied" element={<AccessDenied />} />
        <Route path="/" element={<div data-testid="login">Login page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AccessDenied", () => {
  it("renders the NON_STAFF copy variant when route state says NON_STAFF", () => {
    renderAt("NON_STAFF");
    expect(
      screen.getByRole("heading", { name: /you don't have access to this portal/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/doesn't have access to the staff procurement portal/i),
    ).toBeInTheDocument();
  });

  it("renders the NOT_REGISTERED copy variant when route state says NOT_REGISTERED", () => {
    renderAt("NOT_REGISTERED");
    expect(
      screen.getByRole("heading", { name: /identity not verified/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/couldn't verify your identity/i),
    ).toBeInTheDocument();
  });

  it("defaults to NON_STAFF when no route state is present (AC14-D2)", () => {
    renderAt(undefined);
    expect(
      screen.getByRole("heading", { name: /you don't have access to this portal/i }),
    ).toBeInTheDocument();
  });

  it("'Back to Staff Procurement Portal' posts logout and navigates to /", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("", { status: 204 }));
    globalThis.fetch = fetchMock;

    renderAt("NON_STAFF");
    await userEvent.click(
      screen.getByRole("button", { name: /back to staff procurement portal/i }),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/auth/logout",
        expect.objectContaining({ method: "POST", credentials: "include" }),
      );
    });
    expect(await screen.findByTestId("login")).toBeInTheDocument();
  });

  it("renders the skip link and a <main> landmark", () => {
    renderAt("NON_STAFF");
    expect(
      screen.getByRole("link", { name: /skip to main content/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
  });
});
