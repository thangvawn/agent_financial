from __future__ import annotations

from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_conversation_repository import (
    SqliteConversationRepository,
)
from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_feedback_repository import (
    SqliteFeedbackRepository,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    ConversationEntity,
    FeedbackEntity,
    MessageEntity,
    NumericClaimRef,
    ToolCallRef,
)
from risk_dashboard.platform.database import apply_migrations, clear_db_path_cache, open_app_state_db

NOW = "2026-08-28T12:00:00+00:00"


def test_sqlite_conversation_repository_crud_and_idempotency(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    clear_db_path_cache()

    with open_app_state_db() as conn:
        apply_migrations(conn)

    repo = SqliteConversationRepository()
    conv = ConversationEntity(
        conversation_id="conv_1",
        account_id="acc_1",
        surface="learn",
        context_id="lesson_roe",
        status="active",
        title="Hội thoại Learn",
        idempotency_key="idemp_conv_1",
        created_at=NOW,
        updated_at=NOW,
    )
    repo.create_conversation(conv)

    # Fetch
    fetched = repo.get_conversation(conversation_id="conv_1", account_id="acc_1")
    assert fetched is not None
    assert fetched.conversation_id == "conv_1"
    assert fetched.surface == "learn"

    # Idempotency lookup
    idemp_fetched = repo.get_by_idempotency(account_id="acc_1", idempotency_key="idemp_conv_1")
    assert idemp_fetched is not None
    assert idemp_fetched.conversation_id == "conv_1"

    # Messages save and list ordering
    msg1 = MessageEntity(
        message_id="msg_1",
        conversation_id="conv_1",
        role="user",
        content="ROE là gì?",
        idempotency_key="msg_user_1",
        created_at="2026-08-28T12:01:00+00:00",
    )
    msg2 = MessageEntity(
        message_id="msg_2",
        conversation_id="conv_1",
        role="assistant",
        content="ROE là tỷ suất sinh lời trên vốn chủ sở hữu.",
        citations=(CitationRef(source_type="lesson", source_id="card_roe_01", label="Chỉ số ROE"),),
        numeric_claims=(
            NumericClaimRef(
                claim_id="c1",
                statement="Ngưỡng ROE tốt > 15%",
                value="15%",
                evidence_ref="roe_threshold",
            ),
        ),
        tool_calls=(ToolCallRef(tool_name="learning.get_lesson_context", status="success", summary="Đọc giáo trình"),),
        assumptions=("Chuẩn kế toán VAS",),
        limitations=("Cần đánh giá tối thiểu 3 năm",),
        check_question="Anh đã hiểu rõ công thức tính chưa?",
        next_action="Làm bài quiz",
        trace_id="tr_1",
        idempotency_key="msg_asst_1",
        created_at="2026-08-28T12:01:05+00:00",
    )
    repo.save_message(msg1)
    repo.save_message(msg2)

    messages = repo.list_messages(conversation_id="conv_1", account_id="acc_1")
    assert len(messages) == 2
    assert messages[0].message_id == "msg_1"
    assert messages[1].message_id == "msg_2"
    assert len(messages[1].citations) == 1
    assert messages[1].citations[0].label == "Chỉ số ROE"
    assert len(messages[1].numeric_claims) == 1
    assert messages[1].check_question == "Anh đã hiểu rõ công thức tính chưa?"


def test_sqlite_feedback_repository(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("RISK_DASHBOARD_APP_STATE_DB", str(tmp_path / "app_state.db"))
    clear_db_path_cache()

    with open_app_state_db() as conn:
        apply_migrations(conn)

    conv_repo = SqliteConversationRepository()
    conv_repo.create_conversation(
        ConversationEntity(
            conversation_id="conv_fb",
            account_id="acc_fb",
            surface="learn",
            created_at=NOW,
            updated_at=NOW,
        )
    )

    fb_repo = SqliteFeedbackRepository()
    fb = FeedbackEntity(
        feedback_id="fb_1",
        conversation_id="conv_fb",
        message_id="msg_asst_1",
        account_id="acc_fb",
        rating="helpful",
        comment="Giải thích rất dễ hiểu!",
        idempotency_key="idemp_fb_1",
        created_at=NOW,
    )
    fb_repo.save_feedback(fb)

    fetched = fb_repo.get_by_idempotency(message_id="msg_asst_1", idempotency_key="idemp_fb_1")
    assert fetched is not None
    assert fetched.rating == "helpful"
    assert fetched.comment == "Giải thích rất dễ hiểu!"

