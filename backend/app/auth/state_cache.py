"""
🔴 RED ZONE — implements AC-6 (Story: AC-6 / Epic: AC-2).

Ratified decisions live in:
    docs/decision-log/AC-6-login-init.md

This module implements the OAuth state cache for the ID.me login flow.

Behaviour summary (anchor for code reviewers):

* `issue()` generates a 32-byte URL-safe token (AC6-D1), stores it with the
  current clock-time, and returns it. If the cache is at capacity (1024 by
  default — AC6-D4), it raises `StateCacheError` so the route can return 503.
* `consume(token)` is the **one-shot** lookup (AC6-D5). It pops the entry
  if present, then validates that the entry is not expired. Returns `True`
  on success, `False` on missing-or-expired. The token cannot be reused.
* Expiry sweep runs lazily on `issue()` (AC6-D4) — no background thread.

Concurrency model: this cache is safe ONLY under a single Uvicorn worker
running the standard async event loop (AC6-D2 + AC6-D3). Multi-worker /
multi-process deploys must move to a shared store (Redis) — that's a
phase-2 change.

Time source: a callable injected at construction (defaults to
`time.monotonic`). Tests inject a fake clock to exercise expiry without
sleeping; production uses monotonic time so the cache is immune to
wall-clock changes.
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Callable

# AC6-D5: 10-minute TTL — matches D-FD-08 in FUNCTIONAL_DESIGN.md.
TTL_SECONDS: int = 600

# AC6-D4: bounded memory; over-cap returns 503 at the route layer.
MAX_ENTRIES: int = 1024


class StateCacheError(Exception):
    """Raised when the cache cannot accept a new entry (over capacity)."""


@dataclass(frozen=True)
class _Entry:
    issued_at: float  # value returned by the injected clock


class OAuthStateCache:
    """In-process one-shot OAuth state cache.

    See module docstring for the full behavioural contract. Direct access
    to `_store` is restricted to this class; tests touch it only for
    assertions (e.g. `len(cache)`).
    """

    def __init__(
        self,
        ttl_seconds: int = TTL_SECONDS,
        max_entries: int = MAX_ENTRIES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")
        self._ttl = ttl_seconds
        self._max = max_entries
        self._clock = clock
        self._store: dict[str, _Entry] = {}

    def issue(self) -> str:
        """Generate a new state token, cache it, and return it.

        Raises `StateCacheError` if the cache is at capacity after the
        lazy expiry sweep.
        """
        self._sweep_expired()
        if len(self._store) >= self._max:
            raise StateCacheError("state cache at capacity")

        # AC6-D1: 32-byte URL-safe random token (~43 char output).
        token = secrets.token_urlsafe(32)
        self._store[token] = _Entry(issued_at=self._clock())
        return token

    def consume(self, token: str) -> bool:
        """One-shot lookup: pop the entry, validate it isn't expired.

        Returns True iff the token was present and unexpired. Subsequent
        calls with the same token return False (AC6-D5).
        """
        entry = self._store.pop(token, None)
        if entry is None:
            return False
        if self._clock() - entry.issued_at > self._ttl:
            # Expired — already popped above; nothing else to do.
            return False
        return True

    def _sweep_expired(self) -> None:
        """Lazy expiry sweep on issue (AC6-D4). O(n); fine at our scale."""
        now = self._clock()
        expired = [t for t, e in self._store.items() if now - e.issued_at > self._ttl]
        for t in expired:
            self._store.pop(t, None)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._store)
