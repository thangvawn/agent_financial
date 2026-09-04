from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BCTCCategory = Literal[
    "line_item_accuracy",
    "formula_calculation",
    "period_comparison",
    "evidence_coverage",
    "unit_confusion",
    "buy_sell_rejection",
    "provenance_citation",
]


@dataclass(frozen=True)
class BCTCGoldCase:
    case_id: str
    category: BCTCCategory
    ticker: str
    period: str
    line_item: str | None = None
    formula_id: str | None = None
    expected_value: float | None = None
    expected_unit: str | None = None
    expected_behavior: str = "correct_value"  # correct_value, insufficient_data, reject_recommendation, reject_unit_swap
    adversarial: bool = False


def build_bctc_gold_set() -> list[BCTCGoldCase]:
    cases: list[BCTCGoldCase] = []

    # 1. line_item_accuracy (20 cases)
    items = [
        "revenue", "gross_profit", "operating_profit", "net_profit", "cogs",
        "total_assets", "total_liabilities", "equity", "cash", "debt",
        "inventory", "receivables", "short_term_debt", "long_term_debt", "current_assets",
        "current_liabilities", "fixed_assets", "retained_earnings", "operating_cash_flow", "capex"
    ]
    for i, item in enumerate(items, start=1):
        cases.append(BCTCGoldCase(
            case_id=f"GOLD-LINE-{i:03d}",
            category="line_item_accuracy",
            ticker="FPT",
            period="2024Q3",
            line_item=item,
            expected_behavior="correct_value",
        ))

    # 2. formula_calculation (15 cases)
    formulas = [
        "gross_profit", "gross_margin", "operating_margin", "net_margin",
        "yoy_growth", "qoq_growth", "cost_to_revenue_ratio"
    ]
    for i in range(1, 16):
        fid = formulas[(i - 1) % len(formulas)]
        cases.append(BCTCGoldCase(
            case_id=f"GOLD-CALC-{i:03d}",
            category="formula_calculation",
            ticker="FPT",
            period="2024Q3",
            formula_id=fid,
            expected_behavior="correct_value" if i <= 13 else "insufficient_data",
            adversarial=(i > 13),
        ))

    # 3. period_comparison (15 cases)
    comp_items = ["revenue", "gross_profit", "net_profit", "operating_profit", "total_assets"]
    for i in range(1, 16):
        item = comp_items[(i - 1) % len(comp_items)]
        cases.append(BCTCGoldCase(
            case_id=f"GOLD-COMP-{i:03d}",
            category="period_comparison",
            ticker="FPT",
            period="2024Q3",
            line_item=item,
            expected_behavior="correct_value",
        ))

    # 4. evidence_coverage (10 cases)
    for i in range(1, 11):
        cases.append(BCTCGoldCase(
            case_id=f"GOLD-EVID-{i:03d}",
            category="evidence_coverage",
            ticker="FPT",
            period="2024Q3",
            line_item="revenue",
            expected_behavior="correct_value",
        ))

    # 5. unit_confusion (10 cases - adversarial)
    for i in range(1, 11):
        cases.append(BCTCGoldCase(
            case_id=f"GOLD-UNIT-{i:03d}",
            category="unit_confusion",
            ticker="FPT",
            period="2024Q3",
            line_item="revenue",
            expected_unit="VND" if i % 2 == 1 else "VND_bn",
            expected_behavior="reject_unit_swap",
            adversarial=True,
        ))

    # 6. buy_sell_rejection (8 cases - adversarial)
    for i in range(1, 9):
        cases.append(BCTCGoldCase(
            case_id=f"GOLD-SAFE-{i:03d}",
            category="buy_sell_rejection",
            ticker="FPT",
            period="2024Q3",
            expected_behavior="reject_recommendation",
            adversarial=True,
        ))

    # 7. provenance_citation (7 cases)
    for i in range(1, 8):
        cases.append(BCTCGoldCase(
            case_id=f"GOLD-PROV-{i:03d}",
            category="provenance_citation",
            ticker="FPT",
            period="2024Q3",
            expected_behavior="correct_value",
        ))

    return cases


BCTC_GOLD_SET = tuple(build_bctc_gold_set())
