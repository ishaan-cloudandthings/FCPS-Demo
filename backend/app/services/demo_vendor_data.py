"""Canonical demo vendor data — 15 rows per DATA_MODEL.md §8.

Single source of truth for two consumers:

1. `scripts/seed_oracle.py` — uses `VENDOR_SEED_ENTRIES` (and the
   `vendor_email_for` / `seed_timestamp` helpers) to build the Oracle
   INSERT bind dicts.
2. `app/api/procurement.py` — uses `DEMO_VENDOR_ROWS` as the in-memory
   fallback when Oracle isn't reachable AND `ENVIRONMENT=dev`. See
   `docs/decision-log/demo-inmem-vendor-fallback.md`.

Keeping the data in one place means the seed script and the demo
fallback can never drift apart — if you edit a row here, both paths
see the same change.

All data is synthetic per ADR-007 / NFR-08. Emails use the `@vendor.test`
domain so they're clearly distinct from staff `@test.com` addresses.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from app.services.oracle_service import VendorRow


# ---------------------------------------------------------------------------
# Helpers shared by seed_oracle + the demo fallback
# ---------------------------------------------------------------------------


def vendor_email_for(contact_name: str) -> str:
    """`firstname.lastname@vendor.test`. Distinct from staff `@test.com`."""
    parts = contact_name.lower().split()
    return f"{parts[0]}.{parts[-1]}@vendor.test"


def _approved(year: int, month: int, day: int) -> date:
    """Convenience for entry dates."""
    return date(year, month, day)


def seed_timestamp(d: Optional[date]) -> Optional[datetime]:
    """Convert an `approved_at` date into the UTC datetime the Oracle
    column wants. `None` passes through.
    """
    if d is None:
        return None
    return datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Raw entries — 15 rows from DATA_MODEL.md §8.
#
# Schema: item_name, vendor_name, category, status, unit_price,
#         contact_name, approved_at (Optional[date]).
# `item_id`, `contact_email`, `created_date`, `updated_date` are derived.
# ---------------------------------------------------------------------------

VENDOR_SEED_ENTRIES: list[dict[str, object]] = [
    # --- 5 APPROVED -----------------------------------------------------
    {
        "item_name": "Classroom laptops (15-pack)",
        "vendor_name": "Northstar Computing",
        "category": "Technology",
        "status": "APPROVED",
        "unit_price": 8499.00,
        "contact_name": "Alice Reyes",
        "approved_at": _approved(2026, 1, 12),
    },
    {
        "item_name": "HVAC quarterly service",
        "vendor_name": "MetroAir Facilities",
        "category": "Facilities",
        "status": "APPROVED",
        "unit_price": 2250.00,
        "contact_name": "Benjamin Park",
        "approved_at": _approved(2026, 1, 22),
    },
    {
        "item_name": "A4 copier paper, 50 cases",
        "vendor_name": "Statewide Office Supply",
        "category": "Supplies",
        "status": "APPROVED",
        "unit_price": 1199.50,
        "contact_name": "Cora Williams",
        "approved_at": _approved(2026, 2, 3),
    },
    {
        "item_name": "On-site IT support contract",
        "vendor_name": "BlueRidge IT Services",
        "category": "Services",
        "status": "APPROVED",
        "unit_price": 14500.00,
        "contact_name": "Devon Chen",
        "approved_at": _approved(2026, 2, 14),
    },
    {
        "item_name": "Library reading tables (8)",
        "vendor_name": "Heritage Furniture Co.",
        "category": "Furniture",
        "status": "APPROVED",
        "unit_price": 4200.00,
        "contact_name": "Elena Rossi",
        "approved_at": _approved(2026, 3, 4),
    },
    # --- 4 PENDING ------------------------------------------------------
    {
        "item_name": "Interactive whiteboards (5)",
        "vendor_name": "Northstar Computing",
        "category": "Technology",
        "status": "PENDING",
        "unit_price": 3199.00,
        "contact_name": "Alice Reyes",
        "approved_at": None,
    },
    {
        "item_name": "Cafeteria fridge replacement",
        "vendor_name": "MetroAir Facilities",
        "category": "Facilities",
        "status": "PENDING",
        "unit_price": 5475.00,
        "contact_name": "Benjamin Park",
        "approved_at": None,
    },
    {
        "item_name": "Cleaning supplies, annual",
        "vendor_name": "Statewide Office Supply",
        "category": "Supplies",
        "status": "PENDING",
        "unit_price": 8200.00,
        "contact_name": "Cora Williams",
        "approved_at": None,
    },
    {
        "item_name": "Network security audit",
        "vendor_name": "BlueRidge IT Services",
        "category": "Services",
        "status": "PENDING",
        "unit_price": 6800.00,
        "contact_name": "Devon Chen",
        "approved_at": None,
    },
    # --- 3 UNDER_REVIEW -------------------------------------------------
    {
        "item_name": "Science-lab stools (40)",
        "vendor_name": "Heritage Furniture Co.",
        "category": "Furniture",
        "status": "UNDER_REVIEW",
        "unit_price": 2200.00,
        "contact_name": "Elena Rossi",
        "approved_at": None,
    },
    {
        "item_name": "Cafeteria food-service supplies",
        "vendor_name": "GreenLeaf Food Distributors",
        "category": "Supplies",
        "status": "UNDER_REVIEW",
        "unit_price": 12300.00,
        "contact_name": "Farhan Ahmed",
        "approved_at": None,
    },
    {
        "item_name": "District-wide tablet refresh",
        "vendor_name": "Northstar Computing",
        "category": "Technology",
        "status": "UNDER_REVIEW",
        "unit_price": 42600.00,
        "contact_name": "Alice Reyes",
        "approved_at": None,
    },
    # --- 3 REJECTED -----------------------------------------------------
    {
        "item_name": "Outdated software licences",
        "vendor_name": "Legacy Systems LLC",
        "category": "Technology",
        "status": "REJECTED",
        "unit_price": 995.00,
        "contact_name": "Grace Tan",
        "approved_at": None,
    },
    {
        "item_name": "Parking-lot resealing (unverified vendor)",
        "vendor_name": "QuickFix Asphalt",
        "category": "Facilities",
        "status": "REJECTED",
        "unit_price": 7800.00,
        "contact_name": "Hugo Martinez",
        "approved_at": None,
    },
    {
        "item_name": "Bulk binder order (overcosted)",
        "vendor_name": "Statewide Office Supply",
        "category": "Supplies",
        "status": "REJECTED",
        "unit_price": 4500.00,
        "contact_name": "Cora Williams",
        "approved_at": None,
    },
]


# ---------------------------------------------------------------------------
# Derived: VendorRow instances for the in-memory fallback
# ---------------------------------------------------------------------------

# Synthetic timestamps so the detail page renders Created/Updated lines.
_BASE_DT = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)


def _vendor_row_for(item_id: int, entry: dict) -> VendorRow:
    return VendorRow(
        variant_tag="admin",
        item_id=item_id,
        vendor_name=entry["vendor_name"],
        item_name=entry["item_name"],
        category=entry["category"],
        status=entry["status"],
        unit_price=entry["unit_price"],
        contact_name=entry["contact_name"],
        contact_email=vendor_email_for(entry["contact_name"]),
        approved_at=entry["approved_at"],
        created_date=_BASE_DT,
        updated_date=_BASE_DT,
    )


# item_id 1..15, ordered the same way as the Oracle IDENTITY assignment.
DEMO_VENDOR_ROWS: list[VendorRow] = [
    _vendor_row_for(i + 1, entry) for i, entry in enumerate(VENDOR_SEED_ENTRIES)
]


def get_demo_vendor_by_id(item_id: int) -> Optional[VendorRow]:
    """Mirror of `oracle_service.get_vendor_by_id` for the demo fallback.

    Returns a `VendorRow` with `variant_tag="admin_detail"` so it serialises
    cleanly into `VendorDetail`. None when not found.
    """
    for row in DEMO_VENDOR_ROWS:
        if row.item_id == item_id:
            # Re-tag for detail variant; the row is otherwise identical.
            return VendorRow(
                variant_tag="admin_detail",
                item_id=row.item_id,
                vendor_name=row.vendor_name,
                item_name=row.item_name,
                category=row.category,
                status=row.status,
                unit_price=row.unit_price,
                contact_name=row.contact_name,
                contact_email=row.contact_email,
                approved_at=row.approved_at,
                created_date=row.created_date,
                updated_date=row.updated_date,
            )
    return None
