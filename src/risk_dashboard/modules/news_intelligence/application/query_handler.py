"""On-demand interactive query handler for News Intelligence Telegram requests."""

from __future__ import annotations

import logging
from typing import List, Any
from zoneinfo import ZoneInfo

from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService
from risk_dashboard.modules.news_intelligence.application.translation import NewsTranslator
from risk_dashboard.platform.telegram.command_parser import ParsedCommand
from risk_dashboard.platform.telegram.formatter import escape_html, safe_bold, safe_italic
from risk_dashboard.platform.telegram.section_packer import pack_sections

logger = logging.getLogger(__name__)
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class NewsTelegramQueryHandler:
    def __init__(
        self,
        news_service: NewsIntelligenceService | None = None,
        translator: NewsTranslator | None = None,
    ) -> None:
        self.news_service = news_service or NewsIntelligenceService()
        self.translator = translator or NewsTranslator()

    def handle(self, cmd: ParsedCommand) -> List[str]:
        """Handles /news, /news <topic>, /news <ticker> on-demand queries."""
        query: str | None = None
        if cmd.args:
            raw_arg = " ".join(cmd.args).strip()
            # Normalize ticker symbol if single 3-4 letter word
            if len(raw_arg) in {3, 4} and raw_arg.isalpha():
                query = raw_arg.upper()
            else:
                query = raw_arg.lower()

        logger.info(f"Handling on-demand /news query for query='{query}' in chat {cmd.chat_id}")
        try:
            feed = self.news_service.get_feed(
                query=query,
                limit=5,
                time_range_hours=24,
            )
            articles = feed.get("articles", [])
            if not articles:
                filter_text = f" cho từ khóa '<b>{escape_html(query)}</b>'" if query else ""
                return [
                    f"ℹ️ <b>Không tìm thấy tin tức phù hợp{filter_text} trong 24 giờ gần nhất.</b>"
                ]

            sections = format_news_query_sections(articles, query=query, translator=self.translator)
            chunks = pack_sections(sections)
            return chunks
        except Exception as e:
            logger.error(f"Failed to execute on-demand news query: {e}")
            return [
                "⚠️ <b>Không thể lấy thông tin tin tức lúc này.</b>\n"
                "Hệ thống đang kết nối dữ liệu gián đoạn. Vui lòng thử lại sau."
            ]


def format_news_query_sections(
    articles: List[dict[str, Any]],
    query: str | None = None,
    translator: NewsTranslator | None = None,
) -> List[str]:
    header_title = f"TIN TỨC: {query.upper()}" if query else "DIỄN BIẾN TIN TỨC TÀI CHÍNH"
    header = (
        f"📰 {safe_bold(header_title)}\n"
        "<i>Cập nhật trong 24 giờ qua · Nguồn đã xác thực</i>\n"
    )

    blocks: List[str] = [header]
    for idx, item in enumerate(articles[:5], 1):
        translation = translator.translate_item(item) if translator else {}
        headline_orig = str(item.get("headline") or "Không có tiêu đề")[:300]
        headline_vi = str(translation.get("headline_vi") or headline_orig)[:300]
        summary = str(
            translation.get("summary_vi")
            or item.get("summary")
            or item.get("why_it_matters")
            or ""
        )[:500]

        headline_escaped = escape_html(headline_vi)
        summary_escaped = escape_html(summary)
        source = escape_html(str(item.get("source") or "Nguồn tin"))
        importance = escape_html(str(item.get("importance_label") or "NORMAL")).upper()
        url = str(item.get("url") or "").strip()

        source_line = f'<a href="{escape_html(url)}">Đọc bài viết gốc</a>' if (url and url.startswith("http")) else ""
        meta = f"{source} · {importance}"
        suffix = f"\n{source_line}" if source_line else ""

        blocks.append(
            f"<b>{idx}. {headline_escaped}</b>\n"
            f"{summary_escaped}\n"
            f"<i>{meta}</i>{suffix}"
        )

    return blocks
