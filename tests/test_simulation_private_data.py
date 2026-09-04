from __future__ import annotations

import pytest

from risk_dashboard.modules.pro_lab.application.simulation_actions import SimulationActionService
from risk_dashboard.modules.pro_lab.application.simulation_tools import (
    SimGetRunTool,
    SimGetStrategySpecTool,
    SimGetTradeSummaryTool,
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
    ReproducibilityManifest,
    RunQuery,
    StrategySpecQuery,
    TradeSummaryQuery,
)


@pytest.fixture(autouse=True)
def setup_db():
    reset_pro_lab_state()


def test_private_spec_cross_account_isolation():
    bp_repo = SqliteProLabBlueprintRepository()
    bp = ProLabBlueprint(
        blueprint_id="bp_private_1",
        user_id="user_alice",
        name="Private Alpha",
        objective="Secret strategy",
        asset_universe=("FPT",),
        benchmark="VNINDEX",
        rebalance_frequency="daily",
        risk_constraints="none",
        assumptions_note=None,
    )
    bp_repo.save(bp)

    tool = SimGetStrategySpecTool(blueprint_repo=bp_repo)

    # Owner can access
    spec = tool.execute(StrategySpecQuery(blueprint_id="bp_private_1"), account_id="user_alice")
    assert spec.name == "Private Alpha"

    # Other account cannot access
    with pytest.raises(PermissionError, match="Từ chối truy cập"):
        tool.execute(StrategySpecQuery(blueprint_id="bp_private_1"), account_id="user_attacker")


def test_private_run_cross_account_isolation():
    run_repo = SqliteProLabExperimentRunRepository()
    run = ProLabExperimentRun(
        run_id="run_private_1",
        user_id="user_alice",
        experiment_id=None,
        blueprint_id="bp_private_1",
        provider_id="quant",
        command_id="backtest",
        status="completed",
        input_payload={},
        output_payload={"metrics": {"total_return_pct": 50.0}, "trades": []},
        logs=(),
        progress_pct=100,
        safety_flags=(),
        data_freshness={},
    )
    run_repo.save(run)

    get_run_tool = SimGetRunTool(run_repo=run_repo)
    get_trade_tool = SimGetTradeSummaryTool(run_repo=run_repo)

    # Owner can access
    artifact = get_run_tool.execute(RunQuery(run_id="run_private_1"), account_id="user_alice")
    assert artifact.run_id == "run_private_1"

    # Attacker denied for get_run
    with pytest.raises(PermissionError):
        get_run_tool.execute(RunQuery(run_id="run_private_1"), account_id="user_attacker")

    # Attacker denied for trade summary
    with pytest.raises(PermissionError):
        get_trade_tool.execute(TradeSummaryQuery(run_id="run_private_1"), account_id="user_attacker")


def test_private_proposal_cross_account_isolation():
    service = SimulationActionService()
    manifest = ReproducibilityManifest(
        schema_version="1.0.0",
        strategy_id="strat_private",
        strategy_version="1.0.0",
        dataset_source="cafef_eod",
        dataset_version="v2024.1",
        data_start="2022-01-01",
        data_end="2024-01-01",
        parameters={},
        commission_pct=0.15,
        slippage_pct=0.2,
        benchmark="VNINDEX",
        engine_version="1.0.0",
        execution_timestamp="2026-09-02T12:00:00Z",
        metrics_calculation_version="1.0.0",
    )

    proposal = service.create_proposal(account_id="user_alice", manifest=manifest)

    # Owner can get proposal
    prop_out = service.get_proposal(proposal_id=proposal.proposal_id, account_id="user_alice")
    assert prop_out is not None

    # Other user denied get proposal
    with pytest.raises(PermissionError):
        service.get_proposal(proposal_id=proposal.proposal_id, account_id="user_attacker")

