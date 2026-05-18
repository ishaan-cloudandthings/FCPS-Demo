/**
 * Thin `fetch` wrapper — see FUNCTIONAL_DESIGN.md §7.6.
 *
 * Responsibilities:
 *   - Always send the session cookie (`credentials: "include"`).
 *   - Set `Content-Type: application/json` when a JSON body is provided.
 *   - Map non-2xx to a typed `ApiError` so callers can switch on `.status`.
 *
 * Global 401 handling lives in `useAuthBootstrap` and the page-level
 * `useEffect`s — not here — so this stays a transport-only utility and
 * doesn't surprise callers by mutating navigation state.
 */

export class ApiError extends Error {
  constructor(status, detail, headers) {
    super(detail || `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.headers = headers;
  }
}

export async function apiFetch(path, options = {}) {
  const { body, headers, ...rest } = options;
  const init = {
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    ...rest,
  };
  if (body !== undefined) {
    init.body = typeof body === "string" ? body : JSON.stringify(body);
  }

  const response = await fetch(path, init);

  // 204 → no body; just succeed.
  if (response.status === 204) {
    return null;
  }

  // Empty 200 (rare) → null.
  const text = await response.text();
  const payload = text ? safeJson(text) : null;

  if (!response.ok) {
    const detail =
      (payload && typeof payload === "object" && payload.detail) ||
      `HTTP ${response.status}`;
    throw new ApiError(response.status, detail, response.headers);
  }

  return payload;
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
