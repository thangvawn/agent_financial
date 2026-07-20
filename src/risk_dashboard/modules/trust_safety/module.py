from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.trust_safety.api.admin import router as admin_router

module = ModuleDefinition(
    id="trust_safety",
    slug="trust_safety",
    enabled_by_default=True,
    dependencies=("admin_cms", "community", "insights", "guided_investing"),
    feature_flags=("module.trust_safety.enabled",),
    permission_scopes=("admin:trust_safety:read",),
    admin_router=admin_router,
    admin_mount_prefix="/admin",
)
