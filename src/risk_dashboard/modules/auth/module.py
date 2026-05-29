from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.auth.api.public import router as public_router

module = ModuleDefinition(
    id="auth",
    slug="auth",
    enabled_by_default=True,
    dependencies=(),
    feature_flags=(),
    permission_scopes=(),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
