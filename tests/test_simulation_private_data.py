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


# ==============================================================================
# HTTP Layer IDOR Mitigation Tests (G3: Enforce 404, No 403 Account Oracle)
# ==============================================================================
def test_http_idor_user_b_cannot_access_user_a_proposal_returns_404():
    """G3: User B requesting User A's proposal via HTTP MUST return 404 (not 403)."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from risk_dashboard.modules.auth.application.dependencies import resolve_principal
    from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
    from risk_dashboard.modules.pro_lab.api.agent_router import router as simulation_agent_router

    app = FastAPI()
    app.include_router(simulation_agent_router)

    current_account = "user_alice"

    def mock_principal() -> AuthPrincipal:
        return AuthPrincipal(
            account_id=current_account,
            session_id=f"sess_{current_account}",
            assurance="recent_auth",
            scopes=(
                "pro_lab:strategy:read",
                "pro_lab:experiment:read",
                "pro_lab:run:read",
                "pro_lab:run:propose",
                "pro_lab:run:execute",
            ),
            consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
            resolved_at="2026-09-02T12:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = mock_principal
    client = TestClient(app)

    # 1. User A creates proposal
    manifest = ReproducibilityManifest(
        schema_version="1.0.0",
        strategy_id="strat_alice",
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
    prop_res = client.post("/proposals", json={"manifest": manifest.model_dump(mode="json"), "estimated_cost": 0.05})
    assert prop_res.status_code == 201
    prop_id = prop_res.json()["proposal_id"]

    # 2. User A can read proposal -> 200
    assert client.get(f"/proposals/{prop_id}").status_code == 200

    # 3. User B attempts to read User A's proposal -> MUST return 404 (not 403)
    current_account = "user_bob"
    res_idor = client.get(f"/proposals/{prop_id}")
    assert res_idor.status_code == 404, f"Expected 404 Not Found, got {res_idor.status_code}"


def test_http_idor_user_b_cannot_execute_user_a_proposal_returns_404():
    """G3: User B executing User A's proposal MUST return 404."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from risk_dashboard.modules.auth.application.dependencies import resolve_principal
    from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
    from risk_dashboard.modules.pro_lab.api.agent_router import router as simulation_agent_router
    from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
        SqliteSimulationActionProposalRepository,
    )

    app = FastAPI()
    app.include_router(simulation_agent_router)

    current_account = "user_alice"

    def mock_principal() -> AuthPrincipal:
        return AuthPrincipal(
            account_id=current_account,
            session_id=f"sess_{current_account}",
            assurance="recent_auth",
            scopes=(
                "pro_lab:run:propose",
                "pro_lab:run:execute",
            ),
            consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
            resolved_at="2026-09-02T12:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = mock_principal
    client = TestClient(app)

    # 1. User A creates proposal
    manifest = ReproducibilityManifest(
        schema_version="1.0.0",
        strategy_id="strat_alice_exec",
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
    prop_res = client.post("/proposals", json={"manifest": manifest.model_dump(mode="json"), "estimated_cost": 0.05})
    assert prop_res.status_code == 201
    prop_id = prop_res.json()["proposal_id"]

    entity = SqliteSimulationActionProposalRepository().get(proposal_id=prop_id)
    token = entity.confirmation_token

    # 2. User B attempts to execute User A's proposal -> MUST return 404
    current_account = "user_bob"
    exec_res = client.post(
        "/execute",
        json={
            "proposal_id": prop_id,
            "confirmation_token": token,
            "idempotency_key": "idem_bob_steal",
        },
    )
    assert exec_res.status_code == 404, f"Expected 404 Not Found, got {exec_res.status_code}"


def test_http_idor_user_b_cannot_access_user_a_run_returns_404():
    """G3: User B accessing User A's simulation run via GET /runs/{run_id} MUST return 404."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from risk_dashboard.modules.auth.application.dependencies import resolve_principal
    from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
    from risk_dashboard.modules.pro_lab.api.agent_router import router as simulation_agent_router

    app = FastAPI()
    app.include_router(simulation_agent_router)

    current_account = "user_alice"

    def mock_principal() -> AuthPrincipal:
        return AuthPrincipal(
            account_id=current_account,
            session_id=f"sess_{current_account}",
            assurance="recent_auth",
            scopes=("pro_lab:run:read",),
            consent=ConsentSnapshot(memory=True, analytics=True, policy_version="1.0.0"),
            resolved_at="2026-09-02T12:00:00Z",
        )

    app.dependency_overrides[resolve_principal] = mock_principal
    client = TestClient(app)

    # Save User A's run
    run_repo = SqliteProLabExperimentRunRepository()
    run = ProLabExperimentRun(
        run_id="run_idor_test_1",
        user_id="user_alice",
        experiment_id=None,
        blueprint_id="bp_alice_1",
        provider_id="quant",
        command_id="backtest",
        status="completed",
        input_payload={},
        output_payload={"metrics": {"sharpe": 1.5}},
        logs=(),
        progress_pct=100,
        safety_flags=(),
        data_freshness={},
    )
    run_repo.save(run)

    # User A accesses -> 200
    assert client.get("/runs/run_idor_test_1").status_code == 200

    # User B accesses -> 404
    current_account = "user_bob"
    res_b = client.get("/runs/run_idor_test_1")
    assert res_b.status_code == 404, f"Expected 404 Not Found, got {res_b.status_code}"

