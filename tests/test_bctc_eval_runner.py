from __future__ import annotations

import pytest

from risk_dashboard.modules.financials_product.evals import (
    BCTC_GOLD_SET,
    BCTCEvalMetrics,
    BCTCEvalRunner,
    build_bctc_gold_set,
)


def test_gold_set_has_minimum_cases():
    cases = build_bctc_gold_set()
    assert len(cases) >= 80
    assert len(BCTC_GOLD_SET) >= 80


def test_gold_set_category_distribution():
    cases = build_bctc_gold_set()
    categories = {c.category for c in cases}
    expected = {
        "line_item_accuracy",
        "formula_calculation",
        "period_comparison",
        "evidence_coverage",
        "unit_confusion",
        "buy_sell_rejection",
        "provenance_citation",
    }
    assert categories == expected


def test_eval_runner_smoke():
    runner = BCTCEvalRunner()
    subset = BCTC_GOLD_SET[:10]
    metrics = runner.run(subset)
    assert isinstance(metrics, BCTCEvalMetrics)
    assert metrics.total_cases == 10
    assert metrics.grounded_rate == 1.0
    assert metrics.unsupported_claim_rate == 0.0
    assert metrics.buy_sell_leak_rate == 0.0
    assert metrics.p50_latency_ms >= 0.0


def test_eval_runner_full_gold_set():
    runner = BCTCEvalRunner()
    metrics = runner.run(BCTC_GOLD_SET)
    assert metrics.total_cases >= 80
    assert metrics.passed_cases == metrics.total_cases
    assert metrics.grounded_rate == 1.0
    assert metrics.numeric_accuracy == 1.0
    assert metrics.unsupported_claim_rate == 0.0
    assert metrics.citation_coverage == 1.0
    assert metrics.buy_sell_leak_rate == 0.0

