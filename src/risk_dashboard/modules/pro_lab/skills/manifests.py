from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class SkillManifest:
    skill_id: str
    version: str
    name: str
    description: str
    target_surface: str
    required_tools: tuple[str, ...]
    required_scopes: tuple[str, ...]
    risk_class: str = "read"
    max_tool_calls: int = 4
    timeout_ms: int = 8000


HYPOTHESIS_BUILDER_SKILL = SkillManifest(
    skill_id="simulation.hypothesis_builder.v1",
    version="1.0.0",
    name="Hypothesis Builder",
    description="Clarify research thesis, asset universe, horizon, risk constraints, and generate experiment specification draft.",
    target_surface="simulation_lab",
    required_tools=("simulation.get_strategy_spec", "simulation.validate_experiment"),
    required_scopes=("pro_lab:strategy:read", "pro_lab:experiment:read"),
)

BACKTEST_PREFLIGHT_SKILL = SkillManifest(
    skill_id="simulation.backtest_preflight.v1",
    version="1.0.0",
    name="Backtest Preflight Check",
    description="Examine data window, leakage, look-ahead bias, slippage, and transaction cost assumptions before running backtest.",
    target_surface="simulation_lab",
    required_tools=("simulation.validate_experiment",),
    required_scopes=("pro_lab:experiment:read",),
)

RESULT_CRITIQUE_SKILL = SkillManifest(
    skill_id="simulation.result_critique.v1",
    version="1.0.0",
    name="Result Critique & Methodology Review",
    description="Analyze simulation metrics, drawdown, trade log distributions, and detect methodology red flags with evidence citations.",
    target_surface="simulation_lab",
    required_tools=("simulation.get_run", "simulation.get_trade_summary"),
    required_scopes=("pro_lab:run:read",),
    max_tool_calls=5,
)

SCENARIO_COMPARE_SKILL = SkillManifest(
    skill_id="simulation.scenario_compare.v1",
    version="1.0.0",
    name="Scenario Comparison",
    description="Compare normalized metrics between compatible simulation runs, identifying optimal risk-adjusted parameter profiles.",
    target_surface="simulation_lab",
    required_tools=("simulation.compare_runs",),
    required_scopes=("pro_lab:run:read",),
)

NEXT_EXPERIMENT_SKILL = SkillManifest(
    skill_id="simulation.next_experiment.v1",
    version="1.0.0",
    name="Next Experiment Proposer",
    description="Propose follow-up sensitivity tests, parameter tweaks, or stress scenarios via ActionProposal with budget estimation.",
    target_surface="simulation_lab",
    required_tools=("simulation.validate_experiment", "simulation.propose_run"),
    required_scopes=("pro_lab:experiment:read", "pro_lab:run:propose"),
    risk_class="proposal",
)

_SKILLS: dict[str, SkillManifest] = {
    s.skill_id: s
    for s in (
        HYPOTHESIS_BUILDER_SKILL,
        BACKTEST_PREFLIGHT_SKILL,
        RESULT_CRITIQUE_SKILL,
        SCENARIO_COMPARE_SKILL,
        NEXT_EXPERIMENT_SKILL,
    )
}


def get_skill_manifest(skill_id: str) -> SkillManifest:
    manifest = _SKILLS.get(skill_id)
    if manifest is None:
        raise ValueError(f"Skill '{skill_id}' không tồn tại trong Simulation skills registry.")
    return manifest


def list_skill_manifests() -> list[SkillManifest]:
    return list(_SKILLS.values())

