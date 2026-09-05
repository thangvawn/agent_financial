"""Domain entities for Module 12 Legacy Reactivation Gates Framework."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


GateCategory = Literal["product", "data", "security", "regulatory", "maintenance"]
GateItemStatus = Literal["pending", "passed", "failed", "waived"]
GateOverallStatus = Literal[
    "hold",
    "baseline_captured",
    "gates_documented",
    "decision_recorded",
    "approved",
    "reactivated",
]


class GateCheckItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gate_id: str
    category: GateCategory
    description: str
    status: GateItemStatus = "pending"
    evidence_ref: str | None = None
    approver: str | None = None
    notes: str | None = None


class ReactivationDecisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str
    module_slug: str
    schema_version: Literal["1.0.0"] = "1.0.0"
    outcome: str
    owner_product: str
    owner_engineering: str
    owner_domain: str
    owner_compliance: str
    source_of_truth: str
    risk_class: str
    allowed_actions: tuple[str, ...]
    dependencies: tuple[str, ...]
    eval_criteria: str
    rollout: str
    adr_reference: str
    status: Literal["draft", "approved", "rejected"] = "draft"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class LegacyModuleBaselineReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_slug: str
    schema_version: Literal["1.0.0"] = "1.0.0"
    entities_defined: tuple[str, ...]
    policies_defined: tuple[str, ...]
    services_defined: tuple[str, ...]
    schemas_defined: tuple[str, ...]
    routes_defined: tuple[str, ...]
    tests_count: int
    test_files: tuple[str, ...]
    archived_reason: str
    archived_phase: str
    captured_at: str = Field(default_factory=utc_now_iso)
    identity_debt_notes: tuple[str, ...]


class ModuleGateStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module_slug: str
    overall_status: GateOverallStatus
    gates: tuple[GateCheckItem, ...]
    baseline: LegacyModuleBaselineReport | None = None
    decision_record: ReactivationDecisionRecord | None = None
    total_gates: int
    passed_gates: int
    failed_gates: int
    pending_gates: int
    updated_at: str = Field(default_factory=utc_now_iso)

