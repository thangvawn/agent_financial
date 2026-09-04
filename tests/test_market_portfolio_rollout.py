from __future__ import annotations

import hashlib
import pytest
from fastapi.testclient import TestClient

from risk_dashboard.app.bootstrap.app_factory import create_app
from risk_dashboard.app.registry.registry import get_module_by_slug
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.platform.database import reset_app_state_tables


@pytest.fixture
def app_client(monkeypatch):
    reset_app_state_tables()
    # Mock VN market feed snapshot for fast, deterministic testing
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.vn_market_feed.VnMarketFeedProducer.snapshot",
        lambda self: {
            "items": [{"symbol": "FPT", "price": 100000.0, "last": 100000.0}],
            "indices": [{"symbol": "VNINDEX", "close": 1250.0, "change_pct": 0.5}],
            "as_of": "2026-09-04T10:00:00Z",
        },
    )
    app = create_app()
    client = TestClient(app)
    return app, client


def test_module_feature_flags_and_scopes_registration():
    mod = get_module_by_slug("market_portfolio")
    assert mod is not None
    assert "module.market_portfolio.enabled" in mod.feature_flags
    assert "module.market_portfolio.agent.enabled" in mod.feature_flags
    assert "account:market_portfolio:read" in mod.permission_scopes


def test_ops_rollout_status_when_flag_disabled(app_client):
    app, client = app_client
    res = client.get("/api/v1/market-portfolio/agent/ops/rollout-status")
    assert res.status_code == 200
    data = res.json()
    assert data["schema_version"] == "1.0.0"
    assert data["master_enabled"] is False
    assert data["active_stage"] == "disabled"
    assert data["kill_switch_ready"] is True
    assert data["sla_thresholds"]["forbidden_executions"] == 0
    assert data["sla_thresholds"]["max_cost_usd_per_review"] == 0.03
    assert data["sla_thresholds"]["kill_switch_max_sec"] == 30
    assert data["dependencies_status"]["doc_00_agentic_core"] == "ready"


def test_ops_rollout_status_when_flag_enabled(app_client, monkeypatch):
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED", "1")
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE", "25")
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_ALLOWLIST", "acc-1,acc-2")

    app, client = app_client
    res = client.get("/api/v1/market-portfolio/agent/ops/rollout-status")
    assert res.status_code == 200
    data = res.json()
    assert data["master_enabled"] is True
    assert data["cohort_percentage"] == 25
    assert data["active_stage"] == "cohort_25pct"
    assert data["allowlist_count"] == 2


def test_kill_switch_blocks_reviews_without_affecting_legacy_rest(app_client):
    app, client = app_client
    # 1. Agent review endpoint is disabled (404)
    res_agent = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": "test-kill-switch-port",
            "review_type": "market_context",
            "idempotency_key": "idemp-kill-switch-001",
        },
    )
    assert res_agent.status_code == 404
    assert "disabled" in res_agent.json().get("detail", "").lower()

    # 2. Legacy REST portfolio and watchlist endpoints remain 100% active (200)
    res_port = client.get("/api/v1/market-portfolio/portfolio?session_id=ops-test-session")
    assert res_port.status_code == 200
    assert "cash_balance" in res_port.json()

    res_wl = client.get("/api/v1/market-portfolio/watchlist?session_id=ops-test-session")
    assert res_wl.status_code == 200
    assert "items" in res_wl.json()


def test_cohort_gating_deterministic_buckets(app_client, monkeypatch):
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED", "1")
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE", "5")
    app, client = app_client

    # Find one account with hash bucket < 5 and one with bucket >= 5
    account_in = None
    account_out = None
    for i in range(200):
        test_acc = f"test-acc-cohort-{i}"
        bucket = int(hashlib.sha256(f"mp_cohort:{test_acc}".encode()).hexdigest(), 16) % 100
        if bucket < 5 and account_in is None:
            account_in = test_acc
        elif bucket >= 5 and account_out is None:
            account_out = test_acc
        if account_in and account_out:
            break

    assert account_in is not None
    assert account_out is not None

    # Account in 5% cohort succeeds
    principal_in = AuthPrincipal(
        account_id=account_in,
        session_id="sess-in",
        scopes=("account:market_portfolio:read",),
        resolved_at="2026-09-04T10:00:00Z",
    )
    app.dependency_overrides[resolve_principal] = lambda: principal_in

    res_in = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": account_in,
            "review_type": "market_context",
            "idempotency_key": "idemp-cohort-in-001",
        },
    )
    assert res_in.status_code == 200
    assert res_in.json()["artifact"] is not None

    # Account not in 5% cohort is rejected with 404
    principal_out = AuthPrincipal(
        account_id=account_out,
        session_id="sess-out",
        scopes=("account:market_portfolio:read",),
        resolved_at="2026-09-04T10:00:00Z",
    )
    app.dependency_overrides[resolve_principal] = lambda: principal_out

    res_out = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": account_out,
            "review_type": "market_context",
            "idempotency_key": "idemp-cohort-out-001",
        },
    )
    assert res_out.status_code == 404
    assert "not enabled for this cohort" in res_out.json().get("detail", "")


def test_cohort_allowlist_bypass(app_client, monkeypatch):
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED", "1")
    # Percentage is 0% (only allowlist accounts can enter)
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE", "0")
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_ALLOWLIST", "acc-internal-dogfood")
    app, client = app_client

    # Allowlisted account succeeds
    principal_allowed = AuthPrincipal(
        account_id="acc-internal-dogfood",
        session_id="sess-allow",
        scopes=("account:market_portfolio:read",),
        resolved_at="2026-09-04T10:00:00Z",
    )
    app.dependency_overrides[resolve_principal] = lambda: principal_allowed

    res_allowed = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": "acc-internal-dogfood",
            "review_type": "market_context",
            "idempotency_key": "idemp-allowlist-001",
        },
    )
    assert res_allowed.status_code == 200
    assert res_allowed.json()["artifact"] is not None

    # Non-allowlisted account fails with 404
    principal_other = AuthPrincipal(
        account_id="acc-non-allowlisted",
        session_id="sess-other",
        scopes=("account:market_portfolio:read",),
        resolved_at="2026-09-04T10:00:00Z",
    )
    app.dependency_overrides[resolve_principal] = lambda: principal_other

    res_other = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": "acc-non-allowlisted",
            "review_type": "market_context",
            "idempotency_key": "idemp-allowlist-002",
        },
    )
    assert res_other.status_code == 404

