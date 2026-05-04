from __future__ import annotations

from typing import Iterable

from risk_dashboard.schemas.financials import (
    AltmanZScore,
    DuPontBreakdown,
    FinancialAnalysisResponse,
    FinancialDataset,
    FinancialFlag,
    FinancialMetricSnapshot,
    FinancialPeriodData,
    FinancialTrendPoint,
    HealthRadar,
    PiotroskiFScore,
)

_BANK_INDUSTRIES = frozenset({
    "ngân hàng", "ngan hang", "banking", "bank", "tài chính", "tai chinh",
    "bảo hiểm", "bao hiem", "insurance", "chứng khoán", "chung khoan",
    "securities",
})


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _to_pct(value: float | None) -> float | None:
    if value is None:
        return None
    return value * 100


def _growth_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return ((current - previous) / abs(previous)) * 100


def _sort_periods(periods: Iterable[FinancialPeriodData]) -> list[FinancialPeriodData]:
    def sort_key(item: FinancialPeriodData) -> tuple[int, int]:
        return (item.year or 0, item.quarter or 0)
    return sorted(periods, key=sort_key, reverse=True)


def _is_financial_sector(industry: str | None) -> bool:
    if not industry:
        return False
    return industry.strip().lower() in _BANK_INDUSTRIES


def _yoy_reference(
    periods: list[FinancialPeriodData],
    current: FinancialPeriodData,
) -> FinancialPeriodData | None:
    """Find same-quarter-previous-year period. Never fall back to an adjacent quarter."""
    if current.year is None:
        return None
    target_year = current.year - 1
    for item in periods:
        if item is current:
            continue
        if current.quarter is not None:
            if item.quarter == current.quarter and item.year == target_year:
                return item
        else:
            if item.quarter is None and item.year == target_year:
                return item
    return None


def _ttm_sum(periods: list[FinancialPeriodData], attr: str) -> float | None:
    """Sum last 4 *consecutive* quarters for trailing-twelve-month figure."""
    quarterly = [p for p in periods if p.quarter is not None and p.year is not None]
    if len(quarterly) < 4:
        return None

    base = quarterly[0]
    expected = []
    y, q = base.year, base.quarter  # type: ignore[assignment]
    for _ in range(4):
        expected.append((y, q))
        q -= 1
        if q == 0:
            q = 4
            y -= 1

    values: list[float] = []
    for ey, eq in expected:
        match = next((p for p in quarterly if p.year == ey and p.quarter == eq), None)
        if match is None:
            return None
        v = getattr(match, attr, None)
        if v is None:
            return None
        values.append(v)
    return sum(values)


def _find_yoy_period(
    periods: list[FinancialPeriodData],
    reference: FinancialPeriodData,
) -> FinancialPeriodData | None:
    """Shared helper: find the same quarter one year prior."""
    if reference.year is None:
        return None
    target_year = reference.year - 1
    for p in periods:
        if p is reference:
            continue
        if reference.quarter is not None:
            if p.quarter == reference.quarter and p.year == target_year:
                return p
        else:
            if p.quarter is None and p.year == target_year:
                return p
    return None


# ── DuPont 3-factor decomposition ────────────────────────

def _compute_dupont(current: FinancialPeriodData) -> DuPontBreakdown:
    net_margin = _safe_div(current.net_income, current.revenue)
    asset_turnover = _safe_div(current.revenue, current.total_assets)
    equity_multiplier = _safe_div(current.total_assets, current.equity)

    roe = None
    if net_margin is not None and asset_turnover is not None and equity_multiplier is not None:
        roe = net_margin * asset_turnover * equity_multiplier

    return DuPontBreakdown(
        net_margin=net_margin,
        asset_turnover=asset_turnover,
        equity_multiplier=equity_multiplier,
        roe_decomposed=roe,
    )


# ── Altman Z-Score ───────────────────────────────────────

def _compute_altman_z(
    current: FinancialPeriodData,
    *,
    is_financial: bool = False,
) -> AltmanZScore:
    if is_financial:
        return AltmanZScore(
            score=None,
            zone=None,
            components={"note": None},
        )

    ta = current.total_assets
    if ta is None or ta == 0:
        return AltmanZScore()

    wc = (current.current_assets or 0) - (current.current_liabilities or 0)
    re_proxy = current.equity or 0
    ebit = current.operating_profit or current.ebitda or 0
    equity = current.equity or 0
    tl = current.total_liabilities or 0
    revenue = current.revenue or 0

    x1 = wc / ta
    x2 = re_proxy / ta
    x3 = ebit / ta
    x4 = equity / tl if tl > 0 else 0
    x5 = revenue / ta

    z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

    if z > 2.99:
        zone = "safe"
    elif z > 1.81:
        zone = "grey"
    else:
        zone = "distress"

    return AltmanZScore(
        score=round(z, 2),
        zone=zone,
        components={
            "X1_wc_ta": round(x1, 4),
            "X2_re_ta": round(x2, 4),
            "X3_ebit_ta": round(x3, 4),
            "X4_eq_tl": round(x4, 4),
            "X5_rev_ta": round(x5, 4),
        },
    )


# ── Piotroski F-Score (9 criteria) ───────────────────────

def _compute_piotroski(
    current: FinancialPeriodData,
    previous: FinancialPeriodData | None,
) -> PiotroskiFScore:
    details: dict[str, bool] = {}
    score = 0

    roa = _safe_div(current.net_income, current.total_assets)
    details["roa_positive"] = roa is not None and roa > 0
    score += details["roa_positive"]

    details["ocf_positive"] = (current.operating_cash_flow or 0) > 0
    score += details["ocf_positive"]

    prev_roa = _safe_div(previous.net_income, previous.total_assets) if previous else None
    details["roa_improving"] = roa is not None and prev_roa is not None and roa > prev_roa
    score += details["roa_improving"]

    details["accruals_quality"] = (
        current.operating_cash_flow is not None
        and current.net_income is not None
        and current.operating_cash_flow > current.net_income
    )
    score += details["accruals_quality"]

    de_curr = _safe_div(current.debt, current.equity)
    de_prev = _safe_div(previous.debt, previous.equity) if previous else None
    details["leverage_decreasing"] = de_curr is not None and de_prev is not None and de_curr < de_prev
    score += details["leverage_decreasing"]

    cr_curr = _safe_div(current.current_assets, current.current_liabilities)
    cr_prev = _safe_div(previous.current_assets, previous.current_liabilities) if previous else None
    details["liquidity_improving"] = cr_curr is not None and cr_prev is not None and cr_curr > cr_prev
    score += details["liquidity_improving"]

    details["no_dilution"] = (
        previous is not None
        and current.equity is not None
        and previous.equity is not None
        and current.equity >= previous.equity
    )
    score += details["no_dilution"]

    gm_curr = _safe_div(current.gross_profit, current.revenue)
    gm_prev = _safe_div(previous.gross_profit, previous.revenue) if previous else None
    details["margin_improving"] = gm_curr is not None and gm_prev is not None and gm_curr > gm_prev
    score += details["margin_improving"]

    at_curr = _safe_div(current.revenue, current.total_assets)
    at_prev = _safe_div(previous.revenue, previous.total_assets) if previous else None
    details["turnover_improving"] = at_curr is not None and at_prev is not None and at_curr > at_prev
    score += details["turnover_improving"]

    return PiotroskiFScore(score=score, details=details)


# ── Health Radar (0-100 per dimension) ───────────────────

def _clamp(value: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, value))


def _build_health_radar(snapshot: FinancialMetricSnapshot) -> HealthRadar:
    prof = _clamp((snapshot.net_margin_pct or 0) / 30 * 100)

    growth_raw = snapshot.revenue_growth_yoy_pct or 0
    growth = _clamp((growth_raw + 20) / 60 * 100)

    eff = _clamp((snapshot.roe_pct or 0) / 30 * 100)

    liq = _clamp((snapshot.current_ratio or 0) / 3 * 100)

    de = snapshot.debt_to_equity
    lev = _clamp(100 - (de or 0) / 3 * 100) if de is not None else 50

    cq = _clamp((snapshot.ocf_to_net_income or 0) / 2 * 100)

    return HealthRadar(
        profitability=round(prof, 1),
        growth=round(growth, 1),
        efficiency=round(eff, 1),
        liquidity=round(liq, 1),
        leverage=round(lev, 1),
        cash_quality=round(cq, 1),
    )


# ── Main snapshot builder ────────────────────────────────

def _build_snapshot(
    current: FinancialPeriodData,
    previous: FinancialPeriodData | None,
    periods: list[FinancialPeriodData],
    *,
    is_financial: bool = False,
) -> FinancialMetricSnapshot:
    gross_margin = _safe_div(current.gross_profit, current.revenue)
    operating_margin = _safe_div(current.operating_profit, current.revenue)
    ebitda_margin = _safe_div(current.ebitda, current.revenue)
    net_margin = _safe_div(current.net_income, current.revenue)
    roe = _safe_div(current.net_income, current.equity)
    roa = _safe_div(current.net_income, current.total_assets)
    asset_turnover = _safe_div(current.revenue, current.total_assets)

    # ROIC = NOPAT / Invested Capital (skip if IC <= 0)
    nopat = current.operating_profit * 0.8 if current.operating_profit is not None else None
    raw_ic = (current.equity or 0) + (current.debt or 0) - (current.cash or 0)
    invested_capital = raw_ic if raw_ic > 0 else None
    roic = _safe_div(nopat, invested_capital)

    debt_to_equity = _safe_div(current.debt, current.equity)
    net_debt = (current.debt or 0) - (current.cash or 0)
    net_debt_to_ebitda = _safe_div(net_debt, current.ebitda) if current.ebitda is not None else None

    current_ratio = _safe_div(current.current_assets, current.current_liabilities)
    quick_ratio = _safe_div(
        (current.current_assets or 0) - (current.inventory or 0)
        if current.current_assets is not None and current.inventory is not None
        else None,
        current.current_liabilities,
    )
    cash_ratio = _safe_div(current.cash, current.current_liabilities)

    ocf_to_net_income = _safe_div(current.operating_cash_flow, current.net_income)
    fcf = (
        current.operating_cash_flow - abs(current.capex or 0)
        if current.operating_cash_flow is not None
        else None
    )
    fcf_margin = _safe_div(fcf, current.revenue)

    quarterly_rev = current.revenue
    daily_rev = quarterly_rev / 90 if quarterly_rev else None
    cogs = (quarterly_rev - (current.gross_profit or 0)) if quarterly_rev is not None and current.gross_profit is not None else None
    daily_cogs = cogs / 90 if cogs is not None and cogs > 0 else None
    inventory_days = _safe_div(current.inventory, daily_cogs)
    receivable_days = _safe_div(current.receivables, daily_rev)

    revenue_ttm = _ttm_sum(periods, "revenue")
    net_income_ttm = _ttm_sum(periods, "net_income")
    ocf_ttm = _ttm_sum(periods, "operating_cash_flow")

    dupont = _compute_dupont(current)
    altman_z = _compute_altman_z(current, is_financial=is_financial)
    piotroski_f = _compute_piotroski(current, previous)

    return FinancialMetricSnapshot(
        revenue=current.revenue,
        revenue_growth_yoy_pct=_growth_pct(current.revenue, previous.revenue if previous else None),
        net_income=current.net_income,
        net_income_growth_yoy_pct=_growth_pct(current.net_income, previous.net_income if previous else None),
        gross_margin_pct=_to_pct(gross_margin),
        operating_margin_pct=_to_pct(operating_margin),
        ebitda_margin_pct=_to_pct(ebitda_margin),
        net_margin_pct=_to_pct(net_margin),
        roe_pct=_to_pct(roe),
        roa_pct=_to_pct(roa),
        roic_pct=_to_pct(roic),
        debt_to_equity=debt_to_equity,
        net_debt_to_ebitda=net_debt_to_ebitda,
        interest_coverage=None,
        current_ratio=current_ratio,
        quick_ratio=quick_ratio,
        cash_ratio=cash_ratio,
        ocf_to_net_income=ocf_to_net_income,
        free_cash_flow=fcf,
        fcf_margin_pct=_to_pct(fcf_margin),
        asset_turnover=asset_turnover,
        inventory_days=round(inventory_days, 1) if inventory_days is not None else None,
        receivable_days=round(receivable_days, 1) if receivable_days is not None else None,
        revenue_ttm=revenue_ttm,
        net_income_ttm=net_income_ttm,
        ocf_ttm=ocf_ttm,
        dupont=dupont,
        altman_z=altman_z,
        piotroski_f=piotroski_f,
    )


# ── Advanced flags ───────────────────────────────────────

def _build_flags(
    snapshot: FinancialMetricSnapshot,
    current: FinancialPeriodData,
    periods: list[FinancialPeriodData],
) -> list[FinancialFlag]:
    flags: list[FinancialFlag] = []

    if current.net_income is not None and current.net_income > 0 and (current.operating_cash_flow or 0) < 0:
        flags.append(FinancialFlag(
            level="high",
            title="Lợi nhuận dương nhưng dòng tiền âm",
            detail="Doanh nghiệp ghi nhận lợi nhuận nhưng dòng tiền HĐKD đang âm — dấu hiệu chất lượng lợi nhuận kém.",
        ))

    if snapshot.ocf_to_net_income is not None and snapshot.ocf_to_net_income < 0.8:
        flags.append(FinancialFlag(
            level="medium",
            title="Chất lượng lợi nhuận yếu (OCF/NI < 0.8)",
            detail="Lợi nhuận kế toán chưa chuyển hóa tốt thành tiền mặt.",
        ))

    if snapshot.debt_to_equity is not None and snapshot.debt_to_equity > 1.2:
        flags.append(FinancialFlag(
            level="medium",
            title="Đòn bẩy tài chính cao (D/E > 1.2)",
            detail=f"D/E = {snapshot.debt_to_equity:.2f}. Cần theo dõi áp lực trả nợ và chi phí lãi vay.",
        ))

    if snapshot.current_ratio is not None and snapshot.current_ratio < 1:
        flags.append(FinancialFlag(
            level="medium",
            title="Thanh khoản ngắn hạn yếu (CR < 1)",
            detail="Tài sản ngắn hạn chưa đủ bao phủ nợ ngắn hạn.",
        ))

    if snapshot.net_margin_pct is not None and snapshot.net_margin_pct < 5:
        flags.append(FinancialFlag(
            level="low",
            title="Biên lợi nhuận ròng mỏng (< 5%)",
            detail="Kết quả kinh doanh nhạy cảm với biến động chi phí đầu vào.",
        ))

    if snapshot.altman_z and snapshot.altman_z.zone == "distress":
        flags.append(FinancialFlag(
            level="high",
            title=f"Altman Z-Score vùng nguy hiểm ({snapshot.altman_z.score})",
            detail="Z-Score < 1.81 cho thấy rủi ro phá sản ở mức cao. Cần đánh giá kỹ khả năng trả nợ.",
        ))
    elif snapshot.altman_z and snapshot.altman_z.zone == "grey":
        flags.append(FinancialFlag(
            level="medium",
            title=f"Altman Z-Score vùng xám ({snapshot.altman_z.score})",
            detail="Z-Score 1.81-2.99, cần theo dõi sát sức khỏe tài chính.",
        ))

    if snapshot.piotroski_f and snapshot.piotroski_f.score is not None and snapshot.piotroski_f.score <= 3:
        flags.append(FinancialFlag(
            level="medium",
            title=f"Piotroski F-Score thấp ({snapshot.piotroski_f.score}/9)",
            detail="Dưới 4 điểm cho thấy chất lượng tài chính yếu trên nhiều tiêu chí.",
        ))

    # Inventory/receivables: compare YoY (same quarter last year), not QoQ
    yoy_prev = _find_yoy_period(periods, current) if current.year else None
    if yoy_prev is not None:
        inv_growth = _growth_pct(current.inventory, yoy_prev.inventory)
        rev_growth = _growth_pct(current.revenue, yoy_prev.revenue)
        if inv_growth is not None and rev_growth is not None and inv_growth > rev_growth + 10:
            flags.append(FinancialFlag(
                level="medium",
                title="Tồn kho tăng nhanh hơn doanh thu (YoY)",
                detail=f"Tồn kho YoY +{inv_growth:.1f}% vs doanh thu YoY +{rev_growth:.1f}% — rủi ro hàng tồn ứ đọng.",
            ))

        rec_growth = _growth_pct(current.receivables, yoy_prev.receivables)
        if rec_growth is not None and rev_growth is not None and rec_growth > rev_growth + 15:
            flags.append(FinancialFlag(
                level="medium",
                title="Phải thu tăng nhanh hơn doanh thu (YoY)",
                detail=f"Phải thu YoY +{rec_growth:.1f}% vs doanh thu YoY +{rev_growth:.1f}% — rủi ro nợ xấu.",
            ))

    # FCF negative for 2+ consecutive quarters
    fcf_negative_streak = 0
    for p in periods[:4]:
        ocf = p.operating_cash_flow
        if ocf is not None:
            fcf_val = ocf - abs(p.capex or 0)
            if fcf_val < 0:
                fcf_negative_streak += 1
            else:
                break
        else:
            break
    if fcf_negative_streak >= 2:
        flags.append(FinancialFlag(
            level="high",
            title=f"FCF âm {fcf_negative_streak} quý liên tiếp",
            detail="Dòng tiền tự do âm kéo dài cho thấy doanh nghiệp đang đốt tiền mặt.",
        ))

    # Revenue declining 2+ quarters
    rev_decline_streak = 0
    for i in range(min(3, len(periods) - 1)):
        curr_rev = periods[i].revenue
        prev_rev = periods[i + 1].revenue
        if curr_rev is not None and prev_rev is not None and curr_rev < prev_rev:
            rev_decline_streak += 1
        else:
            break
    if rev_decline_streak >= 2:
        flags.append(FinancialFlag(
            level="medium",
            title=f"Doanh thu giảm {rev_decline_streak} quý liên tiếp",
            detail="Xu hướng doanh thu suy giảm cần đánh giá lại triển vọng kinh doanh.",
        ))

    return flags


# ── Highlights ───────────────────────────────────────────

def _build_highlights(snapshot: FinancialMetricSnapshot, current: FinancialPeriodData) -> list[str]:
    highlights: list[str] = []

    if snapshot.revenue_growth_yoy_pct is not None:
        highlights.append(f"Doanh thu YoY: {snapshot.revenue_growth_yoy_pct:+.1f}%")
    if snapshot.net_income_growth_yoy_pct is not None:
        highlights.append(f"Lợi nhuận ròng YoY: {snapshot.net_income_growth_yoy_pct:+.1f}%")
    if snapshot.gross_margin_pct is not None:
        highlights.append(f"Biên gộp: {snapshot.gross_margin_pct:.1f}%")
    if snapshot.roe_pct is not None:
        highlights.append(f"ROE: {snapshot.roe_pct:.1f}%")
    if snapshot.roic_pct is not None:
        highlights.append(f"ROIC: {snapshot.roic_pct:.1f}%")
    if snapshot.free_cash_flow is not None:
        highlights.append(f"FCF: {snapshot.free_cash_flow:,.0f}")
    if snapshot.current_ratio is not None:
        highlights.append(f"Current Ratio: {snapshot.current_ratio:.2f}")
    if snapshot.piotroski_f and snapshot.piotroski_f.score is not None:
        highlights.append(f"Piotroski F-Score: {snapshot.piotroski_f.score}/9")
    if snapshot.altman_z and snapshot.altman_z.score is not None:
        highlights.append(f"Altman Z-Score: {snapshot.altman_z.score} ({snapshot.altman_z.zone})")

    return highlights[:8]


# ── Trends ───────────────────────────────────────────────

def _build_trends(periods: list[FinancialPeriodData]) -> list[FinancialTrendPoint]:
    points: list[FinancialTrendPoint] = []
    for p in periods[:8]:
        ocf = p.operating_cash_flow
        fcf = ocf - abs(p.capex or 0) if ocf is not None else None
        points.append(FinancialTrendPoint(
            period=p.period,
            revenue=p.revenue,
            net_income=p.net_income,
            operating_cash_flow=ocf,
            free_cash_flow=fcf,
            gross_margin_pct=_to_pct(_safe_div(p.gross_profit, p.revenue)),
            operating_margin_pct=_to_pct(_safe_div(p.operating_profit, p.revenue)),
            net_margin_pct=_to_pct(_safe_div(p.net_income, p.revenue)),
            roe_pct=_to_pct(_safe_div(p.net_income, p.equity)),
            debt_to_equity=_safe_div(p.debt, p.equity),
            current_ratio=_safe_div(p.current_assets, p.current_liabilities),
        ))
    return points


# ── Main entry point ─────────────────────────────────────

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

    is_financial = _is_financial_sector(dataset.industry)
    current = periods[0]
    previous = _yoy_reference(periods, current)
    snapshot = _build_snapshot(current, previous, periods, is_financial=is_financial)
    flags = _build_flags(snapshot, current, periods)
    highlights = _build_highlights(snapshot, current)
    radar = _build_health_radar(snapshot)

    return FinancialAnalysisResponse(
        ticker=dataset.ticker,
        source=dataset.source,
        fetched_at=dataset.fetched_at,
        company_name=dataset.company_name,
        exchange=dataset.exchange,
        industry=dataset.industry,
        latest_period=current.period,
        summary=snapshot,
        health_radar=radar,
        flags=flags,
        highlights=highlights,
        provider_notes=dataset.provider_notes,
        trends=_build_trends(periods),
        periods=periods,
    )
