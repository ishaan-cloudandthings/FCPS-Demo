"""Structured logger wrapper.

A thin wrapper around stdlib `logging`. For the demo we emit plain-text
formatted output to stdout; production would swap the formatter for JSON.

Centralising this here means every module's `get_logger(__name__)` call
gets the same configuration without duplicated `logging.basicConfig` calls.
"""
import logging
import os
import sys

_configured = False


def _configure_once() -> None:
    global _configured
    if _configured:
        return

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root = logging.getLogger()
    # Avoid duplicate handlers if something else (e.g. uvicorn) already added one.
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)
    root.setLevel(level)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger; lazily configures the root handler on first call."""
    _configure_once()
    return logging.getLogger(name)
