"""Tests for legacy gate domain entities and schemas."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.legacy_gate.domain.entities import (
    GateCheckItem,
    LegacyModuleBaselineReport,
    ModuleGateStatus,
    ReactivationDecisionRecord,
)
from risk_dashboard.modules.legacy_gate.schemas.gates import (
    BaselineReportResponse,
    DecisionRecordResponse,
    GateCheckItemResponse,
    ModuleGateListResponse,
    ModuleGateStatusResponse,
    ReactivationDecisionRequest,
)


class TestLegacyGateSchemas:
    def test_gate_check_item_valid(self) -> None:
        item = GateCheckItem(
            gate_id="goals-1", category="product", description="Owner defined", status="pending"
        )
        assert item.gate_id == "goals-1"
        assert item.category == "product"
        assert item.status == "pending"
        assert item.evidence_ref is None

    def test_gate_check_item_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            GateCheckItem(
                gate_id="goals-1", category="product", description="d", unknown="x"
            )

    def test_gate_category_invalid_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GateCheckItem(
                gate_id="goals-1", category="invalid_cat", description="d"  # type: ignore
            )

    def test_gate_item_status_invalid_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GateCheckItem(
                gate_id="goals-1", category="product", description="d", status="bad"  # type: ignore
            )

    def test_reactivation_decision_record_defaults(self) -> None:
        record = ReactivationDecisionRecord(
            record_id="rec-001",
            module_slug="goals",
            outcome="Provide goal tracking learning journey",
            owner_product="alice",
            owner_engineering="bob",
            owner_domain="carol",
            owner_compliance="dave",
            source_of_truth="goals_service",
            risk_class="low_financial",
            allowed_actions=("read", "proposal"),
            dependencies=("auth", "learning"),
            eval_criteria="100% test pass and zero hallucination",
            rollout="cohort beta via feature flag",
            adr_reference="ADR-042",
        )
        assert record.schema_version == "1.0.0"
        assert record.status == "draft"
        assert record.created_at
        assert record.updated_at

    def test_reactivation_decision_record_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            ReactivationDecisionRecord(
                record_id="rec-001",
                module_slug="goals",
                outcome="outcome",
                owner_product="alice",
                owner_engineering="bob",
                owner_domain="carol",
                owner_compliance="dave",
                source_of_truth="sot",
                risk_class="risk",
                allowed_actions=("read",),
                dependencies=(),
                eval_criteria="eval",
                rollout="rollout",
                adr_reference="ADR-001",
                extra_payload="rejected",
            )

    def test_reactivation_decision_request_schema(self) -> None:
        req = ReactivationDecisionRequest(
            outcome="Goal-based learning path",
            owner_product="alice",
            owner_engineering="bob",
            owner_domain="carol",
            owner_compliance="dave",
            source_of_truth="goals domain service",
            risk_class="financial_planning",
            allowed_actions=["read", "proposal"],
            dependencies=["auth"],
            eval_criteria="Safety eval passes 100%",
            rollout="Feature flag module.goals.enabled",
            adr_reference="ADR-045",
            status="draft",
        )
        assert req.status == "draft"
        assert req.allowed_actions == ["read", "proposal"]

    def test_reactivation_decision_request_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            ReactivationDecisionRequest(
                outcome="Goal-based learning path",
                owner_product="alice",
                owner_engineering="bob",
                owner_domain="carol",
                owner_compliance="dave",
                source_of_truth="goals domain service",
                risk_class="financial_planning",
                allowed_actions=["read"],
                dependencies=[],
                eval_criteria="criteria",
                rollout="rollout",
                adr_reference="ADR-045",
                hacker_param="injected",
            )

    def test_baseline_report_schema_version_and_identity_debt(self) -> None:
        report = LegacyModuleBaselineReport(
            module_slug="goals",
            entities_defined=("Goal", "GoalSnapshot"),
            policies_defined=("create_goal", "apply_checkin"),
            services_defined=("CreateGoal", "ListGoals"),
            schemas_defined=("GoalCreateRequest", "GoalResponse"),
            routes_defined=("POST /goals", "GET /goals"),
            tests_count=10,
            test_files=("tests/modules/goals/test_baseline.py",),
            archived_reason="Archived from product surface (Phase 4)",
            archived_phase="Phase 4",
            identity_debt_notes=(
                "goals/api/public.py accepts client-supplied session_id as user identifier",
            ),
        )
        assert report.schema_version == "1.0.0"
        assert len(report.identity_debt_notes) == 1
        assert "session_id" in report.identity_debt_notes[0]

    def test_baseline_report_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            LegacyModuleBaselineReport(
                module_slug="goals", entities_defined=(), policies_defined=(),
                services_defined=(), schemas_defined=(), routes_defined=(),
                tests_count=0, test_files=(), archived_reason="r",
                archived_phase="p", identity_debt_notes=(), unknown="blocked",
            )

    def test_module_gate_status_serialization(self) -> None:
        status = ModuleGateStatus(
            module_slug="goals",
            overall_status="gates_documented",
            gates=(
                GateCheckItem(
                    gate_id="goals-1",
                    category="product",
                    description="Owner defined",
                    status="pending",
                ),
            ),
            total_gates=1,
            passed_gates=0,
            failed_gates=0,
            pending_gates=1,
        )
        data = status.model_dump()
        restored = ModuleGateStatus.model_validate(data)
        assert restored.module_slug == "goals"
        assert restored.total_gates == 1
        assert restored.pending_gates == 1

    def test_module_gate_list_response(self) -> None:
        status_resp = ModuleGateStatusResponse(
            module_slug="goals",
            overall_status="hold",
            gates=[],
            total_gates=0,
            passed_gates=0,
            failed_gates=0,
            pending_gates=0,
            updated_at="2026-09-05T10:00:00Z",
        )
        list_resp = ModuleGateListResponse(modules=[status_resp], total=1)
        assert list_resp.total == 1
        assert list_resp.modules[0].module_slug == "goals"
