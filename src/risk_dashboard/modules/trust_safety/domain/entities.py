from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class TrustModerationResult:
    risk_classes: tuple[str, ...]
    severity: str
    action: str
    explanation: str


@dataclass(frozen=True)
class TrustDisclaimer:
    title: str
    short_text: str
    full_text: str
    severity: str


@dataclass(frozen=True)
class TrustPresentation:
    disclaimer: TrustDisclaimer
    disclaimer_injected: bool
    freshness_status: str
    confidence_label: str
    risk_banner: str | None
    what_this_is: str
    what_this_is_not: str
    surface_state: str = "normal"
    surface_state_reason: str | None = None


@dataclass(frozen=True)
class TrustAuditLog:
    audit_id: str
    surface: str
    channel: str
    route_decision: str
    severity: str
    risk_classes: tuple[str, ...]
    actor_id: str | None = None
    topic: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    guardrails: tuple[str, ...] = ()
    disclaimer_injected: bool = False
    freshness_status: str | None = None
    confidence_label: str | None = None
    escalation_action: str | None = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class TrustIncident:
    incident_id: str
    surface: str
    severity: str
    status: str
    summary: str
    created_by: str
    source_audit_id: str | None = None
    topic: str | None = None
    owner_id: str | None = None
    notes: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    resolved_at: str | None = None


@dataclass(frozen=True)
class TrustSurfaceControl:
    surface: str
    state: str
    severity: str
    incident_id: str
    reason: str
