"""Tests for legacy gate reactivation decisions, governance block, and audit trail."""
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


class TestLegacyGateDecisions:
    def test_record_decision_stores_record_and_updates_status(self, service: LegacyGateService) -> None:
        req = ReactivationDecisionRequest(
            outcome="Provide education-only goal tracking journey",
            owner_product="alice", owner_engineering="bob",
            owner_domain="carol", owner_compliance="dave",
            source_of_truth="goals domain service", risk_class="financial_education",
            allowed_actions=["read", "proposal"], dependencies=["auth", "learning"],
            eval_criteria="Pass 100% baseline regression and zero unauthorized advice",
            rollout="Cohort beta via feature flag", adr_reference="ADR-012-GOALS",
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
            outcome="Test outcome", owner_product="alice",
            owner_engineering="bob", owner_domain="carol", owner_compliance="dave",
            source_of_truth="sot", risk_class="risk", allowed_actions=["read"],
            dependencies=[], eval_criteria="eval criteria", rollout="rollout",
            adr_reference="ADR-001", status="draft",
        )
        with pytest.raises(LegacyGateError) as exc_info:
            service.record_decision("unknown_module", req)
        assert exc_info.value.error_type == "module_not_found"

    def test_overall_status_derivation_chain(self, service: LegacyGateService, repo: InMemoryGateRepository) -> None:
        status = service.initialize_module("goals")
        assert status.overall_status == "gates_documented"

        decision_req = ReactivationDecisionRequest(
            outcome="Goal journey", owner_product="alice",
            owner_engineering="bob", owner_domain="carol", owner_compliance="dave",
            source_of_truth="goals_service", risk_class="low", allowed_actions=["read"],
            dependencies=[], eval_criteria="criteria", rollout="rollout",
            adr_reference="ADR-101", status="draft",
        )
        service.record_decision("goals", decision_req)
        status_after_dec = service.get_module_status("goals")
        assert status_after_dec.overall_status == "decision_recorded"

        passed_gates = tuple(
            GateCheckItem(
                gate_id=g.gate_id, category=g.category,
                description=g.description, status="passed",
            )
            for g in status_after_dec.gates
        )
        repo.save_module_status(
            status_after_dec.model_copy(
                update={
                    "gates": passed_gates,
                    "passed_gates": len(passed_gates),
                    "pending_gates": 0,
                    "failed_gates": 0,
                }
            )
        )
        service.record_decision(
            "goals",
            ReactivationDecisionRequest(
                outcome="Goal journey approved", owner_product="alice",
                owner_engineering="bob", owner_domain="carol", owner_compliance="dave",
                source_of_truth="goals_service", risk_class="low", allowed_actions=["read"],
                dependencies=[], eval_criteria="criteria", rollout="rollout",
                adr_reference="ADR-101", status="approved",
            ),
        )
        status_approved = service.get_module_status("goals")
        assert status_approved.overall_status == "approved"
        assert status_approved.passed_gates == 14
        assert status_approved.pending_gates == 0

    def test_record_decision_approved_blocked_when_gates_pending(self, service: LegacyGateService) -> None:
        req = ReactivationDecisionRequest(
            outcome="Premature approval attempt", owner_product="alice",
            owner_engineering="bob", owner_domain="carol", owner_compliance="dave",
            source_of_truth="goals_service", risk_class="low", allowed_actions=["read"],
            dependencies=[], eval_criteria="criteria", rollout="rollout",
            adr_reference="ADR-101", status="approved",
        )
        with pytest.raises(LegacyGateError) as exc_info:
            service.record_decision("goals", req)
        assert exc_info.value.error_type == "gates_not_passed"

    def test_audit_trail_append_only_preserves_history(self, service: LegacyGateService) -> None:
        req1 = ReactivationDecisionRequest(
            outcome="Initial proposal draft", owner_product="alice",
            owner_engineering="bob", owner_domain="carol", owner_compliance="dave",
            source_of_truth="sot", risk_class="low", allowed_actions=["read"],
            dependencies=[], eval_criteria="eval1", rollout="rollout1",
            adr_reference="ADR-101", status="draft",
        )
        rec1 = service.record_decision("goals", req1)
        req2 = ReactivationDecisionRequest(
            outcome="Revised proposal draft", owner_product="alice",
            owner_engineering="bob", owner_domain="carol", owner_compliance="dave",
            source_of_truth="sot", risk_class="low", allowed_actions=["read"],
            dependencies=[], eval_criteria="eval2", rollout="rollout2",
            adr_reference="ADR-102", status="draft",
        )
        rec2 = service.record_decision("goals", req2)

        history = service.list_decision_records("goals")
        assert len(history) == 2
        assert history[0].record_id == rec1.record_id
        assert history[1].record_id == rec2.record_id
        latest = service.get_module_status("goals").decision_record
        assert latest is not None
        assert latest.record_id == rec2.record_id

    def test_reactivated_status_never_set_by_service(self, service: LegacyGateService) -> None:
        for slug in service.MODULES:
            status = service.get_module_status(slug)
            assert status.overall_status != "reactivated"
