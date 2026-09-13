from __future__ import annotations

from risk_dashboard.schemas.financials import FinancialPeriodData


def extract_ticker(report_id: str) -> str:
    return report_id.split(":")[-1].upper()


def get_line_item_val(period_data: FinancialPeriodData | None, key: str) -> float | None:
    if period_data is None:
        return None
    normalized_key = key.lower().strip()
    if hasattr(period_data, normalized_key):
        val = getattr(period_data, normalized_key)
        if isinstance(val, (int, float)):
            return float(val)
    if normalized_key in ("net_profit", "profit"):
        return float(period_data.net_income) if period_data.net_income is not None else None
    if normalized_key in ("assets", "asset"):
        return float(period_data.total_assets) if period_data.total_assets is not None else None
    if normalized_key in ("liabilities", "liability"):
        return float(period_data.total_liabilities) if period_data.total_liabilities is not None else None
    if normalized_key in ("cogs", "cost_of_goods_sold"):
        if period_data.revenue is not None and period_data.gross_profit is not None:
            return float(period_data.revenue - period_data.gross_profit)
    return None

