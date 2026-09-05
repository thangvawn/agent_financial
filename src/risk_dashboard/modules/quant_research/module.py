"""Module definition for quant_research."""
from __future__ import annotations

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.quant_research.api.public import router as public_router

module = ModuleDefinition(
    id="quant_research",
    slug="quant_research",
    enabled_by_default=False,
    dependencies=("quant_risk",),
    feature_flags=("module.quant_research.enabled",),
    permission_scopes=(
        "quant_research:analysis:read",
        "quant_research:scenario:read",
        "quant_research:model_report:read",
        "public:quant_risk:read",
    ),
    public_router=public_router,
    public_mount_prefix="",
)

