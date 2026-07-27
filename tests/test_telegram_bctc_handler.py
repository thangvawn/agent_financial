"""Unit and integration tests for Financial Statements (BCTC) Module (Phase T5)."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock
import pytest

from risk_dashboard.cli.telegram_bot_daemon import TelegramBotDaemon
from risk_dashboard.modules.financials_product.application.query_handler import (
    FinancialReportSnapshot,
    FinancialsTelegramQueryHandler,
)
from risk_dashboard.modules.financials_product.infrastructure.delivery_repository import FinancialsDeliveryRepository
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


def test_bctc_query_handler_no_args():
    handler = FinancialsTelegramQueryHandler()
    cmd = parse_update({"update_id": 1, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/bctc"}})
    res = handler.handle(cmd)

    assert len(res) == 1
    assert "Vui lòng cung cấp mã cổ phiếu" in res[0]


def test_bctc_query_handler_valid_ticker_and_normalization():
    handler = FinancialsTelegramQueryHandler()
    cmd = parse_update({"update_id": 2, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/bctc fpt"}})
    res = handler.handle(cmd)

    assert len(res) == 1
    assert "BÁO CÁO TÀI CHÍNH: FPT" in res[0]
    assert "Doanh thu:" in res[0]
    assert "LNST:" in res[0]
    assert "ROE:" in res[0]
    assert "Nội dung mang tính thông tin tham khảo" in res[0]


def test_bctc_query_handler_invalid_ticker():
    handler = FinancialsTelegramQueryHandler()
    cmd = parse_update({"update_id": 3, "message": {"chat": {"id": 100}, "from": {"id": 200}, "text": "/bctc INVALID!"}})
    res = handler.handle(cmd)

    assert len(res) == 1
    assert "Mã cổ phiếu không hợp lệ" in res[0]


def test_financials_delivery_repository(in_memory_db):
    repo = FinancialsDeliveryRepository(db_factory=in_memory_db)
    assert repo.is_delivered("FPT", "Q2/2026", chat_id="100") is False

    repo.record_delivery("FPT", "Q2/2026", chat_id="100", telegram_message_id=55)
    assert repo.is_delivered("FPT", "Q2/2026", chat_id="100") is True


def test_bctc_bot_daemon_integration(in_memory_db):
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
        "update_id": 1234,
        "message": {
            "chat": {"id": 100},
            "from": {"id": 456},
            "text": "/bctc FPT",
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
    assert repository.get_next_offset() == 1235
    assert repository.is_processed(1234) is True
    mock_client.send_message.assert_called()
    called_text = mock_client.send_message.call_args[1]["text"]
    assert "BÁO CÁO TÀI CHÍNH: FPT" in called_text
