"""Backward compatibility adapter re-exporting platform TelegramClient."""

from __future__ import annotations

from risk_dashboard.platform.telegram.client import (
    TelegramClient,
    redact_token,
)
from risk_dashboard.platform.telegram.errors import TelegramClientError
from risk_dashboard.platform.telegram.models import TelegramSendResult

__all__ = [
    "TelegramClient",
    "TelegramClientError",
    "TelegramSendResult",
    "redact_token",
]
