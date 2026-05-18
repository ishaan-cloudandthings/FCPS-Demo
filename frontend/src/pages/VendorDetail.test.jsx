/**
 * RTL tests for VendorDetail — AC-22.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { VendorDetail } from "./VendorDetail.jsx";
import { useAuthStore } from "../store/auth.js";


function renderDetail(itemId = 7) {
  useAuthStore.setState({
    status: "authenticated",
    role: "ADMIN",
    procurement_level: 3,
    staff_id: 1,
  });
  return render(
    <MemoryRouter initialEntries={[`/vendors/${itemId}`]}>
      <Routes>
        <Route path="/vendors/:item_id" element={<VendorDetail />} />
        <Route path="/vendors" element={<div data-testid="list">List</div>} />
      </Routes>
    </MemoryRouter>,
  );
}


const DETAIL_PAYLOAD = {
  variant: "admin_detail",
  item_id: 7,
  vendor_name: "Acme Vendor",
  item_name: "Widget",
  category: "Supplies",
  contact_name: "Alice",
  contact_email: "alice@vendor.test",
  status: "APPROVED",
  unit_price: 9.99,
  approved_at: "2026-02-14",
  created_date: "2026-01-01T09:00:00Z",
  updated_date: "2026-02-14T10:30:00Z",
};


describe("VendorDetail", () => {
  it("renders all fields on 200 + APPROVED shows Approved-on", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(DETAIL_PAYLOAD), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    renderDetail(7);

    expect(
      await screen.findByRole("heading", { name: /acme vendor/i }),
    ).toBeInTheDocument();
    const card = screen.getByTestId("vendor-detail-card");
    expect(card).toHaveTextContent("alice@vendor.test");
    expect(card).toHaveTextContent("$9.99");
    expect(card).toHaveTextContent(/approved on/i);
    expect(card).toHaveTextContent("2026-02-14");
  });

  it("renders the friendly 'not found' card on 404", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Vendor not found." }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    );
    renderDetail(999);

    expect(
      await screen.findByText(/vendor not found/i),
    ).toBeInTheDocument();
  });

  it("renders a generic error on 503", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Service temporarily unavailable." }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }),
    );
    renderDetail(1);

    expect(
      await screen.findByText(/couldn't load this vendor/i),
    ).toBeInTheDocument();
  });

  it("has a Back-to-vendors link", () => {
    globalThis.fetch = vi.fn(() => new Promise(() => {}));
    renderDetail(1);
    expect(
      screen.getByRole("link", { name: /back to vendors/i }),
    ).toBeInTheDocument();
  });
});
