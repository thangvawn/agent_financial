from __future__ import annotations

import inspect
from typing import Any

from risk_dashboard.modules.agentic_core.application.tool_registry import get_default_tool_registry
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.learning.agent_tools import (
    LearningGetContextTool,
    LearningGetProgressTool,
    LearningGetQuizItemTool,
    LearningGradeCheckpointTool,
    LearningRecommendNextTool,
    LearningUpdateProgressTool,
)
from risk_dashboard.modules.agentic_core.infrastructure.learning_domain_tools import (
    LearningGetContextDomainTool,
    LearningGetQuizItemDomainTool,
    LearningGradeCheckpointDomainTool,
    LearningRecommendNextDomainTool,
)
from risk_dashboard.modules.agentic_core.infrastructure.bctc_domain_tools import (
    BctcResolveLineItemDomainTool,
)

BctcResolveLineItemTool = BctcResolveLineItemDomainTool


class LearningGetLessonContextTool:
    """Read-only domain tool wrapping learning engine."""

    def __init__(
        self,
        manifest: ToolManifest | None = None,
        service: Any = None,
    ) -> None:
        if manifest is None:
            manifest = get_default_tool_registry().get("learning.get_lesson_context")
            if manifest is None:
                manifest = ToolManifest(
                    tool_id="learning.get_lesson_context",
                    name="Get Lesson Context",
                    module="learning",
                    risk_class=RiskClass.READ,
                    version="1.0.0",
                    description="Fetch educational lesson content.",
                    required_capabilities=("learning:read",),
                )
        self.manifest = manifest
        self.service = service

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        lesson_id = "quant_101"
        res_id = getattr(grant, "resource_id", None)
        if res_id:
            if ":" in res_id:
                lesson_id = res_id.split(":")[-1]
            else:
                lesson_id = res_id

        res_data: dict[str, str] = {}
        if self.service is not None:
            if inspect.iscoroutinefunction(self.service):
                out = await self.service(lesson_id)
            else:
                out = self.service(lesson_id)
            if isinstance(out, dict):
                res_data = {str(k): str(v) for k, v in out.items()}
        else:
            try:
                from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
                catalog = SqliteLearningCatalog()
                lesson = catalog.get_lesson(lesson_id=lesson_id)
                res_data = {
                    "title": str(lesson.title),
                    "canonical_content": "\n".join(str(b) for b in lesson.body),
                    "summary": str(lesson.summary),
                    "status": str(lesson.status),
                    "topic": str(lesson.title),
                    "concept": str(lesson.summary),
                }
            except Exception:
                res_data = {
                    "topic": "Quantitative Foundations",
                    "concept": "Quantitative Risk & Return",
                }

        tool_id = "learning.get_context" if getattr(grant, "tool_id", None) == "learning.get_context" else self.manifest.tool_id

        return {
            "tool_id": tool_id,
            "status": "active",
            "lesson_id": lesson_id,
            **res_data,
        }
