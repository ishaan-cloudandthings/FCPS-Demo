"""
🟡 YELLOW ZONE — procurement router.

Ratified decisions:
    docs/decision-log/AC-18-procurement-router.md
    docs/decision-log/demo-inmem-vendor-fallback.md (DEMO-VENDOR-*)

Endpoints:

    GET /api/vendors          → 200 [VendorListItemAdmin]
    GET /api/vendors/{id}     → 200 VendorDetail
                                404 if not found

Both endpoints require **authentication only** today. RBAC (per-level
filtering, admin-only detail) is intentionally deferred to AC-17 — the
single point of change in this file will be:

* import `rbac_service`
* replace the hardcoded `_params_for_admin()` call with
  `rbac_service.params_for(claims.role)` (post-ADR-015)
* optionally add `Depends(require_role("PROCUREMENT_SUPERVISOR"))` to the detail handler

See `# TODO(AC-17)` markers below.

Dev fallback (DEMO-VENDOR-*): when `ENVIRONMENT=dev` and Oracle is not
reachable, both endpoints serve in-memory data from
`app.services.demo_vendor_data`. The fallback is silently skipped in
non-dev environments — those return 503 as before.
"""
from __future__ import annotations

from typing import Optional

import oracledb
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import _DETAIL_SERVICE_UNAVAILABLE
from app.auth.dependencies import require_authenticated
from app.auth.jwt_session import SessionClaims
from app.core.config import Settings, get_settings
from app.core.database import get_oracle_connection
from app.schemas.vendors import VendorDetail, VendorListItemAdmin
from app.services.demo_vendor_data import (
    DEMO_VENDOR_ROWS,
    get_demo_vendor_by_id,
)
from app.services.oracle_service import (
    OracleUnavailable,
    VendorRow,
    get_vendor_by_id,
    list_vendors,
)
from app.utils.logging import get_logger

router = APIRouter(prefix="/api/vendors", tags=["vendors"])
logger = get_logger(__name__)


_DETAIL_NOT_FOUND = "Vendor not found."


def _params_for_admin() -> dict:
    """Hardcoded "everyone sees everything" params (AC-18 today).

    TODO(AC-17): replace this with
    `rbac_service.params_for(claims.role)` (post-ADR-015).
    Until then, every authenticated caller gets the full admin shape.
    """
    return dict(
        only_approved=False,
        include_contact=True,
        include_status=True,
        variant_tag="admin",
    )


def _vendor_row_to_admin_list_item(row: VendorRow) -> VendorListItemAdmin:
    return VendorListItemAdmin(
        item_id=row.item_id,
        vendor_name=row.vendor_name,
        item_name=row.item_name,
        category=row.category,
        contact_name=row.contact_name,
        status=row.status,                                   # type: ignore[arg-type]
        unit_price=row.unit_price,
    )


def _vendor_row_to_detail(row: VendorRow) -> VendorDetail:
    return VendorDetail(
        item_id=row.item_id,
        vendor_name=row.vendor_name,
        item_name=row.item_name,
        category=row.category,
        contact_name=row.contact_name,
        contact_email=row.contact_email,
        status=row.status,                                   # type: ignore[arg-type]
        unit_price=row.unit_price,
        approved_at=row.approved_at,
        created_date=row.created_date,                       # type: ignore[arg-type]
        updated_date=row.updated_date,                       # type: ignore[arg-type]
    )


def _is_dev(settings: Settings) -> bool:
    return settings.environment == "dev"


@router.get(
    "",
    response_model=list[VendorListItemAdmin],
    status_code=status.HTTP_200_OK,
)
def list_vendors_endpoint(
    claims: SessionClaims = Depends(require_authenticated),  # noqa: ARG001 — TODO(AC-17)
    connection: Optional[oracledb.Connection] = Depends(get_oracle_connection),
    settings: Settings = Depends(get_settings),
) -> list[VendorListItemAdmin]:
    """List vendors. Today returns the admin shape to every authenticated
    caller. AC-17 will narrow the response per claims.

    In dev: if Oracle is unreachable (connection is None, or
    OracleUnavailable raised during query), serve in-memory demo data.
    """
    # TODO(AC-17): swap to `rbac_service.params_for(claims.role)` (post-ADR-015).
    params = _params_for_admin()

    if connection is None:
        # Dev-mode fallback: connection failed at boot, demo data served instead.
        rows = DEMO_VENDOR_ROWS
        logger.info(
            "procurement.list count=%d DEMO_FALLBACK source=no_connection",
            len(rows),
        )
        return [_vendor_row_to_admin_list_item(r) for r in rows]

    try:
        rows = list_vendors(connection, **params)
    except OracleUnavailable:
        if _is_dev(settings):
            rows = DEMO_VENDOR_ROWS
            logger.info(
                "procurement.list count=%d DEMO_FALLBACK source=query_failed",
                len(rows),
            )
            return [_vendor_row_to_admin_list_item(r) for r in rows]
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_DETAIL_SERVICE_UNAVAILABLE,
        )

    logger.info("procurement.list count=%d", len(rows))
    return [_vendor_row_to_admin_list_item(r) for r in rows]


@router.get(
    "/{item_id}",
    response_model=VendorDetail,
    status_code=status.HTTP_200_OK,
)
def get_vendor_endpoint(
    item_id: int,
    claims: SessionClaims = Depends(require_authenticated),  # noqa: ARG001 — TODO(AC-17)
    connection: Optional[oracledb.Connection] = Depends(get_oracle_connection),
    settings: Settings = Depends(get_settings),
) -> VendorDetail:
    """Vendor detail. AC-18 allows every authenticated caller. AC-17 will
    additionally require PROCUREMENT_SUPERVISOR via `Depends(require_role("PROCUREMENT_SUPERVISOR"))`.

    Dev fallback: if Oracle is unreachable, look up in the in-memory
    demo set.
    """
    if connection is None:
        row = get_demo_vendor_by_id(item_id)
        if row is None:
            logger.info(
                "procurement.detail item_id=%d outcome=not_found DEMO_FALLBACK",
                item_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_DETAIL_NOT_FOUND,
            )
        logger.info(
            "procurement.detail item_id=%d outcome=found DEMO_FALLBACK",
            item_id,
        )
        return _vendor_row_to_detail(row)

    try:
        row = get_vendor_by_id(connection, item_id)
    except OracleUnavailable:
        if _is_dev(settings):
            row = get_demo_vendor_by_id(item_id)
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=_DETAIL_NOT_FOUND,
                )
            logger.info(
                "procurement.detail item_id=%d outcome=found DEMO_FALLBACK",
                item_id,
            )
            return _vendor_row_to_detail(row)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_DETAIL_SERVICE_UNAVAILABLE,
        )

    if row is None:
        logger.info("procurement.detail item_id=%d outcome=not_found", item_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETAIL_NOT_FOUND,
        )

    logger.info("procurement.detail item_id=%d outcome=found", item_id)
    return _vendor_row_to_detail(row)
