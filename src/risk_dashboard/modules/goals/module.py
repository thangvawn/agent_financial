from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.goals.api.public import router as public_router

module = ModuleDefinition(
    id="goals",
    slug="goals",
    enabled_by_default=False,  # legacy — out of product surface (Phase 2)
    dependencies=("financial_health", "learning", "home_onboarding"),
    feature_flags=(
        "module.goals.enabled",
        "module.goals.planner_v1.enabled",
    ),
    permission_scopes=(
        "public:goals:read",
        "public:goals:write",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
