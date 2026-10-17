"""Deterministic what-if projections for the BCTC learning workbook.

The scenario surface is intentionally small and auditable.  It applies a
learner's assumptions to one reported period, keeps the reported base values
separate from the projection, and never fills a missing base operand with a
made-up number.
"""

from __future__ import annotations

import math
from typing import Any

from risk_dashboard.modules.financials_product.application.company_workspace import (
    _derive_period,
    _raw_periods,
)
from risk_dashboard.schemas.financials import FinancialDataset


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _bounded(value: Any, *, name: str, minimum: float, maximum: float) -> float:
    number = _finite(value)
    if number is None:
        raise ValueError(f"{name} must be a finite number")
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} must be between {minimum:g} and {maximum:g}")
    return number


def _period_key(item: dict[str, Any]) -> tuple[int, int, str]:
    raw = str(item.get("period") or "")
    if "-Q" in raw:
        year, quarter = raw.split("-Q", 1)
        return (int(year) if year.isdigit() else 0, int(quarter) if quarter.isdigit() else 0, raw)
    return (int(raw) if raw.isdigit() else 0, 0, raw)


def _resolve_period(dataset: FinancialDataset, requested: str | None) -> dict[str, Any]:
    periods = [_derive_period(item) for item in _raw_periods(dataset)]
    if not periods:
        raise ValueError(f"financial dataset {dataset.ticker} has no periods")
    if requested:
        normalized = str(requested).replace("-", "").upper()
        for item in periods:
            actual = str(item.get("period") or "").replace("-", "").upper()
            if actual == normalized:
                return item
        raise ValueError(f"period '{requested}' is not available for {dataset.ticker}")
    return max(periods, key=_period_key)


def _delta(projected: float | None, base: float | None) -> float | None:
    if projected is None or base is None:
        return None
    value = projected - base
    return value if math.isfinite(value) else None


def _delta_pct(projected: float | None, base: float | None) -> float | None:
    if projected is None or base is None or base == 0:
        return None
    value = (projected - base) / abs(base) * 100
    return round(value, 4) if math.isfinite(value) else None


def _safe_product(left: float | None, right: float | None) -> float | None:
    """Multiply finite operands without allowing IEEE overflow into JSON."""

    if left is None or right is None:
        return None
    value = left * right
    return value if math.isfinite(value) else None


def _safe_difference(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    value = left - right
    return value if math.isfinite(value) else None


def _safe_percentage(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    value = numerator / denominator * 100
    return value if math.isfinite(value) else None


def build_financial_scenario(
    dataset: FinancialDataset,
    *,
    period: str | None = None,
    revenue_growth_pct: float = 5.0,
    gross_margin_pct: float | None = None,
    tax_rate_pct: float = 20.0,
    operating_expense_growth_pct: float = 3.0,
) -> dict[str, Any]:
    """Project a transparent income statement from a reported period.

    ``gross_margin_pct`` defaults to the reported margin.  Operating expenses
    are inferred only when both gross profit and operating profit are reported;
    otherwise the projected operating profit remains unavailable.
    """

    base = _resolve_period(dataset, period)
    revenue_growth = _bounded(revenue_growth_pct, name="revenue_growth_pct", minimum=-100, maximum=500)
    tax_rate = _bounded(tax_rate_pct, name="tax_rate_pct", minimum=0, maximum=100)
    opex_growth = _bounded(
        operating_expense_growth_pct,
        name="operating_expense_growth_pct",
        minimum=-100,
        maximum=500,
    )

    base_revenue = _finite(base.get("revenue"))
    base_gross_profit = _finite(base.get("gross_profit"))
    base_operating_profit = _finite(base.get("operating_profit"))
    base_net_income = _finite(base.get("net_income"))
    if base_revenue is None or base_revenue <= 0:
        raise ValueError("selected period must contain a positive reported revenue")

    reported_margin = _safe_percentage(base_gross_profit, base_revenue)
    margin = reported_margin if gross_margin_pct is None else _bounded(
        gross_margin_pct,
        name="gross_margin_pct",
        minimum=0,
        maximum=100,
    )
    projected_revenue = _safe_product(base_revenue, 1 + revenue_growth / 100)
    projected_gross_profit = _safe_product(projected_revenue, margin / 100) if margin is not None else None

    base_operating_expense = _safe_difference(base_gross_profit, base_operating_profit)
    projected_operating_expense = _safe_product(base_operating_expense, 1 + opex_growth / 100)
    projected_operating_profit = _safe_difference(projected_gross_profit, projected_operating_expense)
    projected_net_income = _safe_product(projected_operating_profit, 1 - tax_rate / 100)
    projected_net_margin = _safe_percentage(projected_net_income, projected_revenue)

    warnings: list[str] = []
    if projected_revenue is None:
        warnings.append("Giá trị doanh thu dự phóng vượt giới hạn số hữu hạn; hãy giảm quy mô dữ liệu hoặc giả định.")
    if margin is None:
        warnings.append("Thiếu lợi nhuận gộp nên không thể dự phóng biên gộp và lợi nhuận hoạt động.")
    if base_operating_expense is None:
        warnings.append("Thiếu lợi nhuận gộp hoặc lợi nhuận hoạt động nên không thể suy ra chi phí hoạt động.")
    elif projected_operating_expense is None:
        warnings.append("Chi phí hoạt động dự phóng vượt giới hạn số hữu hạn; hãy giảm giả định tăng trưởng.")
    if projected_gross_profit is not None and projected_operating_profit is None and projected_operating_expense is not None:
        warnings.append("Lợi nhuận hoạt động dự phóng vượt giới hạn số hữu hạn.")
    if projected_operating_profit is not None and projected_net_income is None:
        warnings.append("Lợi nhuận ròng dự phóng vượt giới hạn số hữu hạn.")
    if base_net_income is None:
        warnings.append("Kỳ nền thiếu LNST; phần thay đổi LNST chỉ là kết quả mô phỏng, không có đối chiếu gốc.")

    base_payload = {
        "period": base.get("period"),
        "revenue": base_revenue,
        "gross_profit": base_gross_profit,
        "operating_profit": base_operating_profit,
        "net_income": base_net_income,
        "gross_margin_pct": reported_margin,
        "net_margin_pct": (
            _safe_percentage(base_net_income, base_revenue)
        ),
    }
    projected_payload = {
        "period": f"{base.get('period')} · scenario",
        "revenue": projected_revenue,
        "gross_profit": projected_gross_profit,
        "operating_expense": projected_operating_expense,
        "operating_profit": projected_operating_profit,
        "net_income": projected_net_income,
        "gross_margin_pct": margin,
        "net_margin_pct": projected_net_margin,
    }
    return {
        "schema_version": "1.0",
        "ticker": dataset.ticker,
        "company_name": dataset.company_name or dataset.ticker,
        "base": base_payload,
        "scenario": projected_payload,
        "deltas": {
            key: _delta(projected_payload.get(key), base_payload.get(key))
            for key in ("revenue", "gross_profit", "operating_profit", "net_income")
        },
        "delta_pct": {
            key: _delta_pct(projected_payload.get(key), base_payload.get(key))
            for key in ("revenue", "gross_profit", "operating_profit", "net_income")
        },
        "assumptions": {
            "revenue_growth_pct": revenue_growth,
            "gross_margin_pct": margin,
            "tax_rate_pct": tax_rate,
            "operating_expense_growth_pct": opex_growth,
        },
        "formulas": {
            "revenue": "Doanh thu nền × (1 + tăng trưởng doanh thu)",
            "gross_profit": "Doanh thu dự phóng × biên lợi nhuận gộp",
            "operating_profit": "Lợi nhuận gộp dự phóng − chi phí hoạt động dự phóng",
            "net_income": "Lợi nhuận hoạt động dự phóng × (1 − thuế suất)",
        },
        "warnings": warnings,
        "methodology": "Mô phỏng giáo dục theo một kỳ báo cáo; không phải dự báo doanh nghiệp hay khuyến nghị đầu tư.",
    }
