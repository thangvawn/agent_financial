from __future__ import annotations

from risk_dashboard.modules.pro_lab.application.services import (
    GetProLabWorkspace,
    RunBacktestLab,
    SaveStrategyBlueprint,
)
from risk_dashboard.modules.pro_lab.domain.ports import (
    ProLabAuditRepository,
    ProLabBlueprintRepository,
    ProLabExperimentRepository,
)
from risk_dashboard.modules.pro_lab.schemas.studio import (
    StudioBootstrapResponse,
    StudioRunRequest,
    StudioRunResponse,
)


class GetBacktestStudio:
    def __init__(self, blueprints: ProLabBlueprintRepository, experiments: ProLabExperimentRepository) -> None:
        self.blueprints = blueprints
        self.experiments = experiments

    def execute(self, *, user_id: str) -> StudioBootstrapResponse:
        return StudioBootstrapResponse(
            workspace=GetProLabWorkspace(self.blueprints, self.experiments).execute(user_id=user_id),
            templates=[
                {
                    "id": "trend_following",
                    "name": "VN Trend 20/50",
                    "description": "Theo xu hướng trung hạn, ưu tiên tính dễ kiểm chứng.",
                    "universe": ["FPT", "VCB", "HPG", "MWG"],
                    "entry_rules": [{"field": "close", "operator": "above", "value": "sma_20"}],
                    "exit_rules": [{"field": "close", "operator": "below", "value": "sma_20"}],
                },
                {
                    "id": "volume_confirmation",
                    "name": "Volume confirmation",
                    "description": "Volume spike kèm bộ lọc regime và stop-loss.",
                    "universe": ["FPT", "MBB", "HPG"],
                    "entry_rules": [{"field": "volume", "operator": "above", "value": "sma_volume_20_x2"}],
                    "exit_rules": [{"field": "drawdown", "operator": "below", "value": -4}],
                },
            ],
            data_status={
                "provider": "yfinance",
                "market": "Vietnam equities",
                "mode": "historical_on_demand",
                "fallback": "offline educational result when provider is unavailable",
            },
            execution_profile={
                "market": "HOSE/HNX/UPCOM research profile",
                "defaults": {"commission_pct": 0.15, "slippage_pct": 0.05, "lot_size": 100, "settlement": "T+2"},
                "applied_by_engine": ["historical price path", "equal-weight allocation", "benchmark when available"],
                "recorded_only": ["commission", "slippage", "lot size", "settlement"],
            },
            supported_fields=[
                {"id": "close", "label": "Giá đóng cửa", "kind": "price"},
                {"id": "volume", "label": "Khối lượng", "kind": "volume"},
                {"id": "drawdown", "label": "Drawdown", "kind": "risk"},
                {"id": "btc_regime", "label": "BTC regime", "kind": "regime"},
            ],
        )


class RunBacktestStudio:
    def __init__(
        self,
        blueprints: ProLabBlueprintRepository,
        experiments: ProLabExperimentRepository,
        audit: ProLabAuditRepository,
    ) -> None:
        self.blueprints = blueprints
        self.experiments = experiments
        self.audit = audit

    def execute(self, req: StudioRunRequest) -> StudioRunResponse:
        blueprint_id = req.blueprint_id
        blueprint = self.blueprints.get(blueprint_id=blueprint_id) if blueprint_id else None
        if blueprint is None:
            saved = SaveStrategyBlueprint(self.blueprints, self.audit).execute(
                user_id=req.user_id,
                name=req.strategy.name,
                objective=req.strategy.hypothesis,
                asset_universe=req.strategy.universe,
                benchmark=req.strategy.benchmark,
                rebalance_frequency=req.strategy.rebalance_frequency,
                risk_constraints=f"Lot {req.execution.lot_size}; settlement {req.execution.settlement}",
                assumptions_note="Visual strategy created in Simulation Lab Studio.",
            )
            blueprint_id = saved.blueprint_id
        elif blueprint.user_id != req.user_id:
            raise ValueError("Không tìm thấy blueprint cho user này.")

        strategy_text = _rules_to_text(req)
        experiment = RunBacktestLab(self.blueprints, self.experiments, self.audit).execute(
            user_id=req.user_id,
            blueprint_id=blueprint_id,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.execution.initial_capital,
            timeframe=req.execution.timeframe,
            commission_pct=req.execution.commission_pct,
            slippage_pct=req.execution.slippage_pct,
            strategy_text=strategy_text,
            surface="simulation_lab_studio",
        )
        source = (experiment.engine_result or {}).get("source", "unknown")
        return StudioRunResponse(
            blueprint_id=blueprint_id,
            experiment=experiment,
            fidelity={
                "level": "offline" if source == "offline_fallback" else "research",
                "source": source,
                "costs_applied": False,
                "message": "Phí, trượt giá, lot và T+2 đang được lưu để audit nhưng chưa được khấu trừ trong engine.",
            },
        )


def _rules_to_text(req: StudioRunRequest) -> str:
    def render(items: list[object]) -> str:
        return " AND ".join(f"{item.field} {item.operator} {item.value}" for item in items)

    return (
        f"Entry: {render(req.strategy.entry_rules)}. Exit: {render(req.strategy.exit_rules)}. "
        f"Rebalance: {req.strategy.rebalance_frequency}. "
        f"Execution context: lot {req.execution.lot_size}, {req.execution.settlement}."
    )
