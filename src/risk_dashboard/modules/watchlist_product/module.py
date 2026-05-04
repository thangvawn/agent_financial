from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.watchlist_product.api.public import router as public_router

module = ModuleDefinition(
    id="watchlist_product",
    slug="watchlist_product",
    enabled_by_default=True,
    feature_flags=("module.watchlist_product.enabled",),
    permission_scopes=("public:watchlist:read", "public:watchlist:write"),
    public_router=public_router,
    public_mount_prefix="",
)
