/**
 * VendorList — `/vendors` route, real list rendering (AC-22).
 *
 * Decisions: docs/decision-log/AC-22-vendor-pages.md.
 * Renders inside AC-20's `AppShell` (authenticated header).
 * Uses AC-21's `<VendorTable>`, `<SearchBar>`, `<EmptyState>`,
 * `<LoadingState>`.
 *
 * Today the API returns admin-variant rows for everyone (AC-18 + the
 * deliberate skip of AC-17). When AC-17 lands, the table will render
 * staff_l1 / staff_l2 / admin variants automatically because
 * `<VendorTable>` reads `row.variant`.
 */
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "../components/AppShell.jsx";
import { EmptyState } from "../components/EmptyState.jsx";
import { LoadingState } from "../components/LoadingState.jsx";
import { SearchBar } from "../components/SearchBar.jsx";
import { VendorTable } from "../components/VendorTable.jsx";
import { apiFetch } from "../services/apiFetch.js";

export function VendorList() {
  const [rows, setRows] = useState(null);    // null = loading
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    document.title = "Vendors | Staff Procurement";
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiFetch("/api/vendors")
      .then((data) => {
        if (cancelled) return;
        setRows(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err?.detail ?? "We couldn't load vendors. Please try again.");
        setRows([]); // unstick from loading
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredRows = useMemo(() => {
    if (!rows) return [];
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => r.vendor_name.toLowerCase().includes(q));
  }, [rows, search]);

  let body;
  if (rows === null) {
    body = <LoadingState />;
  } else if (error) {
    body = (
      <div
        role="alert"
        className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      >
        {error}
      </div>
    );
  } else if (rows.length === 0) {
    body = <EmptyState title="No vendors in the system yet." />;
  } else if (filteredRows.length === 0) {
    body = (
      <EmptyState
        title={`No results for "${search}".`}
        hint="Try a different vendor name."
      />
    );
  } else {
    body = <VendorTable rows={filteredRows} />;
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold tracking-tight">Vendors</h1>
          <SearchBar value={search} onChange={setSearch} />
        </div>
        {body}
      </div>
    </AppShell>
  );
}
