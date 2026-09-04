from __future__ import annotations

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.ai_tutor.api.public import router as public_router

module = ModuleDefinition(
    id="ai_tutor",
    slug="ai_tutor",
    enabled_by_default=True,
    dependencies=("auth_access", "trust_safety", "learning"),
    feature_flags=("module.ai_tutor.enabled",),
    permission_scopes=(
        "ai_tutor:conversation:read",
        "ai_tutor:conversation:write",
        "ai_tutor:feedback:write",
    ),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)

