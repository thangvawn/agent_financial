"""Models for platform Telegram transport layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TelegramSendResult:
    ok: bool
    message_id: int | None
    chat_id: str
    status_code: int
    attempts: int
    raw_response: dict[str, Any] | None = None
