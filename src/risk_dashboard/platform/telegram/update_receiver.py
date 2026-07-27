"""Telegram update receiver using long-polling with webhook conflict check."""

from __future__ import annotations

import logging
from typing import Any, List
import requests

from risk_dashboard.platform.telegram.client import redact_token
from risk_dashboard.platform.telegram.errors import TelegramClientError

logger = logging.getLogger(__name__)


class TelegramUpdateReceiver:
    def __init__(
        self,
        token: str,
        timeout: float = 10.0,
    ) -> None:
        self.token = token.strip()
        self.timeout = timeout
        self.api_base = f"https://api.telegram.org/bot{self.token}"

    def check_webhook_conflict(self) -> None:
        """Verifies no webhook is active before starting polling."""
        if not self.token:
            raise TelegramClientError("TELEGRAM_BOT_TOKEN is missing", is_retryable=False)
        try:
            resp = requests.get(f"{self.api_base}/getWebhookInfo", timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") and (data.get("result") or {}).get("url"):
                    webhook_url = data["result"]["url"]
                    raise TelegramClientError(
                        f"Webhook active ({webhook_url}). Cannot start polling daemon.",
                        is_retryable=False,
                    )
        except requests.RequestException as e:
            logger.warning(f"Could not check webhook info: {redact_token(str(e), self.token)}")

    def get_updates(self, offset: int = 0, poll_timeout: int = 10) -> List[dict[str, Any]]:
        """Polls Telegram for new updates using offset."""
        if not self.token:
            return []

        payload = {
            "offset": offset,
            "timeout": poll_timeout,
            "allowed_updates": ["message", "callback_query"],
        }
        try:
            resp = requests.post(
                f"{self.api_base}/getUpdates",
                json=payload,
                timeout=poll_timeout + 5,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return data.get("result", [])
            elif resp.status_code in (401, 403, 400):
                clean_err = redact_token(resp.text, self.token)
                logger.error(f"Telegram getUpdates Non-retryable error ({resp.status_code}): {clean_err}")
                raise TelegramClientError(
                    f"Telegram getUpdates failed ({resp.status_code}): {clean_err}",
                    status_code=resp.status_code,
                    is_retryable=False,
                )
        except requests.RequestException as e:
            clean_err = redact_token(str(e), self.token)
            logger.warning(f"Telegram getUpdates Network error: {clean_err}")

        return []
