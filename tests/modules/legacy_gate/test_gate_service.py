"""Tests for LegacyGateService business logic and gate evaluations."""
from __future__ import annotations

import pytest

from risk_dashboard.modules.legacy_gate.application.service import LegacyGateService
from risk_dashboard.modules.legacy_gate.domain.errors import LegacyGateError
from risk_dashboard.modules.legacy_gate.infrastructure.in_memory import InMemoryGateRepository


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

    @pytest.mark.parametrize(
        ("slug", "expected_count"),
        [("financial_health", 12), ("community", 12), ("guided_investing", 12)],
    )
    def test_gate_counts_legacy_modules(
        self, service: LegacyGateService, slug: str, expected_count: int
    ) -> None:
        status = service.get_module_status(slug)
        assert status.total_gates == expected_count
        assert len(status.gates) == expected_count

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

    def test_evaluate_module_refreshes_baseline(self, service: LegacyGateService) -> None:
        status = service.evaluate_module("financial_health")
        assert status.module_slug == "financial_health"
        assert status.baseline is not None
        assert status.baseline.tests_count > 0
