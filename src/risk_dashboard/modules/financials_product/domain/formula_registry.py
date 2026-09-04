from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class FormulaEntry:
    formula_id: str
    version: str
    display_name: str
    expression: str
    unit: str
    inputs: tuple[str, ...] = ()
    applicability: tuple[str, ...] = ("income_statement",)
    limitations: tuple[str, ...] = ()
    approved: bool = False
    approved_by: str | None = None
    approved_at: str | None = None


_FORMULA_REGISTRY: dict[str, FormulaEntry] = {
    "gross_profit": FormulaEntry(
        formula_id="gross_profit",
        version="1.0.0",
        display_name="Lợi nhuận gộp",
        expression="gross_profit = revenue - cogs",
        unit="VND",
        inputs=("revenue", "cogs"),
        applicability=("income_statement",),
        limitations=("Chưa trừ chi phí bán hàng, quản lý doanh nghiệp và tài chính.",),
        approved=True,
        approved_by="domain_expert",
        approved_at="2026-09-01T00:00:00Z",
    ),
    "gross_margin": FormulaEntry(
        formula_id="gross_margin",
        version="1.0.0",
        display_name="Biên lợi nhuận gộp",
        expression="gross_margin = gross_profit / revenue",
        unit="pct",
        inputs=("gross_profit", "revenue"),
        applicability=("income_statement",),
        limitations=("Không phản ánh hiệu quả quản lý chi phí gián tiếp.",),
        approved=True,
        approved_by="domain_expert",
        approved_at="2026-09-01T00:00:00Z",
    ),
    "operating_margin": FormulaEntry(
        formula_id="operating_margin",
        version="1.0.0",
        display_name="Biên lợi nhuận hoạt động",
        expression="operating_margin = operating_profit / revenue",
        unit="pct",
        inputs=("operating_profit", "revenue"),
        applicability=("income_statement",),
        limitations=("Có thể bị biến động bởi các khoản chi phí hoạt động một lần.",),
        approved=True,
        approved_by="domain_expert",
        approved_at="2026-09-01T00:00:00Z",
    ),
    "net_margin": FormulaEntry(
        formula_id="net_margin",
        version="1.0.0",
        display_name="Biên lợi nhuận ròng",
        expression="net_margin = net_profit / revenue",
        unit="pct",
        inputs=("net_profit", "revenue"),
        applicability=("income_statement",),
        limitations=("Cần đánh giá kèm lưu chuyển tiền tệ để xác định chất lượng lợi nhuận.",),
        approved=True,
        approved_by="domain_expert",
        approved_at="2026-09-01T00:00:00Z",
    ),
    "yoy_growth": FormulaEntry(
        formula_id="yoy_growth",
        version="1.0.0",
        display_name="Tăng trưởng cùng kỳ",
        expression="yoy_growth = (current_period_value - same_period_last_year_value) / abs(same_period_last_year_value)",
        unit="pct",
        inputs=("current_period_value", "same_period_last_year_value"),
        applicability=("income_statement", "balance_sheet", "cash_flow"),
        limitations=("Không phản ánh tính mùa vụ nếu so với quý liền kề.",),
        approved=True,
        approved_by="domain_expert",
        approved_at="2026-09-01T00:00:00Z",
    ),
    "qoq_growth": FormulaEntry(
        formula_id="qoq_growth",
        version="1.0.0",
        display_name="Tăng trưởng so với quý trước",
        expression="qoq_growth = (current_period_value - previous_period_value) / abs(previous_period_value)",
        unit="pct",
        inputs=("current_period_value", "previous_period_value"),
        applicability=("income_statement", "balance_sheet", "cash_flow"),
        limitations=("Có thể chịu ảnh hưởng mạnh bởi tính chu kỳ mùa vụ trong năm.",),
        approved=True,
        approved_by="domain_expert",
        approved_at="2026-09-01T00:00:00Z",
    ),
    "cost_to_revenue_ratio": FormulaEntry(
        formula_id="cost_to_revenue_ratio",
        version="1.0.0",
        display_name="Tỷ lệ chi phí trên doanh thu",
        expression="cost_to_revenue_ratio = expense_item / revenue",
        unit="pct",
        inputs=("expense_item", "revenue"),
        applicability=("income_statement",),
        limitations=("Chỉ áp dụng khi doanh thu lớn hơn 0.",),
        approved=True,
        approved_by="domain_expert",
        approved_at="2026-09-01T00:00:00Z",
    ),
}


def get_formula(formula_id: str, version: str | None = None) -> FormulaEntry:
    """Return approved formula entry or raise ValueError."""
    entry = _FORMULA_REGISTRY.get(formula_id)
    if entry is None:
        raise ValueError(f"Formula '{formula_id}' not found in registry.")
    if not entry.approved:
        raise ValueError(f"Formula '{formula_id}' is not approved.")
    if version is not None and entry.version != version:
        raise ValueError(f"Formula '{formula_id}' version mismatch: requested {version}, have {entry.version}.")
    return entry


def list_approved_formulas() -> list[FormulaEntry]:
    return [f for f in _FORMULA_REGISTRY.values() if f.approved]


def list_all_formulas() -> list[FormulaEntry]:
    return list(_FORMULA_REGISTRY.values())

