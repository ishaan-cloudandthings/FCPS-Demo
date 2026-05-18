"""Tests for `app.api.procurement` — AC-18.

Maps to ratified decisions in `docs/decision-log/AC-18-procurement-router.md`:

* AC18-D2 — both endpoints require auth only (no RBAC today).
* AC18-D3, D4, D5 — response shape.
* AC18-D7 — 503 on OracleUnavailable, 404 on missing detail.
"""
from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import require_authenticated
from app.auth.jwt_session import SessionClaims
from app.core.database import get_oracle_connection
from app.services.oracle_service import OracleUnavailable, VendorRow


@pytest.fixture
def fake_connection():
    """A throwaway sentinel — the procurement handlers don't introspect
    the connection beyond passing it to `list_vendors` / `get_vendor_by_id`,
    which we patch.
    """
    return MagicMock(name="oracle_connection")


@pytest.fixture
def authed_client(fake_connection, monkeypatch):
    """TestClient where `require_authenticated` and `get_oracle_connection`
    are both overridden.
    """
    from main import app

    app.dependency_overrides[require_authenticated] = lambda: SessionClaims(
        staff_id=1, role="ADMIN", procurement_level=3
    )
    app.dependency_overrides[get_oracle_connection] = lambda: fake_connection
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client():
    from main import app
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# GET /api/vendors — list
# ---------------------------------------------------------------------------


def test_list_endpoint_returns_admin_variant_rows(authed_client, monkeypatch):
    rows = [
        VendorRow(
            variant_tag="admin",
            item_id=1,
            vendor_name="Acme",
            item_name="Widget",
            category="Supplies",
            status="APPROVED",
            unit_price=9.99,
            contact_name="Alice",
        ),
        VendorRow(
            variant_tag="admin",
            item_id=2,
            vendor_name="Globex",
            item_name="Gadget",
            category="Technology",
            status="PENDING",
            unit_price=None,
            contact_name=None,
        ),
    ]
    monkeypatch.setattr("app.api.procurement.list_vendors", lambda *_a, **_kw: rows)

    response = authed_client.get("/api/vendors")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0] == {
        "variant": "admin",
        "item_id": 1,
        "vendor_name": "Acme",
        "item_name": "Widget",
        "category": "Supplies",
        "contact_name": "Alice",
        "status": "APPROVED",
        "unit_price": 9.99,
    }
    assert body[1]["status"] == "PENDING"
    assert body[1]["contact_name"] is None


def test_list_endpoint_passes_full_admin_params_to_list_vendors(
    authed_client, monkeypatch
):
    """AC18-D4 — handler should pass everyone-sees-everything params
    until AC-17 wires rbac_service.
    """
    captured = {}

    def fake_list_vendors(connection, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr("app.api.procurement.list_vendors", fake_list_vendors)
    authed_client.get("/api/vendors")

    assert captured == {
        "only_approved": False,
        "include_contact": True,
        "include_status": True,
        "variant_tag": "admin",
    }


def test_list_endpoint_503_on_oracle_unavailable(authed_client, monkeypatch):
    def boom(*_a, **_kw):
        raise OracleUnavailable("simulated")

    monkeypatch.setattr("app.api.procurement.list_vendors", boom)

    response = authed_client.get("/api/vendors")
    assert response.status_code == 503
    assert response.json() == {
        "detail": "Service temporarily unavailable. Please try again shortly."
    }


def test_list_endpoint_requires_authentication(unauthed_client):
    response = unauthed_client.get("/api/vendors")
    assert response.status_code == 401
    assert response.json() == {"detail": "Session invalid or expired."}


# ---------------------------------------------------------------------------
# GET /api/vendors/{id} — detail
# ---------------------------------------------------------------------------


def _detail_row(item_id: int = 7) -> VendorRow:
    return VendorRow(
        variant_tag="admin_detail",
        item_id=item_id,
        vendor_name="Acme",
        item_name="Widget",
        category="Supplies",
        status="APPROVED",
        unit_price=9.99,
        contact_name="Alice Vendor",
        contact_email="alice@vendor.test",
        approved_at=date(2026, 2, 14),
        created_date=datetime(2026, 1, 1, 9, 0, 0),
        updated_date=datetime(2026, 2, 14, 10, 30, 0),
    )


def test_detail_endpoint_returns_full_record(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.procurement.get_vendor_by_id",
        lambda _conn, _id: _detail_row(7),
    )

    response = authed_client.get("/api/vendors/7")

    assert response.status_code == 200
    body = response.json()
    assert body["variant"] == "admin_detail"
    assert body["item_id"] == 7
    assert body["contact_email"] == "alice@vendor.test"
    assert body["approved_at"] == "2026-02-14"


def test_detail_endpoint_404_when_missing(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.procurement.get_vendor_by_id", lambda _conn, _id: None
    )

    response = authed_client.get("/api/vendors/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Vendor not found."}


def test_detail_endpoint_503_on_oracle_unavailable(authed_client, monkeypatch):
    def boom(*_a, **_kw):
        raise OracleUnavailable("simulated")

    monkeypatch.setattr("app.api.procurement.get_vendor_by_id", boom)

    response = authed_client.get("/api/vendors/1")
    assert response.status_code == 503


def test_detail_endpoint_requires_authentication(unauthed_client):
    response = unauthed_client.get("/api/vendors/1")
    assert response.status_code == 401
