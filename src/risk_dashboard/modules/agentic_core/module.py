"""Module definition for agentic_core."""
from __future__ import annotations

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.agentic_core.api.public import router as public_router

module = ModuleDefinition(
    id="agentic_core",
    slug="agentic_core",
    enabled_by_default=True,
    dependencies=(),
    feature_flags=(),
    permission_scopes=(
        "agentic:run:execute",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1/public/agentic",
)
