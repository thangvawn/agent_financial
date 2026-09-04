from __future__ import annotations

from fastapi import APIRouter

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.home_onboarding.api.journey import router as journey_router
from risk_dashboard.modules.home_onboarding.api.public import router as public_router

# Combine legacy public router and authenticated journey router
router = APIRouter()
router.include_router(public_router, prefix="/api/v1/public")
router.include_router(journey_router, prefix="/api/v1/me")

module = ModuleDefinition(
    id="home",
    slug="home",
    enabled_by_default=True,
    dependencies=("learning",),
    feature_flags=(
        "module.home.enabled",
        "module.home_onboarding.enabled",
        "module.home_onboarding.personalized_home_v1.enabled",
        "module.home_onboarding.home_journey.v1.enabled",
    ),
    permission_scopes=(
        "public:home:read",
        "public:home:write",
        "public:home_onboarding:read",
        "public:home_onboarding:write",
        "me:home_journey:read",
        "me:home_journey:feedback",
    ),
    public_router=router,
    public_mount_prefix="",
)
