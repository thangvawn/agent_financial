from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.platform.database import clear_db_path_cache


def _create_user_session(tmp_path, monkeypatch, name_suffix: str):
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    clear_db_path_cache()
    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()
    account, session = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name=f"User {name_suffix}",
        email=f"user_{name_suffix}_{tmp_path.name}@example.com",
        password="secure_password_123",
    )
    return account, session, sessions


def test_ai_tutor_endpoints_require_authentication(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    clear_db_path_cache()
    client = TestClient(app)

    # Missing authorization header
    res_create = client.post(
        "/api/v1/public/ai-tutor/conversations",
        json={"surface": "learn", "idempotency_key": "k1"},
    )
    assert res_create.status_code == 401

    res_get = client.get("/api/v1/public/ai-tutor/conversations/conv_123")
    assert res_get.status_code == 401

    res_msg = client.post(
        "/api/v1/public/ai-tutor/conversations/conv_123/messages",
        json={"content": "Giải thích ROE", "idempotency_key": "k2"},
    )
    assert res_msg.status_code == 401

    res_fb = client.post(
        "/api/v1/public/ai-tutor/messages/msg_123/feedback",
        json={"rating": "helpful", "idempotency_key": "k3"},
    )
    assert res_fb.status_code == 401


def test_ai_tutor_rejects_expired_or_revoked_session(tmp_path, monkeypatch) -> None:
    account, session, sessions = _create_user_session(tmp_path, monkeypatch, "expired")
    sessions.revoke(session_id=session.session_id)
    client = TestClient(app)

    res = client.post(
        "/api/v1/public/ai-tutor/conversations",
        headers={"Authorization": f"Bearer {session.session_id}"},
        json={"surface": "learn", "idempotency_key": "k_revoked"},
    )
    assert res.status_code == 401


def test_cross_user_isolation_strictly_enforced(tmp_path, monkeypatch) -> None:
    acc_a, sess_a, _ = _create_user_session(tmp_path, monkeypatch, "a")
    acc_b, sess_b, _ = _create_user_session(tmp_path, monkeypatch, "b")
    client = TestClient(app)

    # User A creates a conversation
    res_a = client.post(
        "/api/v1/public/ai-tutor/conversations",
        headers={"Authorization": f"Bearer {sess_a.session_id}"},
        json={"surface": "learn", "idempotency_key": "idemp_user_a"},
    )
    assert res_a.status_code == 200
    conv_a_id = res_a.json()["conversation_id"]

    # User B tries to read User A's conversation -> 404
    res_b_read = client.get(
        f"/api/v1/public/ai-tutor/conversations/{conv_a_id}",
        headers={"Authorization": f"Bearer {sess_b.session_id}"},
    )
    assert res_b_read.status_code == 404

    # User B tries to send message into User A's conversation -> 404
    res_b_msg = client.post(
        f"/api/v1/public/ai-tutor/conversations/{conv_a_id}/messages",
        headers={"Authorization": f"Bearer {sess_b.session_id}"},
        json={"content": "Can I hijack this?", "idempotency_key": "idemp_hijack"},
    )
    assert res_b_msg.status_code == 404

