from __future__ import annotations

import json
import uuid

from risk_dashboard.modules.pro_lab.domain.entities import (
    ProLabAuditLog,
    ProLabBlueprint,
    ProLabExperiment,
    ProLabExperimentRun,
    ProLabWorkspaceState,
)
from risk_dashboard.modules.pro_lab.domain.ports import (
    ProLabAuditRepository,
    ProLabBlueprintRepository,
    ProLabExperimentRepository,
    ProLabExperimentRunRepository,
    ProLabWorkspaceStateRepository,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


def new_pro_lab_blueprint_id() -> str:
    return f"plbp_{uuid.uuid4().hex[:12]}"


def new_pro_lab_experiment_id() -> str:
    return f"plexp_{uuid.uuid4().hex[:12]}"


def new_pro_lab_run_id() -> str:
    return f"plrun_{uuid.uuid4().hex[:12]}"


def new_pro_lab_workspace_id() -> str:
    return f"plws_{uuid.uuid4().hex[:12]}"


def new_pro_lab_audit_id() -> str:
    return f"plaud_{uuid.uuid4().hex[:12]}"


class SqliteProLabBlueprintRepository(ProLabBlueprintRepository):
    def save(self, blueprint: ProLabBlueprint) -> ProLabBlueprint:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO pro_lab_blueprints (
                  blueprint_id, user_id, name, objective, asset_universe_json, benchmark,
                  rebalance_frequency, risk_constraints, assumptions_note, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(blueprint_id) DO UPDATE SET
                  name = excluded.name,
                  objective = excluded.objective,
                  asset_universe_json = excluded.asset_universe_json,
                  benchmark = excluded.benchmark,
                  rebalance_frequency = excluded.rebalance_frequency,
                  risk_constraints = excluded.risk_constraints,
                  assumptions_note = excluded.assumptions_note,
                  status = excluded.status,
                  updated_at = excluded.updated_at
                """,
                (
                    blueprint.blueprint_id,
                    blueprint.user_id,
                    blueprint.name,
                    blueprint.objective,
                    json.dumps(list(blueprint.asset_universe), ensure_ascii=False),
                    blueprint.benchmark,
                    blueprint.rebalance_frequency,
                    blueprint.risk_constraints,
                    blueprint.assumptions_note,
                    blueprint.status,
                    blueprint.created_at,
                    blueprint.updated_at,
                ),
            )
            conn.commit()
        return blueprint

    def list_by_user(self, *, user_id: str) -> list[ProLabBlueprint]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM pro_lab_blueprints
                WHERE user_id = ?
                ORDER BY updated_at DESC, created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def get(self, *, blueprint_id: str) -> ProLabBlueprint | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                "SELECT * FROM pro_lab_blueprints WHERE blueprint_id = ?",
                (blueprint_id,),
            ).fetchone()
        return self._to_entity(row) if row is not None else None

    def _to_entity(self, row) -> ProLabBlueprint:
        return ProLabBlueprint(
            blueprint_id=row["blueprint_id"],
            user_id=row["user_id"],
            name=row["name"],
            objective=row["objective"],
            asset_universe=tuple(json.loads(row["asset_universe_json"] or "[]")),
            benchmark=row["benchmark"],
            rebalance_frequency=row["rebalance_frequency"],
            risk_constraints=row["risk_constraints"],
            assumptions_note=row["assumptions_note"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class SqliteProLabExperimentRepository(ProLabExperimentRepository):
    def save(self, experiment: ProLabExperiment) -> ProLabExperiment:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO pro_lab_experiments (
                  experiment_id, user_id, blueprint_id, experiment_type, status, input_json, output_json, created_at,
                  review_status, review_notes, reviewed_at, reviewer_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment.experiment_id,
                    experiment.user_id,
                    experiment.blueprint_id,
                    experiment.experiment_type,
                    experiment.status,
                    json.dumps(experiment.input_payload, ensure_ascii=False),
                    json.dumps(experiment.output_payload, ensure_ascii=False),
                    experiment.created_at,
                    experiment.review_status,
                    experiment.review_notes,
                    experiment.reviewed_at,
                    experiment.reviewer_id,
                ),
            )
            conn.commit()
        return experiment

    def list_by_user(self, *, user_id: str) -> list[ProLabExperiment]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM pro_lab_experiments
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def list_all(self) -> list[ProLabExperiment]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM pro_lab_experiments
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def get(self, *, experiment_id: str) -> ProLabExperiment | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM pro_lab_experiments
                WHERE experiment_id = ?
                """,
                (experiment_id,),
            ).fetchone()
        return self._to_entity(row) if row is not None else None

    def review(
        self,
        *,
        experiment_id: str,
        review_status: str,
        review_notes: str | None,
        reviewer_id: str,
    ) -> ProLabExperiment | None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                UPDATE pro_lab_experiments
                SET review_status = ?, review_notes = ?, reviewed_at = datetime('now'), reviewer_id = ?
                WHERE experiment_id = ?
                """,
                (review_status, review_notes, reviewer_id, experiment_id),
            )
            conn.commit()
        return self.get(experiment_id=experiment_id)

    def _to_entity(self, row) -> ProLabExperiment:
        return ProLabExperiment(
            experiment_id=row["experiment_id"],
            user_id=row["user_id"],
            blueprint_id=row["blueprint_id"],
            experiment_type=row["experiment_type"],
            status=row["status"],
            input_payload=json.loads(row["input_json"] or "{}"),
            output_payload=json.loads(row["output_json"] or "{}"),
            created_at=row["created_at"],
            review_status=row["review_status"] or "pending_review",
            review_notes=row["review_notes"],
            reviewed_at=row["reviewed_at"],
            reviewer_id=row["reviewer_id"],
        )


class SqliteProLabAuditRepository(ProLabAuditRepository):
    def save(self, log: ProLabAuditLog) -> ProLabAuditLog:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO pro_lab_audit_logs (
                  audit_id, actor_id, surface, action, target_type, target_id, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.audit_id,
                    log.actor_id,
                    log.surface,
                    log.action,
                    log.target_type,
                    log.target_id,
                    json.dumps(log.metadata, ensure_ascii=False),
                    log.created_at,
                ),
            )
            conn.commit()
        return log

    def list_all(self) -> list[ProLabAuditLog]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM pro_lab_audit_logs
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [
            ProLabAuditLog(
                audit_id=row["audit_id"],
                actor_id=row["actor_id"],
                surface=row["surface"],
                action=row["action"],
                target_type=row["target_type"],
                target_id=row["target_id"],
                metadata=json.loads(row["metadata_json"] or "{}"),
                created_at=row["created_at"],
            )
            for row in rows
        ]


class SqliteProLabExperimentRunRepository(ProLabExperimentRunRepository):
    def save(self, run: ProLabExperimentRun) -> ProLabExperimentRun:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO pro_lab_experiment_runs (
                  run_id, user_id, experiment_id, blueprint_id, provider_id, command_id, status,
                  input_json, output_json, logs_json, progress_pct, safety_flags_json,
                  data_freshness_json, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                  experiment_id = excluded.experiment_id,
                  status = excluded.status,
                  output_json = excluded.output_json,
                  logs_json = excluded.logs_json,
                  progress_pct = excluded.progress_pct,
                  safety_flags_json = excluded.safety_flags_json,
                  data_freshness_json = excluded.data_freshness_json,
                  completed_at = excluded.completed_at
                """,
                (
                    run.run_id,
                    run.user_id,
                    run.experiment_id,
                    run.blueprint_id,
                    run.provider_id,
                    run.command_id,
                    run.status,
                    json.dumps(run.input_payload, ensure_ascii=False),
                    json.dumps(run.output_payload, ensure_ascii=False),
                    json.dumps(list(run.logs), ensure_ascii=False),
                    run.progress_pct,
                    json.dumps(list(run.safety_flags), ensure_ascii=False),
                    json.dumps(run.data_freshness, ensure_ascii=False),
                    run.created_at,
                    run.completed_at,
                ),
            )
            conn.commit()
        return run

    def get(self, *, run_id: str) -> ProLabExperimentRun | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM pro_lab_experiment_runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        return self._to_entity(row) if row is not None else None

    def list_by_user(self, *, user_id: str) -> list[ProLabExperimentRun]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM pro_lab_experiment_runs
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def list_all(self) -> list[ProLabExperimentRun]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM pro_lab_experiment_runs
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [self._to_entity(row) for row in rows]

    def _to_entity(self, row) -> ProLabExperimentRun:
        return ProLabExperimentRun(
            run_id=row["run_id"],
            user_id=row["user_id"],
            experiment_id=row["experiment_id"],
            blueprint_id=row["blueprint_id"],
            provider_id=row["provider_id"],
            command_id=row["command_id"],
            status=row["status"],
            input_payload=json.loads(row["input_json"] or "{}"),
            output_payload=json.loads(row["output_json"] or "{}"),
            logs=tuple(json.loads(row["logs_json"] or "[]")),
            progress_pct=int(row["progress_pct"] or 0),
            safety_flags=tuple(json.loads(row["safety_flags_json"] or "[]")),
            data_freshness=json.loads(row["data_freshness_json"] or "{}"),
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )


class SqliteProLabWorkspaceStateRepository(ProLabWorkspaceStateRepository):
    def save(self, state: ProLabWorkspaceState) -> ProLabWorkspaceState:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO pro_lab_workspaces (
                  workspace_id, user_id, active_page, open_panels_json, selected_blueprint_id,
                  selected_experiment_id, layout_json, notes, version, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                  active_page = excluded.active_page,
                  open_panels_json = excluded.open_panels_json,
                  selected_blueprint_id = excluded.selected_blueprint_id,
                  selected_experiment_id = excluded.selected_experiment_id,
                  layout_json = excluded.layout_json,
                  notes = excluded.notes,
                  version = pro_lab_workspaces.version + 1,
                  updated_at = excluded.updated_at
                """,
                (
                    state.workspace_id,
                    state.user_id,
                    state.active_page,
                    json.dumps(list(state.open_panels), ensure_ascii=False),
                    state.selected_blueprint_id,
                    state.selected_experiment_id,
                    json.dumps(state.layout, ensure_ascii=False),
                    state.notes,
                    state.version,
                    state.updated_at,
                ),
            )
            conn.commit()
        return self.get(user_id=state.user_id) or state

    def get(self, *, user_id: str) -> ProLabWorkspaceState | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM pro_lab_workspaces
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return ProLabWorkspaceState(
            workspace_id=row["workspace_id"],
            user_id=row["user_id"],
            active_page=row["active_page"],
            open_panels=tuple(json.loads(row["open_panels_json"] or "[]")),
            selected_blueprint_id=row["selected_blueprint_id"],
            selected_experiment_id=row["selected_experiment_id"],
            layout=json.loads(row["layout_json"] or "{}"),
            notes=row["notes"],
            version=int(row["version"] or 1),
            updated_at=row["updated_at"],
        )


def reset_pro_lab_state() -> None:
    reset_app_state_tables()
