from fastapi import APIRouter

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.market_portfolio.api.agent import (
    ops_router,
    router as agent_router,
)
from risk_dashboard.modules.market_portfolio.api.public import router as public_router

# Combine legacy public router, agent router, and ops router under public mount prefix (/api/v1)
router = APIRouter()
router.include_router(public_router)
router.include_router(agent_router)
router.include_router(ops_router)


module = ModuleDefinition(
    id="market_portfolio",
    slug="market_portfolio",
    enabled_by_default=True,
    dependencies=("data_hub",),
    feature_flags=(
        "module.market_portfolio.enabled",
        "module.market_portfolio.agent.enabled",
    ),
    permission_scopes=(
        "public:market_portfolio:read",
        "public:market_portfolio:write",
        "account:market_portfolio:read",
    ),
    public_router=router,
    public_mount_prefix="/api/v1",
)
