from __future__ import annotations

from risk_dashboard.modules.pro_lab.evals.baseline_fixtures import (
    BASELINE_INVENTORY,
    GOLDEN_BACKTEST_CRITIQUE_INPUT,
    GOLDEN_BACKTEST_CRITIQUE_OUTPUT,
    GOLDEN_STRATEGY_COPILOT_INPUT,
    GOLDEN_STRATEGY_COPILOT_OUTPUT,
    GOLDEN_SWARM_COMMITTEE_INPUT,
    GOLDEN_SWARM_COMMITTEE_OUTPUT,
)
from risk_dashboard.modules.pro_lab.evals.eval_runner import (
    SimulationEvalMetrics,
    SimulationEvalRunner,
)
from risk_dashboard.modules.pro_lab.evals.fake_simulation_provider import (
    make_fake_simulation_provider,
)
from risk_dashboard.modules.pro_lab.evals.gold_set import (
    GoldCase,
    load_simulation_gold_set,
)
from risk_dashboard.modules.pro_lab.evals.multi_agent_gate import (
    GateEvaluationResult,
    MultiAgentGateRunner,
)
from risk_dashboard.modules.pro_lab.evals.parity_gate import (
    ParityEvaluationResult,
    ParityGateRunner,
)

__all__ = [
    "BASELINE_INVENTORY",
    "GOLDEN_STRATEGY_COPILOT_INPUT",
    "GOLDEN_STRATEGY_COPILOT_OUTPUT",
    "GOLDEN_BACKTEST_CRITIQUE_INPUT",
    "GOLDEN_BACKTEST_CRITIQUE_OUTPUT",
    "GOLDEN_SWARM_COMMITTEE_INPUT",
    "GOLDEN_SWARM_COMMITTEE_OUTPUT",
    "make_fake_simulation_provider",
    "GoldCase",
    "load_simulation_gold_set",
    "SimulationEvalMetrics",
    "SimulationEvalRunner",
    "GateEvaluationResult",
    "MultiAgentGateRunner",
    "ParityEvaluationResult",
    "ParityGateRunner",
]

