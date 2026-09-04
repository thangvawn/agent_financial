from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountConsentRepository,
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters import (
    SURFACE_READERS,
)
from risk_dashboard.platform.database.config import clear_db_path_cache


def _setup(tmp_path: Path, monkeypatch):
    db_path = str(tmp_path / "app_state.db")
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", db_path)
    monkeypatch.setenv("RISK_FLAG__MODULE__HOME_ONBOARDING__HOME_JOURNEY__V1__ENABLED", "true")
    clear_db_path_cache()
    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()
    account, session = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="Acceptance User",
        email=f"user-{tmp_path.name}@example.com",
        password="password123!",
    )
    return account, session, db_path


def test_finding2_scope_bypass_blocked(tmp_path: Path, monkeypatch) -> None:
    """Finding 2: account:market_portfolio:read MUST NOT bypass journey scopes."""
    account, session, _ = _setup(tmp_path, monkeypatch)

    # Override resolve_principal to simulate principal with ONLY market_portfolio:read
    def _mock_resolve_limited_scopes() -> AuthPrincipal:
        return AuthPrincipal(
            account_id=account.account_id,
            session_id=session.session_id,
            scopes=("account:market_portfolio:read",),  # lacking me:home_journey:*
            resolved_at="2026-09-01T00:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = _mock_resolve_limited_scopes
    try:
        client = TestClient(app)

        # GET /home-journey must return 403 Forbidden
        get_res = client.get("/api/v1/me/home-journey")
        assert get_res.status_code == 403
        assert "Missing required scope" in get_res.json()["detail"]

        # POST feedback must return 403 Forbidden
        post_res = client.post(
            "/api/v1/me/home-journey/cards/card_123/feedback",
            json={"action": "dismiss", "idempotency_key": "idemp_test_1"},
        )
        assert post_res.status_code == 403
        assert "Missing required scope" in post_res.json()["detail"]
    finally:
        app.dependency_overrides.pop(resolve_principal, None)


def test_finding1_consent_flow_enables_personalized_mode(tmp_path: Path, monkeypatch) -> None:
    """Finding 1: ConsentSnapshot loaded in resolve_principal allows personalized mode."""
    account, session, _ = _setup(tmp_path, monkeypatch)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {session.session_id}"}

    # 1. Before consent: non_personalized mode
    res_before = client.get("/api/v1/me/home-journey", headers=headers)
    assert res_before.status_code == 200
    assert res_before.json()["mode"] == "non_personalized"
    assert res_before.json()["consent_required"] is True

    # 2. Grant consent via auth consent API
    consent_res = client.post(
        "/api/v1/public/auth/consent",
        headers=headers,
        json={
            "schema_version": "1.0.0",
            "memory": True,
            "analytics": True,
            "policy_version": "1.0.0",
            "consented_at": "2026-09-01T00:00:00Z",
        },
    )
    assert consent_res.status_code == 200

    # 3. After consent: resolve_principal loads consent -> personalized/empty mode (consent_required = False)
    res_after = client.get("/api/v1/me/home-journey", headers=headers)
    assert res_after.status_code == 200
    data = res_after.json()
    assert data["consent_required"] is False
    assert data["mode"] in ("personalized", "empty")


def test_finding7_no_public_home_journey_endpoint(tmp_path: Path, monkeypatch) -> None:
    """Finding 7: /api/v1/public/home-journey must not exist (404)."""
    _setup(tmp_path, monkeypatch)
    client = TestClient(app)
    resp = client.get("/api/v1/public/home-journey")
    assert resp.status_code == 404


def test_finding3_multisurface_readers_configured() -> None:
    """Finding 3: All 5 surfaces (learn, bctc, simulation, news, market) are wired."""
    expected_surfaces = {"learn", "bctc", "simulation", "news", "market"}
    assert set(SURFACE_READERS.keys()) == expected_surfaces
    for surface, reader in SURFACE_READERS.items():
        assert getattr(reader, "surface") == surface
        assert hasattr(reader, "list_reviewed_summaries")
