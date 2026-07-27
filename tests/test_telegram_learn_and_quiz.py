"""Unit and integration tests for Learn and Quiz modules (Phase T4)."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock
import pytest

from risk_dashboard.cli.telegram_bot_daemon import TelegramBotDaemon
from risk_dashboard.modules.learning.application.query_handler import (
    LearningTelegramQueryHandler,
    sanitize_url,
)
from risk_dashboard.modules.learning.application.quiz_handler import QuizTelegramHandler
from risk_dashboard.modules.learning.infrastructure.delivery_repository import LearningDeliveryRepository
from risk_dashboard.platform.telegram.access_control import TelegramAccessControl
from risk_dashboard.platform.telegram.command_parser import parse_update
from risk_dashboard.platform.telegram.config import TelegramConfig
from risk_dashboard.platform.telegram.models import TelegramSendResult
from risk_dashboard.platform.telegram.quiz_repository import QuizSessionRepository
from risk_dashboard.platform.telegram.update_repository import TelegramUpdateRepository


@pytest.fixture
def in_memory_db():
    conn = sqlite3.connect(":memory:")
    yield lambda: conn
    conn.close()


def test_learn_query_handler_and_topic_filter():
    handler = LearningTelegramQueryHandler()

    # /learn default
    cmd1 = parse_update({"update_id": 1, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/learn"}})
    res1 = handler.handle(cmd1)
    assert len(res1) == 1
    assert "Thẻ kiến thức" in res1[0] or "Chỉ số ROE" in res1[0]

    # /learn dinh_gia
    cmd2 = parse_update({"update_id": 2, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/learn dinh_gia"}})
    res2 = handler.handle(cmd2)
    assert "ROE" in res2[0]

    # /learn invalid_topic
    cmd3 = parse_update({"update_id": 3, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/learn invalid_topic"}})
    res3 = handler.handle(cmd3)
    assert "Không tìm thấy chủ đề" in res3[0]
    assert "dinh_gia" in res3[0]


def test_url_sanitization():
    assert sanitize_url("https://example.com/lesson 1") == "https://example.com/lesson%201"
    assert sanitize_url("javascript:alert(1)") is None


def test_learning_delivery_repository(in_memory_db):
    repo = LearningDeliveryRepository(db_factory=in_memory_db)
    assert repo.is_delivered("chat1", "user1", "card1") is False

    repo.record_delivery("chat1", "user1", "card1", telegram_message_id=99)
    assert repo.is_delivered("chat1", "user1", "card1") is True


def test_quiz_session_and_atomic_answer(in_memory_db):
    quiz_repo = QuizSessionRepository(db_factory=in_memory_db)
    handler = QuizTelegramHandler(repository=quiz_repo)

    # 1. Trigger /quiz command
    cmd_quiz = parse_update({"update_id": 10, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/quiz"}})
    sections, reply_markup = handler.handle_command(cmd_quiz)

    assert "CÂU HỎI TRẮC NGHIỆM" in sections[0]
    assert reply_markup is not None
    assert "inline_keyboard" in reply_markup

    # Extract session_id from callback_data e.g. "quiz:q_xxxx:B"
    cb_data = reply_markup["inline_keyboard"][0][0]["callback_data"]
    parts = cb_data.split(":")
    session_id = parts[1]

    # 2. Test user B clicking user A's quiz button (Ownership error)
    cmd_wrong_user = parse_update({
        "update_id": 11,
        "callback_query": {
            "id": "cb1",
            "from": {"id": 999},  # Wrong user!
            "message": {"chat": {"id": 100}},
            "data": f"quiz:{session_id}:B",
        },
    })
    res_wrong = handler.handle_callback(cmd_wrong_user)
    assert "không thể trả lời" in res_wrong[0]

    # 3. Test correct user A answering B (Correct choice for quiz_roe_01)
    cmd_user_a = parse_update({
        "update_id": 12,
        "callback_query": {
            "id": "cb2",
            "from": {"id": 200},  # Correct user!
            "message": {"chat": {"id": 100}},
            "data": f"quiz:{session_id}:B",
        },
    })
    res_a = handler.handle_callback(cmd_user_a)
    assert "Chính xác" in res_a[0]
    assert "ROE = (LNST / Vốn CSH)" in res_a[0]

    # 4. Test double-click prevention
    res_double = handler.handle_callback(cmd_user_a)
    assert "đã được trả lời" in res_double[0]


def test_learn_and_quiz_bot_daemon_integration(in_memory_db):
    config = TelegramConfig(
        bot_token="test_token",
        default_chat_id="100",
        market_chat_id="100",
        news_chat_id="100",
        learn_chat_id="100",
        bctc_chat_id="100",
    )

    mock_client = MagicMock()
    mock_client.send_message.return_value = TelegramSendResult(
        ok=True, message_id=1, chat_id="100", status_code=200, attempts=1
    )

    mock_receiver = MagicMock()
    fixture_update = {
        "update_id": 999,
        "message": {
            "chat": {"id": 100},
            "from": {"id": 456},
            "text": "/learn dinh_gia",
        },
    }
    mock_receiver.get_updates.return_value = [fixture_update]

    repository = TelegramUpdateRepository(db_factory=in_memory_db)
    access_control = TelegramAccessControl(allowed_chat_ids={"100"}, admin_user_ids={"999"})

    daemon = TelegramBotDaemon(
        config=config,
        client=mock_client,
        receiver=mock_receiver,
        repository=repository,
        access_control=access_control,
    )

    processed = daemon.run_once()
    assert processed == 1
    assert repository.get_next_offset() == 1000
    assert repository.is_processed(999) is True
    mock_client.send_message.assert_called()
