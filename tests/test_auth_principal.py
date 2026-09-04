from __future__ import annotations

from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.domain.policies import check_ownership, has_scope
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.platform.database import clear_db_path_cache


def test_principal_round_trip_and_policies() -> None:
    principal = AuthPrincipal(
        account_id="account-a",
        session_id="session-a",
        scopes=("me:memory:read",),
        consent=ConsentSnapshot(policy_version="v1"),
        resolved_at="2026-08-28T12:00:00+00:00",
    )

    restored = AuthPrincipal.model_validate_json(principal.model_dump_json())

    assert restored == principal
    assert has_scope(restored, "me:memory:read")
    assert not has_scope(restored, "me:memory:delete")
    assert check_ownership(restored, "account-a")
    assert not check_ownership(restored, "account-b")


def _session(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    clear_db_path_cache()
    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()
    account, session = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="Principal User",
        email=f"principal-{tmp_path.name}@example.com",
        password="correct-password",
    )
    return account, session, sessions


def test_me_requires_bearer_session(tmp_path, monkeypatch) -> None:
    account, session, _ = _session(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/api/v1/public/auth/me",
        headers={"Authorization": f"Bearer {session.session_id}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "session_id": session.session_id,
        "profile": {
            "email": account.email,
            "name": account.name,
            "session_mode": "server_account",
        },
    }


def test_me_rejects_query_session_and_malformed_authorization(tmp_path, monkeypatch) -> None:
    _, session, _ = _session(tmp_path, monkeypatch)
    client = TestClient(app)

    query_response = client.get(f"/api/v1/public/auth/me?session_id={session.session_id}")
    malformed_response = client.get(
        "/api/v1/public/auth/me",
        headers={"Authorization": f"Basic {session.session_id}"},
    )
    oversized_response = client.get(
        "/api/v1/public/auth/me",
        headers={"Authorization": f"Bearer {'x' * 257}"},
    )

    assert query_response.status_code == 401
    assert malformed_response.status_code == 401
    assert oversized_response.status_code == 401


def test_me_rejects_revoked_session(tmp_path, monkeypatch) -> None:
    _, session, sessions = _session(tmp_path, monkeypatch)
    sessions.revoke(session_id=session.session_id)
    client = TestClient(app)

    response = client.get(
        "/api/v1/public/auth/me",
        headers={"Authorization": f"Bearer {session.session_id}"},
    )

    assert response.status_code == 401


def test_logout_requires_bearer_and_only_revokes_authenticated_session(tmp_path, monkeypatch) -> None:
    account, session, sessions = _session(tmp_path, monkeypatch)
    other_account, other_session = RegisterAccount(accounts=SqliteAccountRepository(), sessions=sessions).execute(
        name="Other User",
        email=f"other-{tmp_path.name}@example.com",
        password="correct-password",
    )
    client = TestClient(app)

    unauthorized = client.post("/api/v1/public/auth/logout")
    authorized = client.post(
        "/api/v1/public/auth/logout",
        headers={"Authorization": f"Bearer {session.session_id}"},
    )

    assert account.account_id != other_account.account_id
    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert sessions.get(session_id=session.session_id).status == "revoked"
    assert sessions.get(session_id=other_session.session_id).status == "active"
