"""Exceptions for platform Telegram transport layer."""

from __future__ import annotations


class TelegramClientError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        is_retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.is_retryable = is_retryable
