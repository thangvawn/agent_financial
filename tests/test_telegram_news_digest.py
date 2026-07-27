from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from risk_dashboard.modules.news_intelligence.application.telegram_digest import (
    TelegramDigestConfig,
    TelegramDigestService,
    due_periods,
    format_digest_messages,
)
from risk_dashboard.platform.telegram.models import TelegramSendResult


def test_due_periods_uses_vietnam_schedule_and_month_end():
    config = TelegramDigestConfig(token="x", chat_id="1")
    sunday = datetime(2026, 5, 31, 19, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    assert due_periods(sunday.replace(hour=18, minute=30), config) == ["day"]
    assert due_periods(sunday, config) == ["week"]
    assert due_periods(sunday.replace(hour=19, minute=30), config) == ["month"]


def test_digest_keeps_only_trusted_or_important_items_and_escapes_html():
    snapshot = {
        "period": "day",
        "period_key": "2026-05-31",
        "items": [
            {
                "headline": "Official <update>",
                "summary": "Important & verified",
                "source": "Exchange",
                "source_flag": "official",
                "importance_label": "medium",
                "importance_score": 40,
                "affected_markets": ["VN"],
            },
            {
                "headline": "Low quality",
                "summary": "Skip",
                "source": "Unknown",
                "source_flag": "unverified",
                "importance_label": "low",
                "importance_score": 10,
                "affected_markets": [],
            },
        ],
    }
    messages = format_digest_messages(snapshot)
    assert len(messages) == 1
    assert "Official &lt;update&gt;" in messages[0]
    assert "Important &amp; verified" in messages[0]
    assert "Low quality" not in messages[0]


def test_digest_service_send_test_uses_injected_client():
    mock_client = MagicMock()
    mock_client.send_message.return_value = TelegramSendResult(
        ok=True,
        message_id=888,
        chat_id="123456",
        status_code=200,
        attempts=1,
    )

    config = TelegramDigestConfig(token="test_token", chat_id="123456")
    service = TelegramDigestService(config, telegram_client=mock_client)
    res = service.send_test()

    assert res == {"status": "sent", "message_id": 888}
    mock_client.send_message.assert_called_once()
    args, kwargs = mock_client.send_message.call_args
    assert kwargs["chat_id"] == "123456"
    assert "Kết nối Telegram thành công" in kwargs["text"]
