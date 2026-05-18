// Vite config — see docs/decision-log/AC-10-frontend-bootstrap.md (choice 8):
// dev server proxies /api → FastAPI on :8000 so the SPA can fetch same-origin
// in dev (matches the prod Nginx topology — see docs/ARCHITECTURE.md §8.1).
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.js"],
    css: false,
  },
});
