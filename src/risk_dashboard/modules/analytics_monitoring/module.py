from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.analytics_monitoring.api.admin import router as admin_router
from risk_dashboard.modules.analytics_monitoring.api.public import router as public_router

module = ModuleDefinition(
    id="analytics_monitoring",
    slug="analytics_monitoring",
    enabled_by_default=True,
    dependencies=("trust_safety", "simulation_lab"),
    feature_flags=("module.analytics_monitoring.enabled",),
    permission_scopes=(
        "public:analytics_monitoring:write",
        "admin:analytics_monitoring:read",
        "admin:analytics_monitoring:write",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
    admin_router=admin_router,
    admin_mount_prefix="/admin",
)
