"""Tests for legacy_gate REST API and module registration."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.app.registry.registry import get_module_by_slug
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.legacy_gate.api.public import (
    _check_feature_enabled,
    router as legacy_gate_router,
    set_service_for_testing,
)
from risk_dashboard.modules.legacy_gate.application.service import LegacyGateService
from risk_dashboard.modules.legacy_gate.infrastructure.in_memory import InMemoryGateRepository


@pytest.fixture
def clean_repo():
    repo = InMemoryGateRepository()
    service = LegacyGateService(repository=repo)
    set_service_for_testing(service)
    yield repo
    set_service_for_testing(None)


@pytest.fixture
def current_principal():
    return {
        "principal": AuthPrincipal(
            account_id="account-gate-admin",
            session_id="sess-gate-001",
            scopes=("public:legacy_gate:read",),
            resolved_at="2026-09-05T10:00:00Z",
        )
    }


@pytest.fixture
def test_app(current_principal, clean_repo):
    app = FastAPI(title="Legacy Gate Test App")
    app.include_router(legacy_gate_router)

    def _mock_resolve_principal() -> AuthPrincipal:
        return current_principal["principal"]

    app.dependency_overrides[resolve_principal] = _mock_resolve_principal
    return app


@pytest.fixture
def client(test_app):
    test_app.dependency_overrides[_check_feature_enabled] = lambda: None
    return TestClient(test_app)


class TestLegacyGateAPI:
    def test_module_registered_in_app_registry(self) -> None:
        import risk_dashboard.app.registry.registry as reg

        reg._MODULE_BY_SLUG = None  # force refresh index
        mod = get_module_by_slug("legacy_gate")
        assert mod is not None
        assert mod.id == "legacy_gate"
        assert mod.slug == "legacy_gate"
        assert mod.enabled_by_default is True
        assert "public:legacy_gate:read" in mod.permission_scopes
        assert "module.legacy_gate.enabled" in mod.feature_flags

    def test_get_modules_success(self, client: TestClient) -> None:
        resp = client.get("/api/legacy-gates/modules")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        slugs = [m["module_slug"] for m in data["modules"]]
        assert slugs == ["goals", "financial_health", "community", "guided_investing"]

    def test_get_module_by_slug_success(self, client: TestClient) -> None:
        resp = client.get("/api/legacy-gates/modules/goals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module_slug"] == "goals"
        assert data["total_gates"] == 14
        assert len(data["gates"]) == 14
        assert data["overall_status"] in {"hold", "gates_documented"}

    def test_get_module_by_invalid_slug_404(self, client: TestClient) -> None:
        resp = client.get("/api/legacy-gates/modules/non_existent")
        assert resp.status_code == 404
        assert "not one of the recognized legacy modules" in resp.json()["detail"]

    def test_get_baseline_report_success(self, client: TestClient) -> None:
        resp = client.get("/api/legacy-gates/modules/financial_health/baseline")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module_slug"] == "financial_health"
        assert data["tests_count"] > 0
        assert len(data["identity_debt_notes"]) >= 1

    def test_post_evaluate_success(self, client: TestClient) -> None:
        resp = client.post("/api/legacy-gates/modules/community/evaluate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module_slug"] == "community"
        assert data["total_gates"] == 12

    def test_post_decisions_success(self, client: TestClient) -> None:
        payload = {
            "outcome": "Allow goal-based learning path",
            "owner_product": "alice",
            "owner_engineering": "bob",
            "owner_domain": "carol",
            "owner_compliance": "dave",
            "source_of_truth": "goals service",
            "risk_class": "low",
            "allowed_actions": ["read", "proposal"],
            "dependencies": ["auth"],
            "eval_criteria": "baseline passes 100%",
            "rollout": "feature flag cohort",
            "adr_reference": "ADR-012",
            "status": "draft",
        }
        resp = client.post("/api/legacy-gates/modules/goals/decisions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["record_id"].startswith("rec-")
        assert data["module_slug"] == "goals"
        assert data["status"] == "draft"

    def test_post_decisions_approved_blocked_when_gates_pending_400(self, client: TestClient) -> None:
        payload = {
            "outcome": "Premature approval attempt", "owner_product": "alice",
            "owner_engineering": "bob", "owner_domain": "carol", "owner_compliance": "dave",
            "source_of_truth": "goals service", "risk_class": "low", "allowed_actions": ["read"],
            "dependencies": [], "eval_criteria": "eval criteria", "rollout": "rollout plan",
            "adr_reference": "ADR-012", "status": "approved",
        }
        resp = client.post("/api/legacy-gates/modules/goals/decisions", json=payload)
        assert resp.status_code == 400
        assert "gates must pass first" in resp.json()["detail"]

    def test_auth_required_unauthenticated_401(self, test_app: FastAPI, current_principal: dict) -> None:
        # Override principal with unauthenticated / anonymous principal
        current_principal["principal"] = AuthPrincipal(
            account_id="anon-user",
            session_id="anon-001",
            assurance="anonymous",
            scopes=(),
            is_anonymous=True,
            resolved_at="2026-09-05T10:00:00Z",
        )
        test_app.dependency_overrides[_check_feature_enabled] = lambda: None
        raw_client = TestClient(test_app)

        resp = raw_client.get("/api/legacy-gates/modules")
        assert resp.status_code == 401
        assert "Authentication required" in resp.json()["detail"]

    def test_scope_check_missing_scope_403(self, test_app: FastAPI, current_principal: dict) -> None:
        # Authenticated principal but missing public:legacy_gate:read scope
        current_principal["principal"] = AuthPrincipal(
            account_id="account-regular-user",
            session_id="sess-002",
            assurance="session",
            scopes=("public:learning:read",),  # missing public:legacy_gate:read
            is_anonymous=False,
            resolved_at="2026-09-05T10:00:00Z",
        )
        test_app.dependency_overrides[_check_feature_enabled] = lambda: None
        raw_client = TestClient(test_app)

        resp = raw_client.get("/api/legacy-gates/modules")
        assert resp.status_code == 403
        assert "Permission denied" in resp.json()["detail"]

    def test_feature_flag_disabled_404(self, test_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
        # Remove bypass override to test live feature flag
        test_app.dependency_overrides.pop(_check_feature_enabled, None)
        monkeypatch.setenv("RISK_FLAG__MODULE__LEGACY_GATE__ENABLED", "false")
        raw_client = TestClient(test_app)

        resp = raw_client.get("/api/legacy-gates/modules")
        assert resp.status_code == 404
        assert "Legacy gate module is disabled" in resp.json()["detail"]

    def test_compat_v1_public_route(self, client: TestClient) -> None:
        resp = client.get("/api/v1/public/legacy-gates/modules")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
