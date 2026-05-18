/**
 * StatusBadge — coloured pill + visible text label.
 *
 * Colour-only signals fail NFR-04 / FR-18; the badge always carries
 * its label so SR users and colourblind users get the same information.
 */
const STYLES = {
  APPROVED: "bg-green-100 text-green-800 ring-1 ring-green-200",
  UNDER_REVIEW: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
  REJECTED: "bg-red-100 text-red-800 ring-1 ring-red-200",
  PENDING: "bg-gray-100 text-gray-700 ring-1 ring-gray-200",
};

const LABELS = {
  APPROVED: "Approved",
  UNDER_REVIEW: "Under review",
  REJECTED: "Rejected",
  PENDING: "Pending",
};

export function StatusBadge({ status }) {
  const cls =
    STYLES[status] ?? "bg-gray-100 text-gray-700 ring-1 ring-gray-200";
  const label = LABELS[status] ?? status;
  return (
    <span
      data-testid="status-badge"
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}
    >
      {label}
    </span>
  );
}
