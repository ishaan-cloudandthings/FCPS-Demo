"""
🟡 YELLOW ZONE — procurement router.

Ratified decisions: docs/decision-log/AC-18-procurement-router.md.

Endpoints:

    GET /api/vendors          → 200 [VendorListItemAdmin]
    GET /api/vendors/{id}     → 200 VendorDetail
                                404 if not found

Both endpoints require **authentication only** today. RBAC (per-level
filtering, admin-only detail) is intentionally deferred to AC-17 — the
single point of change in this file will be:

* import `rbac_service`
* replace the hardcoded `params_for_admin()` call with
  `rbac_service.params_for(claims.role, claims.procurement_level)`
* optionally add `Depends(require_role("ADMIN"))` to the detail handler

See `# TODO(AC-17)` markers below.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import _DETAIL_SERVICE_UNAVAILABLE
from app.auth.dependencies import require_authenticated
from app.auth.jwt_session import SessionClaims
from app.core.database import get_oracle_connection
from app.schemas.vendors import VendorDetail, VendorListItemAdmin
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
    `rbac_service.params_for(claims.role, claims.procurement_level)`.
    Until then, every authenticated caller gets the full admin shape.
    """
    return dict(
        only_approved=False,
        include_contact=True,
        include_status=True,
        variant_tag="admin",
    )


def _vendor_row_to_admin_list_item(row: VendorRow) -> VendorListItemAdmin:
    # By construction the variant_tag is "admin" — see _params_for_admin().
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


@router.get(
    "",
    response_model=list[VendorListItemAdmin],
    status_code=status.HTTP_200_OK,
)
def list_vendors_endpoint(
    claims: SessionClaims = Depends(require_authenticated),  # noqa: ARG001 — TODO(AC-17)
    connection=Depends(get_oracle_connection),
) -> list[VendorListItemAdmin]:
    """List vendors. AC-18 returns the full admin shape to every
    authenticated caller. AC-17 will narrow the response per claims.
    """
    # TODO(AC-17): swap to `rbac_service.params_for(claims.role, claims.procurement_level)`.
    params = _params_for_admin()

    try:
        rows = list_vendors(connection, **params)
    except OracleUnavailable:
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
    connection=Depends(get_oracle_connection),
) -> VendorDetail:
    """Vendor detail. AC-18 allows every authenticated caller. AC-17 will
    additionally require ADMIN via `Depends(require_role("ADMIN"))`.
    """
    try:
        row = get_vendor_by_id(connection, item_id)
    except OracleUnavailable:
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
