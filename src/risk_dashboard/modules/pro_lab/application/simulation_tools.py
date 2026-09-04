from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.pro_lab.application.helpers import (
    aggregate_trade_summary,
    compare_run_metrics,
)
from risk_dashboard.modules.pro_lab.domain.ports import (
    ProLabBlueprintRepository,
    ProLabExperimentRunRepository,
)
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    SqliteProLabBlueprintRepository,
    SqliteProLabExperimentRunRepository,
)
from risk_dashboard.modules.pro_lab.schemas.simulation_agent import (
    ActionProposal,
    ActionReceipt,
    CompareRunsQuery,
    ExecuteRunRequest,
    ExperimentValidation,
    ReproducibilityManifest,
    RunComparison,
    RunQuery,
    SimulationRunArtifact,
    StrategySpec,
    StrategySpecQuery,
    TradeSummary,
    TradeSummaryQuery,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Tool Manifests

SIM_GET_STRATEGY_SPEC_MANIFEST = ToolManifest(
    tool_id="simulation.get_strategy_spec",
    name="Get Strategy Blueprint Spec",
    module="simulation_lab",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch strategy blueprint definition, asset universe, benchmark, and constraints.",
    required_capabilities=("pro_lab:strategy:read",),
)

SIM_VALIDATE_EXPERIMENT_MANIFEST = ToolManifest(
    tool_id="simulation.validate_experiment",
    name="Validate Experiment Manifest",
    module="simulation_lab",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Validate reproducibility manifest completeness, parameters, data windows, and slippage.",
    required_capabilities=("pro_lab:experiment:read",),
)

SIM_GET_RUN_MANIFEST = ToolManifest(
    tool_id="simulation.get_run",
    name="Get Simulation Run Artifact",
    module="simulation_lab",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Fetch a completed or in-progress simulation run artifact with verified metrics.",
    required_capabilities=("pro_lab:run:read",),
)

SIM_GET_TRADE_SUMMARY_MANIFEST = ToolManifest(
    tool_id="simulation.get_trade_summary",
    name="Get Simulation Trade Summary",
    module="simulation_lab",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Aggregate trade metrics (win rate, profit factor, returns) for a specific run.",
    required_capabilities=("pro_lab:run:read",),
)

SIM_COMPARE_RUNS_MANIFEST = ToolManifest(
    tool_id="simulation.compare_runs",
    name="Compare Simulation Runs",
    module="simulation_lab",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Compare normalized metrics between compatible simulation runs.",
    required_capabilities=("pro_lab:run:read",),
)

SIM_PROPOSE_RUN_MANIFEST = ToolManifest(
    tool_id="simulation.propose_run",
    name="Propose Simulation Run",
    module="simulation_lab",
    risk_class=RiskClass.PROPOSAL,
    version="1.0.0",
    description="Create an action proposal for a simulation run with cost estimation and confirmation token.",
    required_capabilities=("pro_lab:run:propose",),
)

SIM_EXECUTE_RUN_MANIFEST = ToolManifest(
    tool_id="simulation.execute_run",
    name="Execute Confirmed Simulation Run",
    module="simulation_lab",
    risk_class=RiskClass.CONFIRMED_WRITE,
    version="1.0.0",
    description="Execute a confirmed simulation proposal using a valid confirmation token and idempotency key.",
    required_capabilities=("pro_lab:run:execute",),
)


def get_simulation_tool_manifests() -> list[ToolManifest]:
    return [
        SIM_GET_STRATEGY_SPEC_MANIFEST,
        SIM_VALIDATE_EXPERIMENT_MANIFEST,
        SIM_GET_RUN_MANIFEST,
        SIM_GET_TRADE_SUMMARY_MANIFEST,
        SIM_COMPARE_RUNS_MANIFEST,
        SIM_PROPOSE_RUN_MANIFEST,
        SIM_EXECUTE_RUN_MANIFEST,
    ]


# Tool Implementations

class SimGetStrategySpecTool:
    manifest = SIM_GET_STRATEGY_SPEC_MANIFEST

    def __init__(self, blueprint_repo: ProLabBlueprintRepository | None = None) -> None:
        self.blueprint_repo = blueprint_repo or SqliteProLabBlueprintRepository()

    def execute(
        self,
        payload: StrategySpecQuery,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> StrategySpec:
        bp = self.blueprint_repo.get(blueprint_id=payload.blueprint_id)
        if not bp:
            raise ValueError(f"Không tìm thấy strategy blueprint với ID: {payload.blueprint_id}")
        if account_id and bp.user_id != account_id:
            raise PermissionError(f"Từ chối truy cập blueprint của tài khoản khác: {bp.user_id}")

        return StrategySpec(
            schema_version="1.0.0",
            blueprint_id=bp.blueprint_id,
            name=bp.name,
            objective=bp.objective,
            asset_universe=bp.asset_universe,
            benchmark=bp.benchmark,
            rebalance_frequency=bp.rebalance_frequency,
            risk_constraints=bp.risk_constraints,
            assumptions_note=bp.assumptions_note,
            version="1.0.0",
            status=bp.status,
            created_at=bp.created_at,
            updated_at=bp.updated_at,
        )


class SimValidateExperimentTool:
    manifest = SIM_VALIDATE_EXPERIMENT_MANIFEST

    def execute(
        self,
        payload: ReproducibilityManifest,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> ExperimentValidation:
        missing_fields: list[str] = []
        warnings: list[str] = []

        # Check required fields
        if not payload.strategy_id:
            missing_fields.append("strategy_id")
        if not payload.strategy_version:
            missing_fields.append("strategy_version")
        if not payload.dataset_source:
            missing_fields.append("dataset_source")
        if not payload.dataset_version:
            missing_fields.append("dataset_version")
        if not payload.data_start:
            missing_fields.append("data_start")
        if not payload.data_end:
            missing_fields.append("data_end")
        if not payload.engine_version:
            missing_fields.append("engine_version")
        if not payload.metrics_calculation_version:
            missing_fields.append("metrics_calculation_version")

        # Warnings
        if payload.commission_pct == 0.0:
            warnings.append("Commission = 0%: kết quả backtest có thể lạc quan hơn thực tế.")
        if payload.slippage_pct == 0.0:
            warnings.append("Slippage = 0%: chưa tính trượt giá khớp lệnh thị trường.")
        if payload.random_seed is None:
            warnings.append("Random seed chưa được pin; một số thuật toán stochastic có thể không hoàn toàn deterministic.")

        is_valid = len(missing_fields) == 0
        validation_status = "passed" if is_valid and not warnings else ("warning" if is_valid else "rejected")

        return ExperimentValidation(
            schema_version="1.0.0",
            is_valid=is_valid,
            missing_fields=tuple(missing_fields),
            warnings=tuple(warnings),
            data_gap_notes=payload.data_gaps,
            validation_status=validation_status,
        )


class SimGetRunTool:
    manifest = SIM_GET_RUN_MANIFEST

    def __init__(self, run_repo: ProLabExperimentRunRepository | None = None) -> None:
        self.run_repo = run_repo or SqliteProLabExperimentRunRepository()

    def execute(
        self,
        payload: RunQuery,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> SimulationRunArtifact:
        run = self.run_repo.get(run_id=payload.run_id)
        if not run:
            raise ValueError(f"Không tìm thấy simulation run với ID: {payload.run_id}")
        if account_id and run.user_id != account_id:
            raise PermissionError(f"Từ chối truy cập simulation run của tài khoản khác: {run.user_id}")

        # Extract manifest or build standard
        manifest_data = run.input_payload.get("manifest")
        if isinstance(manifest_data, dict):
            manifest = ReproducibilityManifest(**manifest_data)
        else:
            manifest = ReproducibilityManifest(
                schema_version="1.0.0",
                strategy_id=run.blueprint_id or "strat_default",
                strategy_version="1.0.0",
                dataset_source="cafef_eod",
                dataset_version="v2024.1",
                data_start="2022-01-01",
                data_end="2024-01-01",
                parameters=run.input_payload.get("parameters", {}),
                commission_pct=0.15,
                slippage_pct=0.2,
                benchmark="VNINDEX",
                engine_version="1.0.0",
                execution_timestamp=run.created_at,
                metrics_calculation_version="1.0.0",
            )

        status_mapping = {
            "completed": "completed",
            "failed": "failed",
            "running": "running",
            "queued": "queued",
        }
        artifact_status = status_mapping.get(run.status, "completed")

        metrics_raw = run.output_payload.get("metrics", {})
        metrics = {k: v for k, v in metrics_raw.items() if isinstance(v, (int, float)) or v is None}

        return SimulationRunArtifact(
            schema_version="1.0.0",
            artifact_id=f"art_{run.run_id}",
            run_id=run.run_id,
            account_id=run.user_id,
            status=artifact_status,  # type: ignore
            manifest=manifest,
            metrics=metrics,
            trade_summary=run.output_payload.get("trade_summary", {}),
            source_refs=("pro_lab.experiment_runs",),
            limitations=("Paper backtest; results do not guarantee future live execution returns.",),
            created_at=run.created_at,
            completed_at=run.completed_at,
        )


class SimGetTradeSummaryTool:
    manifest = SIM_GET_TRADE_SUMMARY_MANIFEST

    def __init__(self, run_repo: ProLabExperimentRunRepository | None = None) -> None:
        self.run_repo = run_repo or SqliteProLabExperimentRunRepository()

    def execute(
        self,
        payload: TradeSummaryQuery,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> TradeSummary:
        run = self.run_repo.get(run_id=payload.run_id)
        if not run:
            raise ValueError(f"Không tìm thấy simulation run với ID: {payload.run_id}")
        if account_id and run.user_id != account_id:
            raise PermissionError(f"Từ chối truy cập simulation run của tài khoản khác: {run.user_id}")

        trades = run.output_payload.get("trades", [])
        if not trades and "trade_log" in run.output_payload:
            trades = run.output_payload["trade_log"]

        return aggregate_trade_summary(trades, payload.run_id, detail=payload.detail)


class SimCompareRunsTool:
    manifest = SIM_COMPARE_RUNS_MANIFEST

    def __init__(self, run_repo: ProLabExperimentRunRepository | None = None) -> None:
        self.run_repo = run_repo or SqliteProLabExperimentRunRepository()

    def execute(
        self,
        payload: CompareRunsQuery,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> RunComparison:
        run_items: list[dict[str, Any]] = []
        for rid in payload.run_ids:
            run = self.run_repo.get(run_id=rid)
            if not run:
                raise ValueError(f"Không tìm thấy simulation run với ID: {rid}")
            if account_id and run.user_id != account_id:
                raise PermissionError(f"Từ chối so sánh simulation run của tài khoản khác: {run.user_id}")

            manifest_data = run.input_payload.get("manifest", {})
            metrics_calc_ver = manifest_data.get("metrics_calculation_version", "1.0.0")
            strat_ver = manifest_data.get("strategy_version", "1.0.0")

            run_items.append({
                "run_id": run.run_id,
                "strategy_id": run.blueprint_id or "strat_unknown",
                "strategy_version": strat_ver,
                "metrics_calculation_version": metrics_calc_ver,
                "metrics": run.output_payload.get("metrics", {}),
            })

        return compare_run_metrics(run_items)


class SimProposeRunTool:
    manifest = SIM_PROPOSE_RUN_MANIFEST

    def __init__(self, action_service: Any = None) -> None:
        self.action_service = action_service

    def execute(
        self,
        payload: ReproducibilityManifest,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "default_user",
    ) -> ActionProposal:
        if self.action_service:
            return self.action_service.create_proposal(account_id=account_id, manifest=payload)

        # Fallback in-memory proposal generator
        now = datetime.now(timezone.utc)
        proposal_id = f"prop_{uuid.uuid4().hex[:12]}"
        run_id = f"simrun_{uuid.uuid4().hex[:12]}"
        expires_at = (now + timedelta(minutes=15)).isoformat()

        return ActionProposal(
            schema_version="1.0.0",
            proposal_id=proposal_id,
            run_id=run_id,
            account_id=account_id,
            operation="run_simulation",
            manifest=payload,
            estimated_cost=0.02,
            risk_class="proposal",
            requires_confirmation=True,
            policy_version="1.0.0",
            created_at=now.isoformat(),
            expires_at=expires_at,
        )


class SimExecuteRunTool:
    manifest = SIM_EXECUTE_RUN_MANIFEST

    def __init__(self, action_service: Any = None) -> None:
        self.action_service = action_service

    def execute(
        self,
        payload: ExecuteRunRequest,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "default_user",
    ) -> ActionReceipt:
        if not self.action_service:
            raise RuntimeError("SimulationActionService chưa được khởi tạo cho execute_run.")

        return self.action_service.confirm_and_execute(
            proposal_id=payload.proposal_id,
            confirmation_token=payload.confirmation_token,
            idempotency_key=payload.idempotency_key,
            account_id=account_id,
        )

