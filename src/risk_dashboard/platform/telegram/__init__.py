"""Platform Telegram module."""

from __future__ import annotations

from risk_dashboard.platform.telegram.access_control import TelegramAccessControl
from risk_dashboard.platform.telegram.client import TelegramClient, redact_token
from risk_dashboard.platform.telegram.command_parser import ParsedCommand, parse_update
from risk_dashboard.platform.telegram.command_router import TelegramCommandRouter
from risk_dashboard.platform.telegram.config import TelegramConfig
from risk_dashboard.platform.telegram.errors import TelegramClientError
from risk_dashboard.platform.telegram.formatter import (
    escape_html,
    safe_bold,
    safe_italic,
    truncate_text,
)
from risk_dashboard.platform.telegram.models import TelegramSendResult
from risk_dashboard.platform.telegram.section_packer import pack_sections
from risk_dashboard.platform.telegram.update_receiver import TelegramUpdateReceiver
from risk_dashboard.platform.telegram.update_repository import TelegramUpdateRepository

__all__ = [
    "ParsedCommand",
    "TelegramAccessControl",
    "TelegramClient",
    "TelegramClientError",
    "TelegramCommandRouter",
    "TelegramConfig",
    "TelegramSendResult",
    "TelegramUpdateReceiver",
    "TelegramUpdateRepository",
    "escape_html",
    "pack_sections",
    "parse_update",
    "redact_token",
    "safe_bold",
    "safe_italic",
    "truncate_text",
]
