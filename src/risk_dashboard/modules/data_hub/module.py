from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.data_hub.api.public import router as public_router

module = ModuleDefinition(
    id="data_hub",
    slug="data_hub",
    enabled_by_default=True,
    dependencies=("system_surface",),
    feature_flags=("module.data_hub.enabled",),
    permission_scopes=("public:data_hub:read",),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
