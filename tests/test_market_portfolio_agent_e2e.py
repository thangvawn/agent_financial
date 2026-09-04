from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.app.bootstrap.app_factory import create_app
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.platform.database import reset_app_state_tables


@pytest.fixture
def app_client(monkeypatch):
    reset_app_state_tables()
    # Mock VN market feed snapshot for fast, offline deterministic testing
    monkeypatch.setattr(
        "risk_dashboard.modules.data_hub.application.vn_market_feed.VnMarketFeedProducer.snapshot",
        lambda self: {
            "items": [{"symbol": "FPT", "price": 100000.0, "last": 100000.0}],
            "indices": [{"symbol": "VNINDEX", "close": 1250.0, "change_pct": 0.5}],
            "as_of": "2026-09-03T10:00:00Z",
        },
    )
    app = create_app()
    client = TestClient(app)
    return app, client


def test_e2e_feature_flag_off_by_default(app_client):
    app, client = app_client
    res = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": "test-port",
            "review_type": "market_context",
            "idempotency_key": "1234567890123456",
        },
    )
    assert res.status_code == 404
    assert "disabled" in res.json().get("detail", "").lower()


def test_e2e_agent_workflow_when_flag_enabled(app_client, monkeypatch):
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED", "1")
    app, client = app_client

    principal_alice = AuthPrincipal(
        account_id="alice-acc",
        session_id="sess-alice",
        scopes=("account:market_portfolio:read",),
        resolved_at="2026-09-03T10:00:00Z",
    )
    principal_bob = AuthPrincipal(
        account_id="bob-acc",
        session_id="sess-bob",
        scopes=("account:market_portfolio:read",),
        resolved_at="2026-09-03T10:00:00Z",
    )

    # 1. Unauthenticated request returns 401
    res_unauth = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": "alice-acc",
            "review_type": "market_context",
            "idempotency_key": "idemp-test-e2e-001",
        },
    )
    assert res_unauth.status_code == 401

    # Override principal to Alice
    app.dependency_overrides[resolve_principal] = lambda: principal_alice

    # 2. Client supplying forbidden authority fields in payload is rejected with 422
    res_spoof = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": "alice-acc",
            "review_type": "market_context",
            "idempotency_key": "idemp-test-e2e-001",
            "account_id": "malicious-actor",
        },
    )
    assert res_spoof.status_code == 422

    # 3. Valid review request by Alice
    res_review = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": "alice-acc",
            "review_type": "market_context",
            "idempotency_key": "idemp-test-e2e-001",
        },
    )
    assert res_review.status_code == 200
    data = res_review.json()
    assert data["schema_version"] == "1.0.0"
    assert data["artifact"] is not None
    artifact = data["artifact"]
    artifact_id = artifact["artifact_id"]
    assert artifact["account_id"] == "alice-acc"
    assert artifact["portfolio_kind"] == "paper"

    # 4. Fetch artifact as Alice succeeds
    res_get_alice = client.get(f"/api/v1/market-portfolio/agent/reviews/{artifact_id}")
    assert res_get_alice.status_code == 200
    assert res_get_alice.json()["artifact_id"] == artifact_id

    # 5. Fetch artifact as Bob returns 404 (non-disclosing IDOR protection)
    app.dependency_overrides[resolve_principal] = lambda: principal_bob
    res_get_bob = client.get(f"/api/v1/market-portfolio/agent/reviews/{artifact_id}")
    assert res_get_bob.status_code == 404
    assert res_get_bob.json()["detail"] == "Resource not found."


def test_e2e_scope_check_fail_closed(app_client, monkeypatch):
    """Verify that a principal without account:market_portfolio:read scope is strictly rejected with 403."""
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED", "1")
    app, client = app_client

    unprivileged_principal = AuthPrincipal(
        account_id="unprivileged-acc",
        session_id="sess-unpriv",
        scopes=(),  # No scopes!
        resolved_at="2026-09-03T10:00:00Z",
    )
    app.dependency_overrides[resolve_principal] = lambda: unprivileged_principal

    res = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        json={
            "portfolio_id": "unprivileged-acc",
            "review_type": "market_context",
            "idempotency_key": "idemp-scope-fail-closed",
        },
    )
    assert res.status_code == 403
    assert "Missing required scope" in res.json().get("detail", "")


def test_e2e_real_resolve_principal_flow(app_client, monkeypatch):
    """Verify end-to-end request using real resolve_principal without dependency overrides."""
    monkeypatch.setenv("RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__ENABLED", "1")
    app, client = app_client

    # Ensure no overrides
    app.dependency_overrides.pop(resolve_principal, None)

    import uuid

    # Register a real account in database
    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()
    account, session = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="Real User",
        email=f"real_user_{uuid.uuid4().hex[:8]}@example.com",
        password="ValidPassword123!",
    )


    headers = {"Authorization": f"Bearer {session.session_id}"}
    res = client.post(
        "/api/v1/market-portfolio/agent/reviews",
        headers=headers,
        json={
            "portfolio_id": account.account_id,
            "review_type": "market_context",
            "idempotency_key": "idemp-real-auth-001",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["artifact"] is not None
    assert data["artifact"]["account_id"] == account.account_id


def test_e2e_legacy_routes_remain_compatible(app_client):
    app, client = app_client
    res_wl = client.get("/api/v1/market-portfolio/watchlist?session_id=legacy-test-session")
    assert res_wl.status_code == 200
    assert "items" in res_wl.json()

    res_port = client.get("/api/v1/market-portfolio/portfolio?session_id=legacy-test-session")
    assert res_port.status_code == 200
    assert "cash_balance" in res_port.json()
