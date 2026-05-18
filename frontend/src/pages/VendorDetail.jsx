/**
 * VendorDetail — `/vendors/:item_id` route (AC-22).
 *
 * Today every authenticated user can view detail (auth-only). When AC-17
 * lands, the route will additionally guard on `level=3` / `role="ADMIN"`.
 * For now, FE relies on backend gating.
 */
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { AppShell } from "../components/AppShell.jsx";
import { LoadingState } from "../components/LoadingState.jsx";
import { StatusBadge } from "../components/StatusBadge.jsx";
import { ApiError, apiFetch } from "../services/apiFetch.js";

export function VendorDetail() {
  const { item_id } = useParams();
  const [vendor, setVendor] = useState(null);   // null = loading
  const [error, setError] = useState(null);     // {status, detail} | string

  useEffect(() => {
    let cancelled = false;
    apiFetch(`/api/vendors/${encodeURIComponent(item_id)}`)
      .then((data) => {
        if (cancelled) return;
        setVendor(data);
        document.title = `${data.vendor_name} | FCPS Procurement`;
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setError({ status: 404 });
        } else {
          setError({ detail: "We couldn't load this vendor." });
        }
        setVendor(undefined); // signal "done loading" without success
      });
    return () => {
      cancelled = true;
    };
  }, [item_id]);

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <Link
          to="/vendors"
          className="mb-4 inline-block text-sm font-medium text-brand-blue-500 hover:underline"
        >
          ← Back to vendors
        </Link>
        {vendor === null && <LoadingState />}
        {error && error.status === 404 && (
          <div
            role="alert"
            className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
          >
            Vendor not found.
          </div>
        )}
        {error && !error.status && (
          <div
            role="alert"
            className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          >
            {error.detail}
          </div>
        )}
        {vendor && vendor !== undefined && !error && (
          <VendorDetailCard vendor={vendor} />
        )}
      </div>
    </AppShell>
  );
}

function VendorDetailCard({ vendor }) {
  return (
    <section
      data-testid="vendor-detail-card"
      className="rounded-lg border border-gray-200 bg-white p-8 shadow-sm"
    >
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {vendor.vendor_name}
          </h1>
          <p className="mt-1 text-sm text-ink-muted">{vendor.item_name}</p>
        </div>
        <StatusBadge status={vendor.status} />
      </div>
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Category" value={vendor.category} />
        <Field
          label="Unit price"
          value={
            vendor.unit_price == null
              ? "—"
              : `$${Number(vendor.unit_price).toFixed(2)}`
          }
        />
        <Field label="Contact name" value={vendor.contact_name ?? "—"} />
        <Field label="Contact email" value={vendor.contact_email ?? "—"} />
        {vendor.status === "APPROVED" && (
          <Field
            label="Approved on"
            value={vendor.approved_at ?? "—"}
          />
        )}
      </dl>
    </section>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-ink">{value}</dd>
    </div>
  );
}
