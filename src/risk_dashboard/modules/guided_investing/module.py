from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.guided_investing.api.public import router as public_router

# Phase 4: retired from product surface (BCTC uses financials_product). Package kept for AI soft reads.
module = ModuleDefinition(
    id="guided_investing",
    slug="guided_investing",
    enabled_by_default=False,
    dependencies=("learning", "financials_product"),
    feature_flags=("module.guided_investing.enabled",),
    permission_scopes=("public:guided_investing:read", "public:guided_investing:write"),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
