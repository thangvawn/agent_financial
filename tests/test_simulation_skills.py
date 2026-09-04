from __future__ import annotations

import pytest

from risk_dashboard.modules.pro_lab.skills.manifests import (
    BACKTEST_PREFLIGHT_SKILL,
    HYPOTHESIS_BUILDER_SKILL,
    NEXT_EXPERIMENT_SKILL,
    RESULT_CRITIQUE_SKILL,
    SCENARIO_COMPARE_SKILL,
    get_skill_manifest,
    list_skill_manifests,
)
from risk_dashboard.modules.pro_lab.skills.prompts.backtest_preflight import (
    BACKTEST_PREFLIGHT_SYSTEM_PROMPT,
)
from risk_dashboard.modules.pro_lab.skills.prompts.hypothesis_builder import (
    HYPOTHESIS_BUILDER_SYSTEM_PROMPT,
)
from risk_dashboard.modules.pro_lab.skills.prompts.next_experiment import (
    NEXT_EXPERIMENT_SYSTEM_PROMPT,
)
from risk_dashboard.modules.pro_lab.skills.prompts.result_critique import (
    RESULT_CRITIQUE_SYSTEM_PROMPT,
)
from risk_dashboard.modules.pro_lab.skills.prompts.scenario_compare import (
    SCENARIO_COMPARE_SYSTEM_PROMPT,
)


def test_skills_manifest_registry():
    skills = list_skill_manifests()
    assert len(skills) == 5

    s1 = get_skill_manifest("simulation.hypothesis_builder.v1")
    assert s1.skill_id == "simulation.hypothesis_builder.v1"
    assert s1.target_surface == "simulation_lab"
    assert "simulation.get_strategy_spec" in s1.required_tools

    s2 = get_skill_manifest("simulation.result_critique.v1")
    assert s2.skill_id == "simulation.result_critique.v1"
    assert "simulation.get_run" in s2.required_tools

    with pytest.raises(ValueError, match="không tồn tại"):
        get_skill_manifest("simulation.non_existent.v1")


def test_prompts_safety_zero_buy_sell_language():
    prompts = [
        HYPOTHESIS_BUILDER_SYSTEM_PROMPT,
        BACKTEST_PREFLIGHT_SYSTEM_PROMPT,
        RESULT_CRITIQUE_SYSTEM_PROMPT,
        SCENARIO_COMPARE_SYSTEM_PROMPT,
        NEXT_EXPERIMENT_SYSTEM_PROMPT,
    ]

    forbidden_phrases = [
        "hãy mua ngay",
        "hãy bán ngay",
        "khuyến nghị mua vào",
        "khuyến nghị bán ra",
        "cam kết sinh lời",
        "chắc chắn có lãi",
    ]

    for p in prompts:
        assert len(p) > 50
        p_lower = p.lower()
        for phrase in forbidden_phrases:
            assert phrase not in p_lower, f"Found forbidden phrase '{phrase}' in prompt."


def test_prompts_methodology_limitations_present():
    assert "hạn chế" in HYPOTHESIS_BUILDER_SYSTEM_PROMPT.lower() or "limitations" in HYPOTHESIS_BUILDER_SYSTEM_PROMPT.lower()
    assert "look-ahead" in BACKTEST_PREFLIGHT_SYSTEM_PROMPT.lower()
    assert "overfitting" in RESULT_CRITIQUE_SYSTEM_PROMPT.lower() or "curve-fitting" in RESULT_CRITIQUE_SYSTEM_PROMPT.lower()
    assert "metrics_calculation_version" in SCENARIO_COMPARE_SYSTEM_PROMPT.lower()
    assert "actionproposal" in NEXT_EXPERIMENT_SYSTEM_PROMPT.lower()

