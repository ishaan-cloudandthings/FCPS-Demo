// Vitest setup — jest-dom matchers + global fetch reset between tests.
import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, vi } from "vitest";

import { useAuthStore } from "../store/auth.js";

// jsdom under Node 16 doesn't ship `fetch` on globalThis. Define a default
// so tests can `vi.spyOn(globalThis, "fetch")` without "fetch does not
// exist" errors. Each test re-mocks the return value as it needs.
if (typeof globalThis.fetch !== "function") {
  globalThis.fetch = vi.fn();
}

// Minimal Response polyfill — enough for `apiFetch` (uses .status, .ok,
// .text(), .headers.get). jsdom on Node 16 doesn't define `Response`.
if (typeof globalThis.Response === "undefined") {
  globalThis.Response = class PolyResponse {
    constructor(body = "", init = {}) {
      this._body = body == null ? "" : String(body);
      this.status = init.status ?? 200;
      this.ok = this.status >= 200 && this.status < 300;
      const headers = init.headers ?? {};
      this.headers = {
        get: (name) => {
          const target = name.toLowerCase();
          for (const k of Object.keys(headers)) {
            if (k.toLowerCase() === target) return headers[k];
          }
          return null;
        },
      };
    }
    text() {
      return Promise.resolve(this._body);
    }
    json() {
      return Promise.resolve(JSON.parse(this._body));
    }
  };
}

beforeEach(() => {
  // Default: reject so an un-mocked fetch loudly fails the test instead
  // of silently returning `undefined`.
  globalThis.fetch = vi.fn(() =>
    Promise.reject(new Error("fetch not mocked in this test")),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
  useAuthStore.setState({
    status: "loading",
    role: null,
    staff_id: null,
  });
});
