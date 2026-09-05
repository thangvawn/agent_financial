"""Domain ports for legacy gate."""
from __future__ import annotations

from typing import Protocol

from risk_dashboard.modules.legacy_gate.domain.entities import (
    GateCheckItem,
    LegacyModuleBaselineReport,
    ModuleGateStatus,
    ReactivationDecisionRecord,
)


class GateRepositoryPort(Protocol):
    """Port for storing and retrieving module gate statuses and decision records."""

    def get_module_status(self, module_slug: str) -> ModuleGateStatus | None:
        ...

    def save_module_status(self, status: ModuleGateStatus) -> None:
        ...

    def list_module_statuses(self) -> tuple[ModuleGateStatus, ...]:
        ...

    def save_decision_record(self, record: ReactivationDecisionRecord) -> None:
        ...

    def get_decision_record(self, module_slug: str) -> ReactivationDecisionRecord | None:
        ...

    def list_decision_records(
        self, module_slug: str | None = None
    ) -> tuple[ReactivationDecisionRecord, ...]:
        ...


class BaselineReporterPort(Protocol):
    """Port for discovering and building baseline report of a legacy module."""

    def build_baseline_report(self, module_slug: str) -> LegacyModuleBaselineReport:
        ...


class GateEvaluatorPort(Protocol):
    """Port for evaluating gates and determining overall status."""

    def get_gates_for_module(self, module_slug: str) -> tuple[GateCheckItem, ...]:
        ...

