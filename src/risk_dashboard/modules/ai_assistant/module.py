from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.ai_assistant.api.pro import router as pro_router
from risk_dashboard.modules.ai_assistant.api.public import router as public_router

module = ModuleDefinition(
    id="ai_assistant",
    slug="ai_assistant",
    enabled_by_default=True,
    dependencies=("learning", "financial_health", "guided_investing", "pro_lab"),
    feature_flags=("module.ai_assistant.enabled", "module.ai_assistant.public_v1.enabled"),
    permission_scopes=("public:ai_assistant:use", "pro:ai_assistant:use"),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
    pro_router=pro_router,
    pro_mount_prefix="/api/v1/pro",
)
