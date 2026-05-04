from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.guided_investing.api.public import router as public_router

module = ModuleDefinition(
    id="guided_investing",
    slug="guided_investing",
    enabled_by_default=True,
    dependencies=("financial_health", "learning", "watchlist_product", "financials_product", "quant_risk"),
    feature_flags=("module.guided_investing.enabled",),
    permission_scopes=("public:guided_investing:read", "public:guided_investing:write"),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
