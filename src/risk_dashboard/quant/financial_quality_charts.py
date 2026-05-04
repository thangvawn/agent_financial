from __future__ import annotations

from collections.abc import Iterable

from risk_dashboard.schemas.financials import (
    CashFlowChartPoint,
    CashFlowChartResponse,
    CashFlowLatestMetrics,
    FinancialChartFlag,
    FinancialDataset,
    FinancialPeriodData,
    FinancialQualityChartsResponse,
    LatestMarginValues,
    MarginChartPoint,
    MarginChartResponse,
)


MARGIN_FORMULAS = {
    "gross_margin_pct": "Gross Margin = Gross Profit / Revenue × 100",
    "operating_margin_pct": "Operating Margin = Operating Profit / Revenue × 100",
    "ebit_margin_pct": "EBIT Margin = EBIT / Revenue × 100, nếu có EBIT",
    "net_margin_pct": "Net Margin = Net Income / Revenue × 100",
    "change_pp": "YoY/QoQ change = margin_t - margin_reference, theo điểm phần trăm",
}

CASH_FLOW_FORMULAS = {
    "fcf": "FCF = CFO - abs(Capex)",
    "cfo_to_net_income": "CFO/LNST = CFO / Net Income",
    "cfo_margin_pct": "CFO Margin = CFO / Revenue × 100",
    "fcf_margin_pct": "FCF Margin = FCF / Revenue × 100",
    "quality_score": "Cash Flow Quality Score 0-100 từ CFO/LNST, CFO Margin, FCF Margin và red flags",
}


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _pct(value: float | None) -> float | None:
    return round(value * 100, 2) if value is not None else None


def _growth_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round(((current - previous) / abs(previous)) * 100, 2)


def _pp(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return round(current - previous, 2)


def _sort_periods(periods: Iterable[FinancialPeriodData]) -> list[FinancialPeriodData]:
    return sorted(periods, key=lambda item: (item.year or 0, item.quarter or 0, item.period), reverse=True)


def _display_periods(periods: list[FinancialPeriodData], limit: int = 8) -> list[FinancialPeriodData]:
    return list(reversed(periods[:limit]))


def _previous_quarter(periods: list[FinancialPeriodData], current: FinancialPeriodData) -> FinancialPeriodData | None:
    try:
        index = periods.index(current)
    except ValueError:
        return None
    return periods[index + 1] if index + 1 < len(periods) else None


def _same_quarter_last_year(periods: list[FinancialPeriodData], current: FinancialPeriodData) -> FinancialPeriodData | None:
    if current.year is None:
        return None
    for item in periods:
        if item is current:
            continue
        if current.quarter is not None:
            if item.year == current.year - 1 and item.quarter == current.quarter:
                return item
        elif item.year == current.year - 1 and item.quarter is None:
            return item
    return None


def _margin_values(period: FinancialPeriodData) -> dict[str, float | None]:
    return {
        "gross_margin_pct": _pct(_safe_div(period.gross_profit, period.revenue)),
        "operating_margin_pct": _pct(_safe_div(period.operating_profit, period.revenue)),
        "ebit_margin_pct": _pct(_safe_div(period.ebit, period.revenue)),
        "net_margin_pct": _pct(_safe_div(period.net_income, period.revenue)),
    }


def build_margin_analysis(periods_input: Iterable[FinancialPeriodData]) -> MarginChartResponse:
    periods = _sort_periods(periods_input)
    missing_fields: set[str] = set()
    points_desc: list[MarginChartPoint] = []

    for period in periods:
        values = _margin_values(period)
        yoy = _same_quarter_last_year(periods, period)
        qoq = _previous_quarter(periods, period)
        yoy_values = _margin_values(yoy) if yoy else {}
        qoq_values = _margin_values(qoq) if qoq else {}

        if period.revenue in (None, 0):
            missing_fields.add("revenue")
        if period.gross_profit is None:
            missing_fields.add("gross_profit")
        if period.operating_profit is None:
            missing_fields.add("operating_profit")
        if period.ebit is None:
            missing_fields.add("ebit")
        if period.net_income is None:
            missing_fields.add("net_income")

        points_desc.append(MarginChartPoint(
            period=period.period,
            year=period.year,
            quarter=period.quarter,
            revenue=period.revenue,
            gross_profit=period.gross_profit,
            operating_profit=period.operating_profit,
            ebit=period.ebit,
            net_income=period.net_income,
            **values,
            gross_margin_yoy_pp=_pp(values["gross_margin_pct"], yoy_values.get("gross_margin_pct")),
            operating_margin_yoy_pp=_pp(values["operating_margin_pct"], yoy_values.get("operating_margin_pct")),
            ebit_margin_yoy_pp=_pp(values["ebit_margin_pct"], yoy_values.get("ebit_margin_pct")),
            net_margin_yoy_pp=_pp(values["net_margin_pct"], yoy_values.get("net_margin_pct")),
            gross_margin_qoq_pp=_pp(values["gross_margin_pct"], qoq_values.get("gross_margin_pct")),
            operating_margin_qoq_pp=_pp(values["operating_margin_pct"], qoq_values.get("operating_margin_pct")),
            ebit_margin_qoq_pp=_pp(values["ebit_margin_pct"], qoq_values.get("ebit_margin_pct")),
            net_margin_qoq_pp=_pp(values["net_margin_pct"], qoq_values.get("net_margin_pct")),
        ))

    flags = _detect_margin_flags(points_desc)
    latest_point = points_desc[0] if points_desc else MarginChartPoint(period="n/a")
    latest = LatestMarginValues(
        gross_margin_pct=latest_point.gross_margin_pct,
        operating_margin_pct=latest_point.operating_margin_pct,
        ebit_margin_pct=latest_point.ebit_margin_pct,
        net_margin_pct=latest_point.net_margin_pct,
        net_margin_yoy_pp=latest_point.net_margin_yoy_pp,
        net_margin_qoq_pp=latest_point.net_margin_qoq_pp,
    )

    interpretation = _interpret_margin(latest, flags)
    return MarginChartResponse(
        formulas=MARGIN_FORMULAS,
        points=list(reversed(points_desc[:8])),
        latest=latest,
        interpretation=interpretation,
        flags=flags,
        missing_fields=sorted(missing_fields),
    )


def _detect_margin_flags(points_desc: list[MarginChartPoint]) -> list[FinancialChartFlag]:
    flags: list[FinancialChartFlag] = []
    latest = points_desc[0] if points_desc else None
    recent = points_desc[:4]

    if latest and latest.net_margin_pct is not None and latest.net_margin_pct < 0:
        flags.append(FinancialChartFlag(
            severity="high",
            code="net_margin_negative",
            metric="net_margin_pct",
            message="Biên lợi nhuận ròng âm ở kỳ mới nhất.",
        ))

    net_margins = [p.net_margin_pct for p in recent if p.net_margin_pct is not None]
    if len(net_margins) >= 3 and all(net_margins[i] < net_margins[i + 1] for i in range(len(net_margins) - 1)):
        flags.append(FinancialChartFlag(
            severity="medium",
            code="margin_multi_period_decline",
            metric="net_margin_pct",
            message="Biên ròng giảm nhiều kỳ liên tiếp, cần kiểm tra chi phí và mix doanh thu.",
        ))

    if latest and latest.gross_margin_qoq_pp is not None and latest.net_margin_qoq_pp is not None:
        if latest.gross_margin_qoq_pp > 0.5 and latest.net_margin_qoq_pp < -0.5:
            flags.append(FinancialChartFlag(
                severity="medium",
                code="gross_up_net_down",
                metric="gross_margin_pct/net_margin_pct",
                message="Biên gộp cải thiện nhưng biên ròng giảm, có thể chi phí vận hành/tài chính tăng.",
            ))

    return flags


def _interpret_margin(latest: LatestMarginValues, flags: list[FinancialChartFlag]) -> str:
    if latest.net_margin_pct is None:
        return "Chưa đủ dữ liệu doanh thu và lợi nhuận ròng để diễn giải biên lợi nhuận."
    direction = "cải thiện" if (latest.net_margin_yoy_pp or 0) > 0 else "thu hẹp" if (latest.net_margin_yoy_pp or 0) < 0 else "ổn định"
    risk = " Có red flag cần kiểm tra trước khi kết luận." if flags else ""
    return f"Biên ròng mới nhất đạt {latest.net_margin_pct:.1f}% và {direction} so với cùng kỳ nếu có dữ liệu tham chiếu.{risk}"


def build_cash_flow_quality(periods_input: Iterable[FinancialPeriodData]) -> CashFlowChartResponse:
    periods = _sort_periods(periods_input)
    missing_fields: set[str] = set()
    points_desc: list[CashFlowChartPoint] = []

    for period in periods:
        yoy = _same_quarter_last_year(periods, period)
        cfo = period.operating_cash_flow
        cfi = period.investing_cash_flow
        cff = period.financing_cash_flow
        fcf = cfo - abs(period.capex or 0) if cfo is not None else None
        if cfo is None:
            missing_fields.add("operating_cash_flow")
        if cfi is None:
            missing_fields.add("investing_cash_flow")
        if cff is None:
            missing_fields.add("financing_cash_flow")
        if period.capex is None:
            missing_fields.add("capex")
        if period.revenue in (None, 0):
            missing_fields.add("revenue")
        if period.net_income in (None, 0):
            missing_fields.add("net_income")

        points_desc.append(CashFlowChartPoint(
            period=period.period,
            year=period.year,
            quarter=period.quarter,
            revenue=period.revenue,
            net_income=period.net_income,
            cfo=cfo,
            cfi=cfi,
            cff=cff,
            capex=period.capex,
            fcf=fcf,
            cfo_to_net_income=round(_safe_div(cfo, period.net_income), 2) if _safe_div(cfo, period.net_income) is not None else None,
            cfo_margin_pct=_pct(_safe_div(cfo, period.revenue)),
            fcf_margin_pct=_pct(_safe_div(fcf, period.revenue)),
            receivables=period.receivables,
            inventory=period.inventory,
            revenue_yoy_pct=_growth_pct(period.revenue, yoy.revenue if yoy else None),
            receivables_yoy_pct=_growth_pct(period.receivables, yoy.receivables if yoy else None),
            inventory_yoy_pct=_growth_pct(period.inventory, yoy.inventory if yoy else None),
        ))

    flags = _detect_cash_flow_flags(points_desc)
    latest_point = points_desc[0] if points_desc else CashFlowChartPoint(period="n/a")
    quality_score = cash_flow_quality_score(latest_point, flags)
    latest = CashFlowLatestMetrics(
        cfo=latest_point.cfo,
        cfi=latest_point.cfi,
        cff=latest_point.cff,
        fcf=latest_point.fcf,
        cfo_to_net_income=latest_point.cfo_to_net_income,
        cfo_margin_pct=latest_point.cfo_margin_pct,
        fcf_margin_pct=latest_point.fcf_margin_pct,
        quality_score=quality_score,
        quality_label=_quality_label(quality_score),
    )

    return CashFlowChartResponse(
        formulas=CASH_FLOW_FORMULAS,
        points=list(reversed(points_desc[:8])),
        latest=latest,
        interpretation=_interpret_cash_flow(latest, flags),
        flags=flags,
        missing_fields=sorted(missing_fields),
    )


def _detect_cash_flow_flags(points_desc: list[CashFlowChartPoint]) -> list[FinancialChartFlag]:
    flags: list[FinancialChartFlag] = []
    latest = points_desc[0] if points_desc else None
    if latest and latest.net_income is not None and latest.net_income > 0 and (latest.cfo or 0) < 0:
        flags.append(FinancialChartFlag(
            severity="high",
            code="positive_profit_negative_cfo",
            metric="cfo",
            message="LNST dương nhưng CFO âm, lợi nhuận chưa chuyển hóa thành tiền.",
        ))
    if latest and latest.cfo_to_net_income is not None and latest.cfo_to_net_income < 0.8:
        flags.append(FinancialChartFlag(
            severity="medium",
            code="low_cfo_to_net_income",
            metric="cfo_to_net_income",
            message="CFO/LNST thấp hơn 0.8x, cần kiểm tra vốn lưu động và chất lượng lợi nhuận.",
        ))

    fcf_values = [p.fcf for p in points_desc[:4] if p.fcf is not None]
    if len(fcf_values) >= 2 and all(value < 0 for value in fcf_values[:2]):
        flags.append(FinancialChartFlag(
            severity="medium",
            code="negative_fcf_streak",
            metric="fcf",
            message="FCF âm kéo dài ít nhất 2 kỳ gần nhất.",
        ))

    if latest and latest.revenue_yoy_pct is not None:
        if latest.receivables_yoy_pct is not None and latest.receivables_yoy_pct > latest.revenue_yoy_pct + 15:
            flags.append(FinancialChartFlag(
                severity="medium",
                code="receivables_outgrow_revenue",
                metric="receivables",
                message="Phải thu tăng nhanh hơn doanh thu YoY, cần kiểm tra tốc độ thu tiền.",
            ))
        if latest.inventory_yoy_pct is not None and latest.inventory_yoy_pct > latest.revenue_yoy_pct + 10:
            flags.append(FinancialChartFlag(
                severity="medium",
                code="inventory_outgrow_revenue",
                metric="inventory",
                message="Tồn kho tăng nhanh hơn doanh thu YoY, cần kiểm tra rủi ro tồn kho.",
            ))
    return flags


def cash_flow_quality_score(point: CashFlowChartPoint, flags: list[FinancialChartFlag]) -> float:
    score = 55.0
    cfo_to_ni = point.cfo_to_net_income
    if cfo_to_ni is not None:
        if cfo_to_ni >= 1.2:
            score += 22
        elif cfo_to_ni >= 1:
            score += 17
        elif cfo_to_ni >= 0.8:
            score += 8
        elif cfo_to_ni >= 0:
            score -= 12
        else:
            score -= 25
    if point.cfo_margin_pct is not None:
        score += max(-12, min(14, point.cfo_margin_pct * 0.7))
    if point.fcf_margin_pct is not None:
        score += max(-18, min(12, point.fcf_margin_pct * 0.8))
    for flag in flags:
        score -= 18 if flag.severity == "high" else 10 if flag.severity == "medium" else 5
    return round(max(0, min(100, score)), 1)


def _quality_label(score: float) -> str:
    if score >= 75:
        return "Tốt"
    if score >= 55:
        return "Theo dõi"
    return "Cần kiểm tra"


def _interpret_cash_flow(latest: CashFlowLatestMetrics, flags: list[FinancialChartFlag]) -> str:
    if latest.cfo is None:
        return "Chưa đủ dữ liệu CFO để đánh giá chất lượng dòng tiền."
    quality = f"Cash Flow Quality Score {latest.quality_score:.0f}/100 — {latest.quality_label}."
    if latest.cfo_to_net_income is not None:
        quality += f" CFO/LNST ở mức {latest.cfo_to_net_income:.2f}x."
    if flags:
        quality += " Có điểm cần kiểm tra trong dòng tiền hoặc vốn lưu động."
    return quality


def build_financial_quality_charts(dataset: FinancialDataset) -> FinancialQualityChartsResponse:
    periods = _sort_periods(dataset.periods)
    return FinancialQualityChartsResponse(
        ticker=dataset.ticker,
        source=dataset.source,
        latest_period=periods[0].period if periods else None,
        margin_analysis=build_margin_analysis(periods),
        cash_flow_quality=build_cash_flow_quality(periods),
    )
