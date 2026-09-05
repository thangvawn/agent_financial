from __future__ import annotations

import uuid

from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceItem,
    Hypothesis,
    InvestigationRequest,
    OpsActionRecommendation,
    VerifiedFinding,
)


def synthesize_findings_and_hypotheses(
    request: InvestigationRequest,
    items: list[EvidenceItem],
) -> tuple[
    tuple[VerifiedFinding, ...],
    tuple[Hypothesis, ...],
    tuple[OpsActionRecommendation, ...],
    tuple[str, ...],
]:
    findings: list[VerifiedFinding] = []
    hypotheses: list[Hypothesis] = []
    recommendations: list[OpsActionRecommendation] = []
    surfaces = set()

    for item in items:
        ref = item.ref
        surfaces.add(ref.source_module)
        statement = f"Observed {ref.resource_type} '{ref.resource_id}' from {ref.source_module}"
        findings.append(VerifiedFinding(statement=statement, evidence_refs=(ref,)))

        if len(recommendations) < 3:
            recommendations.append(
                OpsActionRecommendation(
                    recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                    action_kind="manual_check",
                    target_ref=ref,
                    rationale=f"Review state of {ref.resource_type} {ref.resource_id}",
                    payload_preview={"resource_id": ref.resource_id},
                )
            )

    if findings:
        hypotheses.append(
            Hypothesis(
                statement=f"Investigation {request.investigation_type} reflects active operational records in {', '.join(surfaces)}",
                confidence=0.8,
                supporting_refs=tuple(item.ref for item in items[:3]),
                falsification_checks=("Verify cross-service telemetry and source health",),
            )
        )

    return tuple(findings), tuple(hypotheses), tuple(recommendations), tuple(surfaces)


def build_blocked_report(
    rep_id: str,
    inv_id: str,
    req: InvestigationRequest,
    reason: str,
    exp: str,
    now_iso: str,
) -> OpsInvestigationReport:
    from risk_dashboard.modules.internal_ops.domain.contracts import OpsInvestigationReport
    return OpsInvestigationReport(
        report_id=rep_id,
        investigation_id=inv_id,
        status="policy_blocked",
        purpose=req.purpose,
        severity="low",
        time_from=req.time_from,
        time_to=req.time_to,
        verified_findings=(),
        hypotheses=(),
        recommendations=(),
        impacted_surfaces=(),
        limitations=(reason,),
        access_expires_at=exp,
        created_at=now_iso,
    )


