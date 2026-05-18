/**
 * VendorTable — variant-aware list rendering.
 *
 * AC-15 ships the `variant` discriminator on every list-item response.
 * This table reads `rows[0].variant` to pick a column set and renders
 * accordingly. Today the API always emits `"admin"` (everyone sees
 * everything). When AC-17 lands, the same component will render
 * staff_l1 / staff_l2 / admin rows naturally — no FE change needed.
 *
 * Empty list → `<EmptyState />` instead of an empty table.
 */
import { useNavigate } from "react-router-dom";

import { EmptyState } from "./EmptyState.jsx";
import { StatusBadge } from "./StatusBadge.jsx";

// AC21-D6: declarative column sets. Each entry is { key, header, render }.
const COLUMNS_BY_VARIANT = {
  staff_l1: [
    { key: "vendor_name", header: "Vendor" },
    { key: "item_name", header: "Item" },
    { key: "category", header: "Category" },
  ],
  staff_l2: [
    { key: "vendor_name", header: "Vendor" },
    { key: "item_name", header: "Item" },
    { key: "category", header: "Category" },
    { key: "contact_name", header: "Contact" },
  ],
  admin: [
    { key: "vendor_name", header: "Vendor" },
    { key: "item_name", header: "Item" },
    { key: "category", header: "Category" },
    { key: "contact_name", header: "Contact" },
    {
      key: "status",
      header: "Status",
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "unit_price",
      header: "Unit price",
      render: (row) =>
        row.unit_price == null
          ? "—"
          : `$${Number(row.unit_price).toFixed(2)}`,
    },
  ],
};

export function VendorTable({ rows, emptyTitle = "No vendors to show." }) {
  const navigate = useNavigate();

  if (!rows || rows.length === 0) {
    return <EmptyState title={emptyTitle} />;
  }

  const variant = rows[0].variant;
  const columns = COLUMNS_BY_VARIANT[variant] ?? COLUMNS_BY_VARIANT.admin;

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <caption className="visually-hidden">
          List of vendors. Click a row to open details.
        </caption>
        <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-ink-muted">
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col" className="px-4 py-3">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map((row) => (
            <tr
              key={row.item_id}
              data-testid={`vendor-row-${row.item_id}`}
              onClick={() => navigate(`/vendors/${row.item_id}`)}
              className="cursor-pointer hover:bg-brand-blue-50"
            >
              {columns.map((c) => (
                <td key={c.key} className="whitespace-nowrap px-4 py-3 text-ink">
                  {c.render ? c.render(row) : (row[c.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
