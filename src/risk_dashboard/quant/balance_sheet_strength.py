from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from risk_dashboard.schemas.financials import (
    BalanceSheetCompositionItem,
    BalanceSheetDataQuality,
    BalanceSheetInterpretation,
    BalanceSheetRatios,
    BalanceSheetRedFlag,
    BalanceSheetStrengthResponse,
    FinancialDataset,
    FinancialPeriodData,
)


FINANCIAL_INDUSTRIES = ("ngân hàng", "bank", "chứng khoán", "securities", "bảo hiểm", "insurance")


class BalanceSheetDataError(ValueError):
    pass


@dataclass(frozen=True)
class BalanceSheetWorkingStatement:
    period: FinancialPeriodData
    unit: str
    total_assets: float
    cash: float | None
    short_term_investments: float | None
    receivables: float | None
    inventory: float | None
    fixed_assets: float | None
    investment_properties: float | None
    long_term_investments: float | None
    other_assets: float | None
    total_liabilities: float | None
    current_liabilities: float | None
    non_current_liabilities: float | None
    short_term_debt: float | None
    long_term_debt: float | None
    total_debt: float | None
    accounts_payable: float | None
    equity: float | None
    current_assets: float | None
    estimated_fields: list[str]
    missing_fields: list[str]


def normalize_balance_sheet_units(value: float | None, source_unit: str = "vnd", target_unit: str = "ty_vnd") -> float | None:
    if value is None:
        return None
    if target_unit != "ty_vnd":
        return float(value)
    normalized_source = (source_unit or "vnd").lower()
    divisor = {
        "vnd": 1_000_000_000,
        "nghin_vnd": 1_000_000,
        "thousand_vnd": 1_000_000,
        "trieu_vnd": 1_000,
        "million_vnd": 1_000,
        "ty_vnd": 1,
        "billion_vnd": 1,
    }.get(normalized_source, 1_000_000_000)
    return round(float(value) / divisor, 3)


def build_balance_sheet_strength(
    dataset: FinancialDataset,
    *,
    period: str | None = None,
    target_unit: str = "ty_vnd",
) -> BalanceSheetStrengthResponse:
    statement = _select_period(dataset, period)
    if statement is None:
        raise BalanceSheetDataError("Không tìm thấy kỳ BCTC phù hợp.")

    working = _prepare_statement(statement, target_unit=target_unit)
    ratios = calculate_balance_sheet_ratios(working)
    asset_items = build_asset_items(working)
    funding_items = build_funding_items(working)
    consistency = validate_balance_sheet_consistency(asset_items, funding_items, working.total_assets)
    red_flags = detect_balance_sheet_red_flags(working, ratios, dataset.industry, consistency)
    interpretation = interpret_balance_sheet_strength(working, ratios, red_flags, dataset.industry)

    total_funding = round(sum(item.value for item in funding_items), 3)
    return BalanceSheetStrengthResponse(
        ticker=dataset.ticker,
        period=working.period.period,
        unit=target_unit,
        total_assets=working.total_assets,
        total_funding=total_funding,
        asset_items=asset_items,
        funding_items=funding_items,
        ratios=ratios,
        interpretation=interpretation,
        red_flags=red_flags,
        data_quality=BalanceSheetDataQuality(
            missing_fields=sorted(set(working.missing_fields)),
            estimated_fields=sorted(set(working.estimated_fields)),
            consistency_warnings=consistency,
            last_updated=_date_only(dataset.fetched_at),
            source=dataset.source,
        ),
    )


def _select_period(dataset: FinancialDataset, period: str | None) -> FinancialPeriodData | None:
    periods = sorted(dataset.periods, key=lambda item: (item.year or 0, item.quarter or 0, item.period), reverse=True)
    if not period:
        return periods[0] if periods else None
    wanted = _normalize_period_key(period)
    return next((item for item in periods if _normalize_period_key(item.period) == wanted), None)


def _normalize_period_key(period: str) -> str:
    text = (period or "").upper().replace("/", "-").replace("_", "-")
    if text.startswith("Q") and "-" in text:
        q, year = text.split("-", 1)
        return f"{year}-{q}"
    return text


def _prepare_statement(period: FinancialPeriodData, *, target_unit: str) -> BalanceSheetWorkingStatement:
    missing: list[str] = []
    estimated: list[str] = []
    source_unit = "vnd"

    def val(field: str) -> float | None:
        raw = getattr(period, field, None)
        if raw is None:
            missing.append(field)
        return normalize_balance_sheet_units(raw, source_unit, target_unit)

    total_assets = val("total_assets")
    if total_assets is None or total_assets <= 0:
        raise BalanceSheetDataError("total_assets phải lớn hơn 0.")

    equity = val("equity")
    total_liabilities = val("total_liabilities")
    if total_liabilities is None and equity is not None:
        total_liabilities = round(total_assets - equity, 3)
        estimated.append("total_liabilities")

    current_liabilities = val("current_liabilities")
    non_current_liabilities = val("non_current_liabilities")
    if non_current_liabilities is None and total_liabilities is not None and current_liabilities is not None:
        non_current_liabilities = round(total_liabilities - current_liabilities, 3)
        estimated.append("non_current_liabilities")

    short_term_debt = val("short_term_debt")
    long_term_debt = val("long_term_debt")
    total_debt = val("debt")
    if total_debt is None and (short_term_debt is not None or long_term_debt is not None):
        total_debt = round((short_term_debt or 0) + (long_term_debt or 0), 3)
        estimated.append("total_debt")

    cash = val("cash")
    receivables = val("receivables")
    inventory = val("inventory")
    fixed_assets = val("fixed_assets")
    short_term_investments = val("short_term_investments")
    investment_properties = val("investment_properties")
    long_term_investments = val("long_term_investments")
    other_assets = val("other_assets")
    if other_assets is None:
        known_assets = sum(v or 0 for v in [
            cash, short_term_investments, receivables, inventory,
            fixed_assets, investment_properties, long_term_investments,
        ])
        other_assets = round(total_assets - known_assets, 3)
        estimated.append("other_assets")

    return BalanceSheetWorkingStatement(
        period=period,
        unit=target_unit,
        total_assets=total_assets,
        cash=cash,
        short_term_investments=short_term_investments,
        receivables=receivables,
        inventory=inventory,
        fixed_assets=fixed_assets,
        investment_properties=investment_properties,
        long_term_investments=long_term_investments,
        other_assets=other_assets,
        total_liabilities=total_liabilities,
        current_liabilities=current_liabilities,
        non_current_liabilities=non_current_liabilities,
        short_term_debt=short_term_debt,
        long_term_debt=long_term_debt,
        total_debt=total_debt,
        accounts_payable=val("accounts_payable"),
        equity=equity,
        current_assets=val("current_assets"),
        estimated_fields=estimated,
        missing_fields=missing,
    )


def build_asset_items(statement: BalanceSheetWorkingStatement) -> list[BalanceSheetCompositionItem]:
    rows = [
        ("cash", "Tiền mặt & tương đương", statement.cash, "teal", 1),
        ("receivables", "Phải thu khách hàng", statement.receivables, "green", 2),
        ("inventory", "Tồn kho", statement.inventory, "blue", 3),
        ("fixed_assets", "TSCĐ & tài sản dài hạn", statement.fixed_assets, "navy", 4),
        ("other_assets", "Tài sản khác", statement.other_assets, "slate", 5),
    ]
    return [_item(*row, total=statement.total_assets) for row in rows if row[2] is not None]


def build_funding_items(statement: BalanceSheetWorkingStatement) -> list[BalanceSheetCompositionItem]:
    rows = [
        ("current_liabilities", "Nợ ngắn hạn", statement.current_liabilities, "red", 1),
        ("non_current_liabilities", "Nợ dài hạn", statement.non_current_liabilities, "purple", 2),
        ("equity", "Vốn chủ sở hữu", statement.equity, "gray", 3),
    ]
    return [_item(*row, total=statement.total_assets) for row in rows if row[2] is not None]


def _item(key: str, label: str, value: float, color: str, order: int, *, total: float) -> BalanceSheetCompositionItem:
    return BalanceSheetCompositionItem(
        key=key,
        label=label,
        value=round(value, 3),
        percentage=round(value / total, 4) if total else 0,
        color_token=color,
        display_order=order,
    )


def calculate_balance_sheet_ratios(statement: BalanceSheetWorkingStatement) -> BalanceSheetRatios:
    working_capital = None
    if statement.current_assets is not None and statement.current_liabilities is not None:
        working_capital = statement.current_assets - statement.current_liabilities
    return BalanceSheetRatios(
        liabilities_to_assets=_ratio(statement.total_liabilities, statement.total_assets),
        equity_ratio=_ratio(statement.equity, statement.total_assets),
        debt_to_assets=_ratio(statement.total_debt, statement.total_assets),
        debt_to_equity=_ratio(statement.total_debt, statement.equity),
        working_capital_ratio=_ratio(working_capital, statement.total_assets),
    )


def validate_balance_sheet_consistency(
    asset_items: list[BalanceSheetCompositionItem],
    funding_items: list[BalanceSheetCompositionItem],
    total_assets: float,
) -> list[str]:
    warnings: list[str] = []
    asset_gap = abs(sum(item.value for item in asset_items) - total_assets) / total_assets
    funding_gap = abs(sum(item.value for item in funding_items) - total_assets) / total_assets
    if asset_gap > 0.05:
        warnings.append("Tổng cấu phần tài sản không khớp với tổng tài sản, cần kiểm tra mapping dữ liệu.")
    if funding_gap > 0.05:
        warnings.append("Tổng cấu phần nguồn vốn không khớp với tổng tài sản, cần kiểm tra mapping dữ liệu.")
    if any(item.value < 0 for item in [*asset_items, *funding_items]):
        warnings.append("Có cấu phần âm bất thường trong bảng cân đối.")
    return warnings


def detect_balance_sheet_red_flags(
    statement: BalanceSheetWorkingStatement,
    ratios: BalanceSheetRatios,
    industry: str | None,
    consistency_warnings: list[str],
) -> list[BalanceSheetRedFlag]:
    if _is_financial_industry(industry):
        return [BalanceSheetRedFlag(
            code="financial_sector_balance_sheet",
            severity="low",
            metric="industry",
            message="Ngành tài chính có cấu trúc bảng cân đối khác doanh nghiệp sản xuất/thương mại.",
            suggested_question="Nên đọc thêm các chỉ tiêu đặc thù ngành như CASA, NIM, nợ xấu hoặc dư nợ margin.",
        )]

    flags: list[BalanceSheetRedFlag] = []
    receivables_ratio = _ratio(statement.receivables, statement.total_assets)
    inventory_ratio = _ratio(statement.inventory, statement.total_assets)
    cash_ratio = _ratio(statement.cash, statement.total_assets)

    if receivables_ratio is not None and receivables_ratio > 0.25:
        flags.append(_flag("receivables_high", "medium", "receivables_ratio", "Phải thu chiếm tỷ trọng cao trong tổng tài sản.", "Phải thu tăng do mở rộng doanh thu hay do thu tiền chậm?"))
    if inventory_ratio is not None and inventory_ratio > 0.25:
        flags.append(_flag("inventory_high", "medium", "inventory_ratio", "Tồn kho chiếm tỷ trọng cao, cần kiểm tra vòng quay tồn kho.", "Tồn kho tăng vì chuẩn bị tăng trưởng hay do hàng bán chậm?"))
    if ratios.liabilities_to_assets is not None and ratios.liabilities_to_assets > 0.60:
        flags.append(_flag("high_liabilities_ratio", "high", "liabilities_to_assets", "Nợ phải trả chiếm tỷ trọng cao trong nguồn vốn.", "Dòng tiền vận hành có đủ hỗ trợ nghĩa vụ nợ không?"))
    if ratios.equity_ratio is not None and ratios.equity_ratio < 0.30:
        flags.append(_flag("thin_equity_buffer", "medium", "equity_ratio", "Vốn chủ sở hữu thấp, đệm an toàn tài chính mỏng.", "Doanh nghiệp có phụ thuộc quá nhiều vào nợ hoặc vốn ngắn hạn không?"))
    if cash_ratio is not None and cash_ratio < 0.05:
        flags.append(_flag("low_cash_buffer", "medium", "cash_ratio", "Tiền mặt thấp so với tổng tài sản.", "Công ty có nguồn thanh khoản dự phòng nào ngoài tiền mặt không?"))
    if consistency_warnings:
        flags.append(_flag("balance_sheet_mapping_gap", "low", "data_quality", "Cấu phần tài sản/nguồn vốn chưa khớp tổng số liệu.", "Có field nào từ provider chưa được map đúng không?"))
    return flags


def interpret_balance_sheet_strength(
    statement: BalanceSheetWorkingStatement,
    ratios: BalanceSheetRatios,
    flags: list[BalanceSheetRedFlag],
    industry: str | None,
) -> BalanceSheetInterpretation:
    if _is_financial_industry(industry):
        return BalanceSheetInterpretation(
            summary="Đây là doanh nghiệp tài chính, cần đọc cấu trúc bảng cân đối theo chuẩn ngành thay vì áp ngưỡng sản xuất/thương mại.",
            strengths=[],
            cautions=["Các tỷ trọng phải thu, nợ và tài sản tài chính có thể mang ý nghĩa khác doanh nghiệp thông thường."],
        )

    equity_pct = _fmt_pct(ratios.equity_ratio)
    liabilities_pct = _fmt_pct(ratios.liabilities_to_assets)
    summary = f"Cơ cấu nguồn vốn có vốn chủ sở hữu chiếm {equity_pct}, nợ phải trả chiếm {liabilities_pct} tổng tài sản."
    strengths: list[str] = []
    cautions: list[str] = []
    if ratios.equity_ratio is not None and ratios.equity_ratio >= 0.5:
        strengths.append("Vốn chủ sở hữu chiếm tỷ trọng cao hơn nợ phải trả.")
    if _ratio(statement.cash, statement.total_assets) is not None and _ratio(statement.cash, statement.total_assets) >= 0.15:
        strengths.append("Tiền mặt chiếm tỷ trọng đáng kể, tạo đệm thanh khoản.")
    for flag in flags:
        cautions.append(flag.message)
    if not cautions:
        cautions.append("Không có red flag lớn từ cấu trúc bảng cân đối ở kỳ hiện tại.")
    return BalanceSheetInterpretation(summary=summary, strengths=strengths[:3], cautions=cautions[:3])


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator, 4)


def _flag(code: str, severity: str, metric: str, message: str, question: str) -> BalanceSheetRedFlag:
    return BalanceSheetRedFlag(code=code, severity=severity, metric=metric, message=message, suggested_question=question)


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _is_financial_industry(industry: str | None) -> bool:
    normalized = (industry or "").strip().lower()
    return any(token in normalized for token in FINANCIAL_INDUSTRIES)


def _date_only(value: datetime) -> str:
    return value.date().isoformat()
