"""Request and response schemas for legacy gate."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReactivationDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: str = Field(..., min_length=5, max_length=2000)
    owner_product: str = Field(..., min_length=2, max_length=100)
    owner_engineering: str = Field(..., min_length=2, max_length=100)
    owner_domain: str = Field(..., min_length=2, max_length=100)
    owner_compliance: str = Field(..., min_length=2, max_length=100)
    source_of_truth: str = Field(..., min_length=2, max_length=500)
    risk_class: str = Field(..., min_length=2, max_length=200)
    allowed_actions: list[str] = Field(..., min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    eval_criteria: str = Field(..., min_length=5, max_length=2000)
    rollout: str = Field(..., min_length=5, max_length=1000)
    adr_reference: str = Field(..., min_length=3, max_length=200)
    status: Literal["draft", "approved", "rejected"] = "draft"


class GateCheckItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gate_id: str
    category: str
    description: str
    status: str
    evidence_ref: str | None = None
    approver: str | None = None
    notes: str | None = None


class BaselineReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_slug: str
    schema_version: str = "1.0.0"
    entities_defined: list[str]
    policies_defined: list[str]
    services_defined: list[str]
    schemas_defined: list[str]
    routes_defined: list[str]
    tests_count: int
    test_files: list[str]
    archived_reason: str
    archived_phase: str
    captured_at: str
    identity_debt_notes: list[str]


class DecisionRecordResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str
    module_slug: str
    schema_version: str = "1.0.0"
    outcome: str
    owner_product: str
    owner_engineering: str
    owner_domain: str
    owner_compliance: str
    source_of_truth: str
    risk_class: str
    allowed_actions: list[str]
    dependencies: list[str]
    eval_criteria: str
    rollout: str
    adr_reference: str
    status: str
    created_at: str
    updated_at: str


class ModuleGateStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_slug: str
    overall_status: str
    gates: list[GateCheckItemResponse]
    baseline: BaselineReportResponse | None = None
    decision_record: DecisionRecordResponse | None = None
    total_gates: int
    passed_gates: int
    failed_gates: int
    pending_gates: int
    updated_at: str


class ModuleGateListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modules: list[ModuleGateStatusResponse]
    total: int

