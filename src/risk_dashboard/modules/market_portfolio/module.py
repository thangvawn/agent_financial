from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.market_portfolio.api.public import router as public_router

module = ModuleDefinition(
    id="market_portfolio",
    slug="market_portfolio",
    enabled_by_default=True,
    dependencies=("data_hub",),
    feature_flags=("module.market_portfolio.enabled",),
    permission_scopes=(
        "public:market_portfolio:read",
        "public:market_portfolio:write",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1",
)
