from __future__ import annotations

from dataclasses import dataclass, replace

from risk_dashboard.modules.trust_safety.domain.entities import (
    TrustAuditLog,
    TrustDisclaimer,
    TrustIncident,
    TrustModerationResult,
    TrustPresentation,
    utc_now_iso,
)
from risk_dashboard.modules.trust_safety.domain.policies import (
    RISK_MISSING_DISCLAIMER,
    build_moderation_explanation,
    build_risk_banner,
    confidence_label_for_quality,
    degrade_banner_for_surface,
    default_disclaimer,
    detect_risk_classes,
    extra_guardrails_for_role,
    freeze_banner_for_surface,
    moderation_action,
    normalize_freshness_status,
    severity_for_risks,
    what_this_is,
    what_this_is_not,
)
from risk_dashboard.modules.trust_safety.infrastructure.repositories.sqlite import (
    SqliteTrustSafetyRepository,
    new_trust_audit_id,
    new_trust_incident_id,
)
from risk_dashboard.modules.trust_safety.schemas.requests import TrustIncidentActionRequest, TrustIncidentOpenRequest
from risk_dashboard.modules.trust_safety.schemas.responses import (
    TrustSafetyAuditResponse,
    TrustIncidentResponse,
    TrustSafetyStatusResponse,
)


@dataclass(frozen=True)
class TrustRuntimeDisclaimer:
    title: str
    short_text: str
    full_text: str
    severity: str


class TrustSafetyService:
    def __init__(self, repo: SqliteTrustSafetyRepository | None = None) -> None:
        self.repo = repo or SqliteTrustSafetyRepository()

    def analyze_text(self, *, surface: str, text: str) -> TrustModerationResult:
        risk_classes = detect_risk_classes(text=text, surface=surface)
        severity = severity_for_risks(risk_classes)
        action = moderation_action(surface=surface, risk_classes=risk_classes)
        explanation = build_moderation_explanation(surface=surface, action=action, risk_classes=risk_classes)
        return TrustModerationResult(
            risk_classes=risk_classes,
            severity=severity,
            action=action,
            explanation=explanation,
        )

    def build_presentation(
        self,
        *,
        surface: str,
        topic: str | None,
        quality_state: str | None,
        freshness_value: str | None,
        disclaimer: object | None,
        existing_banner: str | None = None,
    ) -> TrustPresentation:
        disclaimer_injected = False
        if disclaimer is None:
            resolved = default_disclaimer(surface=surface, topic=topic)
            disclaimer_injected = True
        else:
            resolved = TrustDisclaimer(
                title=str(getattr(disclaimer, "title")),
                short_text=str(getattr(disclaimer, "short_text")),
                full_text=str(getattr(disclaimer, "full_text")),
                severity=str(getattr(disclaimer, "severity")),
            )
        freshness_status = normalize_freshness_status(freshness_value=freshness_value, quality_state=quality_state)
        confidence_label = confidence_label_for_quality(quality_state=quality_state, freshness_status=freshness_status)
        risk_banner = build_risk_banner(
            freshness_status=freshness_status,
            quality_state=quality_state,
            disclaimer_injected=disclaimer_injected,
            existing_banner=existing_banner,
        )
        control = self.repo.get_surface_control(surface=surface)
        surface_state = "normal"
        surface_state_reason = None
        if control is not None:
            surface_state = control.state
            surface_state_reason = control.reason
            if control.state == "freeze":
                freshness_status = "unavailable"
                confidence_label = "low_confidence"
                risk_banner = freeze_banner_for_surface(surface=surface, reason=control.reason)
            elif control.state == "degrade":
                if confidence_label == "high_confidence":
                    confidence_label = "moderate_confidence"
                risk_banner = degrade_banner_for_surface(surface=surface, reason=control.reason)
        return TrustPresentation(
            disclaimer=resolved,
            disclaimer_injected=disclaimer_injected,
            freshness_status=freshness_status,
            confidence_label=confidence_label,
            risk_banner=risk_banner,
            what_this_is=what_this_is(surface=surface),
            what_this_is_not=what_this_is_not(surface=surface),
            surface_state=surface_state,
            surface_state_reason=surface_state_reason,
        )

    def build_guardrails(
        self,
        *,
        surface: str,
        role: str | None,
        risk_classes: tuple[str, ...],
        existing_guardrails: tuple[str, ...] = (),
        disclaimer_injected: bool = False,
    ) -> tuple[str, ...]:
        extra_risks = risk_classes
        if disclaimer_injected and RISK_MISSING_DISCLAIMER not in extra_risks:
            extra_risks = tuple([*risk_classes, RISK_MISSING_DISCLAIMER])
        combined = [*existing_guardrails, *extra_guardrails_for_role(surface=surface, role=role, risk_classes=extra_risks)]
        return tuple(dict.fromkeys(combined))

    def record_audit(
        self,
        *,
        actor_id: str | None,
        surface: str,
        topic: str | None,
        channel: str,
        risk_classes: tuple[str, ...],
        route_decision: str,
        input_summary: str | None = None,
        output_summary: str | None = None,
        guardrails: tuple[str, ...] = (),
        disclaimer_injected: bool = False,
        freshness_status: str | None = None,
        confidence_label: str | None = None,
        escalation_action: str | None = None,
    ) -> TrustAuditLog:
        severity = severity_for_risks(risk_classes)
        control = self.repo.get_surface_control(surface=surface)
        resolved_escalation = escalation_action
        if control is not None:
            resolved_escalation = f"surface_{control.state}"
        return self.repo.save_audit_log(
            TrustAuditLog(
                audit_id=new_trust_audit_id(),
                actor_id=actor_id,
                surface=surface,
                topic=topic,
                channel=channel,
                risk_classes=risk_classes,
                severity=severity,
                route_decision=route_decision,
                input_summary=input_summary[:240] if input_summary else None,
                output_summary=output_summary[:240] if output_summary else None,
                guardrails=guardrails,
                disclaimer_injected=disclaimer_injected,
                freshness_status=freshness_status,
                confidence_label=confidence_label,
                escalation_action=resolved_escalation,
            )
        )


class GetTrustSafetyStatus:
    def __init__(self, repo: SqliteTrustSafetyRepository) -> None:
        self.repo = repo

    def execute(self, *, enabled: bool) -> TrustSafetyStatusResponse:
        overview = self.repo.overview()
        return TrustSafetyStatusResponse(enabled=enabled, **overview)


class ListTrustSafetyAudit:
    def __init__(self, repo: SqliteTrustSafetyRepository) -> None:
        self.repo = repo

    def execute(
        self,
        *,
        surface: str | None = None,
        risk_class: str | None = None,
        severity: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[TrustSafetyAuditResponse]:
        return [
            TrustSafetyAuditResponse(
                audit_id=item.audit_id,
                actor_id=item.actor_id,
                surface=item.surface,
                topic=item.topic,
                channel=item.channel,
                risk_classes=list(item.risk_classes),
                severity=item.severity,
                route_decision=item.route_decision,
                input_summary=item.input_summary,
                output_summary=item.output_summary,
                guardrails=list(item.guardrails),
                disclaimer_injected=item.disclaimer_injected,
                freshness_status=item.freshness_status,
                confidence_label=item.confidence_label,
                escalation_action=item.escalation_action,
                created_at=item.created_at,
            )
            for item in self.repo.list_audit_logs(
                surface=surface,
                risk_class=risk_class,
                severity=severity,
                search=search,
                limit=limit,
            )
        ]


class OpenTrustIncident:
    def __init__(self, repo: SqliteTrustSafetyRepository) -> None:
        self.repo = repo

    def execute(self, *, actor_id: str, req: TrustIncidentOpenRequest) -> TrustIncidentResponse:
        incident = TrustIncident(
            incident_id=new_trust_incident_id(),
            source_audit_id=req.source_audit_id,
            surface=req.surface,
            topic=req.topic,
            severity=req.severity,
            status="open",
            summary=req.summary,
            owner_id=req.owner_id,
            notes=req.notes,
            created_by=actor_id,
        )
        saved = self.repo.save_incident(incident)
        return _to_incident_response(saved)


class UpdateTrustIncident:
    def __init__(self, repo: SqliteTrustSafetyRepository) -> None:
        self.repo = repo

    def execute(self, *, incident_id: str, actor_id: str, req: TrustIncidentActionRequest) -> TrustIncidentResponse:
        incident = self.repo.get_incident(incident_id=incident_id)
        if incident is None:
            raise ValueError("Khong tim thay trust incident.")
        status_map = {
            "investigate": "investigating",
            "mitigate": "mitigated",
            "resolve": "resolved",
            "reopen": "open",
            "reassign": incident.status,
        }
        next_status = status_map[req.action]
        updated = replace(
            incident,
            status=next_status,
            owner_id=req.owner_id if req.owner_id is not None else incident.owner_id,
            notes=req.notes if req.notes is not None else incident.notes,
            updated_at=utc_now_iso(),
            resolved_at=utc_now_iso() if req.action == "resolve" else (None if req.action == "reopen" else incident.resolved_at),
        )
        saved = self.repo.save_incident(updated)
        control = self.repo.get_surface_control(surface=saved.surface)
        self.repo.save_audit_log(
            TrustAuditLog(
                audit_id=new_trust_audit_id(),
                actor_id=actor_id,
                surface=saved.surface,
                topic=saved.topic,
                channel="incident_workflow",
                risk_classes=(),
                severity=saved.severity,
                route_decision=f"incident_{req.action}",
                input_summary=saved.summary,
                output_summary=saved.notes,
                escalation_action=f"surface_{control.state}" if control is not None else req.action,
            )
        )
        return _to_incident_response(saved)


class ListTrustIncidents:
    def __init__(self, repo: SqliteTrustSafetyRepository) -> None:
        self.repo = repo

    def execute(
        self,
        *,
        status: str | None = None,
        surface: str | None = None,
        severity: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[TrustIncidentResponse]:
        return [
            _to_incident_response(item)
            for item in self.repo.list_incidents(
                status=status,
                surface=surface,
                severity=severity,
                search=search,
                limit=limit,
            )
        ]


def _to_incident_response(item: TrustIncident) -> TrustIncidentResponse:
    return TrustIncidentResponse(
        incident_id=item.incident_id,
        source_audit_id=item.source_audit_id,
        surface=item.surface,
        topic=item.topic,
        severity=item.severity,
        status=item.status,
        summary=item.summary,
        owner_id=item.owner_id,
        notes=item.notes,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        resolved_at=item.resolved_at,
    )
