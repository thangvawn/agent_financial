from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION_V1 = "1.0.0"


def _validate_schema_major_1(v: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError("schema_version must be a non-empty string")
    major = v.split(".")[0]
    if major != "1":
        raise ValueError(f"Unsupported schema version major: {major}. Expected major version 1.")
    return v


class OpsBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("schema_version", check_fields=False)
    @classmethod
    def check_schema_version(cls, v: str) -> str:
        return _validate_schema_major_1(v)


class EvidenceRef(OpsBaseModel):
    schema_version: str = SCHEMA_VERSION_V1
    source_module: Literal["analytics_monitoring", "trust_safety", "admin_cms", "agentic_core"]
    resource_type: str
    resource_id: str
    correlation_id: str | None = None
    observed_at: str


class EvidenceItem(OpsBaseModel):
    schema_version: str = SCHEMA_VERSION_V1
    ref: EvidenceRef
    classification: Literal["aggregate", "metadata", "restricted_redacted"]
    fields: dict[str, Any]
    redactions: tuple[str, ...] = ()


class EvidenceBatch(OpsBaseModel):
    schema_version: str = SCHEMA_VERSION_V1
    items: tuple[EvidenceItem, ...] = ()
    source_module: str
    fetched_at: str
    status: Literal["available", "source_unavailable", "partial"] = "available"


class InvestigationRequest(OpsBaseModel):
    schema_version: str = SCHEMA_VERSION_V1
    investigation_type: Literal[
        "incident", "eval_regression", "content_qa", "data_freshness", "run_failure"
    ]
    purpose: str = Field(min_length=8, max_length=240)
    resource_refs: tuple[EvidenceRef, ...] = ()
    time_from: str
    time_to: str
    max_evidence_items: int = Field(default=100, ge=1, le=500)


class VerifiedFinding(OpsBaseModel):
    schema_version: str = SCHEMA_VERSION_V1
    statement: str
    evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)


class Hypothesis(OpsBaseModel):
    schema_version: str = SCHEMA_VERSION_V1
    statement: str
    confidence: float = Field(ge=0, le=1)
    supporting_refs: tuple[EvidenceRef, ...] = ()
    falsification_checks: tuple[str, ...] = ()


class OpsActionRecommendation(OpsBaseModel):
    schema_version: str = SCHEMA_VERSION_V1
    recommendation_id: str
    action_kind: Literal["content_draft_fix", "runbook_step", "owner_escalation", "manual_check"]
    risk_class: Literal["proposal"] = "proposal"
    target_ref: EvidenceRef
    rationale: str
    payload_preview: dict[str, Any]
    status: Literal["draft"] = "draft"
    executable: Literal[False] = False


class OpsInvestigationReport(OpsBaseModel):
    schema_version: str = SCHEMA_VERSION_V1
    report_id: str
    investigation_id: str
    status: Literal["draft", "incomplete", "policy_blocked", "failed"]
    purpose: str
    severity: Literal["info", "low", "medium", "high", "critical"]
    time_from: str
    time_to: str
    verified_findings: tuple[VerifiedFinding, ...]
    hypotheses: tuple[Hypothesis, ...]
    recommendations: tuple[OpsActionRecommendation, ...]
    impacted_surfaces: tuple[str, ...]
    limitations: tuple[str, ...]
    owner_hint: str | None = None
    access_expires_at: str
    created_at: str


class ForbiddenTool(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_id: str
    reason: str


FORBIDDEN_TOOL_NAMES: tuple[str, ...] = (
    "ops.publish_content",
    "ops.change_incident_state",
    "ops.change_prompt_model_flag_config",
    "ops.run_analytics_job",
)

