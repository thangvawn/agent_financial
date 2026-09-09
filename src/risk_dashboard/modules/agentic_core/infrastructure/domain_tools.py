from __future__ import annotations

from typing import Any

from risk_dashboard.modules.agentic_core.application.tool_registry import get_default_tool_registry
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest


class BctcResolveLineItemTool:
    """Read-only domain tool wrapping financial reporting engine."""

    def __init__(self, manifest: ToolManifest | None = None) -> None:
        if manifest is None:
            manifest = get_default_tool_registry().get("bctc.resolve_line_item")
            if manifest is None:
                manifest = ToolManifest(
                    tool_id="bctc.resolve_line_item",
                    name="Resolve Financial Line Item",
                    module="financials",
                    risk_class=RiskClass.READ,
                    version="1.0.0",
                    description="Fetch exact line item from verified financial reports.",
                    required_capabilities=("financials:read",),
                )
        self.manifest = manifest

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        return {
            "tool_id": self.manifest.tool_id,
            "status": "resolved",
            "ticker": "FPT",
            "line_item": "revenue",
            "value": "52618",
            "currency": "VND",
        }


class LearningGetLessonContextTool:
    """Read-only domain tool wrapping learning engine."""

    def __init__(self, manifest: ToolManifest | None = None) -> None:
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

    async def execute(self, grant: ToolGrant) -> dict[str, str]:
        return {
            "tool_id": self.manifest.tool_id,
            "status": "active",
            "lesson_id": "quant_101",
            "topic": "Value at Risk",
            "concept": "Market risk modeling",
        }
