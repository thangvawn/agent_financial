from __future__ import annotations

from typing import Sequence

from risk_dashboard.modules.agentic_core.application.tool_registry import (
    ToolRegistry,
    get_default_tool_registry,
)
from risk_dashboard.modules.agentic_core.domain.tools import ToolManifest


class SkillManifestLoader:
    """Loads and syncs versioned skill manifests from system registries and workspace."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or get_default_tool_registry()

    def load_manifests(self) -> Sequence[ToolManifest]:
        return self._registry.list_tools()

    def get_manifest(self, tool_id: str, version: str | None = None) -> ToolManifest | None:
        return self._registry.get(tool_id, version=version)
