from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.insights.api.public import router as public_router

module = ModuleDefinition(
    id="insights",
    slug="insights",
    enabled_by_default=True,
    dependencies=("quant_risk", "financials_product", "home_onboarding"),
    feature_flags=("module.insights.enabled",),
    permission_scopes=("public:insights:read",),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
