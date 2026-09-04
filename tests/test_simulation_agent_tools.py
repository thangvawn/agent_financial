from __future__ import annotations

import pytest

from risk_dashboard.modules.pro_lab.application.simulation_actions import SimulationActionService
from risk_dashboard.modules.pro_lab.application.simulation_tools import (
    SimCompareRunsTool,
    SimExecuteRunTool,
    SimGetRunTool,
    SimGetStrategySpecTool,
    SimGetTradeSummaryTool,
    SimProposeRunTool,
    SimValidateExperimentTool,
    get_simulation_tool_manifests,
)
from risk_dashboard.modules.pro_lab.domain.entities import (
    ProLabBlueprint,
    ProLabExperimentRun,
)
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    SqliteProLabBlueprintRepository,
    SqliteProLabExperimentRunRepository,
    reset_pro_lab_state,
)
from risk_dashboard.modules.pro_lab.schemas.simulation_agent import (
    CompareRunsQuery,
    ExecuteRunRequest,
    ReproducibilityManifest,
    RunQuery,
    StrategySpecQuery,
    TradeSummaryQuery,
)


@pytest.fixture(autouse=True)
def setup_db():
    reset_pro_lab_state()


def _make_sample_manifest(strategy_id: str = "strat_test", version: str = "1.0.0") -> ReproducibilityManifest:
    return ReproducibilityManifest(
        schema_version="1.0.0",
        strategy_id=strategy_id,
        strategy_version=version,
        dataset_source="cafef_eod",
        dataset_version="v2024.1",
        data_start="2022-01-01",
        data_end="2024-01-01",
        parameters={"lookback": 20},
        commission_pct=0.15,
        slippage_pct=0.2,
        benchmark="VNINDEX",
        engine_version="1.0.0",
        execution_timestamp="2026-09-02T12:00:00Z",
        metrics_calculation_version="1.0.0",
    )


def test_tool_manifests_registration():
    manifests = get_simulation_tool_manifests()
    assert len(manifests) == 7
    ids = [m.tool_id for m in manifests]
    assert "simulation.get_strategy_spec" in ids
    assert "simulation.validate_experiment" in ids
    assert "simulation.get_run" in ids
    assert "simulation.get_trade_summary" in ids
    assert "simulation.compare_runs" in ids
    assert "simulation.propose_run" in ids
    assert "simulation.execute_run" in ids


def test_sim_get_strategy_spec_tool():
    repo = SqliteProLabBlueprintRepository()
    bp = ProLabBlueprint(
        blueprint_id="bp_001",
        user_id="user_alice",
        name="Momentum VN30",
        objective="Trend following",
        asset_universe=("FPT", "MWG"),
        benchmark="VNINDEX",
        rebalance_frequency="weekly",
        risk_constraints="max_dd_10",
        assumptions_note=None,
    )
    repo.save(bp)

    tool = SimGetStrategySpecTool(blueprint_repo=repo)

    # Valid query
    res = tool.execute(StrategySpecQuery(blueprint_id="bp_001"), account_id="user_alice")
    assert res.blueprint_id == "bp_001"
    assert res.name == "Momentum VN30"

    # Cross-user deny
    with pytest.raises(PermissionError):
        tool.execute(StrategySpecQuery(blueprint_id="bp_001"), account_id="user_bob")

    # Non-existent
    with pytest.raises(ValueError):
        tool.execute(StrategySpecQuery(blueprint_id="bp_non_existent"), account_id="user_alice")


def test_sim_validate_experiment_tool():
    tool = SimValidateExperimentTool()

    # Valid manifest
    valid_m = _make_sample_manifest()
    res = tool.execute(valid_m)
    assert res.is_valid is True
    assert res.validation_status in ("passed", "warning")

    # Manifest with 0 commission and 0 slippage
    zero_m = ReproducibilityManifest(
        schema_version="1.0.0",
        strategy_id="strat_zero",
        strategy_version="1.0.0",
        dataset_source="cafef_eod",
        dataset_version="v2024.1",
        data_start="2022-01-01",
        data_end="2024-01-01",
        parameters={},
        commission_pct=0.0,
        slippage_pct=0.0,
        benchmark="VNINDEX",
        engine_version="1.0.0",
        execution_timestamp="2026-09-02T12:00:00Z",
        metrics_calculation_version="1.0.0",
    )
    res_zero = tool.execute(zero_m)
    assert res_zero.is_valid is True
    assert res_zero.validation_status == "warning"
    assert len(res_zero.warnings) >= 2


def test_sim_get_run_tool():
    repo = SqliteProLabExperimentRunRepository()
    run = ProLabExperimentRun(
        run_id="run_001",
        user_id="user_alice",
        experiment_id=None,
        blueprint_id="bp_001",
        provider_id="quant",
        command_id="backtest",
        status="completed",
        input_payload={"parameters": {"fast_ma": 10}},
        output_payload={"metrics": {"total_return_pct": 32.0, "sharpe_ratio": 1.5}},
        logs=(),
        progress_pct=100,
        safety_flags=(),
        data_freshness={},
    )
    repo.save(run)

    tool = SimGetRunTool(run_repo=repo)
    artifact = tool.execute(RunQuery(run_id="run_001"), account_id="user_alice")
    assert artifact.run_id == "run_001"
    assert artifact.metrics["total_return_pct"] == 32.0

    # Cross-user deny
    with pytest.raises(PermissionError):
        tool.execute(RunQuery(run_id="run_001"), account_id="user_bob")


def test_sim_get_trade_summary_tool():
    repo = SqliteProLabExperimentRunRepository()
    run = ProLabExperimentRun(
        run_id="run_trade_test",
        user_id="user_alice",
        experiment_id=None,
        blueprint_id="bp_001",
        provider_id="quant",
        command_id="backtest",
        status="completed",
        input_payload={},
        output_payload={
            "trades": [
                {"ticker": "FPT", "pnl_pct": 10.0},
                {"ticker": "MWG", "pnl_pct": -4.0},
                {"ticker": "TCB", "pnl_pct": 8.0},
            ]
        },
        logs=(),
        progress_pct=100,
        safety_flags=(),
        data_freshness={},
    )
    repo.save(run)

    tool = SimGetTradeSummaryTool(run_repo=repo)
    ts = tool.execute(TradeSummaryQuery(run_id="run_trade_test"), account_id="user_alice")
    assert ts.total_trades == 3
    assert ts.win_trades == 2
    assert ts.loss_trades == 1
    assert ts.win_rate_pct == 66.67
    assert ts.total_return_pct == 14.0


def test_sim_compare_runs_tool():
    repo = SqliteProLabExperimentRunRepository()
    run1 = ProLabExperimentRun(
        run_id="run_c1",
        user_id="user_alice",
        experiment_id=None,
        blueprint_id="bp_1",
        provider_id="quant",
        command_id="backtest",
        status="completed",
        input_payload={"manifest": {"metrics_calculation_version": "1.0.0", "strategy_version": "1.0.0"}},
        output_payload={"metrics": {"total_return_pct": 20.0, "sharpe_ratio": 1.2, "max_drawdown_pct": 10.0, "win_rate_pct": 50.0, "total_trades": 20}},
        logs=(),
        progress_pct=100,
        safety_flags=(),
        data_freshness={},
    )
    run2 = ProLabExperimentRun(
        run_id="run_c2",
        user_id="user_alice",
        experiment_id=None,
        blueprint_id="bp_1",
        provider_id="quant",
        command_id="backtest",
        status="completed",
        input_payload={"manifest": {"metrics_calculation_version": "1.0.0", "strategy_version": "1.1.0"}},
        output_payload={"metrics": {"total_return_pct": 35.0, "sharpe_ratio": 1.8, "max_drawdown_pct": 8.0, "win_rate_pct": 60.0, "total_trades": 25}},
        logs=(),
        progress_pct=100,
        safety_flags=(),
        data_freshness={},
    )
    repo.save(run1)
    repo.save(run2)

    tool = SimCompareRunsTool(run_repo=repo)
    comp = tool.execute(CompareRunsQuery(run_ids=("run_c1", "run_c2")), account_id="user_alice")
    assert comp.is_compatible is True
    assert len(comp.runs) == 2
    assert comp.best_sharpe_run_id == "run_c2"


def test_sim_propose_and_execute_tool_flow():
    action_service = SimulationActionService()
    propose_tool = SimProposeRunTool(action_service=action_service)
    execute_tool = SimExecuteRunTool(action_service=action_service)

    manifest = _make_sample_manifest()
    proposal = propose_tool.execute(manifest, account_id="user_alice")
    assert proposal.proposal_id.startswith("prop_")
    assert proposal.requires_confirmation is True

    # Get proposal entity to fetch confirmation token
    prop_entity = action_service.proposal_repo.get(proposal_id=proposal.proposal_id)
    assert prop_entity is not None

    # Execute with correct token
    receipt = execute_tool.execute(
        ExecuteRunRequest(
            proposal_id=proposal.proposal_id,
            confirmation_token=prop_entity.confirmation_token,
            idempotency_key="idemp_tool_test_1",
        ),
        account_id="user_alice",
    )
    assert receipt.status == "executed"
    assert receipt.receipt_id.startswith("rcpt_")

