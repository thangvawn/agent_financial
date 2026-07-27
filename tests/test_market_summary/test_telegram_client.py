"""Unit tests for TelegramClient and credential redaction."""

from __future__ import annotations

import pytest
from risk_dashboard.modules.market_summary.infrastructure.telegram_client import (
    TelegramClient,
    TelegramClientError,
    redact_token,
)


def test_redact_token():
    token = "712345678:ABCdefGhIJKlmNoPQRsTUVwxyZ"
    text = f"Failed to POST to https://api.telegram.org/bot{token}/sendMessage with status 400"
    clean = redact_token(text, token)
    assert token not in clean
    assert "***REDACTED_BOT_TOKEN***" in clean


def test_telegram_client_missing_credentials():
    client = TelegramClient(token="", chat_id="")
    with pytest.raises(TelegramClientError) as exc_info:
        client.send_html_message("Test message")
    assert exc_info.value.is_retryable is False
