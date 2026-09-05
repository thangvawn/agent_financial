"""Tests for quant_research REST API and module registration (QF3 Exit Gate & IDOR Matrix)."""
from __future__ import annotations

from datetime import date
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.app.registry.registry import get_module_by_slug
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.quant_research.api.public import (
    _check_feature_enabled,
    clear_run_store,
    router as quant_research_router,
)
from risk_dashboard.platform.runtime.panel_store import set_panel_for_testing


@pytest.fixture(autouse=True)
def setup_panel(synthetic_panel):
    set_panel_for_testing(synthetic_panel)
    clear_run_store()
    return synthetic_panel


@pytest.fixture
def current_principal():
    return {
        "principal": AuthPrincipal(
            account_id="account-alpha",
            session_id="sess-alpha-001",
            scopes=(
                "quant_research:analysis:read",
                "quant_research:scenario:read",
                "quant_research:model_report:read",
            ),
            resolved_at="2026-09-05T10:00:00Z",
        )
    }


@pytest.fixture
def test_app(current_principal):
    app = FastAPI(title="Quant Research Test App")
    app.include_router(quant_research_router)

    def _mock_resolve_principal() -> AuthPrincipal:
        return current_principal["principal"]

    app.dependency_overrides[resolve_principal] = _mock_resolve_principal
    return app


@pytest.fixture
def client(test_app):
    # Bypass the feature flag check for functional tests
    test_app.dependency_overrides[_check_feature_enabled] = lambda: None
    return TestClient(test_app)


# ---------------------------------------------------------------------------
# Module Registration
# ---------------------------------------------------------------------------


def test_module_registered_in_app_registry() -> None:
    import risk_dashboard.app.registry.registry as reg

    reg._MODULE_BY_SLUG = None  # force refresh index
    mod = get_module_by_slug("quant_research")
    assert mod is not None
    assert mod.id == "quant_research"
    assert mod.enabled_by_default is False
    assert "quant_research:analysis:read" in mod.permission_scopes
    assert "quant_risk" in mod.dependencies


# ---------------------------------------------------------------------------
# Feature Flag Enforcement
# ---------------------------------------------------------------------------


def test_feature_flag_disabled_by_default(test_app) -> None:
    # Remove bypass override to test live feature flag gate
    test_app.dependency_overrides.pop(_check_feature_enabled, None)
    raw_client = TestClient(test_app)

    response = raw_client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Phân tích rủi ro EOD",
            "as_of": "2015-12-30",
        },
    )
    assert response.status_code == 404
    assert "disabled" in response.json()["detail"].lower()


def test_feature_flag_enabled_via_env(test_app, monkeypatch) -> None:
    test_app.dependency_overrides.pop(_check_feature_enabled, None)
    monkeypatch.setenv("RISK_FLAG__MODULE__QUANT_RESEARCH__ENABLED", "1")
    raw_client = TestClient(test_app)

    response = raw_client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Phân tích rủi ro EOD",
            "as_of": "2015-12-30",
        },
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Auth & Scopes
# ---------------------------------------------------------------------------


def test_unauthenticated_returns_401(client, current_principal) -> None:
    current_principal["principal"] = AuthPrincipal(
        account_id="anonymous-user",
        session_id="anon-session",
        is_anonymous=True,
        resolved_at="2026-09-05T10:00:00Z",
    )
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Test auth",
            "as_of": "2015-12-30",
        },
    )
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_missing_scope_returns_403(client, current_principal) -> None:
    # Principal has scenario scope, but calling eod_analysis
    current_principal["principal"] = AuthPrincipal(
        account_id="account-alpha",
        session_id="sess-01",
        scopes=("quant_research:scenario:read",),
        resolved_at="2026-09-05T10:00:00Z",
    )
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Test scope",
            "as_of": "2015-12-30",
        },
    )
    assert res.status_code == 403
    assert "Missing required scope" in res.json()["detail"]


# ---------------------------------------------------------------------------
# Happy Path E2E via REST
# ---------------------------------------------------------------------------


def test_create_eod_run_success(client, as_of_date) -> None:
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Đánh giá rủi ro cuối ngày",
            "as_of": as_of_date.isoformat(),
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["run_id"] is not None
    assert data["artifact"]["operation"] == "eod_analysis"
    assert "decision_score" in data["artifact"]["metrics"]
    assert len(data["artifact"]["source_refs"]) > 0


def test_create_scenario_run_success(client, as_of_date) -> None:
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "scenario_compare",
            "question": "Kịch bản sốc lãi suất",
            "as_of": as_of_date.isoformat(),
            "usd_vnd_rate": 26000.0,
            "sbv_interest_rate_pct": 5.5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["artifact"]["operation"] == "scenario_compare"


def test_create_model_report_run_success(client) -> None:
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "model_report",
            "question": "Báo cáo benchmark mô hình",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["artifact"]["operation"] == "model_report"


# ---------------------------------------------------------------------------
# Two-Account IDOR Matrix Backtest (Zero Cross-Account Access)
# ---------------------------------------------------------------------------


def test_two_account_idor_defense_matrix(client, current_principal, as_of_date) -> None:
    # Step 1: Account Alpha creates a run
    current_principal["principal"] = AuthPrincipal(
        account_id="account-alpha",
        session_id="sess-alpha",
        scopes=("quant_research:analysis:read",),
        resolved_at="2026-09-05T10:00:00Z",
    )
    post_res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Nghiên cứu của Alpha",
            "as_of": as_of_date.isoformat(),
        },
    )
    assert post_res.status_code == 200
    run_id = post_res.json()["run_id"]

    # Step 2: Account Alpha retrieves their own run -> 200 OK
    get_res_alpha = client.get(f"/api/quant-research/runs/{run_id}")
    assert get_res_alpha.status_code == 200
    assert get_res_alpha.json()["run_id"] == run_id

    # Step 3: Account Beta tries to access Account Alpha's run -> 404 NOT FOUND (Zero IDOR)
    current_principal["principal"] = AuthPrincipal(
        account_id="account-beta",
        session_id="sess-beta",
        scopes=("quant_research:analysis:read",),
        resolved_at="2026-09-05T10:00:00Z",
    )
    get_res_beta = client.get(f"/api/quant-research/runs/{run_id}")
    assert get_res_beta.status_code == 404
    assert "Run not found" in get_res_beta.json()["detail"]

    # Step 4: Non-existent run -> 404
    get_res_nonexistent = client.get("/api/quant-research/runs/qr-nonexistent-12345")
    assert get_res_nonexistent.status_code == 404


# ---------------------------------------------------------------------------
# Stable Error Mapping (400, 503)
# ---------------------------------------------------------------------------


def test_invalid_input_returns_400(client, as_of_date) -> None:
    # Scenario without overrides -> rejected with 422 by Pydantic / 400
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "scenario_compare",
            "question": "Thiếu override",
            "as_of": as_of_date.isoformat(),
        },
    )
    assert res.status_code in {400, 422}


def test_date_out_of_range_returns_400(client) -> None:
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Ngày ngoài phạm vi",
            "as_of": "1980-01-01",
        },
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["error_type"] == "date_out_of_range"
    assert "hint" in detail


# ---------------------------------------------------------------------------
# OpenAPI Snapshot
# ---------------------------------------------------------------------------


def test_openapi_schema_snapshot(test_app) -> None:
    schema = test_app.openapi()
    assert "/api/quant-research/runs" in schema["paths"]
    assert "post" in schema["paths"]["/api/quant-research/runs"]
    assert "/api/quant-research/runs/{run_id}" in schema["paths"]
    assert "get" in schema["paths"]["/api/quant-research/runs/{run_id}"]


# ---------------------------------------------------------------------------
# Reserved Error Taxonomy & LRU Eviction Backtest
# ---------------------------------------------------------------------------


def test_deadline_exceeded_returns_504(client, as_of_date) -> None:
    from risk_dashboard.modules.quant_research.api.public import get_service
    from risk_dashboard.modules.quant_research.domain.errors import QuantAdapterError

    class TimeoutService:
        async def execute_research(self, *, request, principal):
            raise QuantAdapterError("deadline_exceeded", "Engine calculation timed out.", hint="Vui lòng thử lại sau.")

    client.app.dependency_overrides[get_service] = lambda: TimeoutService()
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Timeout check",
            "as_of": as_of_date.isoformat(),
        },
    )
    assert res.status_code == 504
    detail = res.json()["detail"]
    assert detail["error_type"] == "deadline_exceeded"
    assert "hint" in detail
    client.app.dependency_overrides.pop(get_service, None)


def test_numeric_review_failed_returns_422(client, as_of_date) -> None:
    from risk_dashboard.modules.quant_research.api.public import get_service
    from risk_dashboard.modules.quant_research.domain.errors import QuantAdapterError

    class RejectedService:
        async def execute_research(self, *, request, principal):
            raise QuantAdapterError("numeric_review_failed", "Reviewer rejected numbers.", hint="Số liệu không khớp.")

    client.app.dependency_overrides[get_service] = lambda: RejectedService()
    res = client.post(
        "/api/quant-research/runs",
        json={
            "operation": "eod_analysis",
            "question": "Review failure check",
            "as_of": as_of_date.isoformat(),
        },
    )
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert detail["error_type"] == "numeric_review_failed"
    assert "hint" in detail
    client.app.dependency_overrides.pop(get_service, None)


def test_run_store_lru_eviction(client, as_of_date, monkeypatch) -> None:
    import risk_dashboard.modules.quant_research.api.public as api_pub

    monkeypatch.setattr(api_pub, "MAX_RUN_STORE_SIZE", 2)
    api_pub.clear_run_store()

    res1 = client.post(
        "/api/quant-research/runs",
        json={"operation": "eod_analysis", "question": "Run 1", "as_of": as_of_date.isoformat()},
    )
    id1 = res1.json()["run_id"]

    res2 = client.post(
        "/api/quant-research/runs",
        json={"operation": "eod_analysis", "question": "Run 2", "as_of": as_of_date.isoformat()},
    )
    id2 = res2.json()["run_id"]

    assert client.get(f"/api/quant-research/runs/{id1}").status_code == 200
    assert client.get(f"/api/quant-research/runs/{id2}").status_code == 200

    # Creating a 3rd run should evict id1 (since id2 was accessed last, id1 is older)
    res3 = client.post(
        "/api/quant-research/runs",
        json={"operation": "eod_analysis", "question": "Run 3", "as_of": as_of_date.isoformat()},
    )
    id3 = res3.json()["run_id"]

    assert len(api_pub._RUN_STORE) == 2
    assert client.get(f"/api/quant-research/runs/{id3}").status_code == 200
    assert client.get(f"/api/quant-research/runs/{id1}").status_code == 404

