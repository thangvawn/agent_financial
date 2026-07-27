"""Configuration loader for Telegram bot and channel endpoints."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    default_chat_id: str
    market_chat_id: str
    news_chat_id: str
    learn_chat_id: str
    bctc_chat_id: str

    @classmethod
    def from_env(cls) -> TelegramConfig | None:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        default_chat_id = (
            os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "").strip()
            or os.getenv("TELEGRAM_CHAT_ID", "").strip()
        )
        if not token or not default_chat_id:
            return None

        market_chat_id = (
            os.getenv("TELEGRAM_MARKET_CHAT_ID", "").strip() or default_chat_id
        )
        news_chat_id = os.getenv("TELEGRAM_NEWS_CHAT_ID", "").strip() or default_chat_id
        learn_chat_id = (
            os.getenv("TELEGRAM_LEARN_CHAT_ID", "").strip() or default_chat_id
        )
        bctc_chat_id = os.getenv("TELEGRAM_BCTC_CHAT_ID", "").strip() or default_chat_id

        return cls(
            bot_token=token,
            default_chat_id=default_chat_id,
            market_chat_id=market_chat_id,
            news_chat_id=news_chat_id,
            learn_chat_id=learn_chat_id,
            bctc_chat_id=bctc_chat_id,
        )

    def get_chat_id_for_domain(self, domain: str) -> str:
        domain_lower = domain.lower()
        if domain_lower == "market":
            return self.market_chat_id
        if domain_lower == "news":
            return self.news_chat_id
        if domain_lower == "learn":
            return self.learn_chat_id
        if domain_lower == "bctc":
            return self.bctc_chat_id
        return self.default_chat_id
