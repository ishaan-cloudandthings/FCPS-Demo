/**
 * Skip-to-main-content link — accessibility requirement per
 * docs/design/DESIGN_RATIONALE.md §80 + FUNCTIONAL_DESIGN.md §7.8.
 *
 * Renders as the first focusable element. Visually hidden until focused.
 */
export function SkipLink({ targetId = "main" }) {
  return (
    <a href={`#${targetId}`} className="skip-link">
      Skip to main content
    </a>
  );
}
