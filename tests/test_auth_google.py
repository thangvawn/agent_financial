from __future__ import annotations

from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.google_identity import GoogleIdentity
from risk_dashboard.modules.auth.application.services import LoginWithGoogle, RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)


def _repos(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    return SqliteAccountRepository(), SqliteAccountSessionRepository()


def test_google_login_creates_account_session(tmp_path, monkeypatch):
    accounts, sessions = _repos(tmp_path, monkeypatch)

    service = LoginWithGoogle(
        accounts=accounts,
        sessions=sessions,
        verify_credential=lambda _: GoogleIdentity(
            email="USER@Example.com",
            name="Google User",
            subject="google-sub-1",
            email_verified=True,
        ),
    )

    account, session = service.execute(credential="valid-google-token")

    assert account.email == "user@example.com"
    assert account.name == "Google User"
    assert session.account_id == account.account_id
    assert sessions.get(session_id=session.session_id) is not None


def test_google_login_reuses_existing_email_account(tmp_path, monkeypatch):
    accounts, sessions = _repos(tmp_path, monkeypatch)
    existing, _ = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="Existing User",
        email="user@example.com",
        password="correct-password",
    )

    account, session = LoginWithGoogle(
        accounts=accounts,
        sessions=sessions,
        verify_credential=lambda _: GoogleIdentity(
            email="user@example.com",
            name="Google Name",
            subject="google-sub-2",
            email_verified=True,
        ),
    ).execute(credential="valid-google-token")

    assert account.account_id == existing.account_id
    assert account.name == "Existing User"
    assert session.account_id == existing.account_id


def test_google_login_endpoint_returns_internal_session(tmp_path, monkeypatch):
    _repos(tmp_path, monkeypatch)

    def fake_verify(_credential: str) -> GoogleIdentity:
        return GoogleIdentity(
            email="person@example.com",
            name="Person Example",
            subject="google-sub-3",
            email_verified=True,
        )

    monkeypatch.setattr(
        "risk_dashboard.modules.auth.api.public.verify_google_credential",
        fake_verify,
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/public/auth/google",
        json={"credential": "x" * 32},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"].startswith("sess_")
    assert payload["profile"]["email"] == "person@example.com"
    assert payload["profile"]["name"] == "Person Example"
