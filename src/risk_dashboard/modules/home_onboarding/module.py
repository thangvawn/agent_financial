from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.home_onboarding.api.public import router as public_router

# Phase 4: registered slug is home; package folder remains home_onboarding.
module = ModuleDefinition(
    id="home",
    slug="home",
    enabled_by_default=True,
    dependencies=("learning",),
    feature_flags=(
        "module.home.enabled",
        "module.home_onboarding.enabled",
        "module.home_onboarding.personalized_home_v1.enabled",
    ),
    permission_scopes=(
        "public:home:read",
        "public:home:write",
        "public:home_onboarding:read",
        "public:home_onboarding:write",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
