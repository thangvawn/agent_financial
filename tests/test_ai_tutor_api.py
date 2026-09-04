from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import (
    SqliteAccountRepository,
    SqliteAccountSessionRepository,
)
from risk_dashboard.platform.database import apply_migrations, clear_db_path_cache, open_app_state_db


@pytest.fixture
def auth_client(tmp_path, monkeypatch):
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    clear_db_path_cache()

    with open_app_state_db() as conn:
        apply_migrations(conn)

    accounts = SqliteAccountRepository()
    sessions = SqliteAccountSessionRepository()
    account, session = RegisterAccount(accounts=accounts, sessions=sessions).execute(
        name="Tutor Student",
        email=f"student_{tmp_path.name}@example.com",
        password="password123",
    )
    client = TestClient(app)
    return client, session.session_id


def test_ai_tutor_end_to_end_flow(auth_client) -> None:
    client, session_id = auth_client
    headers = {"Authorization": f"Bearer {session_id}"}

    # 1. Create Conversation
    res_conv = client.post(
        "/api/v1/public/ai-tutor/conversations",
        headers=headers,
        json={"surface": "learn", "context_id": "card_roe_01", "idempotency_key": "idemp_conv_test"},
    )
    assert res_conv.status_code == 200
    conv_data = res_conv.json()
    conv_id = conv_data["conversation_id"]
    assert conv_data["surface"] == "learn"
    assert conv_data["status"] == "active"

    # Idempotency test for create conversation
    res_conv_dup = client.post(
        "/api/v1/public/ai-tutor/conversations",
        headers=headers,
        json={"surface": "learn", "context_id": "card_roe_01", "idempotency_key": "idemp_conv_test"},
    )
    assert res_conv_dup.status_code == 200
    assert res_conv_dup.json()["conversation_id"] == conv_id

    # 2. Send Learning Message
    res_msg1 = client.post(
        f"/api/v1/public/ai-tutor/conversations/{conv_id}/messages",
        headers=headers,
        json={
            "content": "Giải thích giúp em bài học về chỉ số ROE",
            "surface": "learn",
            "current_surface_id": "card_roe_01",
            "idempotency_key": "msg_idemp_1",
        },
    )
    assert res_msg1.status_code == 200
    msg1_data = res_msg1.json()
    assert msg1_data["role"] == "assistant"
    assert "ROE" in msg1_data["answer"]
    assert len(msg1_data["citations"]) >= 1
    assert msg1_data["check_question"] is not None
    assert msg1_data["next_action"] is not None
    msg1_id = msg1_data["message_id"]

    # Test message idempotency
    res_msg1_dup = client.post(
        f"/api/v1/public/ai-tutor/conversations/{conv_id}/messages",
        headers=headers,
        json={
            "content": "Giải thích giúp em bài học về chỉ số ROE",
            "surface": "learn",
            "current_surface_id": "card_roe_01",
            "idempotency_key": "msg_idemp_1",
        },
    )
    assert res_msg1_dup.status_code == 200
    assert res_msg1_dup.json()["message_id"] == msg1_id

    # 3. Send Quant Message
    res_msg2 = client.post(
        f"/api/v1/public/ai-tutor/conversations/{conv_id}/messages",
        headers=headers,
        json={
            "content": "Tính giúp em chỉ số rủi ro VaR 95% và CVaR 1 ngày",
            "surface": "quant",
            "idempotency_key": "msg_idemp_2",
        },
    )
    assert res_msg2.status_code == 200
    msg2_data = res_msg2.json()
    assert len(msg2_data["numeric_claims"]) >= 2
    assert len(msg2_data["citations"]) >= 1
    assert "VaR" in msg2_data["answer"]

    # 4. Get Conversation Details with Message History
    res_get = client.get(
        f"/api/v1/public/ai-tutor/conversations/{conv_id}",
        headers=headers,
    )
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["conversation_id"] == conv_id
    assert get_data["message_count"] >= 4  # 2 user messages + 2 assistant messages

    # 5. Submit Feedback
    res_fb = client.post(
        f"/api/v1/public/ai-tutor/messages/{msg1_id}/feedback",
        headers=headers,
        json={
            "conversation_id": conv_id,
            "rating": "helpful",
            "comment": "Câu trả lời rất dễ hiểu và chi tiết!",
            "idempotency_key": "fb_idemp_1",
        },
    )
    assert res_fb.status_code == 200
    fb_data = res_fb.json()
    assert fb_data["message_id"] == msg1_id
    assert fb_data["status"] == "recorded"

