from __future__ import annotations

from typing import Iterable
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolManifest
from risk_dashboard.modules.learning.agent_tools import (
    GET_CONTEXT_MANIFEST,
    GET_PROGRESS_MANIFEST,
    GET_QUIZ_ITEM_MANIFEST,
    GRADE_CHECKPOINT_MANIFEST,
    RECOMMEND_NEXT_MANIFEST,
    UPDATE_PROGRESS_MANIFEST,
)
from risk_dashboard.modules.financials_product.agent_tools import get_bctc_tool_manifests
from risk_dashboard.modules.pro_lab.application.simulation_tools import get_simulation_tool_manifests


class ToolRegistry:
    """Centralized server-side registry for versioned tool manifests."""

    def __init__(self) -> None:
        self._manifests: dict[str, dict[str, ToolManifest]] = {}

    def register(self, manifest: ToolManifest) -> None:
        tid = manifest.tool_id
        if tid not in self._manifests:
            self._manifests[tid] = {}
        self._manifests[tid][manifest.version] = manifest

    def register_many(self, manifests: Iterable[ToolManifest]) -> None:
        for m in manifests:
            self.register(m)

    def get(self, tool_id: str, version: str | None = None) -> ToolManifest | None:
        versions = self._manifests.get(tool_id)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        # Return latest registered version
        return sorted(versions.values(), key=lambda m: m.version, reverse=True)[0]

    def list_tools(
        self,
        *,
        module: str | None = None,
        risk_class: RiskClass | None = None,
    ) -> list[ToolManifest]:
        tools: list[ToolManifest] = []
        for versions in self._manifests.values():
            for manifest in versions.values():
                if module is not None and manifest.module != module:
                    continue
                if risk_class is not None and manifest.risk_class != risk_class:
                    continue
                tools.append(manifest)
        return tools


_CANONICAL_MANIFESTS: tuple[ToolManifest, ...] = (
    # Read-only domain tools
    ToolManifest(
        tool_id="quant.explain_risk",
        name="Explain Quant Risk",
        module="quant",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Explain quantitative risk and VaR metrics.",
        required_capabilities=("quant:read",),
    ),
    ToolManifest(
        tool_id="learning.get_lesson_context",
        name="Get Lesson Context",
        module="learning",
        risk_class=RiskClass.READ,
        version="1.0.0",
        description="Fetch educational lesson content.",
        required_capabilities=("learning:read",),
    ),
    # Canonical BCTC Tools (Module 5 - BW0, BW1, BW3)
    *get_bctc_tool_manifests(),
    # Canonical Simulation Tools (Module 6 - SIM6)
    *get_simulation_tool_manifests(),
    # Canonical Learning Engine Tools (Module 4 - LEA0, LEA1, LEA4)
    GET_CONTEXT_MANIFEST,
    GET_PROGRESS_MANIFEST,
    GET_QUIZ_ITEM_MANIFEST,
    GRADE_CHECKPOINT_MANIFEST,
    UPDATE_PROGRESS_MANIFEST,
    RECOMMEND_NEXT_MANIFEST,
    # Strictly FORBIDDEN tools (Master Plan §7.8 & §10.2)
    ToolManifest(
        tool_id="broker.place_order",
        name="Live Order Placement",
        module="broker",
        risk_class=RiskClass.FORBIDDEN,
        version="1.0.0",
        description="FORBIDDEN: Autonomous live order execution is strictly prohibited.",
        required_capabilities=("forbidden:trading",),
    ),
    ToolManifest(
        tool_id="broker.cancel_order",
        name="Live Order Cancellation",
        module="broker",
        risk_class=RiskClass.FORBIDDEN,
        version="1.0.0",
        description="FORBIDDEN: Autonomous order cancellation is strictly prohibited.",
        required_capabilities=("forbidden:trading",),
    ),
    ToolManifest(
        tool_id="portfolio.reset",
        name="Reset Portfolio",
        module="portfolio",
        risk_class=RiskClass.FORBIDDEN,
        version="1.0.0",
        description="FORBIDDEN: Portfolio reset is prohibited from agent runtime.",
        required_capabilities=("forbidden:mutation",),
    ),
    ToolManifest(
        tool_id="cms.publish",
        name="Publish CMS Content",
        module="admin_cms",
        risk_class=RiskClass.FORBIDDEN,
        version="1.0.0",
        description="FORBIDDEN: Agent cannot auto-publish CMS content.",
        required_capabilities=("forbidden:cms",),
    ),
    ToolManifest(
        tool_id="trust.close_incident",
        name="Close Security Incident",
        module="trust_safety",
        risk_class=RiskClass.FORBIDDEN,
        version="1.0.0",
        description="FORBIDDEN: Agent cannot auto-close security incidents.",
        required_capabilities=("forbidden:trust",),
    ),
)

_DEFAULT_REGISTRY: ToolRegistry | None = None


def get_default_tool_registry() -> ToolRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        reg = ToolRegistry()
        reg.register_many(_CANONICAL_MANIFESTS)
        _DEFAULT_REGISTRY = reg
    return _DEFAULT_REGISTRY


def reset_default_tool_registry() -> None:
    global _DEFAULT_REGISTRY
    _DEFAULT_REGISTRY = None
