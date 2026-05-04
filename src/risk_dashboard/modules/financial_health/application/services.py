from __future__ import annotations

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_product_event
from risk_dashboard.modules.financial_health.domain.entities import FinancialHealthInput
from risk_dashboard.modules.financial_health.domain.policies import build_coach_reply, build_snapshot
from risk_dashboard.modules.financial_health.domain.ports import (
    FinancialHealthInputRepository,
    FinancialHealthSnapshotRepository,
)
from risk_dashboard.modules.financial_health.schemas.requests import FinancialHealthAssessmentRequest
from risk_dashboard.modules.financial_health.schemas.responses import (
    FinancialHealthCoachResponse,
    FinancialHealthResponse,
)


class SubmitFinancialHealthAssessment:
    def __init__(
        self,
        inputs: FinancialHealthInputRepository,
        snapshots: FinancialHealthSnapshotRepository,
    ) -> None:
        self.inputs = inputs
        self.snapshots = snapshots

    def execute(self, req: FinancialHealthAssessmentRequest) -> FinancialHealthResponse:
        payload = FinancialHealthInput(**req.model_dump())
        self.inputs.save(payload)
        snapshot = build_snapshot(payload)
        self.snapshots.save(snapshot)
        emit_product_event(
            event_name="financial_health_input_completed",
            module="financial_health",
            surface="financial_health",
            session_id=req.session_id,
            properties={
                "score_band": snapshot.score_band,
                "health_score": snapshot.health_score,
                "investment_readiness": snapshot.guided_investing_eligible,
            },
        )
        emit_product_event(
            event_name="financial_health_score_viewed",
            module="financial_health",
            surface="financial_health",
            session_id=req.session_id,
            properties={"score_band": snapshot.score_band, "health_score": snapshot.health_score},
        )
        return FinancialHealthResponse.model_validate(_snapshot_to_dict(snapshot))


class GetFinancialHealthSnapshot:
    def __init__(self, snapshots: FinancialHealthSnapshotRepository) -> None:
        self.snapshots = snapshots

    def execute(self, *, session_id: str) -> FinancialHealthResponse:
        snapshot = self.snapshots.get(session_id)
        if snapshot is None:
            raise ValueError("Financial health snapshot not found.")
        emit_product_event(
            event_name="financial_health_score_viewed",
            module="financial_health",
            surface="financial_health",
            session_id=session_id,
            properties={"score_band": snapshot.score_band, "health_score": snapshot.health_score},
        )
        return FinancialHealthResponse.model_validate(_snapshot_to_dict(snapshot))


class ExplainFinancialHealth:
    def __init__(self, snapshots: FinancialHealthSnapshotRepository) -> None:
        self.snapshots = snapshots

    def execute(self, *, session_id: str, focus: str | None) -> FinancialHealthCoachResponse:
        snapshot = self.snapshots.get(session_id)
        if snapshot is None:
            raise ValueError("Financial health snapshot not found.")
        reply = build_coach_reply(snapshot, focus=focus)
        emit_product_event(
            event_name="financial_health_coach_opened",
            module="financial_health",
            surface="financial_health",
            session_id=session_id,
            properties={"focus": focus or "general"},
        )
        return FinancialHealthCoachResponse(
            session_id=session_id,
            summary=reply.summary,
            explanation=reply.explanation,
            next_small_actions=reply.next_small_actions,
            confidence_note=reply.confidence_note,
        )


def _snapshot_to_dict(snapshot) -> dict:
    return {
        "session_id": snapshot.session_id,
        "health_score": snapshot.health_score,
        "score_band": snapshot.score_band,
        "guided_investing_eligible": snapshot.guided_investing_eligible,
        "subscores": [
            {
                "key": item.key,
                "label": item.label,
                "score": item.score,
                "reason": item.reason,
                "improvement_hint": item.improvement_hint,
            }
            for item in snapshot.subscores
        ],
        "flags": [
            {
                "code": item.code,
                "severity": item.severity,
                "title": item.title,
                "description": item.description,
            }
            for item in snapshot.flags
        ],
        "actions": [
            {
                "code": item.code,
                "priority": item.priority,
                "title": item.title,
                "description": item.description,
                "related_lesson_id": item.related_lesson_id,
                "cta_path": item.cta_path,
            }
            for item in snapshot.actions
        ],
        "educational_links": snapshot.educational_links,
        "transparency_note": snapshot.transparency_note,
        "compliance_note": snapshot.compliance_note,
        "computed_at": snapshot.computed_at,
    }
