from fastapi import APIRouter

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.news_intelligence.api.public import router as public_router
from risk_dashboard.modules.news_intelligence.api.social import router as social_router

combined_router = APIRouter()
combined_router.include_router(public_router)
combined_router.include_router(social_router)

module = ModuleDefinition(
    id="news_intelligence",
    slug="news_intelligence",
    enabled_by_default=True,
    dependencies=("system_surface",),
    feature_flags=(
        "module.news_intelligence.enabled",
        "module.news_intelligence.agent.enabled",
    ),
    permission_scopes=(
        "public:news:read",
        "public:news:agent:read",
        "public:news:write",
    ),
    public_router=combined_router,
    public_mount_prefix="/api/v1/public",
)
