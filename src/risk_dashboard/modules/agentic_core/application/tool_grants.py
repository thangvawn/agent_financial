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
    operation: str | None = None,
    resource_id: str | None = None,
    max_calls: int = 1,
) -> ToolGrant | None:
    """Resolve a scoped one-run tool grant against the execution envelope.

    Invariants:
    1. FORBIDDEN tools NEVER receive a grant under any circumstances.
    2. CONFIRMED_WRITE tools require an ActionProposal confirmation, not direct grant.
    3. Tool capabilities must be a strict subset of envelope.allowed_capabilities.
    4. Envelope budget max_tool_calls must be positive.
    """
    if tool_manifest.risk_class in {RiskClass.FORBIDDEN, RiskClass.CONFIRMED_WRITE}:
        return None

    allowed_caps = set(envelope.allowed_capabilities)
    for req in tool_manifest.required_capabilities:
        if req not in allowed_caps and "*" not in allowed_caps:
            prefix = req.split(":")[0] if ":" in req else req
            if not (
                f"{prefix}:*" in allowed_caps
                or f"{prefix}:all" in allowed_caps
                or (prefix == "learn" and "learning:all" in allowed_caps)
                or (prefix == "learn" and "learning:read" in allowed_caps and ":write" not in req)
            ):
                return None

    if envelope.budget.max_tool_calls <= 0:
        return None

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    return ToolGrant(
        grant_id=str(uuid4()),
        run_id=envelope.run_id,
        tool_id=tool_manifest.tool_id,
        scopes=envelope.scopes,
        operation=operation,
        resource_id=resource_id,
        max_calls=max_calls,
        expires_at=expires_at.isoformat(),
    )


def validate_grant(grant: ToolGrant, *, run_id: str, tool_id: str) -> bool:
    """Validate that a tool grant is currently active, matches the run and tool."""
    if grant.run_id != run_id:
        return False
    if grant.tool_id != tool_id:
        return False
    try:
        expiry_dt = datetime.fromisoformat(grant.expires_at)
        now_utc = datetime.now(timezone.utc)
        if expiry_dt.tzinfo is None:
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
        return now_utc < expiry_dt
    except (ValueError, TypeError):
        return False

