"""
🟢 GREEN ZONE — Oracle connection factory.

Ratified decisions:
    docs/decision-log/AC-11-oracle-staff-lookup.md (AC11-D2, AC11-D4)
    docs/decision-log/demo-inmem-vendor-fallback.md (DEMO-VENDOR-1)

Thin-mode `oracledb` only — per NFR-17, no Oracle Client installation is
permitted on dev or demo machines. **Never call `oracledb.init_oracle_client()`**.

Lifecycle (AC11-D2): per-request `oracledb.connect()` via the
`get_oracle_connection` FastAPI dependency, which yields the connection
and closes it after the response. No connection pool for the demo.

Dev fallback (DEMO-VENDOR-1): when `ENVIRONMENT=dev` and Oracle is not
reachable at connect time, the dependency yields **None** instead of
raising. Handlers that opt into the demo fallback (e.g. the procurement
router) detect `None` and serve in-memory demo data. Outside dev, the
connect failure is wrapped as `OracleUnavailable` so handlers can return
503.
"""
from __future__ import annotations

from typing import Iterator, Optional

import oracledb
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.oracle_service import OracleUnavailable
from app.utils.logging import get_logger

logger = get_logger(__name__)


def get_oracle_connection(
    settings: Settings = Depends(get_settings),
) -> Iterator[Optional[oracledb.Connection]]:
    """FastAPI dependency. Opens a thin-mode connection and closes it
    after the request finishes (including on exception).

    Yields `None` in dev mode when Oracle is unreachable so handlers
    can fall back to in-memory demo data. Raises `OracleUnavailable`
    in non-dev environments — the procurement router maps that to 503.
    """
    dsn = oracledb.makedsn(
        host=settings.oracle_host,
        port=settings.oracle_port,
        service_name=settings.oracle_service_name,
    )
    try:
        conn = oracledb.connect(
            user=settings.oracle_user,
            password=settings.oracle_password,
            dsn=dsn,
        )
    except oracledb.DatabaseError as exc:
        if settings.environment == "dev":
            logger.warning(
                "DEMO_FALLBACK: Oracle unreachable at boot (%s) — "
                "handlers will serve in-memory demo data.",
                type(exc).__name__,
            )
            yield None
            return
        raise OracleUnavailable("oracle is unreachable") from exc

    try:
        yield conn
    finally:
        conn.close()
