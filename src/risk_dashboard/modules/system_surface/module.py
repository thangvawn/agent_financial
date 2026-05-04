from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.system_surface.api.admin import router as admin_router
from risk_dashboard.modules.system_surface.api.public import router as public_router

module = ModuleDefinition(
    id="system_surface",
    slug="system_surface",
    enabled_by_default=True,
    feature_flags=("module.system_surface.enabled",),
    permission_scopes=("public:system_surface:read", "admin:system_surface:manage"),
    public_router=public_router,
    public_mount_prefix="",
    admin_router=admin_router,
    admin_mount_prefix="/admin",
)
