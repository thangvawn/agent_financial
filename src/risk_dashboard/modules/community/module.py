from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.community.api.public import router as public_router

module = ModuleDefinition(
    id="community",
    slug="community",
    enabled_by_default=True,
    dependencies=("learning", "goals", "home_onboarding"),
    feature_flags=("module.community.enabled",),
    permission_scopes=("public:community:read", "public:community:write"),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
