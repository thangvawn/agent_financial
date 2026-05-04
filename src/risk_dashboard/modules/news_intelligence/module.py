from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.news_intelligence.api.public import router as public_router

module = ModuleDefinition(
    id="news_intelligence",
    slug="news_intelligence",
    enabled_by_default=True,
    dependencies=("system_surface",),
    feature_flags=("module.news_intelligence.enabled",),
    permission_scopes=("public:news:read",),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
