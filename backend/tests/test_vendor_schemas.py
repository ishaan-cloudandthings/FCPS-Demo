"""Tests for `app.schemas.vendors` — AC-15.

Covers AC15-D2 (discriminator), AC15-D3 (extra=forbid), AC15-D4
(nullable fields), AC15-D5 (status enum).
"""
from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.vendors import (
    VendorDetail,
    VendorListItemAdmin,
    VendorListItemL1,
    VendorListItemL2,
)


# ---------------------------------------------------------------------------
# Minimum-required payloads parse cleanly (AC15-D2 default + AC15-D4 nullables)
# ---------------------------------------------------------------------------


def test_l1_minimum_payload_parses():
    item = VendorListItemL1(
        item_id=1, vendor_name="Acme", item_name="Widget", category="Supplies"
    )
    assert item.variant == "staff_l1"


def test_l2_minimum_payload_parses_with_null_contact_name():
    item = VendorListItemL2(
        item_id=1, vendor_name="Acme", item_name="Widget", category="Supplies"
    )
    assert item.variant == "staff_l2"
    assert item.contact_name is None


def test_admin_minimum_payload_parses():
    item = VendorListItemAdmin(
        item_id=1,
        vendor_name="Acme",
        item_name="Widget",
        category="Supplies",
        status="APPROVED",
    )
    assert item.variant == "admin"
    assert item.unit_price is None


def test_detail_minimum_payload_parses():
    detail = VendorDetail(
        item_id=1,
        vendor_name="Acme",
        item_name="Widget",
        category="Supplies",
        status="APPROVED",
        created_date=datetime(2026, 1, 1, 9, 0, 0),
        updated_date=datetime(2026, 1, 5, 9, 0, 0),
    )
    assert detail.variant == "admin_detail"
    assert detail.contact_email is None
    assert detail.approved_at is None


# ---------------------------------------------------------------------------
# extra=forbid (AC15-D3) — every schema rejects unknown fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "schema_cls,base",
    [
        (
            VendorListItemL1,
            dict(item_id=1, vendor_name="A", item_name="B", category="C"),
        ),
        (
            VendorListItemL2,
            dict(item_id=1, vendor_name="A", item_name="B", category="C"),
        ),
        (
            VendorListItemAdmin,
            dict(item_id=1, vendor_name="A", item_name="B", category="C", status="APPROVED"),
        ),
        (
            VendorDetail,
            dict(
                item_id=1,
                vendor_name="A",
                item_name="B",
                category="C",
                status="APPROVED",
                created_date=datetime(2026, 1, 1),
                updated_date=datetime(2026, 1, 5),
            ),
        ),
    ],
)
def test_extra_field_rejected(schema_cls, base):
    with pytest.raises(ValidationError):
        schema_cls(**base, bank_details="LEAK")


# ---------------------------------------------------------------------------
# Variant discriminator (AC15-D2)
# ---------------------------------------------------------------------------


def test_wrong_variant_literal_rejected():
    """The default is the right literal — passing the wrong one explicitly fails."""
    with pytest.raises(ValidationError):
        VendorListItemL1(
            item_id=1,
            vendor_name="A",
            item_name="B",
            category="C",
            variant="admin",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Status enum (AC15-D5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", ["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED"])
def test_admin_accepts_each_status(status):
    item = VendorListItemAdmin(
        item_id=1, vendor_name="A", item_name="B", category="C", status=status
    )
    assert item.status == status


def test_unknown_status_rejected():
    with pytest.raises(ValidationError):
        VendorListItemAdmin(
            item_id=1, vendor_name="A", item_name="B", category="C", status="DRAFT"
        )


# ---------------------------------------------------------------------------
# contact_email is detail-only (ADR-013)
# ---------------------------------------------------------------------------


def test_list_schemas_have_no_contact_email_field():
    for cls in (VendorListItemL1, VendorListItemL2, VendorListItemAdmin):
        assert "contact_email" not in cls.model_fields, (
            f"ADR-013 violation: {cls.__name__} has contact_email"
        )


def test_detail_carries_contact_email_and_approved_at():
    detail = VendorDetail(
        item_id=1,
        vendor_name="A",
        item_name="B",
        category="C",
        status="APPROVED",
        contact_email="alice@example.test",
        approved_at=date(2026, 2, 14),
        created_date=datetime(2026, 1, 1),
        updated_date=datetime(2026, 2, 14),
    )
    assert detail.contact_email == "alice@example.test"
    assert detail.approved_at == date(2026, 2, 14)


# ---------------------------------------------------------------------------
# Anti-leak: bank_details must never be addable (ADR-012)
# ---------------------------------------------------------------------------


def test_no_schema_accepts_bank_details():
    base_l1 = dict(item_id=1, vendor_name="A", item_name="B", category="C")
    base_admin = {**base_l1, "status": "APPROVED"}

    for cls, kwargs in (
        (VendorListItemL1, base_l1),
        (VendorListItemL2, base_l1),
        (VendorListItemAdmin, base_admin),
        (
            VendorDetail,
            {
                **base_admin,
                "created_date": datetime(2026, 1, 1),
                "updated_date": datetime(2026, 1, 1),
            },
        ),
    ):
        with pytest.raises(ValidationError):
            cls(**kwargs, bank_details="XXX")
        assert "bank_details" not in cls.model_fields
