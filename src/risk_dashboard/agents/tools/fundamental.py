"""
Fundamental Tool — Kéo dữ liệu BCTC thật từ vnstock API.
Không mock data, không dictionary tĩnh.
"""
from __future__ import annotations

from langchain_core.tools import tool

from risk_dashboard.data.financials import FinancialDataError, get_financial_dataset
from risk_dashboard.quant.financial_analysis import analyze_financial_dataset


@tool
def get_financial_metrics(ticker: str) -> dict:
    """Đọc báo cáo tài chính THẬT (P/E, P/B, ROE, lợi nhuận) của một mã cổ phiếu.
    Input: ticker (ví dụ 'FPT', 'VCB', 'HPG').
    Trả về dict chứa các chỉ số tài chính chính."""
    try:
        dataset = get_financial_dataset(ticker)
        analysis = analyze_financial_dataset(dataset)
        return {
            "ticker": analysis.ticker,
            "latest_period": analysis.latest_period,
            "source": analysis.source,
            "highlights": analysis.highlights,
            "flags": [flag.model_dump() for flag in analysis.flags],
            "summary": analysis.summary.model_dump(),
        }
    except FinancialDataError as exc:
        return {
            "error": exc.message,
            "hint": exc.hint,
            "notes": exc.notes,
        }
