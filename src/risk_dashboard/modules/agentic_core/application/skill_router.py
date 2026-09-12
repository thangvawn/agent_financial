from __future__ import annotations

from typing import Any

from risk_dashboard.modules.agentic_core.domain.ports import ReadOnlyTool
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
        return LearningGetLessonContextTool()

    @classmethod
    def resolve_skill(cls, skill_id: str) -> ReadOnlyTool:
        """Resolve a versioned skill identifier to its primary domain tool."""
        sid = (skill_id or "").lower().strip()
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

        # 2. Direct match for learning tool IDs
        if op in (
            "learning.get_context",
            "learning.get_quiz_item",
            "learning.grade_checkpoint",
            "learning.recommend_next",
        ):
            return cls._tool_from_id(op)

        # 3. Financials
        if s in ("bctc", "bctc_workspace", "financials") or "bctc" in op or "financial" in op:
            return BctcResolveLineItemTool()

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
