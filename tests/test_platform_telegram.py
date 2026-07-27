"""Unit tests for platform Telegram transport layer."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest

from risk_dashboard.platform.telegram import (
    TelegramClient,
    TelegramClientError,
    TelegramConfig,
    TelegramSendResult,
    escape_html,
    pack_sections,
    redact_token,
    safe_bold,
    safe_italic,
    truncate_text,
)


def test_redact_token():
    token = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
    text = f"Failed to POST to https://api.telegram.org/bot{token}/sendMessage"
    clean = redact_token(text, token)
    assert token not in clean
    assert "***REDACTED_BOT_TOKEN***" in clean


def test_telegram_config_fallback(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    monkeypatch.setenv("TELEGRAM_DEFAULT_CHAT_ID", "100200300")
    monkeypatch.delenv("TELEGRAM_MARKET_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_NEWS_CHAT_ID", raising=False)

    config = TelegramConfig.from_env()
    assert config is not None
    assert config.bot_token == "test_bot_token"
    assert config.default_chat_id == "100200300"
    assert config.get_chat_id_for_domain("market") == "100200300"
    assert config.get_chat_id_for_domain("news") == "100200300"


def test_telegram_config_missing_env(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_DEFAULT_CHAT_ID", raising=False)
    assert TelegramConfig.from_env() is None


def test_telegram_client_missing_credentials():
    client = TelegramClient(token="", chat_id="")
    with pytest.raises(TelegramClientError) as exc_info:
        client.send_message(text="Hello")
    assert exc_info.value.is_retryable is False


@patch("requests.post")
def test_telegram_client_send_message_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 999}}
    mock_post.return_value = mock_response

    client = TelegramClient(token="valid_token", chat_id="12345")
    result = client.send_message(text="Hello world")

    assert isinstance(result, TelegramSendResult)
    assert result.ok is True
    assert result.message_id == 999
    assert result.chat_id == "12345"
    assert result.attempts == 1


def test_html_primitives():
    assert escape_html("A & B < C") == "A &amp; B &lt; C"
    assert safe_bold("Header") == "<b>Header</b>"
    assert safe_italic("Note") == "<i>Note</i>"
    assert truncate_text("Long string", 8) == "Long ..."


def test_pack_sections():
    sections = ["Section 1", "Section 2"]
    packed = pack_sections(sections, max_chars=100)
    assert len(packed) == 1
    assert "Section 1\n\nSection 2" in packed[0]
