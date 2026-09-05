from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict

from risk_dashboard.modules.internal_ops.domain.contracts import (
    FORBIDDEN_TOOL_NAMES,
    SCHEMA_VERSION_V1,
)


class ToolManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION_V1
    tool_id: str
    version: str = "1.0.0"
    scope: str
    risk_class: Literal["read", "proposal"]
    is_enabled: bool = True
    description: str


ALLOWED_TOOL_MANIFESTS: dict[str, ToolManifest] = {
    "ops.get_kpi_slice@1.0.0": ToolManifest(
        tool_id="ops.get_kpi_slice@1.0.0",
        scope="analytics_monitoring",
        risk_class="read",
        is_enabled=True,
        description="Query KPI snapshots and window grains",
    ),
    "ops.get_analytics_events@1.0.0": ToolManifest(
        tool_id="ops.get_analytics_events@1.0.0",
        scope="analytics_monitoring",
        risk_class="read",
        is_enabled=True,
        description="Query recent bounded analytics events",
    ),
    "ops.get_source_health@1.0.0": ToolManifest(
        tool_id="ops.get_source_health@1.0.0",
        scope="analytics_monitoring",
        risk_class="read",
        is_enabled=True,
        description="Query data freshness and API health ops metrics",
    ),
    "ops.get_alert_context@1.0.0": ToolManifest(
        tool_id="ops.get_alert_context@1.0.0",
        scope="analytics_monitoring",
        risk_class="read",
        is_enabled=True,
        description="Query active and historical ops alerts",
    ),
    "ops.get_trust_case@1.0.0": ToolManifest(
        tool_id="ops.get_trust_case@1.0.0",
        scope="trust_safety",
        risk_class="read",
        is_enabled=True,
        description="Query trust safety audit and incidents",
    ),
    "ops.get_content_context@1.0.0": ToolManifest(
        tool_id="ops.get_content_context@1.0.0",
        scope="admin_cms",
        risk_class="read",
        is_enabled=True,
        description="Query CMS content details, versions, and review queues",
    ),
    "ops.get_run_trace@1.0.0": ToolManifest(
        tool_id="ops.get_run_trace@1.0.0",
        scope="agentic_core",
        risk_class="read",
        is_enabled=False,  # Disabled until AC6
        description="Query agent run execution traces (disabled until AC6)",
    ),
    "ops.get_skill_eval_diff@1.0.0": ToolManifest(
        tool_id="ops.get_skill_eval_diff@1.0.0",
        scope="agentic_core",
        risk_class="read",
        is_enabled=False,  # Disabled until eval store
        description="Query skill evaluation score diffs (disabled)",
    ),
    "ops.propose_content_fix@1.0.0": ToolManifest(
        tool_id="ops.propose_content_fix@1.0.0",
        scope="admin_cms",
        risk_class="proposal",
        is_enabled=True,
        description="Create non-executable draft content fix recommendation",
    ),
}

# Invariant assertion
for forbidden_name in FORBIDDEN_TOOL_NAMES:
    assert forbidden_name not in ALLOWED_TOOL_MANIFESTS, f"Forbidden tool {forbidden_name} must not be registered"

