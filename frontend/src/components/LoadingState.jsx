/**
 * LoadingState — bounded skeleton rows.
 *
 * FUNCTIONAL_DESIGN.md §7.4: never an indefinite spinner. We render a
 * small fixed number of placeholder rows; if the data arrives, the
 * caller swaps to the real `VendorTable`.
 */
const PLACEHOLDER_ROWS = 5;

export function LoadingState() {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-live="polite"
      className="space-y-2"
    >
      <span className="visually-hidden">Loading vendors…</span>
      {Array.from({ length: PLACEHOLDER_ROWS }).map((_, i) => (
        <div
          key={i}
          aria-hidden="true"
          className="h-10 animate-pulse rounded-md bg-gray-100"
        />
      ))}
    </div>
  );
}
