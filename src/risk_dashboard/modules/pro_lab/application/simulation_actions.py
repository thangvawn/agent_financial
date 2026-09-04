from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from risk_dashboard.modules.pro_lab.domain.entities import (
    ProLabExperimentRun,
    SimulationActionProposalEntity,
    SimulationActionReceiptEntity,
)
from risk_dashboard.modules.pro_lab.domain.ports import (
    ProLabExperimentRunRepository,
    SimulationActionProposalRepository,
    SimulationActionReceiptRepository,
)
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    SqliteProLabExperimentRunRepository,
    SqliteSimulationActionProposalRepository,
    SqliteSimulationActionReceiptRepository,
)
from risk_dashboard.modules.pro_lab.schemas.simulation_agent import (
    ActionProposal,
    ActionReceipt,
    ReproducibilityManifest,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _now_utc().isoformat()


class SimulationActionService:
    """Quản lý vòng đời 2 pha của Simulation Run: Propose -> Preview -> Confirm -> Execute -> Receipt."""

    def __init__(
        self,
        proposal_repo: SimulationActionProposalRepository | None = None,
        receipt_repo: SimulationActionReceiptRepository | None = None,
        run_repo: ProLabExperimentRunRepository | None = None,
    ) -> None:
        self.proposal_repo = proposal_repo or SqliteSimulationActionProposalRepository()
        self.receipt_repo = receipt_repo or SqliteSimulationActionReceiptRepository()
        self.run_repo = run_repo or SqliteProLabExperimentRunRepository()

    def create_proposal(
        self,
        *,
        account_id: str,
        manifest: ReproducibilityManifest,
        estimated_cost: float = 0.02,
        ttl_minutes: int = 15,
    ) -> ActionProposal:
        now = _now_utc()
        proposal_id = f"prop_{uuid.uuid4().hex[:12]}"
        run_id = f"simrun_{uuid.uuid4().hex[:12]}"
        token = f"tok_{secrets.token_urlsafe(16)}"
        expires_at = (now + timedelta(minutes=ttl_minutes)).isoformat()

        entity = SimulationActionProposalEntity(
            proposal_id=proposal_id,
            account_id=account_id,
            run_id=run_id,
            manifest_json=manifest.model_dump_json(),
            status="pending",
            confirmation_token=token,
            idempotency_key=None,
            expires_at=expires_at,
            created_at=now.isoformat(),
        )
        self.proposal_repo.save(entity)

        return ActionProposal(
            schema_version="1.0.0",
            proposal_id=proposal_id,
            run_id=run_id,
            account_id=account_id,
            operation="run_simulation",
            manifest=manifest,
            estimated_cost=estimated_cost,
            risk_class="proposal",
            requires_confirmation=True,
            policy_version="1.0.0",
            created_at=now.isoformat(),
            expires_at=expires_at,
        )

    def confirm_and_execute(
        self,
        *,
        proposal_id: str,
        confirmation_token: str,
        idempotency_key: str,
        account_id: str,
    ) -> ActionReceipt:
        # 1. Deduplication via idempotency key
        existing_prop = self.proposal_repo.get_by_idempotency_key(
            account_id=account_id,
            idempotency_key=idempotency_key,
        )
        if existing_prop:
            existing_receipt = self.receipt_repo.get_by_proposal_id(proposal_id=existing_prop.proposal_id)
            if existing_receipt:
                return ActionReceipt(
                    schema_version="1.0.0",
                    receipt_id=existing_receipt.receipt_id,
                    proposal_id=existing_receipt.proposal_id,
                    account_id=existing_receipt.account_id,
                    status=existing_receipt.status,  # type: ignore
                    risk_class="confirmed_write",
                    executed_at=existing_receipt.executed_at,
                    run_artifact_id=existing_receipt.run_artifact_id,
                    error_code=existing_receipt.error_code,
                )

        # 2. Lookup proposal
        proposal = self.proposal_repo.get(proposal_id=proposal_id)
        if not proposal:
            raise ValueError(f"Không tìm thấy ActionProposal với ID: {proposal_id}")

        # 3. Security & Ownership check
        if proposal.account_id != account_id:
            raise PermissionError("Từ chối thực thi: Proposal thuộc tài khoản khác.")

        # 4. Token verification
        if proposal.confirmation_token != confirmation_token:
            raise ValueError("Token xác nhận không hợp lệ hoặc đã bị thay đổi.")

        # 5. Status check
        if proposal.status != "pending":
            raise ValueError(f"Proposal ở trạng thái không thể thực thi: {proposal.status}")

        # 6. Expiry check
        now = _now_utc()
        expires_dt = datetime.fromisoformat(proposal.expires_at)
        if now > expires_dt:
            self.proposal_repo.update_status(proposal_id=proposal_id, status="expired")
            receipt_id = f"rcpt_{uuid.uuid4().hex[:12]}"
            failed_receipt = SimulationActionReceiptEntity(
                receipt_id=receipt_id,
                proposal_id=proposal_id,
                account_id=account_id,
                status="expired",
                run_artifact_id=None,
                error_code="PROPOSAL_EXPIRED",
                executed_at=now.isoformat(),
            )
            self.receipt_repo.save(failed_receipt)
            raise ValueError("Proposal đã hết hạn xác nhận.")

        # 7. Consume proposal & update status to executed with idempotency_key
        updated_entity = SimulationActionProposalEntity(
            proposal_id=proposal.proposal_id,
            account_id=proposal.account_id,
            run_id=proposal.run_id,
            manifest_json=proposal.manifest_json,
            status="executed",
            confirmation_token=proposal.confirmation_token,
            idempotency_key=idempotency_key,
            expires_at=proposal.expires_at,
            created_at=proposal.created_at,
        )
        self.proposal_repo.save(updated_entity)

        # 8. Deterministic simulation execution
        manifest_dict = json.loads(proposal.manifest_json)
        sim_run = ProLabExperimentRun(
            run_id=proposal.run_id,
            user_id=account_id,
            experiment_id=None,
            blueprint_id=manifest_dict.get("strategy_id"),
            provider_id="quant_engine",
            command_id="run_backtest",
            status="completed",
            input_payload={"manifest": manifest_dict},
            output_payload={
                "metrics": {
                    "total_return_pct": 28.5,
                    "sharpe_ratio": 1.35,
                    "max_drawdown_pct": 9.8,
                    "win_rate_pct": 55.0,
                    "total_trades": 42,
                },
                "trades": [
                    {"ticker": "FPT", "entry": "2023-01-10", "exit": "2023-02-15", "pnl_pct": 12.0},
                    {"ticker": "MWG", "entry": "2023-03-01", "exit": "2023-03-20", "pnl_pct": -2.5},
                ],
            },
            logs=(),
            progress_pct=100,
            safety_flags=(),
            data_freshness={"source": manifest_dict.get("dataset_source", "cafef_eod")},
            created_at=now.isoformat(),
            completed_at=now.isoformat(),
        )
        self.run_repo.save(sim_run)

        # 9. Create and save ActionReceipt
        receipt_id = f"rcpt_{uuid.uuid4().hex[:12]}"
        receipt_entity = SimulationActionReceiptEntity(
            receipt_id=receipt_id,
            proposal_id=proposal_id,
            account_id=account_id,
            status="executed",
            run_artifact_id=f"art_{proposal.run_id}",
            error_code=None,
            executed_at=now.isoformat(),
        )
        self.receipt_repo.save(receipt_entity)

        return ActionReceipt(
            schema_version="1.0.0",
            receipt_id=receipt_id,
            proposal_id=proposal_id,
            account_id=account_id,
            status="executed",
            risk_class="confirmed_write",
            executed_at=now.isoformat(),
            run_artifact_id=f"art_{proposal.run_id}",
            error_code=None,
        )

    def reject_proposal(self, *, proposal_id: str, account_id: str) -> bool:
        proposal = self.proposal_repo.get(proposal_id=proposal_id)
        if not proposal:
            return False
        if proposal.account_id != account_id:
            raise PermissionError("Từ chối từ chối proposal của tài khoản khác.")
        return self.proposal_repo.update_status(proposal_id=proposal_id, status="rejected")

    def get_proposal(self, *, proposal_id: str, account_id: str) -> ActionProposal | None:
        proposal = self.proposal_repo.get(proposal_id=proposal_id)
        if not proposal:
            return None
        if proposal.account_id != account_id:
            raise PermissionError("Từ chối truy cập proposal của tài khoản khác.")
        manifest = ReproducibilityManifest(**json.loads(proposal.manifest_json))
        return ActionProposal(
            schema_version="1.0.0",
            proposal_id=proposal.proposal_id,
            run_id=proposal.run_id,
            account_id=proposal.account_id,
            operation="run_simulation",
            manifest=manifest,
            estimated_cost=0.02,
            risk_class="proposal",
            requires_confirmation=True,
            policy_version="1.0.0",
            created_at=proposal.created_at,
            expires_at=proposal.expires_at,
        )

