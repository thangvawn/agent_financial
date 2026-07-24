from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from risk_dashboard.engines.quant.financial_analysis import analyze_financial_dataset
from risk_dashboard.schemas.financials import FinancialDataset


FLOW_FIELDS = {
    "revenue", "gross_profit", "operating_profit", "ebit", "ebitda", "net_income",
    "operating_cash_flow", "investing_cash_flow", "financing_cash_flow", "capex",
}

INCOME_LINES = (
    ("revenue", "Doanh thu thuần", "reported", True),
    ("cost_of_goods_sold", "Giá vốn hàng bán", "derived", False),
    ("gross_profit", "Lợi nhuận gộp", "reported", True),
    ("operating_profit", "Lợi nhuận từ hoạt động kinh doanh", "reported", True),
    ("ebit", "EBIT", "reported", False),
    ("ebitda", "EBITDA", "reported", False),
    ("net_income", "Lợi nhuận sau thuế", "reported", True),
)

BALANCE_LINES = (
    ("cash", "Tiền và tương đương tiền", "reported", False),
    ("short_term_investments", "Đầu tư tài chính ngắn hạn", "reported", False),
    ("receivables", "Các khoản phải thu", "reported", False),
    ("inventory", "Hàng tồn kho", "reported", False),
    ("current_assets", "Tài sản ngắn hạn", "reported", True),
    ("fixed_assets", "Tài sản cố định", "reported", False),
    ("investment_properties", "Bất động sản đầu tư", "reported", False),
    ("long_term_investments", "Đầu tư tài chính dài hạn", "reported", False),
    ("other_assets", "Tài sản khác", "reported", False),
    ("total_assets", "Tổng tài sản", "reported", True),
    ("accounts_payable", "Phải trả người bán", "reported", False),
    ("short_term_debt", "Nợ vay ngắn hạn", "reported", False),
    ("long_term_debt", "Nợ vay dài hạn", "reported", False),
    ("current_liabilities", "Nợ ngắn hạn", "reported", False),
    ("non_current_liabilities", "Nợ dài hạn", "reported", False),
    ("total_liabilities", "Tổng nợ phải trả", "reported", True),
    ("equity", "Vốn chủ sở hữu", "reported", True),
    ("retained_earnings", "Lợi nhuận sau thuế chưa phân phối", "reported", False),
)

CASH_FLOW_LINES = (
    ("operating_cash_flow", "Lưu chuyển tiền thuần từ HĐKD", "reported", True),
    ("investing_cash_flow", "Lưu chuyển tiền thuần từ HĐĐT", "reported", True),
    ("financing_cash_flow", "Lưu chuyển tiền thuần từ HĐTC", "reported", True),
    ("capex", "Chi đầu tư tài sản cố định", "reported", False),
    ("free_cash_flow", "Dòng tiền tự do (FCF)", "derived", True),
    ("net_cash_change", "Lưu chuyển tiền thuần trong kỳ", "derived", False),
)

RATIO_GROUPS = (
    ("profitability", "Khả năng sinh lời", (
        ("gross_margin_pct", "Biên lợi nhuận gộp", "%"),
        ("operating_margin_pct", "Biên lợi nhuận hoạt động", "%"),
        ("net_margin_pct", "Biên lợi nhuận ròng", "%"),
        ("roe_pct", "ROE", "%"),
        ("roa_pct", "ROA", "%"),
        ("roic_pct", "ROIC", "%"),
    )),
    ("liquidity", "Thanh khoản", (
        ("current_ratio", "Khả năng thanh toán hiện hành", "x"),
        ("quick_ratio", "Khả năng thanh toán nhanh", "x"),
        ("cash_ratio", "Khả năng thanh toán bằng tiền", "x"),
    )),
    ("leverage", "Đòn bẩy", (
        ("debt_to_equity", "Nợ vay / Vốn chủ sở hữu", "x"),
        ("liabilities_to_assets", "Nợ phải trả / Tổng tài sản", "%"),
        ("net_debt_to_ebitda", "Nợ ròng / EBITDA", "x"),
    )),
    ("efficiency", "Hiệu quả hoạt động", (
        ("asset_turnover", "Vòng quay tổng tài sản", "x"),
        ("inventory_days", "Số ngày tồn kho", "ngày"),
        ("receivable_days", "Số ngày phải thu", "ngày"),
    )),
    ("cash_quality", "Chất lượng dòng tiền", (
        ("ocf_to_net_income", "CFO / LNST", "x"),
        ("fcf_margin_pct", "Biên dòng tiền tự do", "%"),
        ("cash_conversion_pct", "Chuyển đổi lợi nhuận thành tiền", "%"),
    )),
)

EVALUATION_GROUPS = (
    ("profitability", "Sinh lời", 20, (
        ("roe_pct", "ROE", "%", True),
        ("net_margin_pct", "Biên lợi nhuận ròng", "%", True),
    )),
    ("growth", "Tăng trưởng", 15, (
        ("revenue_growth_yoy_pct", "Tăng trưởng doanh thu YoY", "%", True),
        ("net_income_growth_yoy_pct", "Tăng trưởng LNST YoY", "%", True),
    )),
    ("efficiency", "Hiệu quả hoạt động", 15, (
        ("asset_turnover", "Vòng quay tổng tài sản", "x", True),
        ("receivable_days", "Số ngày phải thu", "ngày", False),
    )),
    ("liquidity", "Thanh khoản", 15, (
        ("current_ratio", "Khả năng thanh toán hiện hành", "x", True),
        ("quick_ratio", "Khả năng thanh toán nhanh", "x", True),
    )),
    ("leverage", "Đòn bẩy", 15, (
        ("debt_to_equity", "Nợ vay / VCSH", "x", False),
        ("net_debt_to_ebitda", "Nợ ròng / EBITDA", "x", False),
    )),
    ("cash_quality", "Chất lượng dòng tiền", 20, (
        ("ocf_to_net_income", "CFO / LNST", "x", True),
        ("fcf_margin_pct", "Biên dòng tiền tự do", "%", True),
    )),
)


def _safe_div(numerator: Any, denominator: Any) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return float(numerator) / float(denominator)


def _pct(numerator: Any, denominator: Any) -> float | None:
    value = _safe_div(numerator, denominator)
    return round(value * 100, 4) if value is not None else None


def _growth(current: Any, reference: Any) -> float | None:
    if current is None or reference in (None, 0):
        return None
    return round(((float(current) - float(reference)) / abs(float(reference))) * 100, 4)


def _raw_periods(dataset: FinancialDataset) -> list[dict[str, Any]]:
    periods = [item.model_dump(mode="json") for item in dataset.periods]
    return sorted(periods, key=lambda item: (item.get("year") or 0, item.get("quarter") or 0, item.get("period") or ""))


def _annualize(periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    years: dict[int, list[dict[str, Any]]] = {}
    annual_reported = [item for item in periods if item.get("quarter") is None and item.get("year")]
    if annual_reported:
        return annual_reported
    for item in periods:
        if item.get("year"):
            years.setdefault(int(item["year"]), []).append(item)
    annual: list[dict[str, Any]] = []
    for year, items in sorted(years.items()):
        items.sort(key=lambda item: item.get("quarter") or 0)
        latest = dict(items[-1])
        latest["period"] = str(year)
        latest["quarter"] = None
        latest["period_kind"] = "annualized" if len(items) == 4 else "year_to_date"
        for field in FLOW_FIELDS:
            values = [item.get(field) for item in items if item.get(field) is not None]
            latest[field] = sum(values) if values else None
        annual.append(latest)
    return annual


def _derive_period(item: dict[str, Any]) -> dict[str, Any]:
    row = dict(item)
    revenue = row.get("revenue")
    gross_profit = row.get("gross_profit")
    cfo = row.get("operating_cash_flow")
    capex = row.get("capex")
    row["cost_of_goods_sold"] = revenue - gross_profit if revenue is not None and gross_profit is not None else None
    row["free_cash_flow"] = cfo - abs(capex or 0) if cfo is not None else None
    cash_parts = [row.get("operating_cash_flow"), row.get("investing_cash_flow"), row.get("financing_cash_flow")]
    row["net_cash_change"] = sum(cash_parts) if all(value is not None for value in cash_parts) else None
    row["gross_margin_pct"] = _pct(gross_profit, revenue)
    row["operating_margin_pct"] = _pct(row.get("operating_profit"), revenue)
    row["net_margin_pct"] = _pct(row.get("net_income"), revenue)
    row["roe_pct"] = _pct(row.get("net_income"), row.get("equity"))
    row["roa_pct"] = _pct(row.get("net_income"), row.get("total_assets"))
    invested_capital = (row.get("equity") or 0) + (row.get("debt") or 0) - (row.get("cash") or 0)
    row["roic_pct"] = _pct((row.get("operating_profit") or 0) * .8, invested_capital) if invested_capital > 0 else None
    row["current_ratio"] = _safe_div(row.get("current_assets"), row.get("current_liabilities"))
    quick_assets = None if row.get("current_assets") is None else row.get("current_assets") - (row.get("inventory") or 0)
    row["quick_ratio"] = _safe_div(quick_assets, row.get("current_liabilities"))
    row["cash_ratio"] = _safe_div(row.get("cash"), row.get("current_liabilities"))
    row["debt_to_equity"] = _safe_div(row.get("debt"), row.get("equity"))
    row["liabilities_to_assets"] = _pct(row.get("total_liabilities"), row.get("total_assets"))
    net_debt = (row.get("debt") or 0) - (row.get("cash") or 0)
    row["net_debt_to_ebitda"] = _safe_div(net_debt, row.get("ebitda"))
    row["asset_turnover"] = _safe_div(revenue, row.get("total_assets"))
    days = 365 if row.get("quarter") is None else 90
    row["inventory_days"] = _safe_div(row.get("inventory"), row.get("cost_of_goods_sold") / days if row.get("cost_of_goods_sold") else None)
    row["receivable_days"] = _safe_div(row.get("receivables"), revenue / days if revenue else None)
    row["ocf_to_net_income"] = _safe_div(cfo, row.get("net_income"))
    row["fcf_margin_pct"] = _pct(row.get("free_cash_flow"), revenue)
    row["cash_conversion_pct"] = _pct(cfo, row.get("net_income"))
    return row


def _same_period_yoy(periods: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any] | None:
    for item in periods:
        if item.get("year") == (current.get("year") or 0) - 1 and item.get("quarter") == current.get("quarter"):
            return item
    return None


def _statement(definitions: Iterable[tuple[str, str, str, bool]], periods: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for key, label, source, emphasis in definitions:
        values = [{"period": item.get("period"), "value": item.get(key)} for item in periods]
        if any(item["value"] is not None for item in values):
            rows.append({"key": key, "label": label, "source": source, "emphasis": emphasis, "values": values})
    return {"periods": [item.get("period") for item in periods], "rows": rows}


def _workspace_statements(dataset: FinancialDataset, periods: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    fallback = {
        "income": {"label": "Báo cáo thu nhập", **_statement(INCOME_LINES, periods)},
        "balance": {"label": "Cân đối kế toán", **_statement(BALANCE_LINES, periods)},
        "cash_flow": {"label": "Lưu chuyển tiền tệ", **_statement(CASH_FLOW_LINES, periods)},
    }
    if not dataset.raw_statements:
        return fallback

    result: dict[str, Any] = {}
    for key, statement in dataset.raw_statements.items():
        available = sorted(
            list(statement.get("periods") or []),
            key=lambda period: _normalize_workspace_period(period),
        )[-limit:][::-1]
        rows = []
        for row in statement.get("rows") or []:
            values = [value for value in row.get("values") or [] if value.get("period") in available]
            rows.append({**row, "values": values})
        result[key] = {**statement, "periods": available, "rows": rows}
    for key, statement in fallback.items():
        result.setdefault(key, statement)
    return result


def _normalize_workspace_period(period: Any) -> tuple[int, int]:
    raw = str(period or "")
    if "-Q" in raw:
        year, quarter = raw.split("-Q", 1)
        return (int(year) if year.isdigit() else 0, int(quarter) if quarter.isdigit() else 0)
    return (int(raw) if raw.isdigit() else 0, 0)


def _metric(key: str, label: str, value: Any, unit: str, yoy: Any = None) -> dict[str, Any]:
    return {"key": key, "label": label, "value": value, "unit": unit, "yoy_pct": yoy}


def _quality(periods: list[dict[str, Any]]) -> dict[str, Any]:
    latest = periods[-1]
    conversion = latest.get("cash_conversion_pct")
    accruals = None
    if latest.get("net_income") is not None and latest.get("operating_cash_flow") is not None:
        accruals = latest["net_income"] - latest["operating_cash_flow"]
    alerts: list[dict[str, Any]] = []
    if conversion is not None and conversion < 80:
        alerts.append({"code": "weak_cash_conversion", "severity": "warning", "title": "Lợi nhuận chuyển thành tiền ở mức thấp", "detail": "CFO thấp hơn 80% LNST ở kỳ mới nhất."})
    if latest.get("free_cash_flow") is not None and latest["free_cash_flow"] < 0:
        alerts.append({"code": "negative_fcf", "severity": "warning", "title": "Dòng tiền tự do âm", "detail": "Cần phân biệt đầu tư mở rộng với áp lực dòng tiền vận hành."})
    if latest.get("current_ratio") is not None and latest["current_ratio"] < 1:
        alerts.append({"code": "liquidity_below_one", "severity": "risk", "title": "Thanh khoản ngắn hạn dưới 1 lần", "detail": "Tài sản ngắn hạn chưa bao phủ toàn bộ nợ ngắn hạn."})
    if latest.get("liabilities_to_assets") is not None and latest["liabilities_to_assets"] > 70:
        alerts.append({"code": "high_liabilities", "severity": "risk", "title": "Tỷ trọng nợ phải trả cao", "detail": "Nợ phải trả vượt 70% tổng tài sản."})
    return {
        "latest": {
            "cash_conversion_pct": conversion,
            "free_cash_flow": latest.get("free_cash_flow"),
            "accruals": accruals,
            "current_ratio": latest.get("current_ratio"),
        },
        "series": [{"period": item.get("period"), "net_income": item.get("net_income"), "operating_cash_flow": item.get("operating_cash_flow"), "free_cash_flow": item.get("free_cash_flow"), "cash_conversion_pct": item.get("cash_conversion_pct")} for item in periods],
        "alerts": alerts,
    }


def _coverage(periods: list[dict[str, Any]]) -> dict[str, Any]:
    required = ("revenue", "net_income", "total_assets", "total_liabilities", "equity", "operating_cash_flow")
    missing = [{"period": item.get("period"), "fields": [field for field in required if item.get(field) is None]} for item in periods]
    complete = sum(1 for item in missing if not item["fields"])
    return {
        "score_pct": round(complete / len(periods) * 100, 1) if periods else 0,
        "complete_periods": complete,
        "total_periods": len(periods),
        "missing_by_period": [item for item in missing if item["fields"]],
    }


def _direction_signal(current: float, reference: float, higher_is_better: bool, tolerance: float) -> int:
    scale = max(abs(reference), 1.0)
    delta = (current - reference) / scale
    if abs(delta) <= tolerance:
        return 0
    improved = delta > 0 if higher_is_better else delta < 0
    return 1 if improved else -1


def _absolute_signal(field: str, value: float) -> tuple[int, str] | None:
    if field in {"revenue_growth_yoy_pct", "net_income_growth_yoy_pct", "net_margin_pct", "fcf_margin_pct"}:
        return (1, "Dương") if value > 0 else (-1, "Âm")
    if field == "current_ratio":
        if value < 1:
            return (-1, "Dưới 1 lần")
        return (1, "Từ 1 lần trở lên")
    if field == "ocf_to_net_income":
        if value >= 1:
            return (1, "CFO bao phủ LNST")
        if value < .8:
            return (-1, "CFO thấp hơn 80% LNST")
    return None


def _evaluation(periods: list[dict[str, Any]], analysis: dict[str, Any], peers: dict[str, Any] | None) -> dict[str, Any]:
    latest = periods[-1]
    yoy = _same_period_yoy(periods, latest) or {}
    prior_yoy = _same_period_yoy(periods, yoy) or {} if yoy else {}
    summary = analysis.get("summary") or {}
    peer_metrics = {
        item.get("field"): item
        for item in (peers or {}).get("metrics", [])
        if item.get("field")
    }
    category_rows: list[dict[str, Any]] = []
    evaluated_metrics = 0
    total_metrics = sum(len(specs) for _, _, _, specs in EVALUATION_GROUPS)

    for category_key, category_label, weight, specs in EVALUATION_GROUPS:
        metrics: list[dict[str, Any]] = []
        category_points: list[int] = []
        for field, label, unit, higher_is_better in specs:
            value = latest.get(field)
            if value is None:
                value = summary.get(field)
            reference = yoy.get(field)
            if field == "revenue_growth_yoy_pct":
                value = _growth(latest.get("revenue"), yoy.get("revenue")) if yoy else value
                reference = _growth(yoy.get("revenue"), prior_yoy.get("revenue")) if prior_yoy else None
            elif field == "net_income_growth_yoy_pct":
                value = _growth(latest.get("net_income"), yoy.get("net_income")) if yoy else value
                reference = _growth(yoy.get("net_income"), prior_yoy.get("net_income")) if prior_yoy else None
            peer = peer_metrics.get(field) or {}
            peer_median = peer.get("peer_median")
            signals: list[int] = []
            evidence: list[str] = []

            trend_reference = reference
            if field in {"revenue_growth_yoy_pct", "net_income_growth_yoy_pct"} and trend_reference is None:
                trend_reference = 0
            if value is not None and trend_reference is not None:
                signal = _direction_signal(float(value), float(trend_reference), higher_is_better, .03)
                signals.append(signal)
                evidence.append("Tốt hơn cùng kỳ" if signal > 0 else "Yếu hơn cùng kỳ" if signal < 0 else "Ít thay đổi so với cùng kỳ")
            if value is not None and peer_median is not None:
                signal = _direction_signal(float(value), float(peer_median), higher_is_better, .10)
                signals.append(signal)
                evidence.append("Tốt hơn trung vị peers" if signal > 0 else "Yếu hơn trung vị peers" if signal < 0 else "Gần trung vị peers")
            if value is not None:
                absolute = _absolute_signal(field, float(value))
                if absolute:
                    signals.append(absolute[0])
                    evidence.append(absolute[1])

            if value is None or not signals:
                status = "unavailable"
            else:
                evaluated_metrics += 1
                total = sum(signals)
                status = "good" if total > 0 else "risk" if total < 0 else "watch"
                category_points.append({"good": 100, "watch": 55, "risk": 20}[status])

            metrics.append({
                "key": field,
                "label": label,
                "unit": unit,
                "value": value,
                "yoy_reference": reference,
                "peer_median": peer_median,
                "peer_rank": peer.get("rank"),
                "peer_count": peer.get("total_peers") or 0,
                "higher_is_better": higher_is_better,
                "status": status,
                "evidence": evidence,
            })

        score = round(sum(category_points) / len(category_points)) if category_points else None
        category_rows.append({
            "key": category_key,
            "label": category_label,
            "weight_pct": weight,
            "score": score,
            "status": "good" if score is not None and score >= 70 else "watch" if score is not None and score >= 45 else "risk" if score is not None else "unavailable",
            "metrics": metrics,
        })

    scored = [item for item in category_rows if item["score"] is not None]
    weight_total = sum(item["weight_pct"] for item in scored)
    overall_score = round(sum(item["score"] * item["weight_pct"] for item in scored) / weight_total) if weight_total else None
    overall_status = (
        "good" if overall_score is not None and overall_score >= 70
        else "watch" if overall_score is not None and overall_score >= 45
        else "risk" if overall_score is not None
        else "unavailable"
    )
    coverage_pct = round(evaluated_metrics / total_metrics * 100, 1) if total_metrics else 0
    confidence = "high" if coverage_pct >= 75 else "medium" if coverage_pct >= 50 else "low"
    return {
        "framework": "Northstar evidence-weighted screening v1",
        "overall": {
            "score": overall_score,
            "status": overall_status,
            "coverage_pct": coverage_pct,
            "confidence": confidence,
        },
        "categories": category_rows,
        "models": {
            "piotroski_f": summary.get("piotroski_f"),
            "altman_z": summary.get("altman_z"),
        },
        "methodology": {
            "description": "Tổng hợp nhiều nhóm tỷ lệ, xu hướng cùng kỳ và trung vị doanh nghiệp so sánh; không dùng một chỉ tiêu đơn lẻ để kết luận.",
            "status_rules": {
                "good": "Tín hiệu thuận chiếm ưu thế",
                "watch": "Tín hiệu cân bằng hoặc chênh lệch chưa đáng kể",
                "risk": "Tín hiệu bất lợi chiếm ưu thế",
            },
            "sources": [
                {
                    "title": "CFA Institute — Financial Analysis Techniques",
                    "url": "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/financial-analysis-techniques",
                },
                {
                    "title": "Piotroski (2000) — Value Investing",
                    "url": "https://doi.org/10.2307/2672906",
                },
                {
                    "title": "Altman (1968) — Financial Ratios and Corporate Bankruptcy",
                    "url": "https://doi.org/10.1111/j.1540-6261.1968.tb00843.x",
                },
            ],
            "limitations": [
                "Ngưỡng tổng hợp là heuristic minh bạch của Northstar, chưa phải mô hình dự báo lợi suất đã được kiểm định cho thị trường Việt Nam.",
                "So sánh chỉ có ý nghĩa khi doanh nghiệp cùng ngành và cùng chuẩn kỳ báo cáo.",
                "Một số thành phần Piotroski và Altman dùng biến đại diện khi nguồn dữ liệu thiếu số cổ phiếu phát hành, lợi nhuận giữ lại hoặc giá trị vốn hóa; cần xem chi tiết trước khi kết luận.",
                "Altman Z không áp dụng cho ngân hàng, chứng khoán và bảo hiểm; dữ liệu thiếu làm giảm độ tin cậy.",
                "Kết quả là công cụ sàng lọc và giáo dục, không phải khuyến nghị mua hoặc bán.",
            ],
        },
    }


def build_company_financial_workspace(
    dataset: FinancialDataset,
    *,
    period_mode: str = "quarter",
    limit: int = 12,
    peers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if period_mode not in {"quarter", "year"}:
        raise ValueError("period_mode must be 'quarter' or 'year'")
    raw = _raw_periods(dataset)
    selected = [item for item in raw if item.get("quarter") is not None] if period_mode == "quarter" else _annualize(raw)
    if not selected:
        selected = raw
    periods = [_derive_period(item) for item in selected[-max(4, min(limit, 20)):]]
    if not periods:
        raise ValueError("financial dataset has no periods")
    latest = periods[-1]
    yoy = _same_period_yoy(periods, latest)
    analysis = analyze_financial_dataset(dataset).model_dump(mode="json")
    summary = analysis.get("summary") or {}
    headline = [
        _metric("revenue", "Doanh thu", latest.get("revenue"), "VND", _growth(latest.get("revenue"), (yoy or {}).get("revenue"))),
        _metric("net_income", "LNST", latest.get("net_income"), "VND", _growth(latest.get("net_income"), (yoy or {}).get("net_income"))),
        _metric("gross_margin_pct", "Biên gộp", latest.get("gross_margin_pct"), "%", None),
        _metric("roe_pct", "ROE", latest.get("roe_pct"), "%", None),
        _metric("debt_to_equity", "Nợ vay / VCSH", latest.get("debt_to_equity"), "x", None),
        _metric("operating_cash_flow", "Dòng tiền HĐKD", latest.get("operating_cash_flow"), "VND", _growth(latest.get("operating_cash_flow"), (yoy or {}).get("operating_cash_flow"))),
    ]
    ratio_groups = []
    for group_key, group_label, definitions in RATIO_GROUPS:
        ratio_groups.append({
            "key": group_key,
            "label": group_label,
            "metrics": [{"key": key, "label": label, "unit": unit, "value": latest.get(key), "series": [{"period": item.get("period"), "value": item.get(key)} for item in periods]} for key, label, unit in definitions],
        })
    return {
        "schema_version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company": {
            "ticker": dataset.ticker,
            "name": dataset.company_name or dataset.ticker,
            "exchange": dataset.exchange,
            "industry": dataset.industry,
            "latest_period": latest.get("period"),
            "currency": latest.get("currency") or "VND",
        },
        "controls": {"period_mode": period_mode, "available_period_modes": ["quarter", "year"], "period_limit": len(periods)},
        "headline_metrics": headline,
        "trend": {
            "periods": [item.get("period") for item in periods],
            "series": [{"key": key, "label": label, "unit": unit, "values": [{"period": item.get("period"), "value": item.get(key)} for item in periods]} for key, label, unit in (
                ("revenue", "Doanh thu", "VND"), ("gross_profit", "Lợi nhuận gộp", "VND"),
                ("net_income", "LNST", "VND"), ("operating_cash_flow", "CFO", "VND"),
                ("free_cash_flow", "FCF", "VND"), ("total_assets", "Tổng tài sản", "VND"),
            )],
        },
        "statements": _workspace_statements(dataset, periods, limit),
        "ratio_groups": ratio_groups,
        "quality": _quality(periods),
        "health": {
            "radar": analysis.get("health_radar") or {},
            "altman_z": summary.get("altman_z"),
            "piotroski_f": summary.get("piotroski_f"),
        },
        "evaluation": _evaluation(periods, analysis, peers),
        "peers": peers or {"metrics": [], "peer_tickers": []},
        "data_provenance": {
            "provider": dataset.source,
            "license_notice": "Nguồn phát triển hiện tại có thể giới hạn mục đích sử dụng; production cần provider có hợp đồng thương mại.",
            "fetched_at": dataset.fetched_at.isoformat(),
            "provider_notes": dataset.provider_notes,
            "coverage": _coverage(periods),
            "methodology": [
                "Chỉ tiêu reported lấy từ bộ dữ liệu BCTC chuẩn hóa.",
                "Chỉ tiêu derived được tính từ các khoản mục reported và không thay thế báo cáo gốc.",
                "Dữ liệu năm được cộng các chỉ tiêu dòng và lấy kỳ cuối cho chỉ tiêu thời điểm.",
            ],
        },
    }
