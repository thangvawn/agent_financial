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


# ==============================================================================
# HTTP Agent Router Contract Tests (G1, G4, G5)
# ==============================================================================
@pytest.fixture
def sim_client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from risk_dashboard.modules.auth.application.dependencies import resolve_principal
    from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
    from risk_dashboard.modules.pro_lab.api.agent_router import router as simulation_agent_router

    app = FastAPI()
    app.include_router(simulation_agent_router)

    def mock_principal() -> AuthPrincipal:
        return AuthPrincipal(
            account_id="user_test_sim",
            session_id="sess_sim_123",
            assurance="recent_auth",
            scopes=(
                "pro_lab:strategy:read",
                "pro_lab:experiment:read",
                "pro_lab:run:read",
                "pro_lab:trade_detail:read",
                "pro_lab:run:propose",
                "pro_lab:run:execute",
            ),
            consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
            resolved_at="2026-09-02T12:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = mock_principal
    return TestClient(app)


def test_http_list_simulation_tools(sim_client):
    res = sim_client.get("/tools")
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    tool_ids = [t["tool_id"] for t in data["tools"]]
    assert "simulation.validate_experiment" in tool_ids
    assert "simulation.propose_run" in tool_ids
    assert "simulation.execute_run" in tool_ids


def test_http_invoke_validate_experiment_tool(sim_client):
    manifest = _make_sample_manifest().model_dump(mode="json")
    res = sim_client.post(
        "/tools/simulation.validate_experiment:invoke",
        json={"input": manifest},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["tool_id"] == "simulation.validate_experiment"
    assert "output" in data
    assert "latency_ms" in data
    assert data["output"]["is_valid"] is True


def test_http_forbidden_broker_tool_rejected(sim_client):
    res = sim_client.post(
        "/tools/broker.place_order:invoke",
        json={"input": {}},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "FORBIDDEN_OPERATION"


def test_http_propose_and_execute_simulation_flow(sim_client):
    manifest = _make_sample_manifest().model_dump(mode="json")
    # 1. Create proposal
    prop_res = sim_client.post("/proposals", json={"manifest": manifest, "estimated_cost": 0.05})
    assert prop_res.status_code == 201
    prop_data = prop_res.json()
    proposal_id = prop_data["proposal_id"]
    assert proposal_id.startswith("prop_")
    assert prop_data["estimated_cost"] == 0.05

    # 2. Get proposal
    get_res = sim_client.get(f"/proposals/{proposal_id}")
    assert get_res.status_code == 200
    assert get_res.json()["proposal_id"] == proposal_id

    # 3. Lookup entity to get confirmation token for execution
    from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
        SqliteSimulationActionProposalRepository,
    )
    entity = SqliteSimulationActionProposalRepository().get(proposal_id=proposal_id)
    assert entity is not None
    token = entity.confirmation_token

    # 4. Execute confirmed run
    import uuid

    idem_key = f"idem_contract_{uuid.uuid4().hex[:8]}"
    exec_res = sim_client.post(
        "/execute",
        json={
            "proposal_id": proposal_id,
            "confirmation_token": token,
            "idempotency_key": idem_key,
        },
    )
    assert exec_res.status_code == 200
    receipt = exec_res.json()
    assert receipt["status"] == "executed"
    assert receipt["proposal_id"] == proposal_id

    # 5. Idempotent re-execution returns identical receipt
    exec_res2 = sim_client.post(
        "/execute",
        json={
            "proposal_id": proposal_id,
            "confirmation_token": token,
            "idempotency_key": idem_key,
        },
    )
    assert exec_res2.status_code == 200
    assert exec_res2.json()["receipt_id"] == receipt["receipt_id"]


def test_http_agent_run_grounding_gate(sim_client):
    # Valid run passes
    res_valid = sim_client.post("/runs", json={"skill_id": "simulation.result_critique.v1"})
    assert res_valid.status_code == 200
    data_valid = res_valid.json()
    assert data_valid["status"] == "completed"
    assert len(data_valid["citations"]) > 0

    # Unsupported claim triggers 422 GroundingFailed
    res_hallucinated = sim_client.post(
        "/runs",
        json={"skill_id": "simulation.result_critique.v1", "test_inject_unsupported_claim": True},
    )
    assert res_hallucinated.status_code == 422
    err_data = res_hallucinated.json()["detail"]
    assert err_data["error"] == "GROUNDING_FAILED"
    assert len(err_data["unsupported_claims"]) > 0

