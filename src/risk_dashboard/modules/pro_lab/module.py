from fastapi import APIRouter

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.pro_lab.api.public import router as public_router
from risk_dashboard.modules.pro_lab.api.pro import router as pro_router
from risk_dashboard.modules.pro_lab.api.admin import router as admin_router
from risk_dashboard.modules.pro_lab.api.ai import router as ai_router

_combined_pro_router = APIRouter()
_combined_pro_router.include_router(pro_router)
_combined_pro_router.include_router(ai_router)

module = ModuleDefinition(
    id="pro_lab",
    slug="pro_lab",
    enabled_by_default=True,
    feature_flags=("module.pro_lab.enabled",),
    permission_scopes=("public:pro_lab:read", "pro:pro_lab:use", "admin:pro_lab:manage"),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
    pro_router=_combined_pro_router,
    admin_router=admin_router,
    admin_mount_prefix="/admin",
)
