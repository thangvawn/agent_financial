"""Unit and integration tests for News Interactive Chat (Phase T3)."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock
import pytest

from risk_dashboard.cli.telegram_bot_daemon import TelegramBotDaemon
from risk_dashboard.modules.news_intelligence.application.query_handler import (
    NewsTelegramQueryHandler,
    format_news_query_sections,
)
from risk_dashboard.platform.telegram.access_control import TelegramAccessControl
from risk_dashboard.platform.telegram.command_parser import parse_update
from risk_dashboard.platform.telegram.config import TelegramConfig
from risk_dashboard.platform.telegram.models import TelegramSendResult
from risk_dashboard.platform.telegram.update_repository import TelegramUpdateRepository


@pytest.fixture
def in_memory_db():
    conn = sqlite3.connect(":memory:")
    yield lambda: conn
    conn.close()


def test_news_query_handler_empty_results():
    mock_service = MagicMock()
    mock_service.get_feed.return_value = {"articles": []}

    handler = NewsTelegramQueryHandler(news_service=mock_service)
    cmd = parse_update(
        {"update_id": 1, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/news FPT"}}
    )
    result = handler.handle(cmd)

    assert len(result) == 1
    assert "Không tìm thấy tin tức phù hợp cho từ khóa '<b>FPT</b>'" in result[0]
    mock_service.get_feed.assert_called_once_with(query="FPT", limit=5, time_range_hours=24)


def test_news_query_handler_ticker_normalization():
    mock_service = MagicMock()
    mock_service.get_feed.return_value = {
        "articles": [
            {
                "headline": "FPT Reports Profit <Record>",
                "summary": "Q2 earnings & revenue up",
                "source": "VnExpress",
                "importance_label": "high",
                "url": "https://example.com/news/1",
            }
        ]
    }

    handler = NewsTelegramQueryHandler(news_service=mock_service)
    cmd = parse_update(
        {"update_id": 2, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/news fpt"}}
    )
    result = handler.handle(cmd)

    assert len(result) == 1
    assert "FPT Reports Profit &lt;Record&gt;" in result[0]
    assert '<a href="https://example.com/news/1">Đọc bài viết gốc</a>' in result[0]
    mock_service.get_feed.assert_called_once_with(query="FPT", limit=5, time_range_hours=24)


def test_news_query_handler_invalid_url_safety():
    mock_service = MagicMock()
    mock_service.get_feed.return_value = {
        "articles": [
            {
                "headline": "Dangerous Link Test",
                "summary": "Summary",
                "source": "Source",
                "importance_label": "low",
                "url": "javascript:alert(1)",
            }
        ]
    }

    handler = NewsTelegramQueryHandler(news_service=mock_service)
    cmd = parse_update(
        {"update_id": 3, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/news"}}
    )
    result = handler.handle(cmd)

    assert len(result) == 1
    # Invalid javascript: link should NOT be rendered as an <a href>
    assert "javascript:alert" not in result[0]


def test_news_bot_daemon_integration(in_memory_db):
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
        "update_id": 888,
        "message": {
            "chat": {"id": 100},
            "from": {"id": 456},
            "text": "/news ngan_hang",
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
    assert repository.get_next_offset() == 889
    assert repository.is_processed(888) is True
    mock_client.send_message.assert_called()
