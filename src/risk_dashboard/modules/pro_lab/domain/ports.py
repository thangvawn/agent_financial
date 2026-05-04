from __future__ import annotations

from typing import Protocol

from risk_dashboard.modules.pro_lab.domain.entities import (
    ProLabAuditLog,
    ProLabBlueprint,
    ProLabExperiment,
    ProLabExperimentRun,
    ProLabWorkspaceState,
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
