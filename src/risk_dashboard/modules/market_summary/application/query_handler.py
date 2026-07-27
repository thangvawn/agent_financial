"""On-demand interactive query handler for Market Summary Telegram requests."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

from risk_dashboard.modules.market_summary.application.summarizer import MarketSummarizer
from risk_dashboard.modules.market_summary.infrastructure.data_provider import (
    MarketDataProvider,
    VnstockMarketDataProvider,
)
from risk_dashboard.modules.market_summary.presentation.telegram_renderer import (
    pack_sections,
    render_report_sections,
)
from risk_dashboard.platform.telegram.command_parser import ParsedCommand

logger = logging.getLogger(__name__)
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class MarketTelegramQueryHandler:
    def __init__(
        self,
        data_provider: MarketDataProvider | None = None,
        summarizer: MarketSummarizer | None = None,
    ) -> None:
        self.data_provider = data_provider or VnstockMarketDataProvider()
        self.summarizer = summarizer or MarketSummarizer(self.data_provider)

    def handle(self, cmd: ParsedCommand) -> List[str]:
        """Handles /market command on-demand without mutating cron delivery deduplication state."""
        mode = "analytical"
        if cmd.args and cmd.args[0].lower() in {"fast", "analytical"}:
            mode = cmd.args[0].lower()

        logger.info(f"Handling on-demand /market query in {mode} mode for chat {cmd.chat_id}")
        try:
            today = datetime.now(LOCAL_TZ).date()
            report = self.summarizer.build_report(report_date=today, mode=mode)
            sections = render_report_sections(report, mode=mode)
            chunks = pack_sections(sections)
            return chunks
        except Exception as e:
            logger.error(f"Failed to execute on-demand market query: {e}")
            return [
                "⚠️ <b>Không thể lấy dữ liệu thị trường lúc này.</b>\n"
                "Hệ thống đang cập nhật hoặc kết nối dữ liệu gián đoạn. Vui lòng thử lại sau."
            ]
