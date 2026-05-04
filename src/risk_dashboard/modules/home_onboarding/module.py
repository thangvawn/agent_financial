from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.home_onboarding.api.public import router as public_router

module = ModuleDefinition(
    id="home_onboarding",
    slug="home_onboarding",
    enabled_by_default=True,
    dependencies=("learning",),
    feature_flags=(
        "module.home_onboarding.enabled",
        "module.home_onboarding.personalized_home_v1.enabled",
    ),
    permission_scopes=(
        "public:home_onboarding:read",
        "public:home_onboarding:write",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
