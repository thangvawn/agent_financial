"""Unit and integration tests for Telegram Bot Core (Phase T2)."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch
import pytest

from risk_dashboard.cli.telegram_bot_daemon import TelegramBotDaemon
from risk_dashboard.modules.market_summary.infrastructure.data_provider import FixtureMarketDataProvider
from risk_dashboard.platform.telegram.access_control import TelegramAccessControl
from risk_dashboard.platform.telegram.command_parser import parse_update
from risk_dashboard.platform.telegram.command_router import TelegramCommandRouter
from risk_dashboard.platform.telegram.config import TelegramConfig
from risk_dashboard.platform.telegram.models import TelegramSendResult
from risk_dashboard.platform.telegram.update_repository import TelegramUpdateRepository


@pytest.fixture
def in_memory_db():
    conn = sqlite3.connect(":memory:")
    yield lambda: conn
    conn.close()


def test_update_repository(in_memory_db):
    repo = TelegramUpdateRepository(db_factory=in_memory_db)
    assert repo.get_next_offset() == 0
    assert repo.is_processed(100) is False

    repo.record_received(100, chat_id="123", user_id="456", command="/market")
    assert repo.get_next_offset() == 101

    repo.mark_status(100, "processed")
    assert repo.is_processed(100) is True


def test_access_control():
    ac = TelegramAccessControl(
        allowed_chat_ids={"100", "200"},
        admin_user_ids={"999"},
    )
    # Admin allowed for everything
    assert ac.check_access("/status", chat_id="555", user_id="999") is True
    assert ac.check_access("/market", chat_id="555", user_id="999") is True

    # Non-admin denied for /status
    assert ac.check_access("/status", chat_id="100", user_id="456") is False

    # Allowed chat allowed for /market and /help
    assert ac.check_access("/market", chat_id="100", user_id="456") is True
    assert ac.check_access("/help", chat_id="200", user_id="456") is True

    # Unauthorized chat denied
    assert ac.check_access("/market", chat_id="9999", user_id="456") is False


def test_command_parser():
    raw_update = {
        "update_id": 42,
        "message": {
            "chat": {"id": 100200},
            "from": {"id": 300400},
            "text": "/market@NorthstarBot analytical",
        },
    }
    parsed = parse_update(raw_update)
    assert parsed is not None
    assert parsed.update_id == 42
    assert parsed.chat_id == "100200"
    assert parsed.user_id == "300400"
    assert parsed.command == "/market"
    assert parsed.args == ["analytical"]


def test_command_router_defaults():
    router = TelegramCommandRouter()

    # /help
    p_help = parse_update({"update_id": 1, "message": {"chat": {"id": 1}, "from": {"id": 1}, "text": "/help"}})
    res_help, _ = router.dispatch(p_help)
    assert "Northstar Finance Lab" in res_help[0]

    # /status
    p_status = parse_update({"update_id": 2, "message": {"chat": {"id": 1}, "from": {"id": 1}, "text": "/status"}})
    res_status, _ = router.dispatch(p_status)
    assert "BÁO CÁO TRẠNG THÁI HỆ THỐNG" in res_status[0]

    # Unknown command
    p_unknown = parse_update({"update_id": 3, "message": {"chat": {"id": 1}, "from": {"id": 1}, "text": "/unknown"}})
    res_unknown, _ = router.dispatch(p_unknown)
    assert "Lệnh không hợp lệ" in res_unknown[0]


def test_bot_daemon_end_to_end_integration(in_memory_db):
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
        "update_id": 777,
        "message": {
            "chat": {"id": 100},
            "from": {"id": 456},
            "text": "/market",
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

    # Replace market query handler provider with fixture provider for offline deterministic output
    with patch(
        "risk_dashboard.modules.market_summary.application.query_handler.VnstockMarketDataProvider",
        FixtureMarketDataProvider,
    ):
        processed = daemon.run_once()

    assert processed == 1
    assert repository.get_next_offset() == 778
    assert repository.is_processed(777) is True

    # Verify Telegram client was invoked with market report HTML
    mock_client.send_message.assert_called()
    called_text = mock_client.send_message.call_args[1]["text"]
    assert "TỔNG KẾT THỊ TRƯỜNG" in called_text
