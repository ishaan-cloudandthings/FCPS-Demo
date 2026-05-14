---
name: ui-mockup
description: Produce a self-contained HTML+Tailwind hi-fi mockup of a screen described by a Jira story or a Functional Design section, plus a Markdown design rationale, plus an accessibility audit. Output lives under docs/design/. Used by the Designer agent.
---

# Skill: UI Mockup

## When to use this

You have a story and need to produce a hi-fi mockup that a developer can implement, a stakeholder can review, and an accessibility audit can be run against — all without leaving the repo.

## Output files

For story `<slug>`:

1. `docs/design/<slug>.html` — single self-contained HTML using Tailwind (CDN).
2. `docs/design/<slug>.md` — design rationale.

## HTML rules

- Use Tailwind CDN: `<script src="https://cdn.tailwindcss.com"></script>`.
- No external CSS framework other than Tailwind. No custom Tailwind plugins.
- Render every state on the same page, side-by-side, labelled: default / hover / focus / disabled / loading / error / success.
- Render at three breakpoints if relevant: 360 / 768 / 1280 px (the page itself can be 1280 wide; use Tailwind responsive classes).
- Fonts: system stack `font-sans` or `font-mono` only, unless `docs/design/brand.md` specifies otherwise.
- Colours: Tailwind palette only, unless `docs/design/brand.md` specifies otherwise. Document the mapping (e.g., "primary = blue-600").
- Synthetic data only. Never reference a real vendor / customer.
- Header includes a placeholder for app chrome so reviewers see in-context.

## Rationale doc structure

```markdown
# Design rationale: <story title>

## Component breakdown
List every reusable component this screen needs (with proposed name).

## Typography & spacing
Type scale. Spacing system. Reasoning.

## Colour
Primary, secondary, danger, success. Mapping to Tailwind.

## Accessibility
- Contrast ratios (compute and list).
- Keyboard order.
- Focus management.
- ARIA roles where applicable.
- Screen-reader copy for non-text indicators.

## Interaction & motion
Validation triggers. Animation. Async/loading states.

## Open questions
- …
```

## Refuse-and-flag

- Asked to drop accessibility states "just for the demo". Refuse.
- Asked to use real customer data in screenshots. Refuse.
- Brand assets unspecified and the design is going public-facing. Flag.
