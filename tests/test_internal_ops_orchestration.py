from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.internal_ops.application.investigation_service import InvestigationService
from risk_dashboard.modules.internal_ops.application.policy import PolicyEngine
from risk_dashboard.modules.internal_ops.application.verifier import Verifier
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceItem,
    EvidenceRef,
    InvestigationRequest,
    OpsActionRecommendation,
    OpsInvestigationReport,
    VerifiedFinding,
)


def _make_principal(scopes: tuple[str, ...]) -> AuthPrincipal:
    return AuthPrincipal(
        account_id="ops-analyst-1",
        session_id="sess-1",
        scopes=scopes,
        resolved_at="2026-09-05T10:00:00Z",
    )


def _sample_item(module: str = "analytics_monitoring", rtype: str = "kpi", rid: str = "lat-1") -> EvidenceItem:
    ref = EvidenceRef(
        source_module=module,  # type: ignore
        resource_type=rtype,
        resource_id=rid,
        observed_at="2026-09-05T10:00:00Z",
    )
    return EvidenceItem(
        ref=ref,
        classification="aggregate",
        fields={"val": 100},
    )


def test_verifier_citation_filtering():
    item1 = _sample_item("analytics_monitoring", "kpi", "cpu")
    item2 = _sample_item("analytics_monitoring", "kpi", "mem")

    valid_f = VerifiedFinding(
        statement="CPU usage high",
        evidence_refs=(item1.ref,),
    )
    invalid_f = VerifiedFinding(
        statement="Disk full",
        evidence_refs=(EvidenceRef(
            source_module="analytics_monitoring",
            resource_type="kpi",
            resource_id="disk",
            observed_at="2026-09-05T10:00:00Z",
        ),),
    )

    verified, dropped = Verifier.verify_citations(
        (valid_f, invalid_f),
        (item1, item2),
    )
    assert len(verified) == 1
    assert verified[0].statement == "CPU usage high"
    assert len(dropped) == 1


def test_verifier_forbidden_intent():
    item = _sample_item()
    finding = VerifiedFinding(statement="Safe observation", evidence_refs=(item.ref,))
    rec = OpsActionRecommendation(
        recommendation_id="r1",
        action_kind="manual_check",
        target_ref=item.ref,
        rationale="Safe manual check",
        payload_preview={},
    )
    safe_rep = OpsInvestigationReport(
        report_id="rep-1",
        investigation_id="inv-1",
        status="draft",
        purpose="Safe purpose check",
        severity="info",
        time_from="2026-09-05T00:00:00Z",
        time_to="2026-09-05T10:00:00Z",
        verified_findings=(finding,),
        hypotheses=(),
        recommendations=(rec,),
        impacted_surfaces=(),
        limitations=(),
        access_expires_at="2026-09-06T00:00:00Z",
        created_at="2026-09-05T10:00:00Z",
    )
    assert Verifier.check_forbidden_intent(safe_rep) == "pass"

    # Forbidden recommendation: auto-publish content
    forbidden_rec = OpsActionRecommendation(
        recommendation_id="r2",
        action_kind="content_draft_fix",
        target_ref=item.ref,
        rationale="auto-publish content to CMS right now",
        payload_preview={},
    )
    unsafe_rep = safe_rep.model_copy(update={"recommendations": (forbidden_rec,)})
    assert Verifier.check_forbidden_intent(unsafe_rep) == "policy_blocked"


def test_investigation_service_full_flow():
    mock_analytics = MagicMock()
    mock_analytics.get_source_health.return_value = EvidenceBatch(
        items=(_sample_item("analytics_monitoring", "metric", "freshness"),),
        source_module="analytics_monitoring",
        fetched_at="2026-09-05T10:00:00Z",
        status="available",
    )
    mock_analytics.get_alert_context.return_value = EvidenceBatch(
        items=(),
        source_module="analytics_monitoring",
        fetched_at="2026-09-05T10:00:00Z",
        status="available",
    )
    adapters = {"analytics": mock_analytics}

    service = InvestigationService(adapters=adapters)
    principal = _make_principal(("admin:internal_ops:support_viewer",))
    req = InvestigationRequest(
        investigation_type="data_freshness",
        purpose="Investigate data freshness degradation",
        time_from="2026-09-05T00:00:00Z",
        time_to="2026-09-05T10:00:00Z",
    )

    report = service.run_investigation(principal, req)
    assert report.status == "draft"
    assert len(report.verified_findings) >= 1
    assert all(len(f.evidence_refs) >= 1 for f in report.verified_findings)
    assert all(r.executable is False for r in report.recommendations)


def test_investigation_service_policy_blocked():
    service = InvestigationService(adapters={})
    unauth_principal = _make_principal(())
    req = InvestigationRequest(
        investigation_type="incident",
        purpose="Investigate without any scope",
        time_from="2026-09-05T00:00:00Z",
        time_to="2026-09-05T10:00:00Z",
    )
    report = service.run_investigation(unauth_principal, req)
    assert report.status == "policy_blocked"
    assert len(report.verified_findings) == 0


def test_investigation_service_missing_source_incomplete():
    service = InvestigationService(adapters={})
    principal = _make_principal(("admin:internal_ops:reliability_operator",))
    req = InvestigationRequest(
        investigation_type="run_failure",
        purpose="Investigate run failure without agentic core",
        time_from="2026-09-05T00:00:00Z",
        time_to="2026-09-05T10:00:00Z",
    )
    report = service.run_investigation(principal, req)
    assert report.status == "incomplete"
    assert any("Agentic core" in lim for lim in report.limitations)

