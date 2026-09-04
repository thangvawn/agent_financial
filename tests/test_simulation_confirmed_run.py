from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from risk_dashboard.modules.pro_lab.application.simulation_actions import SimulationActionService
from risk_dashboard.modules.pro_lab.domain.entities import SimulationActionProposalEntity
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    SqliteProLabExperimentRunRepository,
    SqliteSimulationActionProposalRepository,
    SqliteSimulationActionReceiptRepository,
    reset_pro_lab_state,
)
from risk_dashboard.modules.pro_lab.schemas.simulation_agent import ReproducibilityManifest


@pytest.fixture(autouse=True)
def setup_db():
    reset_pro_lab_state()


def _make_manifest() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        schema_version="1.0.0",
        strategy_id="strat_trend_v1",
        strategy_version="1.0.0",
        dataset_source="cafef_eod",
        dataset_version="v2024.1",
        data_start="2022-01-01",
        data_end="2024-01-01",
        parameters={"fast_ma": 10},
        commission_pct=0.15,
        slippage_pct=0.2,
        benchmark="VNINDEX",
        engine_version="1.0.0",
        execution_timestamp="2026-09-02T12:00:00Z",
        metrics_calculation_version="1.0.0",
    )


def test_valid_confirmed_run_flow():
    service = SimulationActionService()
    manifest = _make_manifest()

    # 1. Create Proposal
    proposal = service.create_proposal(account_id="user_alice", manifest=manifest)
    assert proposal.proposal_id.startswith("prop_")
    assert proposal.requires_confirmation is True

    # Retrieve internal entity to get confirmation token
    prop_entity = service.proposal_repo.get(proposal_id=proposal.proposal_id)
    assert prop_entity is not None
    token = prop_entity.confirmation_token

    # 2. Confirm and Execute
    receipt = service.confirm_and_execute(
        proposal_id=proposal.proposal_id,
        confirmation_token=token,
        idempotency_key="idemp_key_1",
        account_id="user_alice",
    )
    assert receipt.status == "executed"
    assert receipt.receipt_id.startswith("rcpt_")
    assert receipt.run_artifact_id == f"art_{proposal.run_id}"

    # Verify run was saved in experiment runs repo
    run = service.run_repo.get(run_id=proposal.run_id)
    assert run is not None
    assert run.user_id == "user_alice"
    assert run.output_payload["metrics"]["total_return_pct"] == 28.5


def test_idempotency_deduplication():
    service = SimulationActionService()
    manifest = _make_manifest()

    proposal = service.create_proposal(account_id="user_alice", manifest=manifest)
    prop_entity = service.proposal_repo.get(proposal_id=proposal.proposal_id)
    assert prop_entity is not None
    token = prop_entity.confirmation_token

    # First execution
    receipt1 = service.confirm_and_execute(
        proposal_id=proposal.proposal_id,
        confirmation_token=token,
        idempotency_key="same_idemp_key",
        account_id="user_alice",
    )

    # Second execution with exact same idempotency_key
    receipt2 = service.confirm_and_execute(
        proposal_id=proposal.proposal_id,
        confirmation_token=token,
        idempotency_key="same_idemp_key",
        account_id="user_alice",
    )

    # Must return exact same receipt and NOT generate second run
    assert receipt1.receipt_id == receipt2.receipt_id
    assert receipt1.executed_at == receipt2.executed_at


def test_expired_proposal_rejection():
    service = SimulationActionService()
    manifest = _make_manifest()

    now = datetime.now(timezone.utc)
    expired_time = (now - timedelta(minutes=5)).isoformat()

    # Manually insert expired proposal
    prop_entity = SimulationActionProposalEntity(
        proposal_id="prop_expired_1",
        account_id="user_alice",
        run_id="simrun_exp_1",
        manifest_json=manifest.model_dump_json(),
        status="pending",
        confirmation_token="tok_valid_token",
        idempotency_key=None,
        expires_at=expired_time,
        created_at=(now - timedelta(minutes=20)).isoformat(),
    )
    service.proposal_repo.save(prop_entity)

    with pytest.raises(ValueError, match="Proposal đã hết hạn xác nhận"):
        service.confirm_and_execute(
            proposal_id="prop_expired_1",
            confirmation_token="tok_valid_token",
            idempotency_key="idemp_exp",
            account_id="user_alice",
        )

    # Proposal status updated to expired
    updated = service.proposal_repo.get(proposal_id="prop_expired_1")
    assert updated is not None
    assert updated.status == "expired"


def test_cross_user_confirmation_rejection():
    service = SimulationActionService()
    manifest = _make_manifest()

    proposal = service.create_proposal(account_id="user_alice", manifest=manifest)
    prop_entity = service.proposal_repo.get(proposal_id=proposal.proposal_id)
    assert prop_entity is not None

    with pytest.raises(PermissionError, match="Từ chối thực thi"):
        service.confirm_and_execute(
            proposal_id=proposal.proposal_id,
            confirmation_token=prop_entity.confirmation_token,
            idempotency_key="idemp_cross",
            account_id="user_bob",  # Cross-user attempt
        )


def test_invalid_token_rejection():
    service = SimulationActionService()
    manifest = _make_manifest()

    proposal = service.create_proposal(account_id="user_alice", manifest=manifest)

    with pytest.raises(ValueError, match="Token xác nhận không hợp lệ"):
        service.confirm_and_execute(
            proposal_id=proposal.proposal_id,
            confirmation_token="tok_wrong_token",
            idempotency_key="idemp_bad_token",
            account_id="user_alice",
        )


def test_reject_proposal():
    service = SimulationActionService()
    manifest = _make_manifest()

    proposal = service.create_proposal(account_id="user_alice", manifest=manifest)
    ok = service.reject_proposal(proposal_id=proposal.proposal_id, account_id="user_alice")
    assert ok is True

    # Try executing rejected proposal
    prop_entity = service.proposal_repo.get(proposal_id=proposal.proposal_id)
    assert prop_entity is not None
    assert prop_entity.status == "rejected"

    with pytest.raises(ValueError, match="Proposal ở trạng thái không thể thực thi"):
        service.confirm_and_execute(
            proposal_id=proposal.proposal_id,
            confirmation_token=prop_entity.confirmation_token,
            idempotency_key="idemp_rejected",
            account_id="user_alice",
        )

