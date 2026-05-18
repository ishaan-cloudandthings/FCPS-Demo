/**
 * Footer used on anonymous-shell screens. From docs/design/01-login.html
 * lines 469-477. Logo asset lives in docs/design/assets/ — for the SPA
 * build we use a text-only attribution to avoid copying the binary into
 * `frontend/public/`. Swap to the image once the brand-asset folder is
 * promoted into the FE static assets.
 */
export function AuthShellFooter() {
  return (
    <footer
      role="contentinfo"
      className="flex items-center justify-between border-t border-gray-200 bg-white px-8 py-3 text-xs text-ink-subtle"
    >
      <span>© Fairfax County Public Schools · Procurement Portal demo</span>
      <span>
        Built by <span className="font-semibold text-ink-muted">Cloud &amp; Things</span>
      </span>
    </footer>
  );
}
