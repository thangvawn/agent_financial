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
    zero_leakage_enforced: bool = False
    max_tool_calls: int = 3
    timeout_ms: int = 5000


EXPLAIN_LINE_ITEM_SKILL = SkillManifest(
    skill_id="bctc.explain_line_item.v1",
    version="1.0.0",
    name="Explain BCTC Line Item",
    description="Explain a specific line item in financial statements with definitions, composition, caveats, and citations.",
    target_surface="bctc",
    required_tools=("bctc.resolve_report", "bctc.resolve_line_item"),
    required_scopes=("bctc:report:read",),
)

COMPARE_PERIODS_SKILL = SkillManifest(
    skill_id="bctc.compare_periods.v1",
    version="1.0.0",
    name="Compare BCTC Periods",
    description="Compare financial metrics across multiple accounting periods with growth rates and trend analysis.",
    target_surface="bctc",
    required_tools=("bctc.resolve_report", "bctc.compare_periods"),
    required_scopes=("bctc:report:read",),
)

RATIO_WALKTHROUGH_SKILL = SkillManifest(
    skill_id="bctc.ratio_walkthrough.v1",
    version="1.0.0",
    name="BCTC Ratio Walkthrough",
    description="Step-by-step financial ratio calculation walkthrough with formula substitution, units, and limitations.",
    target_surface="bctc",
    required_tools=("bctc.resolve_report", "bctc.calculate_ratio"),
    required_scopes=("bctc:report:read", "bctc:formula:read"),
)

EARNINGS_QUALITY_REVIEW_SKILL = SkillManifest(
    skill_id="bctc.earnings_quality_review.v1",
    version="1.0.0",
    name="Earnings Quality Review",
    description="Review quality of earnings by assessing cash conversion, margin stability, and non-operating drivers.",
    target_surface="bctc",
    required_tools=("bctc.resolve_report", "bctc.build_evidence_table", "bctc.calculate_ratio"),
    required_scopes=("bctc:report:read", "bctc:evidence:read", "bctc:formula:read"),
    max_tool_calls=5,
)

RESEARCH_CHECKLIST_SKILL = SkillManifest(
    skill_id="bctc.research_checklist.v1",
    version="1.0.0",
    name="BCTC Research Checklist",
    description="Generate structured due-diligence questions and verification checklists based on report provenance.",
    target_surface="bctc",
    required_tools=("bctc.resolve_report", "bctc.trace_provenance"),
    required_scopes=("bctc:report:read",),
)

_SKILLS: dict[str, SkillManifest] = {
    s.skill_id: s
    for s in (
        EXPLAIN_LINE_ITEM_SKILL,
        COMPARE_PERIODS_SKILL,
        RATIO_WALKTHROUGH_SKILL,
        EARNINGS_QUALITY_REVIEW_SKILL,
        RESEARCH_CHECKLIST_SKILL,
    )
}


def get_skill_manifest(skill_id: str) -> SkillManifest:
    manifest = _SKILLS.get(skill_id)
    if manifest is None:
        raise ValueError(f"Skill '{skill_id}' not found in BCTC skills registry.")
    return manifest


def list_skill_manifests() -> list[SkillManifest]:
    return list(_SKILLS.values())

