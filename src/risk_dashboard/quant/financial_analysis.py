from __future__ import annotations

from typing import Iterable

from risk_dashboard.schemas.financials import (
    FinancialAnalysisResponse,
    FinancialDataset,
    FinancialFlag,
    FinancialMetricSnapshot,
    FinancialPeriodData,
    FinancialTrendPoint,
)


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _to_pct(value: float | None) -> float | None:
    if value is None:
        return None
    return value * 100


def _growth_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return ((current - previous) / abs(previous)) * 100


def _sort_periods(periods: Iterable[FinancialPeriodData]) -> list[FinancialPeriodData]:
    def sort_key(item: FinancialPeriodData) -> tuple[int, int]:
        return (item.year or 0, item.quarter or 0)

    return sorted(periods, key=sort_key, reverse=True)


def _yoy_reference(periods: list[FinancialPeriodData], current: FinancialPeriodData) -> FinancialPeriodData | None:
    for item in periods:
        if item is current:
            continue
        if current.quarter is not None and item.quarter == current.quarter and item.year == (current.year or 0) - 1:
            return item
    return periods[1] if len(periods) > 1 else None


def _build_snapshot(current: FinancialPeriodData, previous: FinancialPeriodData | None) -> FinancialMetricSnapshot:
    gross_margin = _safe_div(current.gross_profit, current.revenue)
    net_margin = _safe_div(current.net_income, current.revenue)
    roe = _safe_div(current.net_income, current.equity)
    roa = _safe_div(current.net_income, current.total_assets)
    debt_to_equity = _safe_div(current.debt, current.equity)
    current_ratio = _safe_div(current.current_assets, current.current_liabilities)
    quick_ratio = _safe_div(
        None
        if current.current_assets is None or current.inventory is None
        else current.current_assets - current.inventory,
        current.current_liabilities,
    )
    ocf_to_net_income = _safe_div(current.operating_cash_flow, current.net_income)
    free_cash_flow = (
        None
        if current.operating_cash_flow is None
        else current.operating_cash_flow - abs(current.capex or 0)
    )

    return FinancialMetricSnapshot(
        revenue=current.revenue,
        revenue_growth_yoy_pct=_growth_pct(current.revenue, previous.revenue if previous else None),
        net_income=current.net_income,
        net_income_growth_yoy_pct=_growth_pct(current.net_income, previous.net_income if previous else None),
        gross_margin_pct=_to_pct(gross_margin),
        net_margin_pct=_to_pct(net_margin),
        roe_pct=_to_pct(roe),
        roa_pct=_to_pct(roa),
        debt_to_equity=debt_to_equity,
        current_ratio=current_ratio,
        quick_ratio=quick_ratio,
        ocf_to_net_income=ocf_to_net_income,
        free_cash_flow=free_cash_flow,
    )


def _build_flags(snapshot: FinancialMetricSnapshot, current: FinancialPeriodData) -> list[FinancialFlag]:
    flags: list[FinancialFlag] = []

    if current.net_income is not None and current.net_income > 0 and (current.operating_cash_flow or 0) < 0:
        flags.append(
            FinancialFlag(
                level="high",
                title="Lợi nhuận dương nhưng dòng tiền âm",
                detail="Doanh nghiệp ghi nhận lợi nhuận nhưng dòng tiền từ hoạt động kinh doanh đang âm.",
            )
        )

    if snapshot.ocf_to_net_income is not None and snapshot.ocf_to_net_income < 0.8:
        flags.append(
            FinancialFlag(
                level="medium",
                title="Chất lượng lợi nhuận yếu",
                detail="OCF/Net Income thấp cho thấy lợi nhuận kế toán chưa chuyển hóa tốt thành tiền.",
            )
        )

    if snapshot.debt_to_equity is not None and snapshot.debt_to_equity > 1.2:
        flags.append(
            FinancialFlag(
                level="medium",
                title="Đòn bẩy tài chính cao",
                detail="Tỷ lệ nợ trên vốn chủ sở hữu đang ở mức cao, cần theo dõi áp lực trả nợ.",
            )
        )

    if snapshot.current_ratio is not None and snapshot.current_ratio < 1:
        flags.append(
            FinancialFlag(
                level="medium",
                title="Thanh khoản ngắn hạn yếu",
                detail="Current ratio dưới 1 cho thấy tài sản ngắn hạn chưa đủ bao phủ nợ ngắn hạn.",
            )
        )

    if snapshot.net_margin_pct is not None and snapshot.net_margin_pct < 5:
        flags.append(
            FinancialFlag(
                level="low",
                title="Biên lợi nhuận ròng mỏng",
                detail="Biên lợi nhuận ròng thấp khiến kết quả kinh doanh nhạy với biến động chi phí.",
            )
        )

    return flags


def _build_highlights(snapshot: FinancialMetricSnapshot, current: FinancialPeriodData) -> list[str]:
    highlights: list[str] = []

    if snapshot.revenue_growth_yoy_pct is not None:
        highlights.append(f"Doanh thu YoY: {snapshot.revenue_growth_yoy_pct:.1f}%")
    if snapshot.net_income_growth_yoy_pct is not None:
        highlights.append(f"Lợi nhuận ròng YoY: {snapshot.net_income_growth_yoy_pct:.1f}%")
    if snapshot.gross_margin_pct is not None:
        highlights.append(f"Biên gộp: {snapshot.gross_margin_pct:.1f}%")
    if snapshot.current_ratio is not None:
        highlights.append(f"Current ratio: {snapshot.current_ratio:.2f}")
    if current.operating_cash_flow is not None:
        highlights.append(f"Dòng tiền HĐKD: {current.operating_cash_flow:,.0f}")

    return highlights[:5]


def _build_trends(periods: list[FinancialPeriodData]) -> list[FinancialTrendPoint]:
    trend_points: list[FinancialTrendPoint] = []

    for period in periods[:8]:
        trend_points.append(
            FinancialTrendPoint(
                period=period.period,
                revenue=period.revenue,
                net_income=period.net_income,
                operating_cash_flow=period.operating_cash_flow,
                gross_margin_pct=_to_pct(_safe_div(period.gross_profit, period.revenue)),
                net_margin_pct=_to_pct(_safe_div(period.net_income, period.revenue)),
                debt_to_equity=_safe_div(period.debt, period.equity),
                current_ratio=_safe_div(period.current_assets, period.current_liabilities),
            )
        )

    return trend_points


def analyze_financial_dataset(dataset: FinancialDataset) -> FinancialAnalysisResponse:
    periods = _sort_periods(dataset.periods)
    if not periods:
        return FinancialAnalysisResponse(
            ticker=dataset.ticker,
            source=dataset.source,
            fetched_at=dataset.fetched_at,
            company_name=dataset.company_name,
            exchange=dataset.exchange,
            industry=dataset.industry,
            latest_period=None,
            summary=FinancialMetricSnapshot(),
            flags=[],
            highlights=["Chưa có dữ liệu BCTC đã chuẩn hóa cho mã này."],
            provider_notes=dataset.provider_notes,
            trends=[],
            periods=[],
        )

    current = periods[0]
    previous = _yoy_reference(periods, current)
    snapshot = _build_snapshot(current, previous)
    flags = _build_flags(snapshot, current)
    highlights = _build_highlights(snapshot, current)

    return FinancialAnalysisResponse(
        ticker=dataset.ticker,
        source=dataset.source,
        fetched_at=dataset.fetched_at,
        company_name=dataset.company_name,
        exchange=dataset.exchange,
        industry=dataset.industry,
        latest_period=current.period,
        summary=snapshot,
        flags=flags,
        highlights=highlights,
        provider_notes=dataset.provider_notes,
        trends=_build_trends(periods),
        periods=periods,
    )
