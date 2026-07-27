"""On-demand interactive query handler for Financial Statements (BCTC) Telegram requests."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

from risk_dashboard.platform.telegram.command_parser import ParsedCommand
from risk_dashboard.platform.telegram.formatter import escape_html, safe_bold, safe_italic
from risk_dashboard.platform.telegram.section_packer import pack_sections

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FinancialReportSnapshot:
    ticker: str
    report_period: str
    report_type: str
    revenue_bil: float | None
    revenue_yoy_pct: float | None
    net_income_bil: float | None
    net_income_yoy_pct: float | None
    gross_margin_pct: float | None
    roe_pct: float | None
    roa_pct: float | None
    cfo_to_net_income: float | None
    debt_to_equity: float | None
    warnings: List[str]
    source: str = "BCTC Công bố"


MOCK_BCTC_DATABASE: dict[str, FinancialReportSnapshot] = {
    "FPT": FinancialReportSnapshot(
        ticker="FPT",
        report_period="Q2/2026",
        report_type="Quý",
        revenue_bil=16200.0,
        revenue_yoy_pct=20.5,
        net_income_bil=2450.0,
        net_income_yoy_pct=22.8,
        gross_margin_pct=28.4,
        roe_pct=25.2,
        roa_pct=11.5,
        cfo_to_net_income=1.15,
        debt_to_equity=0.45,
        warnings=[
            "Tỷ lệ Nợ/VCSH ở mức an toàn (0.45x)",
            "Chất lượng dòng tiền CFO/LNST tốt (1.15x)",
        ],
    ),
    "HPG": FinancialReportSnapshot(
        ticker="HPG",
        report_period="Q2/2026",
        report_type="Quý",
        revenue_bil=38500.0,
        revenue_yoy_pct=15.2,
        net_income_bil=3200.0,
        net_income_yoy_pct=45.0,
        gross_margin_pct=16.8,
        roe_pct=14.1,
        roa_pct=7.2,
        cfo_to_net_income=0.88,
        debt_to_equity=0.72,
        warnings=[
            "CFO/LNST < 1.0 (0.88x) — Cần theo dõi biến động hàng tồn kho",
        ],
    ),
    "VNM": FinancialReportSnapshot(
        ticker="VNM",
        report_period="Q2/2026",
        report_type="Quý",
        revenue_bil=16800.0,
        revenue_yoy_pct=4.1,
        net_income_bil=2600.0,
        net_income_yoy_pct=6.5,
        gross_margin_pct=41.2,
        roe_pct=28.5,
        roa_pct=18.0,
        cfo_to_net_income=1.20,
        debt_to_equity=0.25,
        warnings=[
            "Tỷ lệ Nợ/VCSH thấp (0.25x), đòn bẩy an toàn",
            "Tăng trưởng doanh thu duy trì mức vừa phải (+4.1% YoY)",
        ],
    ),
}


class FinancialsTelegramQueryHandler:
    def __init__(self, database: dict[str, FinancialReportSnapshot] | None = None) -> None:
        self.database = database or MOCK_BCTC_DATABASE

    def handle(self, cmd: ParsedCommand) -> List[str]:
        """Handles /bctc <ticker> [period] commands."""
        if not cmd.args:
            return [
                "⚠️ <b>Vui lòng cung cấp mã cổ phiếu.</b>\n\n"
                "Cú pháp hỗ trợ:\n"
                "• <code>/bctc FPT</code> — Xem BCTC mới nhất của FPT\n"
                "• <code>/bctc HPG Q2-2026</code> — Xem BCTC quý cụ thể\n"
                "• <code>/bctc VNM annual</code> — Xem BCTC năm mới nhất"
            ]

        raw_ticker = cmd.args[0].strip()

        # Validate ticker format (3-4 alphanumeric characters)
        if not raw_ticker.isalnum() or len(raw_ticker) not in {3, 4}:
            clean_ticker = escape_html(raw_ticker)
            return [f"⚠️ <b>Mã cổ phiếu không hợp lệ:</b> <code>{clean_ticker}</code>"]

        ticker = raw_ticker.upper()
        logger.info(f"Handling on-demand /bctc query for ticker {ticker} in chat {cmd.chat_id}")

        snapshot = self.database.get(ticker)
        if not snapshot:
            return [
                f"ℹ️ <b>Không tìm thấy dữ liệu BCTC cho mã</b> <code>{escape_html(ticker)}</code>.\n"
                "Hệ thống hiện hỗ trợ tra cứu các mã trong VN30/Watchlist (VD: FPT, HPG, VNM)."
            ]

        sections = render_financial_snapshot(snapshot)
        return pack_sections(sections)


def format_growth(val: float | None) -> str:
    if val is None:
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"


def render_financial_snapshot(snapshot: FinancialReportSnapshot) -> List[str]:
    ticker_esc = escape_html(snapshot.ticker)
    period_esc = escape_html(snapshot.report_period)
    type_esc = escape_html(snapshot.report_type)

    rev_str = f"{snapshot.revenue_bil:,.1f} tỷ" if snapshot.revenue_bil is not None else "N/A"
    rev_yoy = format_growth(snapshot.revenue_yoy_pct)

    ni_str = f"{snapshot.net_income_bil:,.1f} tỷ" if snapshot.net_income_bil is not None else "N/A"
    ni_yoy = format_growth(snapshot.net_income_yoy_pct)

    gm_str = f"{snapshot.gross_margin_pct:.1f}%" if snapshot.gross_margin_pct is not None else "N/A"
    roe_str = f"{snapshot.roe_pct:.1f}%" if snapshot.roe_pct is not None else "N/A"
    cfo_str = f"{snapshot.cfo_to_net_income:.2f}x" if snapshot.cfo_to_net_income is not None else "N/A"
    debt_str = f"{snapshot.debt_to_equity:.2f}x" if snapshot.debt_to_equity is not None else "N/A"

    lines = [
        f"📑 {safe_bold(f'BÁO CÁO TÀI CHÍNH: {ticker_esc}')} ({period_esc} - {type_esc})\n",
        f"• <b>Doanh thu:</b> {rev_str} <i>(YoY: {rev_yoy})</i>",
        f"• <b>LNST:</b> {ni_str} <i>(YoY: {ni_yoy})</i>",
        f"• <b>Biên lợi nhuận gộp:</b> {gm_str}",
        f"• <b>ROE:</b> {roe_str}",
        f"• <b>CFO / LNST:</b> {cfo_str}",
        f"• <b>Nợ vay / VCSH:</b> {debt_str}\n",
    ]

    if snapshot.warnings:
        warn_items = "\n".join([f"• {escape_html(w)}" for w in snapshot.warnings])
        lines.append(f"🔍 <b>ĐÁNH GIÁ & CẢNH BÁO TÀI CHÍNH:</b>\n{warn_items}\n")

    lines.append(
        f"⏱ <i>Nguồn: {escape_html(snapshot.source)}</i>\n"
        "⚠️ <i>Nội dung mang tính thông tin tham khảo, không phải khuyến nghị đầu tư.</i>"
    )

    return ["\n".join(lines)]
