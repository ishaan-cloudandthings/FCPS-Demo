/**
 * RTL tests for VendorList — AC-22.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { VendorList } from "./VendorList.jsx";
import { useAuthStore } from "../store/auth.js";


function renderList() {
  useAuthStore.setState({
    status: "authenticated",
    role: "ADMIN",
    procurement_level: 3,
    staff_id: 1,
  });
  return render(
    <MemoryRouter initialEntries={["/vendors"]}>
      <Routes>
        <Route path="/vendors" element={<VendorList />} />
      </Routes>
    </MemoryRouter>,
  );
}

const SAMPLE_ROWS = [
  {
    variant: "admin",
    item_id: 1,
    vendor_name: "Northstar Computing",
    item_name: "Laptops",
    category: "Technology",
    contact_name: "Alice",
    status: "APPROVED",
    unit_price: 8499.0,
  },
  {
    variant: "admin",
    item_id: 2,
    vendor_name: "MetroAir Facilities",
    item_name: "HVAC service",
    category: "Facilities",
    contact_name: "Ben",
    status: "PENDING",
    unit_price: 2250.0,
  },
];


describe("VendorList", () => {
  it("renders rows fetched from /api/vendors", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(SAMPLE_ROWS), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    renderList();
    expect(
      await screen.findByText(/northstar computing/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/metroair facilities/i)).toBeInTheDocument();
  });

  it("filters by vendor name (case-insensitive)", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(SAMPLE_ROWS), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    renderList();
    await screen.findByText(/northstar computing/i);

    await userEvent.type(screen.getByRole("searchbox"), "metro");

    await waitFor(() => {
      expect(screen.queryByText(/northstar computing/i)).toBeNull();
    });
    expect(screen.getByText(/metroair facilities/i)).toBeInTheDocument();
  });

  it("renders the empty state when zero rows", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    renderList();
    expect(
      await screen.findByText(/no vendors in the system yet/i),
    ).toBeInTheDocument();
  });

  it("renders a friendly error on fetch failure", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ detail: "Service temporarily unavailable." }),
        { status: 503, headers: { "Content-Type": "application/json" } },
      ),
    );
    renderList();
    expect(
      await screen.findByText(/service temporarily unavailable/i),
    ).toBeInTheDocument();
  });
});
