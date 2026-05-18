/**
 * RTL tests for AccessDenied.jsx — AC-14.
 *
 * Maps to decisions in `docs/decision-log/AC-14-access-denied.md`:
 *   - AC14-D1 — variant selection by route state.
 *   - AC14-D2 — default to LEVEL_ZERO when no state.
 *   - AC14-D3 — "Back to FCPS" posts logout and navigates to "/".
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
  it("renders the LEVEL_ZERO copy variant when route state says LEVEL_ZERO", () => {
    renderAt("LEVEL_ZERO");
    expect(
      screen.getByRole("heading", { name: /you don't have access to this portal/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/procurement clearance needed to view vendor records/i),
    ).toBeInTheDocument();
  });

  it("renders the NOT_REGISTERED copy variant when route state says NOT_REGISTERED", () => {
    renderAt("NOT_REGISTERED");
    expect(
      screen.getByRole("heading", { name: /we can't sign you in/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/not registered in the fcps procurement system/i),
    ).toBeInTheDocument();
  });

  it("defaults to LEVEL_ZERO when no route state is present (AC14-D2)", () => {
    renderAt(undefined);
    expect(
      screen.getByRole("heading", { name: /you don't have access to this portal/i }),
    ).toBeInTheDocument();
  });

  it("'Back to FCPS' posts logout and navigates to /", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("", { status: 204 }));
    globalThis.fetch = fetchMock;

    renderAt("LEVEL_ZERO");
    await userEvent.click(
      screen.getByRole("button", { name: /back to fcps/i }),
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
    renderAt("LEVEL_ZERO");
    expect(
      screen.getByRole("link", { name: /skip to main content/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
  });
});
