from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.learning.api.admin import router as admin_router
from risk_dashboard.modules.learning.api.public import router as public_router

module = ModuleDefinition(
    id="learning",
    slug="learning",
    enabled_by_default=True,
    dependencies=("auth_access", "trust_safety"),
    feature_flags=("module.learning.enabled", "module.learning.tutor_v1.enabled"),
    permission_scopes=("public:learning:read", "public:learning:write"),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
    admin_router=admin_router,
    admin_mount_prefix="/admin",
)
