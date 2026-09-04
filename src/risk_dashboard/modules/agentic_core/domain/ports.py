from __future__ import annotations

from typing import Protocol

from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant, ToolManifest


class ReadOnlyTool(Protocol):
    manifest: ToolManifest

    async def execute(self, grant: ToolGrant) -> dict[str, str]: ...
