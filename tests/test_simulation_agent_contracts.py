from __future__ import annotations

import pytest
from pydantic import ValidationError

from risk_dashboard.modules.pro_lab.schemas.simulation_agent import (
    ActionProposal,
    ActionReceipt,
    CompareRunsQuery,
    ExecuteRunRequest,
    ExperimentValidation,
    ReproducibilityManifest,
    RunComparison,
    RunComparisonItem,
    RunQuery,
    SimulationRunArtifact,
    StrategySpec,
    StrategySpecQuery,
    TradeSummary,
    TradeSummaryQuery,
)


def _make_sample_manifest() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        schema_version="1.0.0",
        strategy_id="strat_donchian_breakout",
        strategy_version="1.0.0",
        dataset_source="cafef_eod",
        dataset_version="v2024.1",
        data_start="2022-01-01",
        data_end="2024-01-01",
        parameters={"lookback": 20, "atr_multiplier": 2.0},
        commission_pct=0.15,
        slippage_pct=0.2,
        benchmark="VNINDEX",
        random_seed=42,
        engine_version="1.0.0",
        execution_timestamp="2026-09-02T12:00:00Z",
        metrics_calculation_version="1.0.0",
        warnings=(),
        data_gaps=(),
    )


def test_reproducibility_manifest_frozen_and_valid():
    manifest = _make_sample_manifest()
    assert manifest.strategy_id == "strat_donchian_breakout"
    assert manifest.schema_version == "1.0.0"
    assert manifest.commission_pct == 0.15
    assert manifest.random_seed == 42

    with pytest.raises(ValidationError):
        manifest.commission_pct = 0.20  # Frozen immutability


def test_reproducibility_manifest_validation_error_on_missing_fields():
    with pytest.raises(ValidationError):
        ReproducibilityManifest(
            strategy_id="",  # Empty string rejected by min_length=1
            strategy_version="1.0.0",
            dataset_source="cafef_eod",
            dataset_version="v2024.1",
            data_start="2022-01-01",
            data_end="2024-01-01",
            commission_pct=-0.1,  # Negative rejected
            slippage_pct=0.2,
            benchmark="VNINDEX",
            engine_version="1.0.0",
            execution_timestamp="2026-09-02T12:00:00Z",
            metrics_calculation_version="1.0.0",
        )


def test_simulation_run_artifact_contract():
    manifest = _make_sample_manifest()
    artifact = SimulationRunArtifact(
        schema_version="1.0.0",
        artifact_id="art_12345",
        run_id="simrun_9999",
        account_id="acc_user1",
        status="completed",
        manifest=manifest,
        metrics={"total_return_pct": 25.5, "sharpe_ratio": 1.4},
        trade_summary={"total_trades": 30},
        source_refs=("pro_lab.experiment_runs",),
        limitations=("Paper backtest only",),
        created_at="2026-09-02T12:00:00Z",
        completed_at="2026-09-02T12:00:05Z",
    )
    assert artifact.artifact_id == "art_12345"
    assert artifact.status == "completed"
    assert artifact.metrics["sharpe_ratio"] == 1.4

    with pytest.raises(ValidationError):
        artifact.status = "failed"


def test_action_proposal_contract():
    manifest = _make_sample_manifest()
    proposal = ActionProposal(
        schema_version="1.0.0",
        proposal_id="prop_111",
        run_id="simrun_222",
        account_id="acc_user1",
        operation="run_simulation",
        manifest=manifest,
        estimated_cost=0.02,
        risk_class="proposal",
        requires_confirmation=True,
        policy_version="1.0.0",
        created_at="2026-09-02T12:00:00Z",
        expires_at="2026-09-02T12:15:00Z",
    )
    assert proposal.requires_confirmation is True
    assert proposal.risk_class == "proposal"

    with pytest.raises(ValidationError):
        proposal.estimated_cost = -1.0


def test_execute_run_request_contract():
    req = ExecuteRunRequest(
        schema_version="1.0.0",
        proposal_id="prop_111",
        confirmation_token="tok_secret",
        idempotency_key="idemp_123",
    )
    assert req.proposal_id == "prop_111"
    assert req.confirmation_token == "tok_secret"


def test_action_receipt_contract():
    receipt = ActionReceipt(
        schema_version="1.0.0",
        receipt_id="rcpt_555",
        proposal_id="prop_111",
        account_id="acc_user1",
        status="executed",
        risk_class="confirmed_write",
        executed_at="2026-09-02T12:01:00Z",
        run_artifact_id="art_12345",
    )
    assert receipt.status == "executed"
    assert receipt.risk_class == "confirmed_write"


def test_tool_query_and_output_contracts():
    q = StrategySpecQuery(blueprint_id="bp_123")
    assert q.blueprint_id == "bp_123"

    spec = StrategySpec(
        blueprint_id="bp_123",
        name="Breakout",
        objective="Trend",
        asset_universe=("FPT", "MWG"),
        benchmark="VNINDEX",
        rebalance_frequency="daily",
        risk_constraints="max_dd_15",
        created_at="2026-09-02T12:00:00Z",
        updated_at="2026-09-02T12:00:00Z",
    )
    assert len(spec.asset_universe) == 2

    val = ExperimentValidation(
        is_valid=True,
        missing_fields=(),
        warnings=("Low slippage",),
        validation_status="warning",
    )
    assert val.validation_status == "warning"

    ts = TradeSummary(
        run_id="simrun_1",
        total_trades=10,
        win_trades=6,
        loss_trades=4,
        win_rate_pct=60.0,
        profit_factor=1.8,
        max_drawdown_pct=8.5,
        total_return_pct=15.0,
        avg_trade_return_pct=1.5,
    )
    assert ts.win_rate_pct == 60.0

    comp = RunComparison(
        runs=(
            RunComparisonItem(
                run_id="simrun_1",
                strategy_id="strat_1",
                strategy_version="1.0.0",
                metrics_calculation_version="1.0.0",
                total_return_pct=15.0,
                sharpe_ratio=1.2,
                max_drawdown_pct=8.5,
                win_rate_pct=60.0,
                trade_count=10,
            ),
        ),
        is_compatible=True,
    )
    assert comp.is_compatible is True

