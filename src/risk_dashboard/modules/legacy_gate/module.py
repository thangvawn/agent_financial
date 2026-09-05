"""Module definition for legacy_gate."""
from __future__ import annotations

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.legacy_gate.api.public import router as public_router

module = ModuleDefinition(
    id="legacy_gate",
    slug="legacy_gate",
    enabled_by_default=True,  # Gate must always be active
    dependencies=(),
    feature_flags=("module.legacy_gate.enabled",),
    permission_scopes=("public:legacy_gate:read",),
    public_router=public_router,
    public_mount_prefix="",
)

