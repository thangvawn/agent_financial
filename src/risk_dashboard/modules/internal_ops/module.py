from __future__ import annotations

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.internal_ops.api.admin import router as admin_router

module = ModuleDefinition(
    id="internal_ops",
    slug="internal_ops",
    enabled_by_default=False,
    dependencies=("analytics_monitoring", "trust_safety", "admin_cms"),
    feature_flags=("module.internal_ops.enabled",),
    permission_scopes=(
        "admin:internal_ops:investigate",
        "admin:internal_ops:content_read",
        "admin:internal_ops:trust_read",
        "admin:internal_ops:report_read",
    ),
    admin_router=admin_router,
    admin_mount_prefix="/admin",
)

