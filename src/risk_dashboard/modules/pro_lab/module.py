from fastapi import APIRouter

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.pro_lab.api.public import router as public_router
from risk_dashboard.modules.pro_lab.api.pro import router as pro_router
from risk_dashboard.modules.pro_lab.api.admin import router as admin_router
from risk_dashboard.modules.pro_lab.api.ai import router as ai_router

_combined_pro_router = APIRouter()
_combined_pro_router.include_router(pro_router)
_combined_pro_router.include_router(ai_router)

# Phase 4: registered slug is simulation_lab; package folder remains pro_lab (HTTP /pro-lab kept for FE).
module = ModuleDefinition(
    id="simulation_lab",
    slug="simulation_lab",
    enabled_by_default=True,
    feature_flags=(
        "module.simulation_lab.enabled",
        "module.pro_lab.enabled",  # backward-compatible flag
    ),
    permission_scopes=(
        "public:simulation_lab:read",
        "pro:simulation_lab:use",
        "admin:simulation_lab:manage",
        "public:pro_lab:read",
        "pro:pro_lab:use",
        "admin:pro_lab:manage",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
    pro_router=_combined_pro_router,
    admin_router=admin_router,
    admin_mount_prefix="/admin",
)
