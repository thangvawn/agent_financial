from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope


def resolve_grant(
    envelope: TrustedExecutionEnvelope,
    tool_manifest: ToolManifest,
    *,
    ttl_seconds: int = 300,
) -> ToolGrant | None:
    if tool_manifest.risk_class in {RiskClass.FORBIDDEN, RiskClass.CONFIRMED_WRITE}:
        return None
    if not set(tool_manifest.required_capabilities).issubset(envelope.allowed_capabilities):
        return None
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    return ToolGrant(
        grant_id=str(uuid4()),
        run_id=envelope.run_id,
        tool_id=tool_manifest.tool_id,
        scopes=envelope.scopes,
        expires_at=expires_at.isoformat(),
    )
