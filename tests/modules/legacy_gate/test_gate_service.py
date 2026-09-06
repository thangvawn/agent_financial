"""Tests for LegacyGateService business logic and gate evaluations."""
from __future__ import annotations

import pytest

from risk_dashboard.modules.legacy_gate.application.service import LegacyGateService
from risk_dashboard.modules.legacy_gate.domain.entities import GateCheckItem
from risk_dashboard.modules.legacy_gate.domain.errors import LegacyGateError
from risk_dashboard.modules.legacy_gate.infrastructure.in_memory import InMemoryGateRepository
from risk_dashboard.modules.legacy_gate.schemas.gates import ReactivationDecisionRequest


@pytest.fixture
def repo():
    return InMemoryGateRepository()


@pytest.fixture
def service(repo):
    return LegacyGateService(repository=repo)


class TestLegacyGateService:
    def test_list_modules_returns_four_legacy_modules(self, service: LegacyGateService) -> None:
        statuses = service.list_modules()
        assert len(statuses) == 4
        slugs = [s.module_slug for s in statuses]
        assert slugs == ["goals", "financial_health", "community", "guided_investing"]

    def test_initialize_module_idempotent(self, service: LegacyGateService) -> None:
        status1 = service.initialize_module("goals")
        status2 = service.initialize_module("goals")
        assert status1.module_slug == status2.module_slug
        assert status1.total_gates == status2.total_gates == 14
        assert len(status1.gates) == len(status2.gates) == 14

    def test_initialize_module_not_found(self, service: LegacyGateService) -> None:
        with pytest.raises(LegacyGateError) as exc_info:
            service.initialize_module("non_existent_module")
        assert exc_info.value.error_type == "module_not_found"

    def test_baseline_captured_with_identity_debt_notes(self, service: LegacyGateService) -> None:
        report = service.get_baseline_report("goals")
        assert report.module_slug == "goals"
        assert report.schema_version == "1.0.0"
        assert report.tests_count > 0
        assert len(report.test_files) >= 1
        assert len(report.identity_debt_notes) >= 1
        assert any("session_id" in note for note in report.identity_debt_notes)

    def test_gate_counts_goals_14(self, service: LegacyGateService) -> None:
        status = service.get_module_status("goals")
        assert status.total_gates == 14
        assert len(status.gates) == 14
        common = [g for g in status.gates if g.gate_id.startswith("goals-") and int(g.gate_id.split("-")[1]) <= 8]
        specific = [g for g in status.gates if g.gate_id.startswith("goals-") and int(g.gate_id.split("-")[1]) > 8]
        assert len(common) == 8
        assert len(specific) == 6

    def test_gate_counts_financial_health_12(self, service: LegacyGateService) -> None:
        status = service.get_module_status("financial_health")
        assert status.total_gates == 12
        assert len(status.gates) == 12

    def test_gate_counts_community_12(self, service: LegacyGateService) -> None:
        status = service.get_module_status("community")
        assert status.total_gates == 12
        assert len(status.gates) == 12

    def test_gate_counts_guided_investing_12(self, service: LegacyGateService) -> None:
        status = service.get_module_status("guided_investing")
        assert status.total_gates == 12
        assert len(status.gates) == 12

    def test_guided_investing_includes_regulatory_and_paper_gates(self, service: LegacyGateService) -> None:
        status = service.get_module_status("guided_investing")
        gate_ids = {g.gate_id: g for g in status.gates}
        assert "gi-9" in gate_ids
        assert gate_ids["gi-9"].category == "regulatory"
        assert "Securities Law" in gate_ids["gi-9"].description or "advisory" in gate_ids["gi-9"].description

        assert "gi-10" in gate_ids
        assert "paper portfolio" in gate_ids["gi-10"].description

        assert "gi-11" in gate_ids
        assert "No broker connection" in gate_ids["gi-11"].description

    def test_record_decision_stores_record_and_updates_status(self, service: LegacyGateService) -> None:
        req = ReactivationDecisionRequest(
            outcome="Provide education-only goal tracking journey",
            owner_product="alice",
            owner_engineering="bob",
            owner_domain="carol",
            owner_compliance="dave",
            source_of_truth="goals domain service",
            risk_class="financial_education",
            allowed_actions=["read", "proposal"],
            dependencies=["auth", "learning"],
            eval_criteria="Pass 100% baseline regression and zero unauthorized advice",
            rollout="Cohort beta via feature flag",
            adr_reference="ADR-012-GOALS",
            status="draft",
        )
        record = service.record_decision("goals", req)
        assert record.record_id.startswith("rec-")
        assert record.module_slug == "goals"
        assert record.status == "draft"

        status = service.get_module_status("goals")
        assert status.decision_record is not None
        assert status.decision_record.record_id == record.record_id
        assert status.overall_status == "decision_recorded"

    def test_record_decision_invalid_slug_raises_error(self, service: LegacyGateService) -> None:
        req = ReactivationDecisionRequest(
            outcome="Test outcome",
            owner_product="alice",
            owner_engineering="bob",
            owner_domain="carol",
            owner_compliance="dave",
            source_of_truth="sot",
            risk_class="risk",
            allowed_actions=["read"],
            dependencies=[],
            eval_criteria="eval criteria",
            rollout="rollout",
            adr_reference="ADR-001",
            status="draft",
        )
        with pytest.raises(LegacyGateError) as exc_info:
            service.record_decision("unknown_module", req)
        assert exc_info.value.error_type == "module_not_found"

    def test_evaluate_module_refreshes_baseline(self, service: LegacyGateService) -> None:
        status = service.evaluate_module("financial_health")
        assert status.module_slug == "financial_health"
        assert status.baseline is not None
        assert status.baseline.tests_count > 0

    def test_overall_status_derivation_chain(self, service: LegacyGateService, repo: InMemoryGateRepository) -> None:
        # 1. Fresh initialized status -> "gates_documented" (has gates and baseline tests)
        status = service.initialize_module("goals")
        assert status.overall_status == "gates_documented"

        # 2. Add decision record -> "decision_recorded"
        decision_req = ReactivationDecisionRequest(
            outcome="Goal journey",
            owner_product="alice",
            owner_engineering="bob",
            owner_domain="carol",
            owner_compliance="dave",
            source_of_truth="goals_service",
            risk_class="low",
            allowed_actions=["read"],
            dependencies=[],
            eval_criteria="criteria",
            rollout="rollout",
            adr_reference="ADR-101",
            status="draft",
        )
        service.record_decision("goals", decision_req)
        status_after_dec = service.get_module_status("goals")
        assert status_after_dec.overall_status == "decision_recorded"

        # 3. Simulate all gates passed and decision approved -> "approved"
        passed_gates = tuple(
            GateCheckItem(
                gate_id=g.gate_id,
                category=g.category,
                description=g.description,
                status="passed",
            )
            for g in status_after_dec.gates
        )
        repo.save_module_status(
            status_after_dec.model_copy(
                update={
                    "gates": passed_gates,
                    "overall_status": "approved",
                    "passed_gates": len(passed_gates),
                    "pending_gates": 0,
                    "failed_gates": 0,
                }
            )
        )
        approved_decision = service.record_decision(
            "goals",
            ReactivationDecisionRequest(
                outcome="Goal journey approved",
                owner_product="alice",
                owner_engineering="bob",
                owner_domain="carol",
                owner_compliance="dave",
                source_of_truth="goals_service",
                risk_class="low",
                allowed_actions=["read"],
                dependencies=[],
                eval_criteria="criteria",
                rollout="rollout",
                adr_reference="ADR-101",
                status="approved",
            ),
        )
        status_approved = service.get_module_status("goals")
        assert status_approved.overall_status == "approved"
        assert status_approved.passed_gates == 14
        assert status_approved.pending_gates == 0

    def test_reactivated_status_never_set_by_service(self, service: LegacyGateService) -> None:
        # Even if all gates pass, service never marks a module as "reactivated"
        # Reactivation is an external deployment/runtime action
        for slug in service.MODULES:
            status = service.get_module_status(slug)
            assert status.overall_status != "reactivated"
