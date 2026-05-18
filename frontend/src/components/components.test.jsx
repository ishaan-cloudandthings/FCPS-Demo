/**
 * AC-21 component tests. One file so the small components share fixtures.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { EmptyState } from "./EmptyState.jsx";
import { LoadingState } from "./LoadingState.jsx";
import { SearchBar } from "./SearchBar.jsx";
import { StatusBadge } from "./StatusBadge.jsx";
import { VendorTable } from "./VendorTable.jsx";


// ---------------------------------------------------------------------------
// StatusBadge
// ---------------------------------------------------------------------------


describe("StatusBadge", () => {
  it("renders the human label, not the raw enum", () => {
    render(<StatusBadge status="UNDER_REVIEW" />);
    expect(screen.getByText(/under review/i)).toBeInTheDocument();
    // Belt-and-braces: the raw enum (with underscore) must not be visible.
    expect(screen.queryByText("UNDER_REVIEW")).toBeNull();
  });

  it("falls back gracefully for an unknown status", () => {
    render(<StatusBadge status="MYSTERY" />);
    expect(screen.getByText("MYSTERY")).toBeInTheDocument();
  });
});


// ---------------------------------------------------------------------------
// SearchBar
// ---------------------------------------------------------------------------


describe("SearchBar", () => {
  it("is a searchbox and emits its new value", async () => {
    const onChange = vi.fn();
    render(<SearchBar value="" onChange={onChange} />);
    const input = screen.getByRole("searchbox");
    await userEvent.type(input, "ab");
    // Two keystrokes → two onChange calls with cumulative values.
    expect(onChange).toHaveBeenCalledTimes(2);
    expect(onChange).toHaveBeenLastCalledWith("b");
  });
});


// ---------------------------------------------------------------------------
// EmptyState
// ---------------------------------------------------------------------------


describe("EmptyState", () => {
  it("has role=status and renders title + hint", () => {
    render(<EmptyState title="Nothing here" hint="Try a different filter" />);
    const region = screen.getByRole("status");
    expect(region).toHaveTextContent(/nothing here/i);
    expect(region).toHaveTextContent(/try a different filter/i);
  });
});


// ---------------------------------------------------------------------------
// LoadingState
// ---------------------------------------------------------------------------


describe("LoadingState", () => {
  it("renders a bounded skeleton with aria-busy", () => {
    render(<LoadingState />);
    const region = screen.getByRole("status");
    expect(region).toHaveAttribute("aria-busy", "true");
  });
});


// ---------------------------------------------------------------------------
// VendorTable
// ---------------------------------------------------------------------------


function renderWithRouter(ui) {
  return render(
    <MemoryRouter initialEntries={["/vendors"]}>
      <Routes>
        <Route path="/vendors" element={ui} />
        <Route path="/vendors/:item_id" element={<div data-testid="detail">detail</div>} />
      </Routes>
    </MemoryRouter>,
  );
}


const ADMIN_ROW = {
  variant: "admin",
  item_id: 1,
  vendor_name: "Acme",
  item_name: "Widget",
  category: "Supplies",
  contact_name: "Alice",
  status: "APPROVED",
  unit_price: 9.99,
};

const L1_ROW = {
  variant: "staff_l1",
  item_id: 2,
  vendor_name: "Globex",
  item_name: "Gadget",
  category: "Technology",
};


describe("VendorTable", () => {
  it("renders the EmptyState when no rows", () => {
    renderWithRouter(<VendorTable rows={[]} emptyTitle="No vendors yet." />);
    expect(screen.getByText(/no vendors yet/i)).toBeInTheDocument();
  });

  it("renders the admin column set when rows.variant=admin", () => {
    renderWithRouter(<VendorTable rows={[ADMIN_ROW]} />);
    for (const header of ["Vendor", "Item", "Category", "Contact", "Status", "Unit price"]) {
      expect(
        screen.getByRole("columnheader", { name: header }),
      ).toBeInTheDocument();
    }
    expect(screen.getByText("$9.99")).toBeInTheDocument();
  });

  it("renders only the L1 columns when rows.variant=staff_l1", () => {
    renderWithRouter(<VendorTable rows={[L1_ROW]} />);
    for (const header of ["Vendor", "Item", "Category"]) {
      expect(
        screen.getByRole("columnheader", { name: header }),
      ).toBeInTheDocument();
    }
    for (const hidden of ["Contact", "Status", "Unit price"]) {
      expect(
        screen.queryByRole("columnheader", { name: hidden }),
      ).toBeNull();
    }
  });

  it("clicking a row navigates to /vendors/:item_id", async () => {
    renderWithRouter(<VendorTable rows={[ADMIN_ROW]} />);
    await userEvent.click(screen.getByTestId("vendor-row-1"));
    expect(await screen.findByTestId("detail")).toBeInTheDocument();
  });
});
