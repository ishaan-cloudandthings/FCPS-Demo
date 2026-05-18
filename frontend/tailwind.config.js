// Tailwind config — colour palette mirrors docs/design/brand.md and the CSS
// custom-properties in docs/design/01-login.html / 02-verification-callback.html.
// Keep these in sync with brand.md; any deviation should be a deliberate
// brand decision, not a drift.
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // C&T brand — from docs/design/brand.md
        brand: {
          blue: {
            50: "#EEF1FB",
            100: "#DDE3F5",
            300: "#8895D1",
            500: "#3B4EA8", // Primary
            700: "#2D3D8A", // Hover
            900: "#1F2C66",
          },
          orange: {
            50: "#FEF3E2",
            100: "#FCD9A8",
            500: "#F47920", // Accent
            600: "#DA660D",
            700: "#B85510",
          },
        },
        // Neutrals — match the 01-login.html `:root` custom properties.
        surface: "#F5F6FA",
        "surface-2": "#EDF0F7",
        ink: {
          DEFAULT: "#111827",
          muted: "#4B5563",
          subtle: "#9CA3AF",
        },
        amber: { text: "#92400E" },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
      // Bounded progress animation — from 02-verification-callback.html
      // (.bounded-progress::after — `slide 3s cubic-bezier forwards`).
      // Drives the 0..100% fill behind the spinner during the 0–10 s
      // verifying window (DESIGN_RATIONALE.md §218).
      keyframes: {
        slide: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
      },
      animation: {
        slide: "slide 3s cubic-bezier(0.4, 0, 0.2, 1) forwards",
      },
      // Background gradient layers used on the auth-shell pages — extracted
      // from 01-login.html `body { background: ... }`.
      backgroundImage: {
        "auth-shell":
          "radial-gradient(ellipse at top left, #EEF1FB 0%, transparent 50%), radial-gradient(ellipse at bottom right, #FEF3E2 0%, transparent 60%)",
        "brand-panel":
          "radial-gradient(circle at 100% 0%, rgba(244,121,32,0.32) 0%, transparent 55%), radial-gradient(circle at 0% 100%, rgba(136,149,209,0.45) 0%, transparent 60%), linear-gradient(135deg, #2D3D8A 0%, #3B4EA8 55%, #1F2C66 100%)",
        "btn-orange":
          "linear-gradient(180deg, #F47920 0%, #DA660D 100%)",
      },
    },
  },
  plugins: [],
};
