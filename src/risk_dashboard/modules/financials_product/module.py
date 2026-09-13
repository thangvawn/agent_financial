from __future__ import annotations

from fastapi import APIRouter
from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.financials_product.api.public import router as base_public_router
from risk_dashboard.modules.financials_product.api.agent_router import router as agent_router

public_router = APIRouter()
public_router.include_router(base_public_router)
public_router.include_router(agent_router, prefix="/api/v1/public/bctc/agent")
public_router.include_router(agent_router, prefix="/api/v1/bctc/agent")
public_router.include_router(agent_router, prefix="/bctc/agent")

module = ModuleDefinition(
    id="financials_product",
    slug="financials_product",
    enabled_by_default=True,
    feature_flags=(
        "module.financials_product.enabled",
        "module.financials_product.bctc_agent.enabled",
    ),
    permission_scopes=(
        "public:financials:read",
        "public:financials:write",
        "bctc:report:read",
        "bctc:formula:read",
        "bctc:evidence:read",
    ),
    public_router=public_router,
    public_mount_prefix="",
)
