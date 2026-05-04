from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.portfolio_product.api.public import router as public_router

module = ModuleDefinition(
    id="portfolio_product",
    slug="portfolio_product",
    enabled_by_default=True,
    feature_flags=("module.portfolio_product.enabled",),
    permission_scopes=("public:portfolio:read",),
    public_router=public_router,
    public_mount_prefix="",
)
