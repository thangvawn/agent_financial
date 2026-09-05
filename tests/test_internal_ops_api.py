from __future__ import annotations

import sqlite3
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.app.registry.registry import get_module_by_slug, get_registered_modules
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.internal_ops.api.admin import _check_feature_flag, _repo, router as admin_ops_router
from risk_dashboard.modules.internal_ops.infrastructure.sqlite import (
    SqliteInternalOpsRepository,
    init_ops_tables,
)
from risk_dashboard.platform.feature_flags.service import FeatureFlagService


@pytest.fixture
def in_memory_repo():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    init_ops_tables(conn)

    class InMemoryFactory:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return SqliteInternalOpsRepository(conn_factory=InMemoryFactory)


@pytest.fixture
def test_client(in_memory_repo):
    app = FastAPI()
    app.include_router(admin_ops_router, prefix="/admin")

    # Mock principal
    def mock_principal() -> AuthPrincipal:
        return AuthPrincipal(
            account_id="ops-admin-1",
            session_id="sess-100",
            scopes=("admin:internal_ops:security_admin",),
            resolved_at="2026-09-05T10:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = mock_principal
    app.dependency_overrides[_repo] = lambda: in_memory_repo
    app.dependency_overrides[_check_feature_flag] = lambda: None  # bypass disabled flag for functional tests
    return TestClient(app)


def test_module_registered_in_registry():
    mod = get_module_by_slug("internal_ops")
    assert mod is not None
    assert mod.id == "internal_ops"
    assert mod.enabled_by_default is False
    assert "admin:internal_ops:investigate" in mod.permission_scopes
    assert "analytics_monitoring" in mod.dependencies

    all_mods = [m.slug for m in get_registered_modules()]
    assert "internal_ops" in all_mods


def test_api_create_investigation(test_client):
    payload = {
        "schema_version": "1.0.0",
        "investigation_type": "incident",
        "purpose": "Investigate critical API latency degradation",
        "resource_refs": [],
        "time_from": "2026-09-05T00:00:00Z",
        "time_to": "2026-09-05T10:00:00Z",
        "max_evidence_items": 100,
    }
    resp = test_client.post("/admin/internal-ops/investigations", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["schema_version"] == "1.0.0"
    assert data["status"] in ("draft", "incomplete")
    assert "investigation_id" in data
    assert data["purpose"] == payload["purpose"]


def test_api_get_investigation_and_evidence(test_client, in_memory_repo):
    # Create an investigation
    create_payload = {
        "schema_version": "1.0.0",
        "investigation_type": "data_freshness",
        "purpose": "Verify pipeline data freshness",
        "time_from": "2026-09-05T00:00:00Z",
        "time_to": "2026-09-05T10:00:00Z",
    }
    create_resp = test_client.post("/admin/internal-ops/investigations", json=create_payload)
    inv_id = create_resp.json()["investigation_id"]

    # GET investigation
    get_resp = test_client.get(f"/admin/internal-ops/investigations/{inv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["investigation_id"] == inv_id

    # GET evidence
    ev_resp = test_client.get(f"/admin/internal-ops/investigations/{inv_id}/evidence?limit=50")
    assert ev_resp.status_code == 200
    ev_data = ev_resp.json()
    assert ev_data["investigation_id"] == inv_id
    assert "items" in ev_data

    # POST recommendations
    rec_resp = test_client.post(f"/admin/internal-ops/investigations/{inv_id}/recommendations")
    assert rec_resp.status_code == 200
    recs = rec_resp.json()
    assert isinstance(recs, list)
    for r in recs:
        assert r["executable"] is False
        assert r["status"] == "draft"


def test_api_get_nonexistent_investigation_404(test_client):
    resp = test_client.get("/admin/internal-ops/investigations/nonexistent-id")
    assert resp.status_code == 404


def test_api_idor_non_owner_blocked(in_memory_repo):
    app = FastAPI()
    app.include_router(admin_ops_router, prefix="/admin")

    # 1. Create with owner user1
    def user1_principal():
        return AuthPrincipal(
            account_id="user-1",
            session_id="s1",
            scopes=("admin:internal_ops:support_viewer",),
            resolved_at="2026-09-05T10:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = user1_principal
    app.dependency_overrides[_repo] = lambda: in_memory_repo
    app.dependency_overrides[_check_feature_flag] = lambda: None

    client = TestClient(app)
    c_resp = client.post(
        "/admin/internal-ops/investigations",
        json={
            "schema_version": "1.0.0",
            "investigation_type": "incident",
            "purpose": "User 1 incident triage",
            "time_from": "2026-09-05T00:00:00Z",
            "time_to": "2026-09-05T10:00:00Z",
        },
    )
    inv_id = c_resp.json()["investigation_id"]

    # 2. Switch to user2 (support_viewer, non-owner, non-security-admin)
    def user2_principal():
        return AuthPrincipal(
            account_id="user-2",
            session_id="s2",
            scopes=("admin:internal_ops:support_viewer",),
            resolved_at="2026-09-05T10:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = user2_principal
    idor_resp = client.get(f"/admin/internal-ops/investigations/{inv_id}")
    assert idor_resp.status_code == 404  # Non-disclosing IDOR rejection


def test_api_disabled_module_returns_404(in_memory_repo):
    app = FastAPI()
    app.include_router(admin_ops_router, prefix="/admin")

    def mock_principal():
        return AuthPrincipal(
            account_id="admin",
            session_id="s",
            scopes=("admin:internal_ops:security_admin",),
            resolved_at="2026-09-05T10:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = mock_principal
    app.dependency_overrides[_repo] = lambda: in_memory_repo
    # Do NOT override _check_feature_flag -> feature flag is disabled by default!

    client = TestClient(app)
    resp = client.get("/admin/internal-ops/investigations/any-id")
    assert resp.status_code == 404
    assert "disabled" in resp.json()["detail"].lower()

