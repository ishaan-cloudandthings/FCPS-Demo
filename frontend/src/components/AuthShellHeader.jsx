/**
 * Header used on anonymous-shell screens (Login + VerificationCallback +
 * AccessDenied). See docs/design/01-login.html lines 405-415 and
 * docs/design/DESIGN_RATIONALE.md §707 ("Why the header is the Login-style
 * header"). The authenticated app header (with logout, user identity, etc.)
 * is a different component owned by the authenticated layout — out of
 * scope for AC-10.
 */
export function AuthShellHeader() {
  return (
    <header
      role="banner"
      className="flex items-center justify-between border-b border-gray-200 bg-white px-8 py-4"
    >
      <span className="flex items-center gap-2 text-sm font-semibold text-ink">
        <span
          aria-hidden="true"
          className="inline-flex h-7 w-7 items-center justify-center rounded bg-brand-blue-500 text-xs font-bold text-white"
        >
          F
        </span>
        Staff Procurement Portal
      </span>
      <span className="text-xs text-ink-subtle">Built by Cloud &amp; Things</span>
    </header>
  );
}
