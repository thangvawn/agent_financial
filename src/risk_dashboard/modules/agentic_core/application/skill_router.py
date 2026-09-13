from __future__ import annotations

from typing import Any

from risk_dashboard.modules.agentic_core.domain.ports import ReadOnlyTool
from risk_dashboard.modules.agentic_core.infrastructure.bctc_domain_tools import (
    BctcBuildEvidenceTableDomainTool,
    BctcCalculateRatioDomainTool,
    BctcComparePeriodsDomainTool,
    BctcResolveLineItemDomainTool,
    BctcResolveReportDomainTool,
    BctcTraceProvenanceDomainTool,
)
from risk_dashboard.modules.agentic_core.infrastructure.domain_tools import (
    BctcResolveLineItemTool,
    LearningGetLessonContextTool,
)
from risk_dashboard.modules.agentic_core.infrastructure.learning_domain_tools import (
    LearningGetContextDomainTool,
    LearningGetQuizItemDomainTool,
    LearningGradeCheckpointDomainTool,
    LearningRecommendNextDomainTool,
)
from risk_dashboard.modules.agentic_core.infrastructure.quant_tool import QuantRiskReadOnlyTool

LEARNING_SKILL_TOOL_MAP: dict[str, str] = {
    "learn.explain.v1": "learning.get_context",
    "learn.socratic_hint.v1": "learning.get_quiz_item",
    "learn.formula_walkthrough.v1": "learning.get_context",
    "learn.check_misconception.v1": "learning.get_context",
    "learn.run_checkpoint.v1": "learning.grade_checkpoint",
    "learn.next_step.v1": "learning.recommend_next",
}

BCTC_SKILL_TOOL_MAP: dict[str, str] = {
    "bctc.explain_line_item.v1": "bctc.resolve_line_item",
    "bctc.compare_periods.v1": "bctc.compare_periods",
    "bctc.ratio_walkthrough.v1": "bctc.calculate_ratio",
    "bctc.earnings_quality_review.v1": "bctc.build_evidence_table",
    "bctc.research_checklist.v1": "bctc.trace_provenance",
}


class SkillRouter:
    """Deterministic intent-to-skill-to-tool routing based on surface and operation."""

    @classmethod
    def _tool_from_id(cls, tool_id: str) -> ReadOnlyTool:
        if tool_id == "learning.get_context":
            return LearningGetContextDomainTool()
        if tool_id == "learning.get_quiz_item":
            return LearningGetQuizItemDomainTool()
        if tool_id == "learning.grade_checkpoint":
            return LearningGradeCheckpointDomainTool()
        if tool_id == "learning.recommend_next":
            return LearningRecommendNextDomainTool()
        if tool_id == "bctc.resolve_report":
            return BctcResolveReportDomainTool()
        if tool_id == "bctc.resolve_line_item":
            return BctcResolveLineItemDomainTool()
        if tool_id == "bctc.compare_periods":
            return BctcComparePeriodsDomainTool()
        if tool_id == "bctc.calculate_ratio":
            return BctcCalculateRatioDomainTool()
        if tool_id == "bctc.trace_provenance":
            return BctcTraceProvenanceDomainTool()
        if tool_id == "bctc.build_evidence_table":
            return BctcBuildEvidenceTableDomainTool()
        return LearningGetLessonContextTool()

    @classmethod
    def resolve_skill(cls, skill_id: str) -> ReadOnlyTool:
        """Resolve a versioned skill identifier to its primary domain tool."""
        sid = (skill_id or "").lower().strip()
        if sid in BCTC_SKILL_TOOL_MAP:
            return cls._tool_from_id(BCTC_SKILL_TOOL_MAP[sid])
        tool_id = LEARNING_SKILL_TOOL_MAP.get(sid, sid)
        return cls._tool_from_id(tool_id)

    @classmethod
    def resolve_tool(
        cls,
        surface: str,
        operation: str | None = None,
        default_tool: ReadOnlyTool | None = None,
    ) -> ReadOnlyTool:
        s = (surface or "").lower().strip()
        op = (operation or "").lower().strip()

        # 1. Direct match for registered 6 learning skills
        if op in LEARNING_SKILL_TOOL_MAP:
            return cls.resolve_skill(op)

        # 1b. Direct match for registered 5 BCTC skills
        if op in BCTC_SKILL_TOOL_MAP:
            return cls.resolve_skill(op)

        # 2. Direct match for learning tool IDs
        if op in (
            "learning.get_context",
            "learning.get_quiz_item",
            "learning.grade_checkpoint",
            "learning.recommend_next",
        ):
            return cls._tool_from_id(op)

        # 2b. Direct match for BCTC tool IDs
        if op in (
            "bctc.resolve_report",
            "bctc.resolve_line_item",
            "bctc.compare_periods",
            "bctc.calculate_ratio",
            "bctc.trace_provenance",
            "bctc.build_evidence_table",
        ):
            return cls._tool_from_id(op)

        # 3. Financials
        if s in ("bctc", "bctc_workspace", "financials") or "bctc" in op or "financial" in op:
            if "ratio" in op or "margin" in op:
                return BctcCalculateRatioDomainTool()
            if "compare" in op or "period" in op:
                return BctcComparePeriodsDomainTool()
            if "evidence" in op:
                return BctcBuildEvidenceTableDomainTool()
            if "provenance" in op or "trace" in op:
                return BctcTraceProvenanceDomainTool()
            if "report" in op:
                return BctcResolveReportDomainTool()
            return BctcResolveLineItemDomainTool()

        # 4. Learning surface or explicit learning operation
        if s in ("learn", "learn_hub", "learning", "tutor") or op.startswith("learn"):
            if op == "get_lesson":
                return LearningGetLessonContextTool()
            if "checkpoint" in op or "grade" in op:
                return cls._tool_from_id("learning.grade_checkpoint")
            if "quiz" in op or "hint" in op:
                return cls._tool_from_id("learning.get_quiz_item")
            if "recommend" in op or "next_step" in op or "next" in op:
                return cls._tool_from_id("learning.recommend_next")
            if "explain" in op or "formula" in op or "misconception" in op or "context" in op:
                return cls._tool_from_id("learning.get_context")
            return LearningGetLessonContextTool()

        if default_tool is not None:
            return default_tool
        return QuantRiskReadOnlyTool()

    @classmethod
    def get_required_capabilities(cls, tool: ReadOnlyTool) -> tuple[str, ...]:
        return getattr(tool.manifest, "required_capabilities", ())
