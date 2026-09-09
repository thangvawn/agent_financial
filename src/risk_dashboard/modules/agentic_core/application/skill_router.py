from __future__ import annotations

from typing import Any

from risk_dashboard.modules.agentic_core.domain.ports import ReadOnlyTool
from risk_dashboard.modules.agentic_core.infrastructure.domain_tools import (
    BctcResolveLineItemTool,
    LearningGetLessonContextTool,
)
from risk_dashboard.modules.agentic_core.infrastructure.quant_tool import QuantRiskReadOnlyTool


class SkillRouter:
    """Deterministic intent-to-skill-to-tool routing based on surface and operation."""

    @classmethod
    def resolve_tool(
        cls,
        surface: str,
        operation: str | None = None,
        default_tool: ReadOnlyTool | None = None,
    ) -> ReadOnlyTool:
        s = (surface or "").lower().strip()
        op = (operation or "").lower().strip()

        if s in ("bctc", "bctc_workspace", "financials") or "bctc" in op or "financial" in op:
            return BctcResolveLineItemTool()

        if s in ("learn", "learn_hub", "learning", "tutor") or "lesson" in op or "learn" in op:
            return LearningGetLessonContextTool()

        if default_tool is not None:
            return default_tool
        return QuantRiskReadOnlyTool()

    @classmethod
    def get_required_capabilities(cls, tool: ReadOnlyTool) -> tuple[str, ...]:
        return getattr(tool.manifest, "required_capabilities", ())
