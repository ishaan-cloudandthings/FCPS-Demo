/**
 * EmptyState — `<div role="status">` with a friendly title + optional hint.
 *
 * Used by `VendorTable` when rows.length === 0.
 */
export function EmptyState({ title, hint }) {
  return (
    <div
      role="status"
      className="rounded-lg border border-dashed border-gray-300 bg-white px-6 py-10 text-center"
    >
      <p className="text-sm font-semibold text-ink">{title}</p>
      {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
    </div>
  );
}
