from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.admin_cms.api.admin import router as admin_router

module = ModuleDefinition(
    id="admin_cms",
    slug="admin_cms",
    enabled_by_default=True,
    dependencies=("learning", "community", "insights"),
    feature_flags=("module.admin_cms.enabled",),
    permission_scopes=("admin:cms:manage",),
    admin_router=admin_router,
    admin_mount_prefix="/admin",
)
