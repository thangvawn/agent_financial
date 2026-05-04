from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.agent_orchestration.api.public import router as public_router

module = ModuleDefinition(
    id="agent_orchestration",
    slug="agent_orchestration",
    enabled_by_default=True,
    feature_flags=("module.agent_orchestration.enabled",),
    permission_scopes=("public:agent_orchestration:read",),
    public_router=public_router,
    public_mount_prefix="",
)
