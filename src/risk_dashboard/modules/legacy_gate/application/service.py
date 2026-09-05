"""Application service for legacy reactivation gates management."""
from __future__ import annotations

from uuid import uuid4

from risk_dashboard.modules.legacy_gate.application.evaluators import (
    build_baseline_report,
    get_module_gates,
)
from risk_dashboard.modules.legacy_gate.domain.entities import (
    GateCheckItem,
    GateOverallStatus,
    LegacyModuleBaselineReport,
    ModuleGateStatus,
    ReactivationDecisionRecord,
    utc_now_iso,
)
from risk_dashboard.modules.legacy_gate.domain.errors import LegacyGateError
from risk_dashboard.modules.legacy_gate.domain.ports import GateRepositoryPort
from risk_dashboard.modules.legacy_gate.infrastructure.in_memory import InMemoryGateRepository
from risk_dashboard.modules.legacy_gate.schemas.gates import ReactivationDecisionRequest


class LegacyGateService:
    """Service governing legacy module reactivation gates and baseline tracking."""

    MODULES: tuple[str, ...] = ("goals", "financial_health", "community", "guided_investing")

    def __init__(self, repository: GateRepositoryPort | None = None) -> None:
        self._repo: GateRepositoryPort = repository or InMemoryGateRepository()

    def _validate_module_slug(self, module_slug: str) -> None:
        if module_slug not in self.MODULES:
            raise LegacyGateError(
                f"Module '{module_slug}' is not one of the recognized legacy modules: {self.MODULES}",
                error_type="module_not_found",
                module_slug=module_slug,
            )

    def _derive_overall_status(
        self,
        baseline: LegacyModuleBaselineReport | None,
        gates: tuple[GateCheckItem, ...],
        decision: ReactivationDecisionRecord | None,
    ) -> GateOverallStatus:
        if baseline is None:
            return "hold"
        if gates and all(g.status == "passed" for g in gates):
            if decision is not None and decision.status == "approved":
                return "approved"
        if decision is not None:
            return "decision_recorded"
        if len(gates) > 0:
            return "gates_documented"
        if baseline.tests_count > 0:
            return "baseline_captured"
        return "hold"

    def initialize_module(self, module_slug: str) -> ModuleGateStatus:
        self._validate_module_slug(module_slug)
        existing = self._repo.get_module_status(module_slug)
        baseline = build_baseline_report(module_slug)
        gates = existing.gates if existing else get_module_gates(module_slug)
        decision = existing.decision_record if existing else self._repo.get_decision_record(module_slug)

        overall = self._derive_overall_status(baseline, gates, decision)
        passed = sum(1 for g in gates if g.status == "passed")
        failed = sum(1 for g in gates if g.status == "failed")
        pending = sum(1 for g in gates if g.status == "pending")

        status = ModuleGateStatus(
            module_slug=module_slug,
            overall_status=overall,
            gates=gates,
            baseline=baseline,
            decision_record=decision,
            total_gates=len(gates),
            passed_gates=passed,
            failed_gates=failed,
            pending_gates=pending,
            updated_at=utc_now_iso(),
        )
        self._repo.save_module_status(status)
        return status

    def get_module_status(self, module_slug: str) -> ModuleGateStatus:
        self._validate_module_slug(module_slug)
        status = self._repo.get_module_status(module_slug)
        return status if status is not None else self.initialize_module(module_slug)

    def list_modules(self) -> tuple[ModuleGateStatus, ...]:
        return tuple(self.get_module_status(slug) for slug in self.MODULES)

    def evaluate_module(self, module_slug: str) -> ModuleGateStatus:
        self._validate_module_slug(module_slug)
        return self.initialize_module(module_slug)

    def get_baseline_report(self, module_slug: str) -> LegacyModuleBaselineReport:
        self._validate_module_slug(module_slug)
        status = self.get_module_status(module_slug)
        return status.baseline if status.baseline is not None else build_baseline_report(module_slug)

    def record_decision(
        self,
        module_slug: str,
        decision_req: ReactivationDecisionRequest,
    ) -> ReactivationDecisionRecord:
        self._validate_module_slug(module_slug)
        curr = self.get_module_status(module_slug)
        if not curr.gates:
            raise LegacyGateError(
                f"Cannot record decision for '{module_slug}': gates must be documented first.",
                error_type="gate_not_ready",
                module_slug=module_slug,
            )

        if decision_req.status == "approved":
            if (
                curr.failed_gates > 0
                or curr.pending_gates > 0
                or curr.passed_gates != curr.total_gates
                or curr.total_gates == 0
            ):
                raise LegacyGateError(
                    f"Cannot approve '{module_slug}': all {curr.total_gates} gates must pass first.",
                    error_type="gates_not_passed",
                    module_slug=module_slug,
                )

        now = utc_now_iso()
        record = ReactivationDecisionRecord(
            record_id=f"rec-{uuid4().hex[:12]}",
            module_slug=module_slug,
            schema_version="1.0.0",
            outcome=decision_req.outcome,
            owner_product=decision_req.owner_product,
            owner_engineering=decision_req.owner_engineering,
            owner_domain=decision_req.owner_domain,
            owner_compliance=decision_req.owner_compliance,
            source_of_truth=decision_req.source_of_truth,
            risk_class=decision_req.risk_class,
            allowed_actions=tuple(decision_req.allowed_actions),
            dependencies=tuple(decision_req.dependencies),
            eval_criteria=decision_req.eval_criteria,
            rollout=decision_req.rollout,
            adr_reference=decision_req.adr_reference,
            status=decision_req.status,
            created_at=now,
            updated_at=now,
        )
        self._repo.save_decision_record(record)
        upd = self.get_module_status(module_slug)
        new_overall = self._derive_overall_status(upd.baseline, upd.gates, record)
        self._repo.save_module_status(
            ModuleGateStatus(
                module_slug=module_slug,
                overall_status=new_overall,
                gates=upd.gates,
                baseline=upd.baseline,
                decision_record=record,
                total_gates=upd.total_gates,
                passed_gates=upd.passed_gates,
                failed_gates=upd.failed_gates,
                pending_gates=upd.pending_gates,
                updated_at=now,
            )
        )
        return record

    def list_decision_records(
        self, module_slug: str | None = None
    ) -> tuple[ReactivationDecisionRecord, ...]:
        if module_slug is not None:
            self._validate_module_slug(module_slug)
        return self._repo.list_decision_records(module_slug)
