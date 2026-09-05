from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from risk_dashboard.modules.internal_ops.application.policy import (
    GrantExpiredError,
    PolicyDeniedError,
    PurposeGrant,
    parse_iso,
    utc_now,
)
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceRef,
    FORBIDDEN_TOOL_NAMES,
    OpsActionRecommendation,
    SCHEMA_VERSION_V1,
)
from risk_dashboard.modules.internal_ops.domain.manifests import (
    ALLOWED_TOOL_MANIFESTS,
    ToolManifest,
)

__all__ = [
    "ALLOWED_TOOL_MANIFESTS",
    "InvestigationToolGrant",
    "ToolManifest",
    "ToolRegistry",
]


class InvestigationToolGrant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION_V1
    grant_id: str
    investigation_id: str
    tool_id: str
    purpose: str
    expires_at: str
    max_calls: int = Field(default=10, ge=1, le=100)
    call_count: int = 0

    def consume(self) -> None:
        if parse_iso(self.expires_at) <= utc_now():
            raise GrantExpiredError(f"Tool grant {self.grant_id} for {self.tool_id} has expired.")
        if self.call_count >= self.max_calls:
            raise PolicyDeniedError(f"Tool grant call limit ({self.max_calls}) exhausted for {self.tool_id}.")
        self.call_count += 1


class ToolRegistry:
    @staticmethod
    def get_manifest(tool_id: str) -> ToolManifest:
        if tool_id in FORBIDDEN_TOOL_NAMES:
            raise PolicyDeniedError(f"Tool '{tool_id}' is forbidden and never registered.")
        if tool_id not in ALLOWED_TOOL_MANIFESTS:
            raise PolicyDeniedError(f"Tool '{tool_id}' is unknown or not registered.")
        return ALLOWED_TOOL_MANIFESTS[tool_id]

    @classmethod
    def execute(
        cls,
        tool_id: str,
        grant: InvestigationToolGrant,
        purpose_grant: PurposeGrant,
        adapters: dict[str, Any],
        params: dict[str, Any],
    ) -> Any:
        manifest = cls.get_manifest(tool_id)
        if not manifest.is_enabled:
            return EvidenceBatch(
                items=(),
                source_module=manifest.scope,
                fetched_at=datetime.now(timezone.utc).isoformat(),
                status="source_unavailable",
            )

        grant.consume()

        if tool_id == "ops.get_kpi_slice@1.0.0":
            return adapters["analytics"].get_kpi_slice(
                purpose_grant, kpi_name=params.get("kpi_name"), window=params.get("window")
            )
        if tool_id == "ops.get_analytics_events@1.0.0":
            return adapters["analytics"].get_analytics_events(
                purpose_grant, event_name=params.get("event_name"), limit=params.get("limit", 100)
            )
        if tool_id == "ops.get_source_health@1.0.0":
            return adapters["analytics"].get_source_health(
                purpose_grant, metric_group=params.get("metric_group", "data_freshness")
            )
        if tool_id == "ops.get_alert_context@1.0.0":
            return adapters["analytics"].get_alert_context(
                purpose_grant, status=params.get("status")
            )
        if tool_id == "ops.get_trust_case@1.0.0":
            return adapters["trust_safety"].get_trust_case(
                purpose_grant, surface=params.get("surface"), status=params.get("status"), limit=params.get("limit", 100)
            )
        if tool_id == "ops.get_content_context@1.0.0":
            return adapters["admin_cms"].get_content_context(
                purpose_grant, content_id=params.get("content_id"), content_type=params.get("content_type")
            )
        if tool_id == "ops.propose_content_fix@1.0.0":
            target_ref = params.get("target_ref")
            if not isinstance(target_ref, EvidenceRef):
                target_ref = EvidenceRef.model_validate(target_ref)
            return OpsActionRecommendation(
                recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                action_kind="content_draft_fix",
                target_ref=target_ref,
                rationale=params.get("rationale", "Propose draft fix for reviewed content"),
                payload_preview=params.get("payload_preview", {}),
            )

        raise PolicyDeniedError(f"No execution handler registered for {tool_id}")


