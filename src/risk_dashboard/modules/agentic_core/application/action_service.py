from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from risk_dashboard.modules.agentic_core.domain.memory import MemoryItem
from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticActionRepository
from risk_dashboard.modules.agentic_core.infrastructure.sqlite_memory import SqliteMemoryRepository
from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal, ActionReceipt
from risk_dashboard.platform.database import open_app_state_db


class ActionExecutionError(Exception):
    def __init__(self, message: str, status_code: int = 400, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


FORBIDDEN_OPERATIONS = frozenset({
    "direct_db_drop",
    "modify_auth_roles",
    "bypass_review",
    "rm_rf",
    "shell_exec",
    "unrestricted_transfer",
})


class ActionService:
    def __init__(
        self,
        action_repo: AgenticActionRepository | None = None,
        memory_repo: SqliteMemoryRepository | None = None,
    ) -> None:
        self._action_repo = action_repo or AgenticActionRepository()
        self._memory_repo = memory_repo or SqliteMemoryRepository()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def confirm(self, *, proposal_id: str, account_id: str) -> ActionReceipt:
        with open_app_state_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            proposal = self._action_repo.get_proposal(conn, proposal_id=proposal_id, account_id=account_id)
            if proposal is None:
                raise ActionExecutionError("Action proposal not found.", status_code=404)

            # Check if previously rejected -> 409 Conflict
            receipt = self._action_repo.get_receipt(conn, proposal_id=proposal_id, account_id=account_id)
            if receipt is not None and receipt.status == "rejected":
                raise ActionExecutionError("Cannot confirm previously rejected proposal.", status_code=409)

            # Idempotency: if already confirmed/executed
            if receipt is not None:
                return receipt

            # Defense-in-depth: Block forbidden operations even if user confirmed
            if proposal.operation in FORBIDDEN_OPERATIONS or proposal.risk_class.lower() == "forbidden":
                now_iso = self._now_iso()
                blocked_receipt = ActionReceipt(
                    schema_version="1.0.0",
                    receipt_id=f"rcpt_{uuid.uuid4().hex}",
                    proposal_id=proposal_id,
                    account_id=account_id,
                    status="failed",
                    executed_at=now_iso,
                    error_code="FORBIDDEN_ACTION_BLOCKED",
                )
                self._action_repo.update_proposal_status(conn, proposal_id=proposal_id, account_id=account_id, status="blocked")
                self._action_repo.save_receipt(conn, blocked_receipt)
                conn.commit()
                raise ActionExecutionError(
                    "Execution of forbidden operation is blocked.",
                    status_code=403,
                    error_code="FORBIDDEN_ACTION_BLOCKED",
                )

            # Check expiration
            now_iso = self._now_iso()
            if proposal.expires_at < now_iso:
                raise ActionExecutionError("Action proposal has expired.", status_code=400)

            # Execute the actual operation side-effect within same transaction
            self._execute_side_effect(proposal, conn=conn)

            # Record success receipt
            receipt = ActionReceipt(
                schema_version="1.0.0",
                receipt_id=f"rcpt_{uuid.uuid4().hex}",
                proposal_id=proposal_id,
                account_id=account_id,
                status="executed",
                executed_at=now_iso,
                result_ref=proposal.target,
            )
            self._action_repo.update_proposal_status(conn, proposal_id=proposal_id, account_id=account_id, status="confirmed")
            self._action_repo.save_receipt(conn, receipt)
            conn.commit()
            return receipt

    def reject(self, *, proposal_id: str, account_id: str) -> ActionReceipt:
        with open_app_state_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            proposal = self._action_repo.get_proposal(conn, proposal_id=proposal_id, account_id=account_id)
            if proposal is None:
                raise ActionExecutionError("Action proposal not found.", status_code=404)

            receipt = self._action_repo.get_receipt(conn, proposal_id=proposal_id, account_id=account_id)
            if receipt is not None:
                if receipt.status == "executed":
                    raise ActionExecutionError("Cannot reject previously confirmed proposal.", status_code=409)
                return receipt  # Idempotent rejection

            now_iso = self._now_iso()
            self._action_repo.update_proposal_status(conn, proposal_id=proposal_id, account_id=account_id, status="rejected")
            receipt = ActionReceipt(
                schema_version="1.0.0",
                receipt_id=f"rcpt_{uuid.uuid4().hex}",
                proposal_id=proposal_id,
                account_id=account_id,
                status="rejected",
                executed_at=now_iso,
            )
            self._action_repo.save_receipt(conn, receipt)
            conn.commit()
            return receipt

    def _execute_side_effect(self, proposal: ActionProposal, conn: Any | None = None) -> None:
        """Execute real side-effects based on operation type.

        Known operations without side-effects (e.g. export_report) are no-ops.
        Truly unknown operations raise ActionExecutionError.
        """
        _NO_SIDE_EFFECT_OPS = frozenset({"export_report", "delete_chart", "update_preference_view"})
        op = proposal.operation.lower()
        if op == "save_preference":
            content = proposal.payload_preview.get("content") or proposal.payload_preview.get("preference") or "Saved preference"
            item = MemoryItem(
                memory_id=f"mem_{uuid.uuid4().hex}",
                account_id=proposal.account_id,
                run_id=proposal.run_id,
                memory_type="preference",
                content=str(content),
                provenance="user_stated",
                confidence=1.0,
                sensitivity="normal",
                created_at=self._now_iso(),
                updated_at=self._now_iso(),
            )
            self._memory_repo.save(item, conn=conn)
        elif op == "forget_memory":
            target_mem_id = proposal.payload_preview.get("memory_id") or proposal.target.resource_id
            if target_mem_id:
                self._memory_repo.delete(memory_id=target_mem_id, account_id=proposal.account_id, conn=conn)
        elif op in _NO_SIDE_EFFECT_OPS:
            pass  # Known operation, no side-effect needed
        else:
            raise ActionExecutionError(f"Unsupported operation: {op}", status_code=400)
