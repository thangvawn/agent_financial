from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.quant_risk.api.public import router as public_router

module = ModuleDefinition(
    id="quant_risk",
    slug="quant_risk",
    enabled_by_default=True,
    feature_flags=("module.quant_risk.enabled",),
    permission_scopes=("public:quant_risk:read",),
    public_router=public_router,
    public_mount_prefix="",
)
