from __future__ import annotations

from pydantic import BaseModel


class TrustSafetyStatusResponse(BaseModel):
    enabled: bool
    total_events: int
    critical_events: int
    blocked_events: int
    default_disclaimer_injections: int
    frozen_surfaces: int = 0
    degraded_surfaces: int = 0


class TrustSafetyAuditResponse(BaseModel):
    audit_id: str
    actor_id: str | None = None
    surface: str
    topic: str | None = None
    channel: str
    risk_classes: list[str]
    severity: str
    route_decision: str
    input_summary: str | None = None
    output_summary: str | None = None
    guardrails: list[str]
    disclaimer_injected: bool
    freshness_status: str | None = None
    confidence_label: str | None = None
    escalation_action: str | None = None
    created_at: str


class TrustIncidentResponse(BaseModel):
    incident_id: str
    source_audit_id: str | None = None
    surface: str
    topic: str | None = None
    severity: str
    status: str
    summary: str
    owner_id: str | None = None
    notes: str | None = None
    created_by: str
    created_at: str
    updated_at: str
    resolved_at: str | None = None
