from __future__ import annotations

from risk_dashboard.schemas.financials import FinancialPeriodData


def extract_ticker(report_id: str) -> str:
    return report_id.split(":")[-1].upper()


def get_line_item_val(period_data: FinancialPeriodData | None, key: str) -> float | None:
    if period_data is None:
        return None
    if hasattr(period_data, key):
        val = getattr(period_data, key)
        if isinstance(val, (int, float)):
            return float(val)
    if key == "cogs" and period_data.revenue is not None and period_data.gross_profit is not None:
        return float(period_data.revenue - period_data.gross_profit)
    if key == "net_profit" and period_data.net_income is not None:
        return float(period_data.net_income)
    return None

