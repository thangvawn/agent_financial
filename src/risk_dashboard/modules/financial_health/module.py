from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.financial_health.api.public import router as public_router

module = ModuleDefinition(
    id="financial_health",
    slug="financial_health",
    enabled_by_default=True,
    dependencies=("learning", "home_onboarding"),
    feature_flags=(
        "module.financial_health.enabled",
        "module.financial_health.coach_v1.enabled",
    ),
    permission_scopes=(
        "public:financial_health:read",
        "public:financial_health:write",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
