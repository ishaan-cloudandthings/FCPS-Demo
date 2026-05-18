"""Pydantic schemas for vendor list + detail responses.

Maps to the api-spec.yaml `VendorListItemL1`, `VendorListItemL2`,
`VendorListItemAdmin`, `VendorDetail` schemas, plus the `VendorStatus`
enum.

Why four schemas (AC-15 decision log):

The `variant` discriminator lets the API tag each row with the shape it
fits. The frontend reads the discriminator and renders accordingly. AC-17
will use this to narrow the response per role; until then, the procurement
router always emits `"admin"` list rows (everyone sees everything).

PII discipline (per ADR-013):
* `contact_email` lives only on `VendorDetail` — list schemas never carry
  it.
* `bank_details` is fully out of scope (ADR-012); never appears anywhere.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


VendorStatus = Literal["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED"]


class VendorListItemL1(BaseModel):
    """List item visible to `STAFF` / `PROCUREMENT_LEVEL = 1`.

    Per FUNCTIONAL_DESIGN.md §6.7 + api-spec.yaml: vendor name, item,
    category only. Status and contact are hidden at this level.
    """

    model_config = ConfigDict(extra="forbid")

    variant: Literal["staff_l1"] = "staff_l1"
    item_id: int
    vendor_name: str
    item_name: str
    category: str


class VendorListItemL2(BaseModel):
    """List item visible to `STAFF` / `PROCUREMENT_LEVEL = 2`.

    Adds `contact_name` to the L1 shape. `contact_email` is NOT here —
    that's detail-only per ADR-013.
    """

    model_config = ConfigDict(extra="forbid")

    variant: Literal["staff_l2"] = "staff_l2"
    item_id: int
    vendor_name: str
    item_name: str
    category: str
    contact_name: Optional[str] = None


class VendorListItemAdmin(BaseModel):
    """List item visible to `ADMIN` / `PROCUREMENT_LEVEL = 3`.

    Adds `status` and `unit_price` to the L2 shape. Still no
    `contact_email` (detail-only) and never `bank_details` (ADR-012).
    """

    model_config = ConfigDict(extra="forbid")

    variant: Literal["admin"] = "admin"
    item_id: int
    vendor_name: str
    item_name: str
    category: str
    contact_name: Optional[str] = None
    status: VendorStatus
    unit_price: Optional[float] = None


class VendorDetail(BaseModel):
    """Full vendor record returned by `GET /api/vendors/{id}`.

    The ONLY schema in the API that returns `contact_email` (ADR-013).
    `bank_details` is not here and not anywhere (ADR-012).
    """

    model_config = ConfigDict(extra="forbid")

    variant: Literal["admin_detail"] = "admin_detail"
    item_id: int
    vendor_name: str
    item_name: str
    category: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    status: VendorStatus
    unit_price: Optional[float] = None
    approved_at: Optional[date] = None
    created_date: datetime
    updated_date: datetime
