from __future__ import annotations

from risk_dashboard.modules.pro_lab.evals.baseline_fixtures import (
    BASELINE_INVENTORY,
    GOLDEN_BACKTEST_CRITIQUE_OUTPUT,
    GOLDEN_STRATEGY_COPILOT_OUTPUT,
    GOLDEN_SWARM_COMMITTEE_OUTPUT,
)
from risk_dashboard.modules.pro_lab.evals.eval_runner import SimulationEvalRunner
from risk_dashboard.modules.pro_lab.evals.gold_set import load_simulation_gold_set
from risk_dashboard.modules.pro_lab.evals.multi_agent_gate import MultiAgentGateRunner
from risk_dashboard.modules.pro_lab.evals.parity_gate import ParityGateRunner


def test_gold_set_size_and_categories():
    cases = load_simulation_gold_set()
    assert len(cases) >= 85

    categories = {c.category for c in cases}
    assert "strategy_spec_accuracy" in categories
    assert "manifest_validation" in categories
    assert "run_comparison" in categories
    assert "methodology_detection" in categories
    assert "trade_summary_accuracy" in categories
    assert "buy_sell_rejection" in categories
    assert "proposal_confirmation" in categories
    assert "reproducibility" in categories


def test_simulation_eval_runner_produces_all_metrics():
    runner = SimulationEvalRunner()
    metrics = runner.run_all()

    assert metrics.total_cases >= 85
    assert metrics.passed_cases == metrics.total_cases
    assert metrics.grounded_rate == 1.0
    assert metrics.numeric_precision >= 0.95
    assert metrics.methodology_issue_recall >= 0.95
    assert metrics.buy_sell_leak_rate == 0.0
    assert metrics.citation_coverage == 1.0
    assert metrics.reproducible_run_rate == 1.0
    assert metrics.p50_latency_ms > 0
    assert metrics.p95_latency_ms > 0


def test_multi_agent_gate_runner():
    gate = MultiAgentGateRunner(min_uplift_pp=5.0, max_cost_increase_pct=50.0)

    # 1. Low uplift -> keep single specialist
    res_low_uplift = gate.evaluate(
        single_specialist_score=85.0,
        multi_agent_score=87.0,  # only +2 pp
        single_latency_p95_ms=2000.0,
        multi_latency_p95_ms=3000.0,
        single_cost_usd=0.01,
        multi_cost_usd=0.012,
    )
    assert res_low_uplift.decision == "keep_single_specialist"
    assert "dưới ngưỡng tối thiểu" in res_low_uplift.decision_reason

    # 2. High cost -> keep single specialist
    res_high_cost = gate.evaluate(
        single_specialist_score=80.0,
        multi_agent_score=88.0,  # +8 pp (good)
        single_latency_p95_ms=2000.0,
        multi_latency_p95_ms=3000.0,
        single_cost_usd=0.01,
        multi_cost_usd=0.025,  # +150% cost (too expensive)
    )
    assert res_high_cost.decision == "keep_single_specialist"
    assert "Chi phí tăng quá cao" in res_high_cost.decision_reason

    # 3. Valid uplift and within budget -> enable multi agent
    res_pass = gate.evaluate(
        single_specialist_score=80.0,
        multi_agent_score=87.5,  # +7.5 pp
        single_latency_p95_ms=2000.0,
        multi_latency_p95_ms=2800.0,
        single_cost_usd=0.01,
        multi_cost_usd=0.013,  # +30% cost (within 50% budget)
    )
    assert res_pass.decision == "enable_multi_agent"

    history = gate.get_history()
    assert len(history) == 3


def test_parity_gate_runner():
    parity_gate = ParityGateRunner(max_latency_drift_pct=30.0, max_cost_drift_pct=20.0)

    # Clean match
    res_ok = parity_gate.verify_parity(
        baseline_output=GOLDEN_STRATEGY_COPILOT_OUTPUT,
        runtime_output=GOLDEN_STRATEGY_COPILOT_OUTPUT.copy(),
        baseline_latency_ms=1200.0,
        runtime_latency_ms=1300.0,
        baseline_cost_usd=0.005,
        runtime_cost_usd=0.0052,
    )
    assert res_ok.is_parity_passed is True
    assert res_ok.schema_compatible is True

    # Missing field
    incomplete_output = {"strategy_name": "Test"}
    res_missing = parity_gate.verify_parity(
        baseline_output=GOLDEN_STRATEGY_COPILOT_OUTPUT,
        runtime_output=incomplete_output,
    )
    assert res_missing.is_parity_passed is False
    assert res_missing.schema_compatible is False
    assert len(res_missing.mismatched_fields) > 0


def test_baseline_inventory_doc():
    assert "strategy_copilot" in BASELINE_INVENTORY
    assert "backtest_critique" in BASELINE_INVENTORY
    assert "swarm_committee" in BASELINE_INVENTORY
    assert BASELINE_INVENTORY["swarm_committee"]["model_invocation_count"] == 1

