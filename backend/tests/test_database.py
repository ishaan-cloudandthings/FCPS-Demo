"""Tests for `app.core.database` — AC-11.

Covers AC11-D2 (per-request connection lifecycle) and AC11-D4 (thin-mode
only — never `init_oracle_client`).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.core.config import get_settings
from app.core.database import get_oracle_connection


def test_get_oracle_connection_opens_thin_mode_connection_with_env_settings():
    """The dependency calls `oracledb.connect` with the kwargs derived
    from Settings (env-driven, no hardcoded values).
    """
    with patch("app.core.database.oracledb") as mock_oracledb:
        mock_oracledb.makedsn.return_value = "FAKE-DSN"
        mock_oracledb.connect.return_value = MagicMock(name="connection")

        settings = get_settings()
        gen = get_oracle_connection(settings)
        next(gen)  # advance to yield

        mock_oracledb.makedsn.assert_called_once_with(
            host="test-oracle-host",
            port=1521,
            service_name="XEPDB1",
        )
        mock_oracledb.connect.assert_called_once_with(
            user="test_user",
            password="test_password",
            dsn="FAKE-DSN",
        )
        # AC11-D4 — thin-mode only. init_oracle_client must NEVER be called.
        assert not mock_oracledb.init_oracle_client.called


def test_get_oracle_connection_closes_on_cleanup():
    """The generator must close the connection when the request lifecycle
    completes — the yield/close pattern.
    """
    with patch("app.core.database.oracledb") as mock_oracledb:
        mock_oracledb.makedsn.return_value = "FAKE-DSN"
        mock_conn = MagicMock(name="connection")
        mock_oracledb.connect.return_value = mock_conn

        gen = get_oracle_connection(get_settings())
        next(gen)
        # Exhaust the generator — equivalent to FastAPI's post-response cleanup.
        for _ in gen:
            pass

        mock_conn.close.assert_called_once()
