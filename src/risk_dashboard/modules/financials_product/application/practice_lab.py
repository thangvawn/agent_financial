"""Deterministic practice-lab calculations for the BCTC product surface.

The practice lab deliberately keeps the calculation path explicit.  It starts
with the normalized ``FinancialPeriodData`` values, derives ratios from those
values, and produces a comparable score with coverage and formula provenance.
There is no silent imputation: a missing input makes the affected calculation
unavailable and lowers the confidence shown to the learner.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from risk_dashboard.modules.financials_product.application.company_workspace import (
    EVALUATION_GROUPS,
    _annualize,
    _derive_period,
    _raw_periods,
)
from risk_dashboard.modules.financials_product.domain.provenance import derive_revision_id
from risk_dashboard.schemas.financials import FinancialDataset

RAW_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("revenue", "Doanh thu thuần", "VND"),
    ("gross_profit", "Lợi nhuận gộp", "VND"),
    ("operating_profit", "Lợi nhuận hoạt động", "VND"),
    ("net_income", "Lợi nhuận sau thuế", "VND"),
    ("total_assets", "Tổng tài sản", "VND"),
    ("total_liabilities", "Tổng nợ phải trả", "VND"),
    ("equity", "Vốn chủ sở hữu", "VND"),
    ("cash", "Tiền và tương đương tiền", "VND"),
    ("debt", "Nợ vay", "VND"),
    ("current_assets", "Tài sản ngắn hạn", "VND"),
    ("current_liabilities", "Nợ ngắn hạn", "VND"),
    ("inventory", "Hàng tồn kho", "VND"),
    ("receivables", "Các khoản phải thu", "VND"),
    ("ebitda", "EBITDA", "VND"),
    ("operating_cash_flow", "Dòng tiền HĐKD", "VND"),
    ("investing_cash_flow", "Dòng tiền HĐĐT", "VND"),
    ("financing_cash_flow", "Dòng tiền HĐTC", "VND"),
    ("capex", "Chi đầu tư TSCĐ", "VND"),
)

DERIVED_FIELDS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    ("cost_of_goods_sold", "Giá vốn hàng bán", "VND", "Doanh thu − Lợi nhuận gộp", ("revenue", "gross_profit")),
    ("free_cash_flow", "Dòng tiền tự do", "VND", "CFO − |CAPEX|", ("operating_cash_flow", "capex")),
    ("net_cash_change", "Thay đổi tiền thuần", "VND", "CFO + CFI + CFF", ("operating_cash_flow", "investing_cash_flow", "financing_cash_flow")),
    ("gross_margin_pct", "Biên lợi nhuận gộp", "%", "Lợi nhuận gộp ÷ Doanh thu × 100", ("gross_profit", "revenue")),
    ("operating_margin_pct", "Biên lợi nhuận hoạt động", "%", "Lợi nhuận hoạt động ÷ Doanh thu × 100", ("operating_profit", "revenue")),
    ("net_margin_pct", "Biên lợi nhuận ròng", "%", "LNST ÷ Doanh thu × 100", ("net_income", "revenue")),
    ("roe_pct", "ROE", "%", "LNST ÷ Vốn chủ sở hữu × 100", ("net_income", "equity")),
    ("roa_pct", "ROA", "%", "LNST ÷ Tổng tài sản × 100", ("net_income", "total_assets")),
    ("roic_pct", "ROIC xấp xỉ", "%", "NOPAT (80% LNHĐKD) ÷ vốn đầu tư × 100", ("operating_profit", "equity", "debt", "cash")),
    ("current_ratio", "Current ratio", "x", "Tài sản ngắn hạn ÷ Nợ ngắn hạn", ("current_assets", "current_liabilities")),
    ("quick_ratio", "Quick ratio", "x", "(Tài sản ngắn hạn − Tồn kho) ÷ Nợ ngắn hạn", ("current_assets", "inventory", "current_liabilities")),
    ("cash_ratio", "Cash ratio", "x", "Tiền ÷ Nợ ngắn hạn", ("cash", "current_liabilities")),
    ("debt_to_equity", "Nợ vay / VCSH", "x", "Nợ vay ÷ Vốn chủ sở hữu", ("debt", "equity")),
    ("liabilities_to_assets", "Nợ phải trả / Tổng tài sản", "%", "Tổng nợ ÷ Tổng tài sản × 100", ("total_liabilities", "total_assets")),
    ("net_debt_to_ebitda", "Nợ ròng / EBITDA", "x", "(Nợ vay − Tiền) ÷ EBITDA", ("debt", "cash", "ebitda")),
    ("asset_turnover", "Vòng quay tổng tài sản", "x", "Doanh thu ÷ Tổng tài sản", ("revenue", "total_assets")),
    ("inventory_days", "Số ngày tồn kho", "ngày", "Tồn kho ÷ (Giá vốn / số ngày kỳ)", ("inventory", "cost_of_goods_sold")),
    ("receivable_days", "Số ngày phải thu", "ngày", "Phải thu ÷ (Doanh thu / số ngày kỳ)", ("receivables", "revenue")),
    ("ocf_to_net_income", "CFO / LNST", "x", "CFO ÷ LNST", ("operating_cash_flow", "net_income")),
    ("fcf_margin_pct", "Biên dòng tiền tự do", "%", "FCF ÷ Doanh thu × 100", ("free_cash_flow", "revenue")),
    ("cash_conversion_pct", "Chuyển đổi lợi nhuận thành tiền", "%", "CFO ÷ LNST × 100", ("operating_cash_flow", "net_income")),
)

GROWTH_FIELDS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("revenue_growth_yoy_pct", "Tăng trưởng doanh thu YoY", ("revenue", "revenue@YoY")),
    ("net_income_growth_yoy_pct", "Tăng trưởng LNST YoY", ("net_income", "net_income@YoY")),
)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _divide(numerator: Any, denominator: Any) -> float | None:
    top = _number(numerator)
    bottom = _number(denominator)
    if top is None or bottom is None or bottom == 0:
        return None
    result = top / bottom
    return result if math.isfinite(result) else None


def _percent(numerator: Any, denominator: Any) -> float | None:
    value = _divide(numerator, denominator)
    return round(value * 100, 4) if value is not None else None


def _period_matches(period: dict[str, Any], requested: str) -> bool:
    actual = str(period.get("period") or "").replace("-", "").upper()
    wanted = str(requested or "").replace("-", "").upper()
    return bool(actual and wanted and actual == wanted)


def _period_sort_key(value: str) -> tuple[int, int, str]:
    raw = str(value or "")
    if "-Q" in raw:
        year, quarter = raw.split("-Q", 1)
        return (int(year) if year.isdigit() else 0, int(quarter) if quarter.isdigit() else 0, raw)
    return (int(raw) if raw.isdigit() else 0, 0, raw)


def _select_periods(dataset: FinancialDataset, period_mode: str, limit: int) -> list[dict[str, Any]]:
    raw = _raw_periods(dataset)
    selected = [item for item in raw if item.get("quarter") is not None] if period_mode == "quarter" else _annualize(raw)
    if not selected:
        selected = raw
    return [_derive_period(item) for item in selected[-max(4, min(limit, 20)):]]


def _derive_row(row: dict[str, Any]) -> dict[str, Any]:
    """Recalculate the displayed fields from raw values with finite arithmetic."""
    data = {key: _number(value) for key, value in row.items() if key not in {"period", "year", "quarter", "currency", "period_kind"}}
    revenue = data.get("revenue")
    gross_profit = data.get("gross_profit")
    cfo = data.get("operating_cash_flow")
    capex = data.get("capex")
    cogs = revenue - gross_profit if revenue is not None and gross_profit is not None else None
    fcf = cfo - abs(capex) if cfo is not None and capex is not None else None
    cash_components = [data.get(field) for field in ("operating_cash_flow", "investing_cash_flow", "financing_cash_flow")]
    net_cash = sum(cash_components) if all(value is not None for value in cash_components) else None
    capital_inputs = (data.get("equity"), data.get("debt"), data.get("cash"))
    invested = sum(capital_inputs[:2]) - capital_inputs[2] if all(value is not None for value in capital_inputs) else None
    days = 365 if row.get("quarter") is None else 90
    derived = {
        "cost_of_goods_sold": cogs,
        "free_cash_flow": fcf,
        "net_cash_change": net_cash,
        "gross_margin_pct": _percent(gross_profit, revenue),
        "operating_margin_pct": _percent(data.get("operating_profit"), revenue),
        "net_margin_pct": _percent(data.get("net_income"), revenue),
        "roe_pct": _percent(data.get("net_income"), data.get("equity")),
        "roa_pct": _percent(data.get("net_income"), data.get("total_assets")),
        "roic_pct": _percent(data.get("operating_profit") * 0.8, invested) if invested is not None and invested > 0 and data.get("operating_profit") is not None else None,
        "current_ratio": _divide(data.get("current_assets"), data.get("current_liabilities")),
        "quick_ratio": _divide(
            data.get("current_assets") - data.get("inventory")
            if data.get("current_assets") is not None and data.get("inventory") is not None else None,
            data.get("current_liabilities"),
        ),
        "cash_ratio": _divide(data.get("cash"), data.get("current_liabilities")),
        "debt_to_equity": _divide(data.get("debt"), data.get("equity")),
        "liabilities_to_assets": _percent(data.get("total_liabilities"), data.get("total_assets")),
        "net_debt_to_ebitda": _divide(data.get("debt") - data.get("cash"), data.get("ebitda"))
        if data.get("debt") is not None and data.get("cash") is not None else None,
        "asset_turnover": _divide(revenue, data.get("total_assets")),
        "inventory_days": _divide(data.get("inventory"), cogs / days if cogs is not None and cogs > 0 else None),
        "receivable_days": _divide(data.get("receivables"), revenue / days if revenue is not None and revenue > 0 else None),
        "ocf_to_net_income": _divide(cfo, data.get("net_income")),
        "fcf_margin_pct": _percent(fcf, revenue),
        "cash_conversion_pct": _percent(cfo, data.get("net_income")),
    }
    return {**row, **data, **{key: value for key, value in derived.items() if value is None or math.isfinite(value)}}


def _status(field: str, value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "unavailable"
    if field in {"net_margin_pct", "gross_margin_pct", "operating_margin_pct", "roe_pct", "roa_pct", "roic_pct", "fcf_margin_pct"}:
        return "good" if value > 0 else "risk" if value < 0 else "watch"
    if field == "current_ratio":
        return "good" if value >= 1.5 else "watch" if value >= 1 else "risk"
    if field == "quick_ratio":
        return "good" if value >= 1 else "watch" if value >= 0.5 else "risk"
    if field == "ocf_to_net_income":
        return "good" if value >= 1 else "watch" if value >= 0.8 else "risk"
    if field in {"debt_to_equity", "net_debt_to_ebitda", "liabilities_to_assets", "receivable_days", "inventory_days"}:
        limits = {
            "debt_to_equity": (0.5, 1.5),
            "net_debt_to_ebitda": (2, 4),
            "liabilities_to_assets": (50, 70),
            "receivable_days": (30, 60),
            "inventory_days": (30, 90),
        }[field]
        return "good" if value <= limits[0] else "watch" if value <= limits[1] else "risk"
    if field == "asset_turnover":
        return "good" if value >= 1 else "watch" if value >= 0.5 else "risk"
    if field in {"cash_ratio"}:
        return "good" if value >= 0.5 else "watch" if value >= 0.2 else "risk"
    if field in {"revenue_growth_yoy_pct", "net_income_growth_yoy_pct"}:
        return "good" if value > 0 else "risk" if value < 0 else "watch"
    return "watch"


def _score(status: str) -> int | None:
    return {"good": 100, "watch": 55, "risk": 20}.get(status)


def _round(value: Any, digits: int = 4) -> float | None:
    number = _number(value)
    return round(number, digits) if number is not None else None


def _build_company(dataset: FinancialDataset, periods: list[dict[str, Any]], requested_period: str | None) -> dict[str, Any]:
    if not periods:
        raise ValueError(f"financial dataset {dataset.ticker} has no periods")
    requested_match = next((item for item in periods if requested_period and _period_matches(item, requested_period)), None)
    selected = requested_match or periods[-1]
    reference = next((item for item in periods if item.get("year") == (selected.get("year") or 0) - 1 and item.get("quarter") == selected.get("quarter")), None)
    row = _derive_row(selected)
    reference_row = _derive_row(reference) if reference else None
    fields = {field: row.get(field) for field, _, _ in RAW_FIELDS}
    calculated: list[dict[str, Any]] = []
    for field, label, unit, formula, dependencies in DERIVED_FIELDS:
        value = _number(row.get(field))
        calculated.append({
            "field": field,
            "label": label,
            "unit": unit,
            "formula": formula,
            "dependencies": list(dependencies),
            "value": _round(value),
            "status": "calculated" if value is not None else "insufficient_data",
        })
    values = {field: _number(row.get(field)) for field, _, _, _, _ in DERIVED_FIELDS}
    if reference_row:
        values["revenue_growth_yoy_pct"] = _round(
            _divide((row.get("revenue") or 0) - (reference_row.get("revenue") or 0), abs(reference_row.get("revenue"))) * 100
            if reference_row.get("revenue") not in (None, 0) else None,
        )
        values["net_income_growth_yoy_pct"] = _round(
            _divide((row.get("net_income") or 0) - (reference_row.get("net_income") or 0), abs(reference_row.get("net_income"))) * 100
            if reference_row.get("net_income") not in (None, 0) else None,
        )
    else:
        values["revenue_growth_yoy_pct"] = None
        values["net_income_growth_yoy_pct"] = None
    for field, label, dependencies in GROWTH_FIELDS:
        growth_value = _number(values.get(field))
        calculated.append({
            "field": field,
            "label": label,
            "unit": "%",
            "formula": "(Kỳ này − cùng kỳ) ÷ |cùng kỳ| × 100",
            "dependencies": list(dependencies),
            "value": _round(growth_value),
            "status": "calculated" if growth_value is not None else "insufficient_data",
        })

    category_rows: list[dict[str, Any]] = []
    metric_records: list[dict[str, Any]] = []
    for category_key, category_label, weight, specs in EVALUATION_GROUPS:
        metrics: list[dict[str, Any]] = []
        metric_scores: list[int] = []
        for field, label, unit, higher_is_better in specs:
            value = _number(values.get(field))
            status = _status(field, value)
            if field == "ocf_to_net_income" and (
                row.get("operating_cash_flow") is None
                or row.get("net_income") is None
                or row.get("operating_cash_flow") <= 0
                or row.get("net_income") <= 0
            ):
                status = "risk" if value is not None else "unavailable"
            metric_score = _score(status)
            if metric_score is not None:
                metric_scores.append(metric_score)
            metric = {
                "field": field,
                "label": label,
                "unit": unit,
                "value": _round(value),
                "status": status,
                "score": metric_score,
                "higher_is_better": higher_is_better,
                "yoy_reference": _round(reference_row.get(field)) if reference_row else None,
            }
            metrics.append(metric)
            metric_records.append(metric)
        category_score = round(sum(metric_scores) / len(metric_scores)) if metric_scores else None
        category_rows.append({
            "key": category_key,
            "label": category_label,
            "weight_pct": weight,
            "score": category_score,
            "status": "good" if category_score is not None and category_score >= 70 else "watch" if category_score is not None and category_score >= 45 else "risk" if category_score is not None else "unavailable",
            "metrics": metrics,
        })
    scored = [item for item in category_rows if item["score"] is not None]
    weight_total = sum(item["weight_pct"] for item in scored)
    overall_score = round(sum(item["score"] * item["weight_pct"] for item in scored) / weight_total) if weight_total else None
    coverage = round(sum(1 for item in metric_records if item["value"] is not None) / len(metric_records) * 100, 1) if metric_records else 0
    strengths = [item for item in metric_records if item["status"] == "good"][:3]
    risks = [item for item in metric_records if item["status"] == "risk"][:3]
    formula_by_field = {spec[0]: spec[3] for spec in DERIVED_FIELDS}
    formula_by_field.update({field: "(Kỳ này − cùng kỳ) ÷ |cùng kỳ| × 100" for field, _, _ in GROWTH_FIELDS})
    insights = [
        {"kind": "strength", "title": f"{item['label']} đang hỗ trợ chất lượng tài chính", "detail": f"{item['label']} = {item['value']}{item['unit']}. Công thức: {formula_by_field.get(item['field'], 'chỉ tiêu sàng lọc')}.", "field": item["field"]}
        for item in strengths
    ] + [
        {"kind": "risk", "title": f"Cần kiểm tra {item['label']}", "detail": f"{item['label']} = {item['value']}{item['unit']} đang nằm trong vùng cần theo dõi theo ngưỡng sàng lọc.", "field": item["field"]}
        for item in risks
    ]
    raw_available = sum(1 for value in fields.values() if value is not None)
    return {
        "ticker": dataset.ticker,
        "company_name": dataset.company_name or dataset.ticker,
        "industry": dataset.industry,
        "exchange": dataset.exchange,
        "period": selected.get("period"),
        "period_aligned": requested_period is None or requested_match is not None,
        "raw_inputs": [{"field": field, "label": label, "unit": unit, "value": _round(fields[field], 2)} for field, label, unit in RAW_FIELDS],
        "calculated_fields": calculated,
        "values": values,
        "categories": category_rows,
        "overall": {
            "score": overall_score,
            "status": "good" if overall_score is not None and overall_score >= 70 else "watch" if overall_score is not None and overall_score >= 45 else "risk" if overall_score is not None else "unavailable",
            "coverage_pct": coverage,
            "confidence": "high" if coverage >= 75 else "medium" if coverage >= 50 else "low",
        },
        "insights": insights,
        "data_quality": {
            "raw_fields_available": raw_available,
            "raw_fields_total": len(RAW_FIELDS),
            "calculated_fields_available": sum(1 for item in calculated if item["value"] is not None),
            "calculated_fields_total": len(calculated),
            "missing_raw_fields": [field for field, _, _ in RAW_FIELDS if fields[field] is None],
            "source": dataset.source,
            "fetched_at": dataset.fetched_at.isoformat(),
            "revision_id": derive_revision_id(
                dataset.source,
                dataset.fetched_at.isoformat(),
                [str(item.get("period") or "") for item in periods],
            ),
            "provider_notes": dataset.provider_notes,
        },
    }


def _rank_companies(companies: list[dict[str, Any]]) -> None:
    ordered = sorted(
        companies,
        key=lambda item: item["overall"]["score"] if item["overall"]["score"] is not None else -1,
        reverse=True,
    )
    rank = 0
    for company in ordered:
        if company["overall"]["score"] is None:
            company["overall"]["rank"] = None
            continue
        rank += 1
        company["overall"]["rank"] = rank


def build_practice_lab(
    datasets: Sequence[FinancialDataset],
    *,
    period_mode: str = "quarter",
    period: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    if period_mode not in {"quarter", "year"}:
        raise ValueError("period_mode must be 'quarter' or 'year'")
    if not datasets:
        raise ValueError("at least one financial dataset is required")
    periods_by_dataset = [_select_periods(dataset, period_mode, limit) for dataset in datasets]
    warnings: list[str] = []
    effective_period = period
    if effective_period is None and len(periods_by_dataset) > 1:
        normalized_sets = [
            {str(item.get("period") or "").replace("-", "").upper(): str(item.get("period") or "") for item in periods}
            for periods in periods_by_dataset
        ]
        common = set.intersection(*(set(items) for items in normalized_sets)) if normalized_sets else set()
        if common:
            latest_key = max(common, key=lambda key: _period_sort_key(normalized_sets[0][key]))
            effective_period = normalized_sets[0][latest_key]
        else:
            warnings.append("Các mã không có cùng kỳ báo cáo; mỗi mã dùng kỳ mới nhất. Hãy kiểm tra thời điểm trước khi kết luận.")
    companies = [
        _build_company(dataset, periods, effective_period)
        for dataset, periods in zip(datasets, periods_by_dataset, strict=True)
    ]
    if effective_period and any(not company["period_aligned"] for company in companies):
        missing = ", ".join(company["ticker"] for company in companies if not company["period_aligned"])
        warnings.append(f"Không tìm thấy kỳ {effective_period} cho: {missing}; các mã này đang hiển thị kỳ gần nhất có sẵn.")
    _rank_companies(companies)
    field_map: dict[str, dict[str, Any]] = {}
    for company in companies:
        for category in company["categories"]:
            for metric in category["metrics"]:
                field_map.setdefault(metric["field"], {"field": metric["field"], "label": metric["label"], "unit": metric["unit"], "higher_is_better": metric["higher_is_better"], "rows": []})["rows"].append({"ticker": company["ticker"], "value": metric["value"], "status": metric["status"]})
    # Give every metric an explicit cross-company rank and median.  Missing values
    # stay missing and are excluded from the denominator.
    for metric in field_map.values():
        valid = [row for row in metric["rows"] if row["value"] is not None]
        sorted_values = sorted(row["value"] for row in valid)
        if not sorted_values:
            metric["median"] = None
        elif len(sorted_values) % 2:
            metric["median"] = _round(sorted_values[len(sorted_values) // 2])
        else:
            middle = len(sorted_values) // 2
            metric["median"] = _round((sorted_values[middle - 1] + sorted_values[middle]) / 2)
        for row in metric["rows"]:
            if row["value"] is None:
                row["rank"] = None
            else:
                better = [item for item in valid if item["value"] > row["value"]] if metric["higher_is_better"] else [item for item in valid if item["value"] < row["value"]]
                row["rank"] = len(better) + 1
    return {
        "schema_version": "1.0",
        "workflow": [
            {"step": 1, "key": "raw", "label": "Chọn dữ liệu raw", "description": "Chọn mã và kỳ báo cáo từ bộ dữ liệu chuẩn hóa."},
            {"step": 2, "key": "calculate", "label": "Tính trường dẫn xuất", "description": "Tính tỷ lệ từ các khoản mục gốc, không điền số thiếu."},
            {"step": 3, "key": "interpret", "label": "Tìm insight", "description": "Đánh dấu vùng tốt, theo dõi và rủi ro kèm công thức."},
            {"step": 4, "key": "compare", "label": "So sánh doanh nghiệp", "description": "Xếp hạng theo điểm tổng hợp và đối chiếu từng chỉ tiêu."},
        ],
        "controls": {"period_mode": period_mode, "period": effective_period, "requested_period": period, "limit": limit, "company_count": len(companies)},
        "warnings": warnings,
        "companies": companies,
        "ranking": [
            {"rank": item["overall"]["rank"], "ticker": item["ticker"], "company_name": item["company_name"], **item["overall"]}
            for item in sorted(companies, key=lambda item: item["overall"]["rank"] if item["overall"]["rank"] is not None else 10_000)
        ],
        "comparison": {"metrics": list(field_map.values())},
        "methodology": {
            "score": "Trung bình có trọng số của sáu nhóm: sinh lời 20%, tăng trưởng 15%, hiệu quả 15%, thanh khoản 15%, đòn bẩy 15%, chất lượng dòng tiền 20%.",
            "status": {"good": "Điểm 70–100 hoặc tín hiệu tuyệt đối thuận lợi", "watch": "Điểm 45–69 hoặc dữ liệu chưa đủ để kết luận mạnh", "risk": "Điểm dưới 45 hoặc tín hiệu tuyệt đối bất lợi"},
            "limitations": [
                "Ngưỡng sàng lọc là heuristic giáo dục; phải so sánh doanh nghiệp cùng ngành và cùng kỳ.",
                "Thiếu khoản mục làm giảm coverage và confidence; hệ thống không tự tạo số thay thế.",
                "Điểm không phải khuyến nghị mua hoặc bán.",
            ],
        },
        "learning": {
            "objective": "Đọc raw data, kiểm tra công thức và so sánh chất lượng tài chính trên cùng một kỳ.",
            "prompt": "Doanh nghiệp nào có tín hiệu cân bằng hơn trong nhóm? Hãy dùng ít nhất hai chỉ tiêu và mở raw input trước khi kết luận.",
            "estimated_minutes": 15,
            "steps": [
                {"key": "frame", "label": "Đặt câu hỏi", "description": "Chọn mã, kỳ và viết giả thuyết trước khi chạy."},
                {"key": "explore", "label": "Khám phá dữ liệu", "description": "Đọc khoản mục gốc và trường dẫn xuất."},
                {"key": "compare", "label": "So sánh bằng chứng", "description": "Đối chiếu chỉ tiêu, coverage và kỳ dữ liệu."},
                {"key": "reflect", "label": "Giải thích", "description": "Viết quan sát, nguyên nhân và giới hạn kết luận."},
            ],
            "reflection_prompts": [
                "Bạn quan sát thấy điều gì từ hai chỉ tiêu quan trọng nhất?",
                "Bằng chứng nào trong raw data hỗ trợ cho nhận định của bạn?",
                "Thiếu dữ liệu hoặc giới hạn nào có thể làm kết luận thay đổi?",
            ],
        },
    }
