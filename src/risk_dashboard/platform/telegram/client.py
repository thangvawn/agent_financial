"""Classified Telegram HTTP client with retry, backoff, and credential redaction."""

from __future__ import annotations

import logging
import time
from typing import Any
import requests

from risk_dashboard.platform.telegram.errors import TelegramClientError
from risk_dashboard.platform.telegram.models import TelegramSendResult

logger = logging.getLogger(__name__)


def redact_token(text: str, token: str) -> str:
    if not token or not text:
        return text
    return text.replace(token, "***REDACTED_BOT_TOKEN***")


class TelegramClient:
    def __init__(
        self,
        token: str,
        chat_id: str = "",
        max_attempts: int = 4,
        base_delay: float = 1.0,
        timeout: float = 10.0,
    ) -> None:
        self.token = token.strip()
        self.chat_id = chat_id.strip()
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.timeout = timeout
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.api_base = f"https://api.telegram.org/bot{self.token}"

    def send_message(
        self,
        *,
        text: str,
        chat_id: str | None = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
        reply_markup: dict[str, Any] | None = None,
    ) -> TelegramSendResult:
        """Sends formatted message to Telegram API returning a TelegramSendResult."""
        target_chat_id = (chat_id or self.chat_id).strip()
        if not self.token or not target_chat_id:
            raise TelegramClientError(
                "TELEGRAM_BOT_TOKEN or target chat_id is missing",
                is_retryable=False,
            )

        payload: dict[str, Any] = {
            "chat_id": target_chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                response = requests.post(self.api_url, json=payload, timeout=self.timeout)
                status_code = response.status_code

                if status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        msg_id = (data.get("result") or {}).get("message_id")
                        return TelegramSendResult(
                            ok=True,
                            message_id=msg_id,
                            chat_id=target_chat_id,
                            status_code=status_code,
                            attempts=attempt,
                            raw_response=data,
                        )

                # Handle HTTP 429 Rate Limit
                if status_code == 429:
                    try:
                        retry_after = response.json().get("parameters", {}).get(
                            "retry_after", self.base_delay * attempt
                        )
                    except Exception:
                        retry_after = self.base_delay * attempt
                    logger.warning(
                        f"Telegram API 429 Rate limited. Waiting {retry_after}s (Attempt {attempt}/{self.max_attempts})"
                    )
                    time.sleep(retry_after)
                    continue

                # Non-retryable errors: 400, 401, 403
                if status_code in (400, 401, 403):
                    raw_err = redact_token(response.text, self.token)
                    err_msg = f"Telegram Non-retryable error ({status_code}): {raw_err}"
                    logger.error(err_msg)
                    raise TelegramClientError(
                        err_msg, status_code=status_code, is_retryable=False
                    )

                # Retryable server errors (5xx)
                if status_code >= 500:
                    logger.warning(
                        f"Telegram Server error ({status_code}). Retrying attempt {attempt}/{self.max_attempts}..."
                    )
                    delay = self.base_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
                    continue

            except (requests.Timeout, requests.ConnectionError) as e:
                clean_err = redact_token(str(e), self.token)
                logger.warning(
                    f"Telegram Network error ({clean_err}). Retrying attempt {attempt}/{self.max_attempts}..."
                )
                last_error = e
                delay = self.base_delay * (2 ** (attempt - 1))
                time.sleep(delay)

        clean_last = redact_token(str(last_error), self.token)
        raise TelegramClientError(
            f"Telegram Delivery failed after {self.max_attempts} attempts: {clean_last}",
            is_retryable=True,
        )

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = True,
    ) -> bool:
        """Responds to inline button callback query."""
        if not self.token or not callback_query_id:
            return False

        payload: dict[str, Any] = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text

        try:
            resp = requests.post(f"{self.api_base}/answerCallbackQuery", json=payload, timeout=self.timeout)
            return resp.status_code == 200 and resp.json().get("ok", False)
        except Exception as e:
            logger.warning(f"Failed to answer callback query: {redact_token(str(e), self.token)}")
            return False

    def send_html_message(self, text: str) -> dict[str, Any]:
        """Legacy compatibility wrapper for Market Summary returning raw Telegram response dict."""
        result = self.send_message(text=text, parse_mode="HTML")
        return result.raw_response or {"ok": True, "result": {"message_id": result.message_id}}
