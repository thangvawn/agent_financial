from __future__ import annotations

import sys
import json
from datetime import datetime, timezone
from collections.abc import Iterable
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from risk_dashboard.data.financials import FinancialDataError, get_financial_dataset, import_financial_dataset
from risk_dashboard.quant.balance_sheet_strength import BalanceSheetDataError, build_balance_sheet_strength
from risk_dashboard.quant.financial_analysis import analyze_financial_dataset
from risk_dashboard.quant.financial_quality_charts import build_financial_quality_charts
from risk_dashboard.schemas.financials import FinancialDataset, FinancialImportRequest
from risk_dashboard.platform.database import open_app_state_db

router = APIRouter(tags=["Financials"])


class StudentIncomeStatementNoteRequest(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=120)
    company_id: str = Field(..., min_length=1, max_length=40)
    period: str = Field(..., min_length=2, max_length=40)
    note_content: str = Field(..., min_length=1, max_length=4000)
    related_metrics: list[str] = Field(default_factory=list, max_length=20)

SECTION_ALIASES = {
    "overview": "overview",
    "tong-quan": "overview",
    "income": "income_statement",
    "income-statement": "income_statement",
    "ket-qua-kinh-doanh": "income_statement",
    "balance": "balance_sheet",
    "balance-sheet": "balance_sheet",
    "bang-can-doi-ke-toan": "balance_sheet",
    "cash-flow": "cash_flow",
    "cashflow": "cash_flow",
    "luu-chuyen-tien-te": "cash_flow",
    "ratios": "ratios",
    "financial-ratios": "ratios",
    "chi-so-tai-chinh": "ratios",
    "horizontal": "horizontal_analysis",
    "horizontal-analysis": "horizontal_analysis",
    "phan-tich-ngang": "horizontal_analysis",
    "vertical": "vertical_analysis",
    "vertical-analysis": "vertical_analysis",
    "phan-tich-doc": "vertical_analysis",
    "risk": "risk_alerts",
    "risk-alerts": "risk_alerts",
    "canh-bao-rui-ro": "risk_alerts",
    "report": "report",
    "bao-cao": "report",
}

SECTION_ORDER = [
    "overview",
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "ratios",
    "horizontal_analysis",
    "vertical_analysis",
    "risk_alerts",
    "report",
]


@router.get("/financials/status", tags=["Financials"])
def financials_status() -> dict[str, object]:
    return {
        "provider": "vnstock-live",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "notes": [
            "Provider BCTC mặc định hiện dùng vnstock 3.x với luồng live fetch.",
            "Môi trường đã nâng lên Python 3.10+ để tương thích provider mới.",
            "Có thể import cache JSON chuẩn hóa nếu provider live thất bại.",
        ],
    }


@router.get("/financials/{ticker}/analysis", tags=["Financials"])
def financial_analysis(ticker: str, refresh: bool = False):
    try:
        dataset = get_financial_dataset(ticker, refresh=refresh)
    except FinancialDataError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "error": exc.notes[0] if exc.notes else None,
                "hint": exc.hint,
                "notes": exc.notes,
            },
        ) from exc
    return analyze_financial_dataset(dataset).model_dump(mode="json")


@router.get("/financials/{ticker}/sections", tags=["Financials"])
def financial_analysis_sections(ticker: str, refresh: bool = False):
    dataset = _load_dataset_or_503(ticker, refresh=refresh)
    context = _build_financial_context(dataset)
    return {
        "ticker": context["analysis"]["ticker"],
        "source": context["analysis"]["source"],
        "latest_period": context["analysis"].get("latest_period"),
        "sections": [_build_section_payload(section, context) for section in SECTION_ORDER],
    }


@router.get("/financials/{ticker}/sections/{section}", tags=["Financials"])
def financial_analysis_section(ticker: str, section: str, refresh: bool = False):
    resolved = SECTION_ALIASES.get(section.strip().lower())
    if not resolved:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Unknown financial section: {section}",
                "available_sections": SECTION_ORDER,
            },
        )
    dataset = _load_dataset_or_503(ticker, refresh=refresh)
    context = _build_financial_context(dataset)
    return _build_section_payload(resolved, context)


@router.get("/financials/{ticker}/quality-charts", tags=["Financials"])
def financial_quality_charts(ticker: str, refresh: bool = False):
    try:
        dataset = get_financial_dataset(ticker, refresh=refresh)
    except FinancialDataError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "error": exc.notes[0] if exc.notes else None,
                "hint": exc.hint,
                "notes": exc.notes,
            },
        ) from exc
    return build_financial_quality_charts(dataset).model_dump(mode="json")


@router.get("/financials/{ticker}/balance-sheet-strength", tags=["Financials"])
def financial_balance_sheet_strength(ticker: str, period: str | None = None, refresh: bool = False):
    try:
        dataset = get_financial_dataset(ticker, refresh=refresh)
        return build_balance_sheet_strength(dataset, period=period).model_dump(mode="json")
    except FinancialDataError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "error": exc.notes[0] if exc.notes else None,
                "hint": exc.hint,
                "notes": exc.notes,
            },
        ) from exc
    except BalanceSheetDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/financials/{ticker}/peers", tags=["Financials"])
def financial_peer_compare(ticker: str, peers: str | None = None):
    from risk_dashboard.quant.peer_compare import compare_peers

    peer_list = [p.strip().upper() for p in peers.split(",") if p.strip()] if peers else None
    result = compare_peers(ticker, peer_tickers=peer_list)
    return result.to_dict()


@router.get("/financials/cached-tickers", tags=["Financials"])
def list_cached_financial_tickers():
    from risk_dashboard.quant.peer_compare import list_cached_tickers

    tickers = list_cached_tickers()
    return {"tickers": tickers, "count": len(tickers)}


@router.post("/financials/import", tags=["Financials"])
def financial_import(req: FinancialImportRequest):
    path = import_financial_dataset(req.dataset)
    analysis = analyze_financial_dataset(req.dataset)
    return {
        "ok": True,
        "path": str(path),
        "ticker": req.dataset.ticker,
        "periods": len(req.dataset.periods),
        "analysis": analysis.model_dump(mode="json"),
    }


@router.get("/api/bctc/income-statement/overview", tags=["Financials"])
def bctc_income_statement_overview(
    company_id: str,
    period: str | None = None,
    period_type: str | None = None,
    compare_with: str = "same_period_last_year",
    unit: str = "ty_vnd",
    refresh: bool = False,
):
    dataset = _load_dataset_or_503(company_id, refresh=refresh)
    model = _build_income_statement_model(
        dataset,
        period=period,
        period_type=period_type,
        compare_with=compare_with,
        unit=unit,
    )
    return {
        "company": model["company"],
        "period": model["current_period"].get("period"),
        "period_type": model["period_type"],
        "currency": model["current_period"].get("currency") or "VND",
        "unit": unit,
        "compare_with": compare_with,
        "kpis": model["kpis"],
        "data_quality": model["data_quality"],
        "disclaimer": _education_disclaimer(),
    }


@router.get("/api/bctc/income-statement/table", tags=["Financials"])
def bctc_income_statement_table(
    company_id: str,
    start_period: str | None = None,
    end_period: str | None = None,
    period_type: str | None = None,
    unit: str = "ty_vnd",
    refresh: bool = False,
):
    dataset = _load_dataset_or_503(company_id, refresh=refresh)
    model = _build_income_statement_model(
        dataset,
        start_period=start_period,
        end_period=end_period,
        period_type=period_type,
        unit=unit,
    )
    return {
        "company": model["company"],
        "periods": [item["period"] for item in model["periods"]],
        "unit": unit,
        "columns": ["line_item", *[item["period"] for item in model["periods"]], "yoy", "qoq", "learning_comment"],
        "rows": model["table_rows"],
        "data_quality": model["data_quality"],
    }


@router.get("/api/bctc/income-statement/trends", tags=["Financials"])
def bctc_income_statement_trends(
    company_id: str,
    start_period: str | None = None,
    end_period: str | None = None,
    metrics: str | None = None,
    refresh: bool = False,
):
    dataset = _load_dataset_or_503(company_id, refresh=refresh)
    requested = [item.strip() for item in metrics.split(",") if item.strip()] if metrics else None
    model = _build_income_statement_model(dataset, start_period=start_period, end_period=end_period)
    points = model["trend_points"]
    if requested:
        allowed = {"period", "year", "quarter", *requested}
        points = [{key: value for key, value in point.items() if key in allowed} for point in points]
    return {
        "company": model["company"],
        "x_key": "period",
        "series": model["trend_series"],
        "points": points,
        "data_quality": model["data_quality"],
    }


@router.get("/api/bctc/income-statement/margins", tags=["Financials"])
def bctc_income_statement_margins(
    company_id: str,
    start_period: str | None = None,
    end_period: str | None = None,
    refresh: bool = False,
):
    dataset = _load_dataset_or_503(company_id, refresh=refresh)
    model = _build_income_statement_model(dataset, start_period=start_period, end_period=end_period)
    return {
        "company": model["company"],
        "x_key": "period",
        "series": model["margin_series"],
        "points": model["margin_points"],
        "formulas": [formula for formula in _income_formulas() if formula["id"] in {"gross_margin", "operating_margin", "net_margin"}],
        "data_quality": model["data_quality"],
    }


@router.get("/api/bctc/income-statement/formulas", tags=["Financials"])
def bctc_income_statement_formulas():
    return {
        "formulas": _income_formulas(),
        "validation_rules": [
            "Nếu revenue bằng 0 hoặc null thì không tính margin và trả calculation_status = insufficient_data.",
            "Nếu kỳ so sánh không tồn tại thì không tính YoY/QoQ.",
            "Nếu gross_profit được tính từ revenue - cogs thì đánh dấu source = calculated.",
            "Không tự tạo số liệu thiếu.",
        ],
        "disclaimer": _education_disclaimer(),
    }


@router.get("/api/bctc/income-statement/explain-line-item", tags=["Financials"])
def bctc_income_statement_explain_line_item(
    line_item_key: str,
    student_level: str = "beginner",
):
    explanations = _line_item_explanations()
    item = explanations.get(line_item_key)
    if not item:
        raise HTTPException(status_code=404, detail={"message": f"Unknown line item: {line_item_key}"})
    return {
        "line_item_key": line_item_key,
        "student_level": student_level,
        **item,
        "learning_questions": _learning_questions(student_level=student_level, line_item_key=line_item_key),
    }


@router.get("/api/bctc/income-statement/insights", tags=["Financials"])
def bctc_income_statement_insights(
    company_id: str,
    period: str | None = None,
    compare_with: str = "same_period_last_year",
    refresh: bool = False,
):
    dataset = _load_dataset_or_503(company_id, refresh=refresh)
    model = _build_income_statement_model(dataset, period=period, compare_with=compare_with)
    return {
        "company": model["company"],
        "period": model["current_period"].get("period"),
        "compare_with": compare_with,
        "insights": model["insights"],
        "disclaimer": _education_disclaimer(),
    }


@router.get("/api/bctc/income-statement/questions", tags=["Financials"])
def bctc_income_statement_questions(
    company_id: str,
    period: str | None = None,
    student_level: str = "beginner",
    refresh: bool = False,
):
    dataset = _load_dataset_or_503(company_id, refresh=refresh)
    model = _build_income_statement_model(dataset, period=period)
    return {
        "company": model["company"],
        "period": model["current_period"].get("period"),
        "student_level": student_level,
        "questions": _learning_questions(student_level=student_level),
        "learning_flow": _income_learning_flow(),
    }


@router.post("/api/bctc/income-statement/student-notes", tags=["Financials"])
def bctc_income_statement_student_notes(req: StudentIncomeStatementNoteRequest):
    now = datetime.now(timezone.utc).isoformat()
    note_id = f"income-note-{uuid4().hex}"
    with open_app_state_db() as conn:
        conn.execute(
            """
            INSERT INTO student_income_statement_notes (
              note_id, student_id, company_id, financial_period, note_content,
              related_metrics_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                note_id,
                req.student_id,
                req.company_id.upper().strip(),
                req.period,
                req.note_content,
                json.dumps(req.related_metrics, ensure_ascii=False),
                now,
                now,
            ),
        )
        conn.commit()
    return {
        "ok": True,
        "note_id": note_id,
        "student_id": req.student_id,
        "company_id": req.company_id.upper().strip(),
        "period": req.period,
        "created_at": now,
    }


@router.get("/api/bctc/income-statement/instructor-review", tags=["Financials"])
def bctc_income_statement_instructor_review(
    company_id: str,
    period: str | None = None,
    student_id: str | None = None,
):
    query = """
        SELECT note_id, student_id, company_id, financial_period, note_content,
               related_metrics_json, created_at, updated_at
        FROM student_income_statement_notes
        WHERE company_id = ?
    """
    params: list[Any] = [company_id.upper().strip()]
    if period:
        query += " AND financial_period = ?"
        params.append(period)
    if student_id:
        query += " AND student_id = ?"
        params.append(student_id)
    query += " ORDER BY updated_at DESC"
    with open_app_state_db() as conn:
        rows = conn.execute(query, params).fetchall()
    notes = [
        {
            "note_id": row["note_id"],
            "student_id": row["student_id"],
            "company_id": row["company_id"],
            "period": row["financial_period"],
            "note_content": row["note_content"],
            "related_metrics": json.loads(row["related_metrics_json"] or "[]"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]
    return {
        "company_id": company_id.upper().strip(),
        "period": period,
        "student_id": student_id,
        "note_count": len(notes),
        "notes": notes,
        "review_guidance": [
            "Kiểm tra sinh viên có nêu được bằng chứng từ doanh thu, giá vốn, biên lợi nhuận hay không.",
            "Ưu tiên phản hồi về công thức và lập luận, không chấm theo kết luận tốt/xấu tuyệt đối.",
            "Nhắc sinh viên tránh diễn giải thành khuyến nghị mua/bán cổ phiếu.",
        ],
    }


def _load_dataset_or_503(ticker: str, *, refresh: bool = False) -> FinancialDataset:
    try:
        return get_financial_dataset(ticker, refresh=refresh)
    except FinancialDataError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": exc.message,
                "error": exc.notes[0] if exc.notes else None,
                "hint": exc.hint,
                "notes": exc.notes,
            },
        ) from exc


def _build_income_statement_model(
    dataset: FinancialDataset,
    *,
    period: str | None = None,
    start_period: str | None = None,
    end_period: str | None = None,
    period_type: str | None = None,
    compare_with: str = "same_period_last_year",
    unit: str = "ty_vnd",
) -> dict[str, Any]:
    raw_periods = [p.model_dump(mode="json") for p in dataset.periods]
    periods = sorted(raw_periods, key=lambda item: (item.get("year") or 0, item.get("quarter") or 0, str(item.get("period") or "")))
    periods = _filter_income_periods(periods, start_period=start_period, end_period=end_period, period_type=period_type)
    if not periods:
        raise HTTPException(status_code=404, detail={"message": "Không có kỳ BCTC phù hợp cho tab Kết quả kinh doanh."})

    enriched = [_enrich_income_period(item) for item in periods]
    current = _select_income_period(enriched, period)
    previous = _previous_period(enriched, current)
    yoy_ref = _same_period_last_year(enriched, current)
    compare_ref = previous if compare_with == "previous_period" else yoy_ref
    data_quality = _income_data_quality(enriched)

    return {
        "company": {
            "id": dataset.ticker.lower(),
            "name": dataset.company_name or f"CTCP {dataset.ticker}",
            "ticker": dataset.ticker,
            "industry": dataset.industry,
            "exchange": dataset.exchange,
        },
        "period_type": "quarter" if current.get("quarter") else "year",
        "periods": enriched[-8:],
        "current_period": current,
        "compare_period": compare_ref,
        "kpis": _income_kpis(current, previous=previous, yoy_ref=yoy_ref, compare_ref=compare_ref),
        "table_rows": _income_table_rows(enriched[-8:]),
        "trend_series": [
            {"key": "revenue", "label": "Doanh thu thuần", "type": "bar"},
            {"key": "cogs", "label": "Giá vốn hàng bán", "type": "bar"},
            {"key": "gross_profit", "label": "Lợi nhuận gộp", "type": "line"},
            {"key": "operating_profit", "label": "Lợi nhuận hoạt động", "type": "line"},
            {"key": "net_profit", "label": "LNST", "type": "line"},
        ],
        "trend_points": [_income_trend_point(item) for item in enriched[-12:]],
        "margin_series": [
            {"key": "gross_margin", "label": "Biên gộp", "type": "line"},
            {"key": "operating_margin", "label": "Biên hoạt động", "type": "line"},
            {"key": "net_margin", "label": "Biên ròng", "type": "line"},
        ],
        "margin_points": [_income_margin_point(item) for item in enriched[-12:]],
        "insights": _income_rule_insights(current, previous=previous, yoy_ref=yoy_ref),
        "data_quality": data_quality,
        "unit": unit,
    }


def _filter_income_periods(
    periods: list[dict[str, Any]],
    *,
    start_period: str | None,
    end_period: str | None,
    period_type: str | None,
) -> list[dict[str, Any]]:
    filtered = []
    for item in periods:
        item_period = str(item.get("period") or "")
        if period_type == "quarter" and not item.get("quarter"):
            continue
        if period_type == "year" and item.get("quarter"):
            continue
        if start_period and item_period < start_period:
            continue
        if end_period and item_period > end_period:
            continue
        filtered.append(item)
    return filtered


def _select_income_period(periods: list[dict[str, Any]], period: str | None) -> dict[str, Any]:
    if period:
        for item in periods:
            if item.get("period") == period:
                return item
        raise HTTPException(status_code=404, detail={"message": f"Không tìm thấy kỳ báo cáo {period}."})
    return periods[-1]


def _enrich_income_period(item: dict[str, Any]) -> dict[str, Any]:
    revenue = _number_or_none(item.get("revenue"))
    gross_profit_reported = _number_or_none(item.get("gross_profit"))
    cogs = _number_or_none(item.get("cogs"))
    if cogs is None and revenue is not None and gross_profit_reported is not None:
        cogs = revenue - gross_profit_reported
        cogs_source = "calculated_from_revenue_minus_gross_profit"
    elif cogs is not None:
        cogs_source = "reported"
    else:
        cogs_source = "missing"

    if gross_profit_reported is not None:
        gross_profit = gross_profit_reported
        gross_profit_source = "reported"
    elif revenue is not None and cogs is not None:
        gross_profit = revenue - cogs
        gross_profit_source = "calculated"
    else:
        gross_profit = None
        gross_profit_source = "insufficient_data"

    operating_profit = _number_or_none(item.get("operating_profit") or item.get("ebit"))
    ebit = _number_or_none(item.get("ebit") or operating_profit)
    net_profit = _number_or_none(item.get("net_profit") or item.get("net_income"))
    enriched = {
        **item,
        "cogs": cogs,
        "cogs_source": cogs_source,
        "gross_profit": gross_profit,
        "gross_profit_source": gross_profit_source,
        "operating_profit": operating_profit,
        "ebit": ebit,
        "net_profit": net_profit,
        "gross_margin": _calculated_ratio(gross_profit, revenue, "gross_margin", "gross_profit / revenue"),
        "operating_margin": _calculated_ratio(operating_profit, revenue, "operating_margin", "operating_profit / revenue"),
        "net_margin": _calculated_ratio(net_profit, revenue, "net_margin", "net_profit / revenue"),
    }
    return enriched


def _calculated_ratio(numerator: Any, denominator: Any, formula_id: str, expression: str) -> dict[str, Any]:
    if numerator is None or denominator in (None, 0):
        return {
            "value": None,
            "formula_id": formula_id,
            "expression": expression,
            "calculation_status": "insufficient_data",
            "message": "Không đủ dữ liệu để tính biên lợi nhuận.",
            "inputs": {"numerator": numerator, "denominator": denominator},
        }
    return {
        "value": float(numerator) / float(denominator),
        "formula_id": formula_id,
        "expression": expression,
        "calculation_status": "ok",
        "inputs": {"numerator": numerator, "denominator": denominator},
    }


def _income_kpis(
    current: dict[str, Any],
    *,
    previous: dict[str, Any] | None,
    yoy_ref: dict[str, Any] | None,
    compare_ref: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    return [
        _income_kpi("revenue", "Doanh thu thuần", current.get("revenue"), current=current, previous=previous, yoy_ref=yoy_ref, compare_ref=compare_ref),
        _income_kpi("gross_profit", "Lợi nhuận gộp", current.get("gross_profit"), current=current, previous=previous, yoy_ref=yoy_ref, compare_ref=compare_ref, formula_id="gross_profit", source=current.get("gross_profit_source")),
        _income_kpi("ebit", "EBIT / Lợi nhuận hoạt động", current.get("ebit") or current.get("operating_profit"), current=current, previous=previous, yoy_ref=yoy_ref, compare_ref=compare_ref),
        _income_kpi("net_profit", "Lợi nhuận sau thuế", current.get("net_profit"), current=current, previous=previous, yoy_ref=yoy_ref, compare_ref=compare_ref),
        _margin_kpi("gross_margin", "Biên lợi nhuận gộp", current.get("gross_margin"), previous=previous),
        _margin_kpi("net_margin", "Biên lợi nhuận ròng", current.get("net_margin"), previous=previous),
    ]


def _income_kpi(
    key: str,
    label: str,
    value: Any,
    *,
    current: dict[str, Any],
    previous: dict[str, Any] | None,
    yoy_ref: dict[str, Any] | None,
    compare_ref: dict[str, Any] | None,
    formula_id: str | None = None,
    source: str = "reported",
) -> dict[str, Any]:
    yoy = _growth_ratio(value, (yoy_ref or {}).get(key))
    qoq = _growth_ratio(value, (previous or {}).get(key))
    compare_growth = _growth_ratio(value, (compare_ref or {}).get(key))
    return {
        "key": key,
        "label": label,
        "value": value,
        "yoy_growth": yoy,
        "qoq_growth": qoq,
        "compare_growth": compare_growth,
        "status": _growth_status(compare_growth),
        "source": source,
        "formula": _formula_by_id(formula_id) if formula_id else None,
        "calculation_status": "ok" if value is not None else "insufficient_data",
        "evidence": {
            "current_period": current.get("period"),
            "same_period_last_year": (yoy_ref or {}).get("period"),
            "previous_period": (previous or {}).get("period"),
            "current_value": value,
            "yoy_reference_value": (yoy_ref or {}).get(key),
            "previous_value": (previous or {}).get(key),
        },
    }


def _margin_kpi(
    key: str,
    label: str,
    calculation: dict[str, Any] | None,
    *,
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    formula_id = key
    value = (calculation or {}).get("value")
    previous_value = ((previous or {}).get(key) or {}).get("value")
    change_point = value - previous_value if value is not None and previous_value is not None else None
    return {
        "key": key,
        "label": label,
        "value": value,
        "change_point": change_point,
        "status": "warning" if change_point is not None and change_point < 0 else "positive" if change_point is not None else "insufficient_data",
        "formula": _formula_by_id(formula_id),
        "calculation_status": (calculation or {}).get("calculation_status") or "insufficient_data",
        "message": (calculation or {}).get("message"),
        "evidence": {
            "inputs": (calculation or {}).get("inputs"),
            "previous_value": previous_value,
        },
    }


def _income_table_rows(periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    line_items = [
        ("revenue", "Doanh thu thuần"),
        ("cogs", "Giá vốn hàng bán"),
        ("gross_profit", "Lợi nhuận gộp"),
        ("operating_profit", "Lợi nhuận hoạt động"),
        ("ebit", "EBIT"),
        ("net_profit", "Lợi nhuận sau thuế"),
        ("gross_margin", "Biên lợi nhuận gộp"),
        ("operating_margin", "Biên lợi nhuận hoạt động"),
        ("net_margin", "Biên lợi nhuận ròng"),
    ]
    rows = []
    latest = periods[-1] if periods else {}
    previous = periods[-2] if len(periods) >= 2 else None
    yoy_ref = _same_period_last_year(periods, latest) if latest else None
    for key, label in line_items:
        values = []
        for item in periods:
            raw = item.get(key)
            values.append({"period": item.get("period"), "value": raw.get("value") if isinstance(raw, dict) else raw})
        current_value = values[-1]["value"] if values else None
        rows.append({
            "line_item_key": key,
            "line_item_name": label,
            "values": values,
            "yoy": _growth_ratio(current_value, _line_value(yoy_ref, key)),
            "qoq": _growth_ratio(current_value, _line_value(previous, key)),
            "calculation_status": "ok" if current_value is not None else "insufficient_data",
            "learning_comment": _line_learning_comment(key, current_value, yoy=_growth_ratio(current_value, _line_value(yoy_ref, key))),
        })
    return rows


def _income_trend_point(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "period": item.get("period"),
        "year": item.get("year"),
        "quarter": item.get("quarter"),
        "revenue": item.get("revenue"),
        "cogs": item.get("cogs"),
        "gross_profit": item.get("gross_profit"),
        "operating_profit": item.get("operating_profit"),
        "ebit": item.get("ebit"),
        "net_profit": item.get("net_profit"),
    }


def _income_margin_point(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "period": item.get("period"),
        "year": item.get("year"),
        "quarter": item.get("quarter"),
        "gross_margin": (item.get("gross_margin") or {}).get("value"),
        "operating_margin": (item.get("operating_margin") or {}).get("value"),
        "net_margin": (item.get("net_margin") or {}).get("value"),
        "gross_margin_status": (item.get("gross_margin") or {}).get("calculation_status"),
        "operating_margin_status": (item.get("operating_margin") or {}).get("calculation_status"),
        "net_margin_status": (item.get("net_margin") or {}).get("calculation_status"),
    }


def _income_rule_insights(
    current: dict[str, Any],
    *,
    previous: dict[str, Any] | None,
    yoy_ref: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    revenue_yoy = _growth_ratio(current.get("revenue"), (yoy_ref or {}).get("revenue"))
    net_profit_yoy = _growth_ratio(current.get("net_profit"), (yoy_ref or {}).get("net_profit"))
    cogs_yoy = _growth_ratio(current.get("cogs"), (yoy_ref or {}).get("cogs"))
    financial_expense_yoy = _growth_ratio(current.get("financial_expense"), (yoy_ref or {}).get("financial_expense"))
    gross_margin_current = (current.get("gross_margin") or {}).get("value")
    gross_margin_previous = ((previous or {}).get("gross_margin") or {}).get("value")
    rules = []
    if revenue_yoy is not None and revenue_yoy > 0:
        rules.append(_insight("revenue_growth_positive", "Doanh thu tăng so với cùng kỳ, cho thấy quy mô hoạt động có sự mở rộng.", "info", {"revenue_yoy_growth": revenue_yoy}))
    if None not in (net_profit_yoy, revenue_yoy) and net_profit_yoy > revenue_yoy:
        rules.append(_insight("net_profit_growth_faster_than_revenue", "LNST tăng nhanh hơn doanh thu, có thể cho thấy hiệu quả sinh lời được cải thiện hoặc chi phí được kiểm soát tốt hơn.", "positive", {"net_profit_yoy_growth": net_profit_yoy, "revenue_yoy_growth": revenue_yoy}))
    if None not in (cogs_yoy, revenue_yoy) and cogs_yoy > revenue_yoy:
        rules.append(_insight("cogs_growth_faster_than_revenue", "Giá vốn tăng nhanh hơn doanh thu, cần kiểm tra áp lực chi phí đầu vào hoặc thay đổi cơ cấu sản phẩm.", "warning", {"cogs_yoy_growth": cogs_yoy, "revenue_yoy_growth": revenue_yoy}))
    if None not in (gross_margin_current, gross_margin_previous) and gross_margin_current < gross_margin_previous:
        rules.append(_insight("gross_margin_decline", "Biên lợi nhuận gộp giảm so với kỳ trước, cần phân tích nguyên nhân từ giá vốn hoặc giá bán.", "warning", {"gross_margin_current": gross_margin_current, "gross_margin_previous": gross_margin_previous}))
    if None not in (revenue_yoy, net_profit_yoy) and revenue_yoy > 0 and net_profit_yoy < 0:
        rules.append(_insight("revenue_up_profit_down", "Doanh thu tăng nhưng lợi nhuận sau thuế giảm, cần kiểm tra chi phí, biên lợi nhuận và yếu tố bất thường.", "risk", {"revenue_yoy_growth": revenue_yoy, "net_profit_yoy_growth": net_profit_yoy}))
    if None not in (financial_expense_yoy, revenue_yoy) and financial_expense_yoy > revenue_yoy:
        rules.append(_insight("financial_expense_increase", "Chi phí tài chính tăng nhanh hơn doanh thu, có thể ảnh hưởng đến lợi nhuận ròng.", "warning", {"financial_expense_yoy_growth": financial_expense_yoy, "revenue_yoy_growth": revenue_yoy}))
    return rules


def _insight(rule_id: str, message: str, severity: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "message": message,
        "severity": severity,
        "evidence_json": evidence,
        "scope": "educational_analysis",
    }


def _income_data_quality(periods: list[dict[str, Any]]) -> dict[str, Any]:
    required = ("revenue", "cogs", "gross_profit", "net_profit")
    missing_by_period = []
    for item in periods:
        missing = []
        for key in required:
            value = (item.get(key) or {}).get("value") if isinstance(item.get(key), dict) else item.get(key)
            if value is None:
                missing.append(key)
        if missing:
            missing_by_period.append({"period": item.get("period"), "missing_fields": missing})
    return {
        "status": "ok" if not missing_by_period else "partial",
        "missing_by_period": missing_by_period,
        "notes": ["Backend không tự tạo số liệu thiếu; chỉ tính khoản mục khi đủ dữ liệu đầu vào."],
    }


def _income_formulas() -> list[dict[str, Any]]:
    return [
        {"id": "gross_profit", "name": "Lợi nhuận gộp", "expression": "gross_profit = revenue - cogs", "inputs": ["revenue", "cogs"]},
        {"id": "gross_margin", "name": "Biên lợi nhuận gộp", "expression": "gross_margin = gross_profit / revenue", "inputs": ["gross_profit", "revenue"]},
        {"id": "operating_margin", "name": "Biên lợi nhuận hoạt động", "expression": "operating_margin = operating_profit / revenue", "inputs": ["operating_profit", "revenue"]},
        {"id": "net_margin", "name": "Biên lợi nhuận ròng", "expression": "net_margin = net_profit / revenue", "inputs": ["net_profit", "revenue"]},
        {"id": "yoy_growth", "name": "Tăng trưởng cùng kỳ", "expression": "yoy_growth = (current_period_value - same_period_last_year_value) / same_period_last_year_value", "inputs": ["current_period_value", "same_period_last_year_value"]},
        {"id": "qoq_growth", "name": "Tăng trưởng so với quý trước", "expression": "qoq_growth = (current_period_value - previous_period_value) / previous_period_value", "inputs": ["current_period_value", "previous_period_value"]},
        {"id": "cost_to_revenue_ratio", "name": "Tỷ lệ chi phí trên doanh thu", "expression": "cost_to_revenue_ratio = expense_item / revenue", "inputs": ["expense_item", "revenue"]},
    ]


def _formula_by_id(formula_id: str | None) -> dict[str, Any] | None:
    if not formula_id:
        return None
    return next((item for item in _income_formulas() if item["id"] == formula_id), None)


def _line_item_explanations() -> dict[str, dict[str, Any]]:
    return {
        "revenue": {
            "definition": "Doanh thu thuần là khoản doanh thu còn lại sau khi trừ các khoản giảm trừ doanh thu.",
            "formula": None,
            "interpretation": "Đây là điểm bắt đầu để phân tích khả năng tạo doanh thu của doanh nghiệp.",
            "common_mistake": "Không nên chỉ nhìn doanh thu tăng mà bỏ qua biên lợi nhuận và dòng tiền.",
        },
        "cogs": {
            "definition": "Giá vốn hàng bán là chi phí trực tiếp liên quan đến hàng hóa hoặc dịch vụ đã bán.",
            "formula": None,
            "interpretation": "Nếu giá vốn tăng nhanh hơn doanh thu, biên lợi nhuận gộp có thể bị thu hẹp.",
            "common_mistake": "Nhầm giá vốn với toàn bộ chi phí hoạt động.",
        },
        "gross_profit": {
            "definition": "Lợi nhuận gộp cho biết doanh nghiệp còn lại bao nhiêu sau khi trừ chi phí trực tiếp.",
            "formula": "gross_profit = revenue - cogs",
            "interpretation": "Khoản này giúp phân tích sức mạnh giá bán, cơ cấu sản phẩm và chi phí đầu vào.",
            "common_mistake": "Xem lợi nhuận gộp là lợi nhuận cuối cùng.",
        },
        "net_profit": {
            "definition": "Lợi nhuận sau thuế là lợi nhuận cuối cùng sau khi trừ tất cả chi phí và thuế.",
            "formula": "net_profit = profit_before_tax - tax_expense",
            "interpretation": "Cần so sánh thêm với dòng tiền từ hoạt động kinh doanh để đánh giá chất lượng lợi nhuận.",
            "common_mistake": "Chỉ nhìn LNST để kết luận doanh nghiệp tốt hoặc xấu.",
        },
    }


def _learning_questions(*, student_level: str = "beginner", line_item_key: str | None = None) -> list[dict[str, str]]:
    base = [
        "Doanh thu tăng nhưng biên lợi nhuận gộp giảm nói lên điều gì?",
        "Vì sao LNST có thể tăng nhanh hơn doanh thu?",
        "Chi phí nào ảnh hưởng nhiều nhất đến lợi nhuận kỳ này?",
        "Chỉ nhìn LNST có đủ để kết luận doanh nghiệp tốt không?",
        "Doanh nghiệp đang tăng trưởng nhờ doanh thu hay nhờ kiểm soát chi phí?",
    ]
    if student_level == "advanced":
        base.extend([
            "Biên hoạt động thay đổi có đến từ đòn bẩy vận hành hay yếu tố một lần?",
            "Nếu giá vốn tăng nhanh hơn doanh thu, cần kiểm tra thêm dữ liệu nào?",
        ])
    if line_item_key:
        base.insert(0, f"Khoản mục {line_item_key} ảnh hưởng đến luồng Doanh thu → LNST như thế nào?")
    return [{"id": f"q{index + 1}", "question": question, "student_level": student_level} for index, question in enumerate(base)]


def _income_learning_flow() -> list[dict[str, Any]]:
    steps = [
        "Quan sát doanh thu",
        "Kiểm tra giá vốn hàng bán",
        "Tính và phân tích lợi nhuận gộp",
        "Kiểm tra chi phí bán hàng, chi phí quản lý và chi phí tài chính",
        "Tính lợi nhuận hoạt động, lợi nhuận trước thuế và lợi nhuận sau thuế",
        "Tính các chỉ số biên lợi nhuận",
        "So sánh YoY, QoQ hoặc theo nhiều kỳ",
        "Sinh viên viết nhận định và kết luận",
    ]
    return [{"order": index + 1, "label": step} for index, step in enumerate(steps)]


def _education_disclaimer() -> str:
    return "Dữ liệu và insight chỉ phục vụ học tập phân tích BCTC, không phải khuyến nghị mua, bán hoặc nắm giữ."


def _previous_period(periods: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any] | None:
    try:
        index = periods.index(current)
    except ValueError:
        return None
    if index <= 0:
        return None
    return periods[index - 1]


def _same_period_last_year(periods: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any] | None:
    year = current.get("year")
    if not year:
        return None
    quarter = current.get("quarter")
    for item in periods:
        if item.get("year") == year - 1 and item.get("quarter") == quarter:
            return item
    return None


def _line_value(period: dict[str, Any] | None, key: str) -> Any:
    if not period:
        return None
    raw = period.get(key)
    return raw.get("value") if isinstance(raw, dict) else raw


def _growth_ratio(current: Any, previous: Any) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (float(current) - float(previous)) / abs(float(previous))


def _growth_status(value: float | None) -> str:
    if value is None:
        return "insufficient_data"
    if value > 0:
        return "positive"
    if value < 0:
        return "warning"
    return "neutral"


def _line_learning_comment(key: str, value: Any, *, yoy: float | None) -> str:
    if value is None:
        return "Thiếu dữ liệu, chưa đủ cơ sở tính toán."
    if key in {"gross_margin", "operating_margin", "net_margin"}:
        return "Đọc cùng doanh thu và cơ cấu chi phí để hiểu chất lượng lợi nhuận."
    if yoy is None:
        return "Chưa có kỳ cùng kỳ để so sánh YoY."
    if yoy > 0:
        return "Tăng so với cùng kỳ; cần kiểm tra động lực tăng đến từ doanh thu hay kiểm soát chi phí."
    if yoy < 0:
        return "Giảm so với cùng kỳ; cần kiểm tra nguyên nhân từ doanh thu, giá vốn hoặc chi phí."
    return "Không đổi đáng kể so với cùng kỳ."


def _number_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_financial_context(dataset: FinancialDataset) -> dict[str, Any]:
    analysis = analyze_financial_dataset(dataset).model_dump(mode="json")
    quality = build_financial_quality_charts(dataset).model_dump(mode="json")
    balance: dict[str, Any] | None = None
    try:
        balance = build_balance_sheet_strength(dataset).model_dump(mode="json")
    except BalanceSheetDataError:
        balance = None
    periods = [p.model_dump(mode="json") for p in dataset.periods]
    sorted_periods = sorted(
        periods,
        key=lambda item: (item.get("year") or 0, item.get("quarter") or 0, str(item.get("period") or "")),
    )
    latest = sorted_periods[-1] if sorted_periods else {}
    previous = sorted_periods[-2] if len(sorted_periods) >= 2 else {}
    return {
        "analysis": analysis,
        "quality": quality,
        "balance": balance,
        "periods": sorted_periods,
        "latest": latest,
        "previous": previous,
    }


def _build_section_payload(section: str, context: dict[str, Any]) -> dict[str, Any]:
    builders = {
        "overview": _overview_section,
        "income_statement": _income_statement_section,
        "balance_sheet": _balance_sheet_section,
        "cash_flow": _cash_flow_section,
        "ratios": _ratios_section,
        "horizontal_analysis": _horizontal_analysis_section,
        "vertical_analysis": _vertical_analysis_section,
        "risk_alerts": _risk_alerts_section,
        "report": _report_section,
    }
    payload = builders[section](context)
    analysis = context["analysis"]
    return {
        "section": section,
        "ticker": analysis["ticker"],
        "company_name": analysis.get("company_name"),
        "latest_period": analysis.get("latest_period"),
        "source": analysis.get("source"),
        **payload,
    }


def _overview_section(context: dict[str, Any]) -> dict[str, Any]:
    analysis = context["analysis"]
    summary = analysis.get("summary") or {}
    return {
        "title": "Tổng quan",
        "learning_goals": [
            "Hiểu xu hướng doanh thu và lợi nhuận.",
            "Đánh giá chất lượng lợi nhuận qua dòng tiền.",
            "Nhận diện rủi ro tài chính nổi bật.",
        ],
        "company": {
            "ticker": analysis["ticker"],
            "name": analysis.get("company_name") or f"CTCP {analysis['ticker']}",
            "exchange": analysis.get("exchange"),
            "industry": analysis.get("industry"),
            "period": analysis.get("latest_period"),
        },
        "summary_cards": _summary_cards(summary),
        "ai_summary": _ai_summary_bullets(analysis),
        "health_radar": analysis.get("health_radar") or {},
        "highlights": analysis.get("highlights") or [],
    }


def _income_statement_section(context: dict[str, Any]) -> dict[str, Any]:
    periods = context["periods"]
    latest = context["latest"]
    previous = context["previous"]
    rows = [
        _statement_row("Doanh thu thuần", "revenue", latest, previous),
        _statement_row("Lợi nhuận gộp", "gross_profit", latest, previous),
        _statement_row("Lợi nhuận HĐKD", "operating_profit", latest, previous),
        _statement_row("LNST", "net_income", latest, previous),
    ]
    return {
        "title": "Kết quả kinh doanh",
        "table": rows,
        "chart": {
            "type": "combo",
            "x_key": "period",
            "series": [
                {"key": "revenue", "label": "Doanh thu thuần", "type": "bar"},
                {"key": "net_income", "label": "LNST", "type": "bar"},
                {"key": "net_margin_pct", "label": "Biên ròng", "type": "line"},
            ],
            "points": _pick_period_fields(periods, ["period", "year", "quarter", "revenue", "net_income"]),
        },
        "margin_analysis": (context["quality"].get("margin_analysis") or {}),
        "insights": _income_insights(context["analysis"]),
    }


def _balance_sheet_section(context: dict[str, Any]) -> dict[str, Any]:
    balance = context["balance"]
    latest = context["latest"]
    previous = context["previous"]
    rows = [
        _statement_row("Tổng tài sản", "total_assets", latest, previous),
        _statement_row("Nợ phải trả", "total_liabilities", latest, previous),
        _statement_row("Vốn chủ sở hữu", "equity", latest, previous),
        _statement_row("Tiền & tương đương", "cash", latest, previous),
        _statement_row("Hàng tồn kho", "inventory", latest, previous),
        _statement_row("Phải thu", "receivables", latest, previous),
    ]
    return {
        "title": "Bảng cân đối kế toán",
        "table": rows,
        "composition": {
            "assets": (balance or {}).get("asset_items", []),
            "funding": (balance or {}).get("funding_items", []),
        },
        "ratios": (balance or {}).get("ratios", {}),
        "interpretation": (balance or {}).get("interpretation", {}),
        "red_flags": (balance or {}).get("red_flags", []),
    }


def _cash_flow_section(context: dict[str, Any]) -> dict[str, Any]:
    latest = context["latest"]
    previous = context["previous"]
    cash_quality = context["quality"].get("cash_flow_quality") or {}
    rows = [
        _statement_row("CFO", "operating_cash_flow", latest, previous),
        _statement_row("CFI", "investing_cash_flow", latest, previous),
        _statement_row("CFF", "financing_cash_flow", latest, previous),
        _statement_row("CAPEX", "capex", latest, previous),
    ]
    return {
        "title": "Lưu chuyển tiền tệ",
        "table": rows,
        "cash_flow_quality": cash_quality,
        "formulas": cash_quality.get("formulas", {}),
        "insights": [
            "Ưu tiên đọc CFO so với LNST để đánh giá chất lượng lợi nhuận.",
            "FCF âm kéo dài cần được giải thích bằng chu kỳ đầu tư hoặc áp lực vận hành.",
        ],
    }


def _ratios_section(context: dict[str, Any]) -> dict[str, Any]:
    summary = context["analysis"].get("summary") or {}
    ratio_groups = {
        "profitability": [
            _ratio("Gross margin", summary.get("gross_margin_pct"), "%"),
            _ratio("Operating margin", summary.get("operating_margin_pct"), "%"),
            _ratio("Net margin", summary.get("net_margin_pct"), "%"),
            _ratio("ROE", summary.get("roe_pct"), "%"),
            _ratio("ROA", summary.get("roa_pct"), "%"),
            _ratio("ROIC", summary.get("roic_pct"), "%"),
        ],
        "liquidity": [
            _ratio("Current ratio", summary.get("current_ratio"), "x"),
            _ratio("Quick ratio", summary.get("quick_ratio"), "x"),
            _ratio("Cash ratio", summary.get("cash_ratio"), "x"),
        ],
        "leverage": [
            _ratio("Debt / Equity", summary.get("debt_to_equity"), "x"),
            _ratio("Net debt / EBITDA", summary.get("net_debt_to_ebitda"), "x"),
            _ratio("Interest coverage", summary.get("interest_coverage"), "x"),
        ],
        "cash_quality": [
            _ratio("OCF / Net income", summary.get("ocf_to_net_income"), "x"),
            _ratio("FCF margin", summary.get("fcf_margin_pct"), "%"),
            _ratio("Asset turnover", summary.get("asset_turnover"), "x"),
        ],
    }
    return {
        "title": "Chỉ số tài chính",
        "groups": ratio_groups,
        "dupont": summary.get("dupont"),
        "health_radar": context["analysis"].get("health_radar") or {},
    }


def _horizontal_analysis_section(context: dict[str, Any]) -> dict[str, Any]:
    periods = context["periods"]
    rows = []
    for current, previous in _pair_adjacent(periods):
        rows.append({
            "period": current.get("period"),
            "metrics": [
                _statement_row("Doanh thu", "revenue", current, previous),
                _statement_row("LNST", "net_income", current, previous),
                _statement_row("Tổng tài sản", "total_assets", current, previous),
                _statement_row("Nợ phải trả", "total_liabilities", current, previous),
                _statement_row("CFO", "operating_cash_flow", current, previous),
            ],
        })
    return {
        "title": "Phân tích ngang",
        "basis": "So sánh thay đổi tuyệt đối và phần trăm giữa các kỳ liền kề.",
        "rows": rows[-8:],
        "flags": _horizontal_flags(rows),
    }


def _vertical_analysis_section(context: dict[str, Any]) -> dict[str, Any]:
    latest = context["latest"]
    income_base = latest.get("revenue")
    asset_base = latest.get("total_assets")
    return {
        "title": "Phân tích dọc",
        "basis": "Chuẩn hóa từng khoản mục theo doanh thu hoặc tổng tài sản.",
        "income_common_size": [
            _common_size("Doanh thu", latest.get("revenue"), income_base),
            _common_size("Lợi nhuận gộp", latest.get("gross_profit"), income_base),
            _common_size("Lợi nhuận HĐKD", latest.get("operating_profit"), income_base),
            _common_size("LNST", latest.get("net_income"), income_base),
            _common_size("CFO", latest.get("operating_cash_flow"), income_base),
        ],
        "balance_common_size": [
            _common_size("Tiền", latest.get("cash"), asset_base),
            _common_size("Phải thu", latest.get("receivables"), asset_base),
            _common_size("Hàng tồn kho", latest.get("inventory"), asset_base),
            _common_size("Tài sản cố định", latest.get("fixed_assets"), asset_base),
            _common_size("Nợ phải trả", latest.get("total_liabilities"), asset_base),
            _common_size("Vốn chủ sở hữu", latest.get("equity"), asset_base),
        ],
    }


def _risk_alerts_section(context: dict[str, Any]) -> dict[str, Any]:
    analysis = context["analysis"]
    balance = context["balance"] or {}
    summary = analysis.get("summary") or {}
    return {
        "title": "Cảnh báo rủi ro",
        "flags": analysis.get("flags", []),
        "balance_sheet_red_flags": balance.get("red_flags", []),
        "risk_scores": {
            "altman_z": summary.get("altman_z"),
            "piotroski_f": summary.get("piotroski_f"),
            "cash_quality": (context["quality"].get("cash_flow_quality") or {}).get("latest", {}),
        },
        "questions": [
            "Doanh thu tăng có đi kèm dòng tiền không?",
            "Biên lợi nhuận giảm do giá vốn, chi phí hay yếu tố một lần?",
            "Đòn bẩy có vượt sức chịu đựng dòng tiền không?",
            "Tồn kho/phải thu có tăng nhanh hơn doanh thu không?",
        ],
    }


def _report_section(context: dict[str, Any]) -> dict[str, Any]:
    analysis = context["analysis"]
    return {
        "title": "Báo cáo",
        "status": "draft",
        "sections": [
            {"id": "company_snapshot", "title": "Thông tin doanh nghiệp", "ready": True},
            {"id": "ai_summary", "title": "AI Financial Summary", "ready": True},
            {"id": "kpi", "title": "KPI tổng quan", "ready": True},
            {"id": "income_statement", "title": "Kết quả kinh doanh", "ready": True},
            {"id": "balance_sheet", "title": "Bảng cân đối kế toán", "ready": bool(context["balance"])},
            {"id": "cash_flow", "title": "Lưu chuyển tiền tệ", "ready": True},
            {"id": "risk_alerts", "title": "Cảnh báo rủi ro", "ready": True},
            {"id": "conclusion", "title": "Kết luận học tập", "ready": False},
        ],
        "suggested_conclusion": _suggested_conclusion(analysis),
        "disclaimer": "Nội dung phục vụ học tập và nghiên cứu, không phải khuyến nghị mua, bán hoặc nắm giữ.",
    }


def _summary_cards(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _card("Doanh thu thuần", summary.get("revenue"), "revenue_growth_yoy_pct", summary),
        _card("LNST", summary.get("net_income"), "net_income_growth_yoy_pct", summary),
        {"label": "Biên lợi nhuận ròng", "value": summary.get("net_margin_pct"), "unit": "%", "note": "Net margin"},
        {"label": "ROE", "value": summary.get("roe_pct"), "unit": "%", "note": "TTM / latest available"},
        {"label": "CFO / Dòng tiền KD", "value": summary.get("operating_cash_flow") or summary.get("ocf_ttm"), "unit": "VND", "note": f"{summary.get('ocf_to_net_income') or 'n/a'}x OCF/LNST"},
        {"label": "Debt / Equity", "value": summary.get("debt_to_equity"), "unit": "x", "note": "Đòn bẩy tài chính"},
    ]


def _card(label: str, value: Any, growth_key: str, summary: dict[str, Any]) -> dict[str, Any]:
    growth = summary.get(growth_key)
    return {"label": label, "value": value, "unit": "VND", "growth_pct": growth, "note": "YoY" if growth is not None else None}


def _ai_summary_bullets(analysis: dict[str, Any]) -> list[dict[str, str]]:
    bullets = [{"tone": "good", "text": item} for item in (analysis.get("highlights") or [])[:4]]
    if bullets:
        return bullets
    summary = analysis.get("summary") or {}
    return [
        {"tone": "good", "text": f"Doanh thu YoY: {summary.get('revenue_growth_yoy_pct') or 'n/a'}%."},
        {"tone": "good", "text": f"Biên ròng hiện ở mức {summary.get('net_margin_pct') or 'n/a'}%."},
        {"tone": "warn", "text": f"Debt/Equity: {summary.get('debt_to_equity') or 'n/a'}."},
    ]


def _statement_row(label: str, key: str, current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    current_value = current.get(key)
    previous_value = previous.get(key)
    return {
        "label": label,
        "key": key,
        "period": current.get("period"),
        "value": current_value,
        "previous_value": previous_value,
        "change": _change(current_value, previous_value),
        "change_pct": _growth_pct(current_value, previous_value),
    }


def _pick_period_fields(periods: list[dict[str, Any]], fields: Iterable[str]) -> list[dict[str, Any]]:
    selected = []
    for item in periods:
        row = {field: item.get(field) for field in fields}
        revenue = item.get("revenue")
        row["net_margin_pct"] = _safe_pct(item.get("net_income"), revenue)
        selected.append(row)
    return selected[-12:]


def _income_insights(analysis: dict[str, Any]) -> list[str]:
    summary = analysis.get("summary") or {}
    return [
        f"Doanh thu YoY: {summary.get('revenue_growth_yoy_pct') or 'n/a'}%.",
        f"LNST YoY: {summary.get('net_income_growth_yoy_pct') or 'n/a'}%.",
        "So sánh biên lợi nhuận để phân biệt tăng trưởng chất lượng và tăng trưởng doanh thu đơn thuần.",
    ]


def _ratio(label: str, value: Any, unit: str) -> dict[str, Any]:
    return {"label": label, "value": value, "unit": unit}


def _pair_adjacent(periods: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [(periods[index], periods[index - 1]) for index in range(1, len(periods))]


def _horizontal_flags(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    flags = []
    for row in rows[-4:]:
        metrics = {item["key"]: item for item in row["metrics"]}
        revenue_growth = metrics.get("revenue", {}).get("change_pct")
        cfo_growth = metrics.get("operating_cash_flow", {}).get("change_pct")
        if revenue_growth is not None and cfo_growth is not None and revenue_growth > 0 and cfo_growth < 0:
            flags.append({
                "severity": "medium",
                "message": f"{row['period']}: Doanh thu tăng nhưng CFO giảm, cần kiểm tra chất lượng lợi nhuận.",
            })
    return flags


def _common_size(label: str, value: Any, base: Any) -> dict[str, Any]:
    return {"label": label, "value": value, "base": base, "percentage": _safe_pct(value, base)}


def _suggested_conclusion(analysis: dict[str, Any]) -> str:
    summary = analysis.get("summary") or {}
    return (
        f"{analysis.get('ticker')} cần được đánh giá qua tăng trưởng doanh thu "
        f"({summary.get('revenue_growth_yoy_pct') or 'n/a'}% YoY), biên ròng "
        f"({summary.get('net_margin_pct') or 'n/a'}%) và chất lượng dòng tiền trước khi kết luận."
    )


def _change(current: Any, previous: Any) -> float | None:
    if current is None or previous is None:
        return None
    return float(current) - float(previous)


def _growth_pct(current: Any, previous: Any) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return ((float(current) - float(previous)) / abs(float(previous))) * 100


def _safe_pct(value: Any, base: Any) -> float | None:
    if value is None or base in (None, 0):
        return None
    return (float(value) / abs(float(base))) * 100
