"""Telegram delivery for trusted News Intelligence highlight snapshots."""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

import requests

from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService
from risk_dashboard.modules.news_intelligence.application.translation import NewsTranslator
from risk_dashboard.platform.database import open_app_state_db

TELEGRAM_MESSAGE_LIMIT = 4096
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


@dataclass(frozen=True)
class TelegramDigestConfig:
    token: str
    chat_id: str
    daily_time: str = "18:30"
    weekly_time: str = "19:00"
    monthly_time: str = "19:30"
    weekly_weekday: int = 6
    max_items: int = 6

    @classmethod
    def from_env(cls) -> "TelegramDigestConfig | None":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat_id:
            return None
        return cls(
            token=token,
            chat_id=chat_id,
            daily_time=os.getenv("TELEGRAM_DAILY_TIME", "18:30").strip(),
            weekly_time=os.getenv("TELEGRAM_WEEKLY_TIME", "19:00").strip(),
            monthly_time=os.getenv("TELEGRAM_MONTHLY_TIME", "19:30").strip(),
            weekly_weekday=int(os.getenv("TELEGRAM_WEEKLY_WEEKDAY", "6")),
            max_items=max(1, min(int(os.getenv("TELEGRAM_DIGEST_MAX_ITEMS", "6")), 10)),
        )


def due_periods(now: datetime, config: TelegramDigestConfig) -> list[str]:
    local = now.astimezone(LOCAL_TZ)
    current_time = local.strftime("%H:%M")
    periods: list[str] = []
    if current_time == config.daily_time:
        periods.append("day")
    if local.weekday() == config.weekly_weekday and current_time == config.weekly_time:
        periods.append("week")
    tomorrow = local.date().fromordinal(local.date().toordinal() + 1)
    if tomorrow.month != local.month and current_time == config.monthly_time:
        periods.append("month")
    return periods


class TelegramDigestService:
    def __init__(
        self,
        config: TelegramDigestConfig,
        *,
        news_service: NewsIntelligenceService | None = None,
        translator: NewsTranslator | None = None,
        post: Callable[..., Any] = requests.post,
    ) -> None:
        self.config = config
        self.news_service = news_service or NewsIntelligenceService()
        self.translator = translator or NewsTranslator()
        self.post = post

    def send_digest(self, period: str, *, force: bool = False) -> dict[str, Any]:
        if period not in {"day", "week", "month"}:
            raise ValueError("period must be day, week, or month")
        snapshot = self.news_service.get_highlights(
            period=period,
            limit=self.config.max_items,
            force=force,
        )
        delivery_key = f"{period}:{snapshot['period_key']}:{self.config.chat_id}"
        if not force and self._already_delivered(delivery_key):
            return {"status": "skipped", "reason": "already_delivered", "delivery_key": delivery_key}

        messages = format_digest_messages(snapshot, translator=self.translator)
        if not messages:
            return {"status": "skipped", "reason": "no_qualified_news", "delivery_key": delivery_key}
        message_ids = [self._send_message(message) for message in messages]
        self._record_delivery(delivery_key, period, snapshot["period_key"], message_ids)
        return {
            "status": "sent",
            "delivery_key": delivery_key,
            "message_count": len(messages),
            "item_count": snapshot["count"],
        }

    def send_test(self) -> dict[str, Any]:
        message_id = self._send_message(
            "<b>Northstar News Intelligence</b>\n\n"
            "Kết nối Telegram thành công. Bot đã sẵn sàng gửi bản tin tự động."
        )
        return {"status": "sent", "message_id": message_id}

    def _send_message(self, text: str) -> int | None:
        try:
            response = self.post(
                f"https://api.telegram.org/bot{self.config.token}/sendMessage",
                json={
                    "chat_id": self.config.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=20,
            )
            payload = response.json()
        except (requests.RequestException, ValueError):
            raise RuntimeError("Telegram request failed; token was not logged") from None
        if response.status_code >= 400:
            raise RuntimeError(
                f"Telegram API returned HTTP {response.status_code}: "
                f"{payload.get('description', 'request rejected')}"
            )
        if not payload.get("ok"):
            raise RuntimeError(payload.get("description") or "Telegram rejected the message")
        return (payload.get("result") or {}).get("message_id")

    @staticmethod
    def _already_delivered(delivery_key: str) -> bool:
        with open_app_state_db() as conn:
            row = conn.execute(
                "SELECT 1 FROM telegram_news_deliveries WHERE delivery_key = ?",
                (delivery_key,),
            ).fetchone()
        return row is not None

    def _record_delivery(
        self,
        delivery_key: str,
        period: str,
        period_key: str,
        message_ids: list[int | None],
    ) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO telegram_news_deliveries (
                  delivery_key, period_kind, period_key, chat_id,
                  telegram_message_ids, delivered_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    delivery_key,
                    period,
                    period_key,
                    self.config.chat_id,
                    ",".join(str(item) for item in message_ids if item is not None),
                    datetime.now(LOCAL_TZ).isoformat(),
                ),
            )


def format_digest_messages(
    snapshot: dict[str, Any],
    *,
    translator: NewsTranslator | None = None,
) -> list[str]:
    items = [
        item for item in snapshot.get("items", [])
        if item.get("source_flag") == "official"
        or item.get("importance_label") in {"critical", "high"}
        or int(item.get("importance_score") or 0) >= 60
    ]
    if not items:
        return []
    labels = {"day": "BẢN TIN NGÀY", "week": "TỔNG HỢP TUẦN", "month": "TỔNG HỢP THÁNG"}
    header = (
        f"<b>{labels.get(snapshot.get('period'), 'BẢN TIN')}</b>\n"
        f"<code>{html.escape(str(snapshot.get('period_key', '')))}</code>\n"
        "Nguồn đã sàng lọc · ưu tiên tin quan trọng\n"
    )
    blocks = []
    for index, item in enumerate(items, 1):
        translation = translator.translate_item(item) if translator else {}
        headline_original = str(item.get("headline") or "Không có tiêu đề")[:350]
        headline_vi = str(translation.get("headline_vi") or headline_original)[:350]
        summary = str(
            translation.get("summary_vi")
            or item.get("summary")
            or item.get("why_it_matters")
            or ""
        )[:900]
        headline = html.escape(headline_vi)
        if headline_vi.strip() != headline_original.strip():
            headline += f" <i>({html.escape(headline_original)})</i>"
        summary = html.escape(summary)
        source = html.escape(str(item.get("source") or "Nguồn chưa xác định"))
        source_url = html.escape(str(item.get("url") or ""), quote=True)
        importance = html.escape(str(item.get("importance_label") or ""))
        markets = ", ".join(str(value) for value in (item.get("affected_markets") or [])[:3])
        meta = f"{source} · {importance.upper()}"
        if markets:
            meta += f" · {html.escape(markets)}"
        source_line = f'<a href="{source_url}">Đọc nguồn gốc</a>' if source_url else ""
        source_suffix = f"\n{source_line}" if source_line else ""
        blocks.append(
            f"\n<b>{index}. {headline}</b>\n{summary}\n<i>{meta}</i>"
            f"{source_suffix}"
        )

    messages: list[str] = []
    current = header
    for block in blocks:
        if len(current) + len(block) > TELEGRAM_MESSAGE_LIMIT - 80:
            messages.append(current)
            current = "<b>Tiếp theo</b>\n" + block
        else:
            current += block
    if current.strip():
        current += "\n\n<i>Nội dung AI hỗ trợ tóm tắt, không phải khuyến nghị đầu tư.</i>"
        messages.append(current)
    return messages
