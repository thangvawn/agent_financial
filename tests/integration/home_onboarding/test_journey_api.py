from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.modules.home_onboarding.infrastructure.sqlite_journey import (
    SqliteHomeCardRepository,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    NextBestActionCardV1,
    SummarySourceRefV1,
)
from risk_dashboard.platform.database.config import clear_db_path_cache


def _setup_account(tmp_path: Path, monkeypatch):
    db_path = str(tmp_path / "app_state.db")
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", db_path)
    clear_db_path_cache()
    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()
    account, session = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="Journey Tester",
        email=f"tester-{tmp_path.name}@example.com",
        password="secure-password-123",
    )
    return account, session, db_path


def test_unauthenticated_request_returns_401(monkeypatch):
    monkeypatch.setenv(
        "RISK_FLAG__MODULE__HOME_ONBOARDING__HOME_JOURNEY__V1__ENABLED", "true"
    )
    client = TestClient(app)
    resp = client.get("/api/v1/me/home-journey")
    assert resp.status_code == 401


def test_invalid_session_returns_401(monkeypatch):
    monkeypatch.setenv(
        "RISK_FLAG__MODULE__HOME_ONBOARDING__HOME_JOURNEY__V1__ENABLED", "true"
    )
    client = TestClient(app)
    resp = client.get(
        "/api/v1/me/home-journey",
        headers={"Authorization": "Bearer invalid_session_id_12345"},
    )
    assert resp.status_code == 401


def test_flag_disabled_returns_404(tmp_path, monkeypatch):
    account, session, _ = _setup_account(tmp_path, monkeypatch)
    monkeypatch.setenv(
        "RISK_FLAG__MODULE__HOME_ONBOARDING__HOME_JOURNEY__V1__ENABLED", "false"
    )
    client = TestClient(app)
    resp = client.get(
        "/api/v1/me/home-journey",
        headers={"Authorization": f"Bearer {session.session_id}"},
    )
    assert resp.status_code == 404


def test_flag_enabled_no_consent_returns_non_personalized(tmp_path, monkeypatch):
    account, session, _ = _setup_account(tmp_path, monkeypatch)
    monkeypatch.setenv(
        "RISK_FLAG__MODULE__HOME_ONBOARDING__HOME_JOURNEY__V1__ENABLED", "true"
    )
    client = TestClient(app)
    resp = client.get(
        "/api/v1/me/home-journey",
        headers={"Authorization": f"Bearer {session.session_id}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "non_personalized"
    assert data["next_best_action"] is None
    assert data["consent_required"] is True


def test_feedback_cross_account_and_duplicate(tmp_path, monkeypatch):
    account, session, db_path = _setup_account(tmp_path, monkeypatch)
    monkeypatch.setenv(
        "RISK_FLAG__MODULE__HOME_ONBOARDING__HOME_JOURNEY__V1__ENABLED", "true"
    )

    card_repo = SqliteHomeCardRepository(db_path)
    card = NextBestActionCardV1(
        card_id="card_target_1",
        candidate_id="cand_1",
        action_type="open_lesson",
        target_surface="learn",
        target_ref=SummarySourceRefV1(
            surface="learn",
            resource_type="lesson",
            resource_id="101",
            resource_version=1,
        ),
        title="Lesson 101",
        why_now="Continue lesson",
        source_summary_ids=("sum_1",),
        cta_label="Start",
        cta_path="/learn?lesson=101",
        created_at="2026-09-01T00:00:00Z",
        expires_at="2026-10-01T00:00:00Z",
    )
    card_repo.save_selected_card(card=card, account_id=account.account_id)

    client = TestClient(app)

    # 1. Non-existent card returns 404
    resp_nf = client.post(
        "/api/v1/me/home-journey/cards/non_existent_card/feedback",
        headers={"Authorization": f"Bearer {session.session_id}"},
        json={
            "action": "dismiss",
            "idempotency_key": "idemp_test_key_01",
        },
    )
    assert resp_nf.status_code == 404

    # 2. Valid card feedback recorded
    resp_rec = client.post(
        f"/api/v1/me/home-journey/cards/{card.card_id}/feedback",
        headers={"Authorization": f"Bearer {session.session_id}"},
        json={
            "action": "snooze",
            "snooze_hours": 24,
            "idempotency_key": "idemp_test_key_02",
        },
    )
    assert resp_rec.status_code == 200
    assert resp_rec.json()["status"] == "recorded"

    # 3. Duplicate idempotency returns duplicate
    resp_dup = client.post(
        f"/api/v1/me/home-journey/cards/{card.card_id}/feedback",
        headers={"Authorization": f"Bearer {session.session_id}"},
        json={
            "action": "snooze",
            "snooze_hours": 24,
            "idempotency_key": "idemp_test_key_02",
        },
    )
    assert resp_dup.status_code == 200
    assert resp_dup.json()["status"] == "duplicate"

