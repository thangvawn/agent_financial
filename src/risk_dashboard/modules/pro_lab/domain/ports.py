from __future__ import annotations

from typing import Protocol

from risk_dashboard.modules.pro_lab.domain.entities import (
    ProLabAuditLog,
    ProLabBlueprint,
    ProLabExperiment,
    ProLabExperimentRun,
    ProLabWorkspaceState,
    SimulationActionProposalEntity,
    SimulationActionReceiptEntity,
    SimulationExperimentSpec,
)


class ProLabBlueprintRepository(Protocol):
    def save(self, blueprint: ProLabBlueprint) -> ProLabBlueprint: ...

    def list_by_user(self, *, user_id: str) -> list[ProLabBlueprint]: ...

    def get(self, *, blueprint_id: str) -> ProLabBlueprint | None: ...


class ProLabExperimentRepository(Protocol):
    def save(self, experiment: ProLabExperiment) -> ProLabExperiment: ...

    def list_by_user(self, *, user_id: str) -> list[ProLabExperiment]: ...

    def list_all(self) -> list[ProLabExperiment]: ...

    def get(self, *, experiment_id: str) -> ProLabExperiment | None: ...

    def review(
        self,
        *,
        experiment_id: str,
        review_status: str,
        review_notes: str | None,
        reviewer_id: str,
    ) -> ProLabExperiment | None: ...


class ProLabAuditRepository(Protocol):
    def save(self, log: ProLabAuditLog) -> ProLabAuditLog: ...

    def list_all(self) -> list[ProLabAuditLog]: ...


class ProLabExperimentRunRepository(Protocol):
    def save(self, run: ProLabExperimentRun) -> ProLabExperimentRun: ...

    def get(self, *, run_id: str) -> ProLabExperimentRun | None: ...

    def list_by_user(self, *, user_id: str) -> list[ProLabExperimentRun]: ...

    def list_all(self) -> list[ProLabExperimentRun]: ...


class ProLabWorkspaceStateRepository(Protocol):
    def save(self, state: ProLabWorkspaceState) -> ProLabWorkspaceState: ...

    def get(self, *, user_id: str) -> ProLabWorkspaceState | None: ...


class SimulationExperimentSpecRepository(Protocol):
    def save(self, spec: SimulationExperimentSpec) -> SimulationExperimentSpec: ...

    def get(self, *, spec_id: str) -> SimulationExperimentSpec | None: ...

    def list_by_account(self, *, account_id: str) -> list[SimulationExperimentSpec]: ...


class SimulationActionProposalRepository(Protocol):
    def save(self, proposal: SimulationActionProposalEntity) -> SimulationActionProposalEntity: ...

    def get(self, *, proposal_id: str) -> SimulationActionProposalEntity | None: ...

    def get_by_idempotency_key(self, *, account_id: str, idempotency_key: str) -> SimulationActionProposalEntity | None: ...

    def update_status(self, *, proposal_id: str, status: str) -> bool: ...


class SimulationActionReceiptRepository(Protocol):
    def save(self, receipt: SimulationActionReceiptEntity) -> SimulationActionReceiptEntity: ...

    def get(self, *, receipt_id: str) -> SimulationActionReceiptEntity | None: ...

    def get_by_proposal_id(self, *, proposal_id: str) -> SimulationActionReceiptEntity | None: ...

