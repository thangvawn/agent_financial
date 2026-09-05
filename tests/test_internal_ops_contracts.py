from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceItem,
    EvidenceRef,
    FORBIDDEN_TOOL_NAMES,
    ForbiddenTool,
    Hypothesis,
    InvestigationRequest,
    OpsActionRecommendation,
    OpsInvestigationReport,
    VerifiedFinding,
)
from risk_dashboard.modules.internal_ops.schemas.api import (
    EvidenceListApiResponse,
    InvestigationApiResponse,
    RecommendationsApiResponse,
)


def _sample_evidence_ref() -> EvidenceRef:
    return EvidenceRef(
        source_module="analytics_monitoring",
        resource_type="kpi_snapshot",
        resource_id="kpi-001",
        correlation_id="corr-123",
        observed_at="2026-09-05T10:00:00Z",
    )


def _sample_evidence_item() -> EvidenceItem:
    return EvidenceItem(
        ref=_sample_evidence_ref(),
        classification="metadata",
        fields={"kpi_name": "api_latency", "value": 120},
        redactions=("token",),
    )


def _sample_recommendation() -> OpsActionRecommendation:
    return OpsActionRecommendation(
        recommendation_id="rec-001",
        action_kind="manual_check",
        target_ref=_sample_evidence_ref(),
        rationale="Check API health endpoint",
        payload_preview={"check": "ping"},
    )


def test_roundtrip_evidence_ref():
    ref = _sample_evidence_ref()
    data = ref.model_dump()
    reconstructed = EvidenceRef.model_validate(data)
    assert reconstructed == ref
    assert reconstructed.schema_version == "1.0.0"


def test_roundtrip_evidence_item_and_batch():
    item = _sample_evidence_item()
    batch = EvidenceBatch(
        items=(item,),
        source_module="analytics_monitoring",
        fetched_at="2026-09-05T10:01:00Z",
        status="available",
    )
    b_data = batch.model_dump()
    reconstructed = EvidenceBatch.model_validate(b_data)
    assert reconstructed == batch


def test_roundtrip_investigation_request():
    req = InvestigationRequest(
        investigation_type="incident",
        purpose="Triage API latency spike in analytics",
        resource_refs=(_sample_evidence_ref(),),
        time_from="2026-09-05T00:00:00Z",
        time_to="2026-09-05T10:00:00Z",
        max_evidence_items=50,
    )
    data = req.model_dump()
    assert InvestigationRequest.model_validate(data) == req


def test_roundtrip_report_and_findings():
    ref = _sample_evidence_ref()
    finding = VerifiedFinding(
        statement="Latency exceeded 500ms threshold",
        evidence_refs=(ref,),
    )
    hypothesis = Hypothesis(
        statement="Database connection pool starvation",
        confidence=0.85,
        supporting_refs=(ref,),
        falsification_checks=("Check connection pool metrics",),
    )
    rec = _sample_recommendation()
    report = OpsInvestigationReport(
        report_id="rep-001",
        investigation_id="inv-001",
        status="draft",
        purpose="Investigate latency spike",
        severity="high",
        time_from="2026-09-05T00:00:00Z",
        time_to="2026-09-05T10:00:00Z",
        verified_findings=(finding,),
        hypotheses=(hypothesis,),
        recommendations=(rec,),
        impacted_surfaces=("analytics",),
        limitations=("Historical log unavailable prior to 00:00",),
        owner_hint="infra-team",
        access_expires_at="2026-09-06T00:00:00Z",
        created_at="2026-09-05T10:05:00Z",
    )
    data = report.model_dump()
    assert OpsInvestigationReport.model_validate(data) == report


def test_unknown_schema_version_major_rejected():
    with pytest.raises(ValidationError) as excinfo:
        EvidenceRef(
            schema_version="2.0.0",
            source_module="analytics_monitoring",
            resource_type="kpi",
            resource_id="kpi-1",
            observed_at="2026-09-05T10:00:00Z",
        )
    assert "Unsupported schema version major" in str(excinfo.value)


def test_invalid_source_module_rejected():
    with pytest.raises(ValidationError):
        EvidenceRef(
            source_module="unauthorized_module",  # type: ignore
            resource_type="kpi",
            resource_id="kpi-1",
            observed_at="2026-09-05T10:00:00Z",
        )


def test_finding_requires_at_least_one_evidence_ref():
    with pytest.raises(ValidationError):
        VerifiedFinding(
            statement="Uncited assertion",
            evidence_refs=(),
        )


def test_recommendation_executable_cannot_be_true():
    with pytest.raises(ValidationError):
        OpsActionRecommendation(
            recommendation_id="rec-1",
            action_kind="runbook_step",
            target_ref=_sample_evidence_ref(),
            rationale="Execute action",
            payload_preview={},
            executable=True,  # type: ignore
        )


def test_purpose_length_validation():
    with pytest.raises(ValidationError):
        InvestigationRequest(
            investigation_type="incident",
            purpose="short",  # < 8 chars
            time_from="2026-09-05T00:00:00Z",
            time_to="2026-09-05T10:00:00Z",
        )


def test_forbidden_tools_sentinel():
    assert "ops.publish_content" in FORBIDDEN_TOOL_NAMES
    assert "ops.change_incident_state" in FORBIDDEN_TOOL_NAMES
    assert "ops.change_prompt_model_flag_config" in FORBIDDEN_TOOL_NAMES
    assert "ops.run_analytics_job" in FORBIDDEN_TOOL_NAMES
    fb = ForbiddenTool(tool_id="ops.publish_content", reason="No auto publish")
    assert fb.tool_id == "ops.publish_content"


def test_api_schemas_wrapping():
    rec = _sample_recommendation()
    res = RecommendationsApiResponse(
        investigation_id="inv-123",
        items=[rec],
    )
    assert res.items[0].executable is False

