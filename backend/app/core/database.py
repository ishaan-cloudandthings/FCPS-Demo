"""
🟢 GREEN ZONE — Oracle connection factory.

Ratified decisions: docs/decision-log/AC-11-oracle-staff-lookup.md
(AC11-D2, AC11-D4).

Thin-mode `oracledb` only — per NFR-17, no Oracle Client installation is
permitted on dev or demo machines. **Never call `oracledb.init_oracle_client()`**.
If you find yourself reaching for it, you are not solving a problem this
codebase wants solved.

Lifecycle (AC11-D2): per-request `oracledb.connect()` via the
`get_oracle_connection` FastAPI dependency, which yields the connection
and closes it after the response. No connection pool for the demo — the
single-worker uvicorn assumption (AC6-D2) makes a pool overkill. Phase 2
revisits this if multi-worker lands.
"""
from __future__ import annotations

from typing import Iterator

import oracledb
from fastapi import Depends

from app.core.config import Settings, get_settings


def get_oracle_connection(
    settings: Settings = Depends(get_settings),
) -> Iterator[oracledb.Connection]:
    """FastAPI dependency. Opens a thin-mode connection and closes it
    after the request finishes (including on exception).

    Yields rather than returns so FastAPI handles the close in the
    request lifecycle.
    """
    dsn = oracledb.makedsn(
        host=settings.oracle_host,
        port=settings.oracle_port,
        service_name=settings.oracle_service_name,
    )
    conn = oracledb.connect(
        user=settings.oracle_user,
        password=settings.oracle_password,
        dsn=dsn,
    )
    try:
        yield conn
    finally:
        conn.close()
