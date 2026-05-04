from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.financials_product.api.public import router as public_router

module = ModuleDefinition(
    id="financials_product",
    slug="financials_product",
    enabled_by_default=True,
    feature_flags=("module.financials_product.enabled",),
    permission_scopes=("public:financials:read", "public:financials:write"),
    public_router=public_router,
    public_mount_prefix="",
)
