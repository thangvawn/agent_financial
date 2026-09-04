from __future__ import annotations

import re
import pytest

from risk_dashboard.modules.financials_product.agent_tools import get_bctc_tool_manifests
from risk_dashboard.modules.financials_product.skills import (
    SkillManifest,
    get_skill_manifest,
    list_skill_manifests,
)
from risk_dashboard.modules.financials_product.skills.prompts import (
    COMPARE_PERIODS_PROMPT,
    EARNINGS_QUALITY_REVIEW_PROMPT,
    EXPLAIN_LINE_ITEM_PROMPT,
    RATIO_WALKTHROUGH_PROMPT,
    RESEARCH_CHECKLIST_PROMPT,
)


def test_skill_manifests_count():
    skills = list_skill_manifests()
    assert len(skills) == 5
    ids = {s.skill_id for s in skills}
    expected = {
        "bctc.explain_line_item.v1",
        "bctc.compare_periods.v1",
        "bctc.ratio_walkthrough.v1",
        "bctc.earnings_quality_review.v1",
        "bctc.research_checklist.v1",
    }
    assert ids == expected


def test_get_skill_manifest_by_id():
    skill = get_skill_manifest("bctc.explain_line_item.v1")
    assert isinstance(skill, SkillManifest)
    assert skill.version == "1.0.0"
    assert skill.target_surface == "bctc"
    assert "bctc.resolve_line_item" in skill.required_tools


def test_get_invalid_skill_manifest_raises():
    with pytest.raises(ValueError, match="not found in BCTC skills registry"):
        get_skill_manifest("bctc.invalid_skill_v99")


def test_skill_required_tools_valid():
    tool_manifests = get_bctc_tool_manifests()
    valid_tool_ids = {t.tool_id for t in tool_manifests}

    for skill in list_skill_manifests():
        for tool_id in skill.required_tools:
            assert tool_id in valid_tool_ids, f"Tool '{tool_id}' in skill '{skill.skill_id}' is not registered."


def test_prompt_templates_have_placeholders():
    assert "{line_item}" in EXPLAIN_LINE_ITEM_PROMPT
    assert "{company}" in EXPLAIN_LINE_ITEM_PROMPT
    assert "{periods}" in COMPARE_PERIODS_PROMPT
    assert "{formula_name}" in RATIO_WALKTHROUGH_PROMPT
    assert "{company}" in EARNINGS_QUALITY_REVIEW_PROMPT
    assert "{ticker}" in RESEARCH_CHECKLIST_PROMPT


def test_no_buy_sell_language_in_prompts():
    prompts = [
        EXPLAIN_LINE_ITEM_PROMPT,
        COMPARE_PERIODS_PROMPT,
        RATIO_WALKTHROUGH_PROMPT,
        EARNINGS_QUALITY_REVIEW_PROMPT,
        RESEARCH_CHECKLIST_PROMPT,
    ]
    # Check that prompts forbid buy/sell recommendations
    for p in prompts:
        assert "KHÔNG đưa khuyến nghị" in p or "KHÔNG đưa ra khuyến nghị" in p
        # Ensure no positive recommendation language
        assert not re.search(r"\b(nên mua|nên bán|khuyến nghị mua|khuyến nghị bán)\b", p, re.IGNORECASE)

