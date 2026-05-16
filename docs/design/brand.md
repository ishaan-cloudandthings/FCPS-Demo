# C&T Brand Guidelines

## Colours

| Role | Name | Hex | Usage |
|---|---|---|---|
| Primary | C&T Blue | `#3B4EA8` | Headers, primary buttons, links, nav background |
| Accent | C&T Orange | `#F47920` | CTAs, highlights, hover states, badges |
| White | White | `#FFFFFF` | Backgrounds, text on dark |
| Light Grey | Surface | `#F5F6FA` | Page background, table alternating rows |
| Mid Grey | Border | `#D1D5DB` | Dividers, input borders |
| Dark Grey | Body text | `#1F2937` | Body copy, labels |
| Success | Approved | `#16A34A` | APPROVED status badge |
| Warning | Under Review | `#D97706` | UNDER_REVIEW status badge |
| Danger | Rejected | `#DC2626` | REJECTED status badge |
| Neutral | Pending | `#6B7280` | PENDING status badge |

## Typography

| Role | Font | Weight | Notes |
|---|---|---|---|
| Headings | Inter | 700 (Bold) | Via Google Fonts |
| Body | Inter | 400 (Regular) | Via Google Fonts |
| Labels / UI | Inter | 500 (Medium) | Buttons, nav items |
| Accent text | Inter | 700 Italic | Mirrors "Things" wordmark style |

Import: `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap`

## Logo

- Full logo: `docs/design/assets/cnt-logo.png`
- Use on white or light backgrounds
- Minimum width: 120px
- Clear space: equal to the height of the cloud icon on all sides
- Do not recolour, stretch, or place on dark backgrounds without a white version

## Button styles

| Variant | Background | Text | Border |
|---|---|---|---|
| Primary | `#3B4EA8` | White | none |
| Primary hover | `#2D3D8A` | White | none |
| Secondary | White | `#3B4EA8` | `#3B4EA8` |
| Destructive | `#DC2626` | White | none |

## Component tokens (Tailwind equivalents)

- Primary blue → `bg-[#3B4EA8]` / `text-[#3B4EA8]`
- Accent orange → `bg-[#F47920]` / `text-[#F47920]`
- Page background → `bg-[#F5F6FA]`
- Card background → `bg-white`
- Sensitive data card → `bg-orange-50 border border-orange-200`
