"""Public REST API endpoints for agentic_core."""
from __future__ import annotations

from datetime import datetime, timezone
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from risk_dashboard.modules.agentic_core.application.graph import GraphResult, run_graph
from risk_dashboard.modules.agentic_core.domain.ports import ReadOnlyTool
from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.agentic_core.infrastructure.quant_tool import QuantRiskReadOnlyTool
from risk_dashboard.modules.agentic_core.infrastructure.repositories import (
    AgenticActionRepository,
    AgenticArtifactRepository,
    AgenticRunRepository,
)
from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal, ActionReceipt, AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.envelope import ExecutionBudget, ResourceRef, TrustedExecutionEnvelope
from risk_dashboard.modules.agentic_core.schemas.requests import AgentRunRequestV1, AgentRunResponseV1
from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.platform.ai_runtime.contracts import ModelTask
from risk_dashboard.platform.ai_runtime.factory import get_default_provider
from risk_dashboard.platform.ai_runtime.provider import LLMProvider
from risk_dashboard.platform.database import open_app_state_db

logger = logging.getLogger(__name__)

_run_repo = AgenticRunRepository()
_artifact_repo = AgenticArtifactRepository()
_action_repo = AgenticActionRepository()


def _check_auth(principal: AuthPrincipal) -> None:
    if not principal.account_id or principal.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )


def _check_scope(principal: AuthPrincipal, required_scope: str) -> None:
    if required_scope not in principal.scopes and "*" not in principal.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: Missing required scope '{required_scope}'.",
        )


router = APIRouter()


@router.post("/runs", response_model=AgentRunResponseV1)
async def create_agentic_run(
    request: AgentRunRequestV1,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> AgentRunResponseV1:
    """Create and execute agent run persisted in SQLite."""
    _check_auth(principal)

    run_id = f"run_{uuid.uuid4().hex}"
    now_iso = datetime.now(timezone.utc).isoformat()

    envelope = TrustedExecutionEnvelope(
        run_id=run_id,
        correlation_id=run_id,
        idempotency_key=run_id,
        account_id=principal.account_id,
        scopes=tuple(principal.scopes),
        surface=request.surface,
        resource_refs=tuple(request.resource_refs),
        locale=request.locale,
        allowed_capabilities=("quant:read",),
        policy_version="1.0.0",
        model_policy_version="1.0.0",
        consent=ConsentSnapshot(memory=True, analytics=True, consented_at=now_iso, policy_version="1.0"),
        created_at=now_iso,
    )

    task = ModelTask(
        task_id=f"task_{uuid.uuid4().hex}",
        task_type="agentic_read",
        system_instructions_ref="default",
        messages=(),
        correlation_id=run_id,
    )

    provider = get_default_provider()
    tool = QuantRiskReadOnlyTool()

    # Persist running state to SQLite (Iron Rule #1)
    with open_app_state_db() as conn:
        _run_repo.save(
            conn,
            AgentRun(
                run_id=run_id,
                account_id=principal.account_id,
                surface=request.surface,
                status="running",
                correlation_id=run_id,
                idempotency_key=run_id,
                created_at=now_iso,
                updated_at=now_iso,
            ),
        )

    try:
        result = await run_graph(envelope, task, provider, tool)
        status_code = "completed" if result.get("status") == "success" else "failed"

        artifact = AgentArtifact(
            artifact_id=f"art_{uuid.uuid4().hex}",
            artifact_type="text",
            domain="general",
            account_id=principal.account_id,
            authoring_run_id=run_id,
            created_at=now_iso,
        )

        completed_iso = datetime.now(timezone.utc).isoformat()
        with open_app_state_db() as conn:
            _artifact_repo.save(conn, artifact)
            _run_repo.save(
                conn,
                AgentRun(
                    run_id=run_id,
                    account_id=principal.account_id,
                    surface=request.surface,
                    status=status_code,
                    correlation_id=run_id,
                    idempotency_key=run_id,
                    result_payload={"result": result},
                    created_at=now_iso,
                    updated_at=completed_iso,
                ),
            )

        return AgentRunResponseV1(run_id=run_id, status=status_code, artifact=artifact)
    except Exception as exc:
        failed_iso = datetime.now(timezone.utc).isoformat()
        with open_app_state_db() as conn:
            _run_repo.save(
                conn,
                AgentRun(
                    run_id=run_id,
                    account_id=principal.account_id,
                    surface=request.surface,
                    status="failed",
                    correlation_id=run_id,
                    idempotency_key=run_id,
                    created_at=now_iso,
                    updated_at=failed_iso,
                ),
            )
        logger.error("Error running graph", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute agent run.",
        ) from exc


@router.get("/runs/{run_id}", response_model=AgentRunResponseV1)
def get_agentic_run(
    run_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> AgentRunResponseV1:
    """Get run status/result from SQLite."""
    _check_auth(principal)

    with open_app_state_db() as conn:
        run = _run_repo.get(conn, run_id=run_id, account_id=principal.account_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

        artifacts = _artifact_repo.list_by_run(conn, run_id=run_id, account_id=principal.account_id)
        artifact = artifacts[0] if artifacts else None

    return AgentRunResponseV1(
        run_id=run.run_id,
        status=run.status,
        artifact=artifact,
    )


@router.post("/runs/{run_id}:cancel")
def cancel_agentic_run(
    run_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, str]:
    """Cancel active run in SQLite."""
    _check_auth(principal)

    with open_app_state_db() as conn:
        run = _run_repo.get(conn, run_id=run_id, account_id=principal.account_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

        if run.status in ["running", "accepted"]:
            now_iso = datetime.now(timezone.utc).isoformat()
            _run_repo.save(
                conn,
                AgentRun(
                    run_id=run.run_id,
                    account_id=run.account_id,
                    surface=run.surface,
                    status="canceled",
                    correlation_id=run.correlation_id,
                    idempotency_key=run.idempotency_key,
                    created_at=run.created_at,
                    updated_at=now_iso,
                ),
            )

    return {"status": "canceled"}


@router.get("/artifacts/{artifact_id}", response_model=AgentArtifact)
def get_artifact(
    artifact_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> AgentArtifact:
    """Get artifact from SQLite."""
    _check_auth(principal)

    with open_app_state_db() as conn:
        artifact = _artifact_repo.get(conn, artifact_id=artifact_id, account_id=principal.account_id)
        if artifact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found.")
        return artifact


@router.post("/action-proposals/{proposal_id}:confirm")
def confirm_action_proposal(
    proposal_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, str]:
    """Confirm write action with idempotency and expiry checks."""
    _check_auth(principal)

    with open_app_state_db() as conn:
        proposal = _action_repo.get_proposal(conn, proposal_id=proposal_id, account_id=principal.account_id)
        if proposal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action proposal not found.")

        # Idempotency check: if receipt already exists, return existing receipt
        existing_receipt = _action_repo.get_receipt(conn, proposal_id=proposal_id, account_id=principal.account_id)
        if existing_receipt is not None:
            return {"status": "confirmed", "receipt_id": existing_receipt.receipt_id}

        # Check proposal expiry
        now_iso = datetime.now(timezone.utc).isoformat()
        if proposal.expires_at < now_iso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action proposal has expired.",
            )

        # Create immutable ActionReceipt
        receipt_id = f"rcpt_{uuid.uuid4().hex}"
        receipt = ActionReceipt(
            schema_version="1.0.0",
            receipt_id=receipt_id,
            proposal_id=proposal_id,
            account_id=principal.account_id,
            status="executed",
            executed_at=now_iso,
        )
        _action_repo.update_proposal_status(conn, proposal_id=proposal_id, account_id=principal.account_id, status="confirmed")
        _action_repo.save_receipt(conn, receipt)

    return {"status": "confirmed", "receipt_id": receipt_id}


@router.post("/action-proposals/{proposal_id}:reject")
def reject_action_proposal(
    proposal_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, str]:
    """Reject write action."""
    _check_auth(principal)

    with open_app_state_db() as conn:
        proposal = _action_repo.get_proposal(conn, proposal_id=proposal_id, account_id=principal.account_id)
        if proposal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action proposal not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        _action_repo.update_proposal_status(conn, proposal_id=proposal_id, account_id=principal.account_id, status="rejected")
        receipt = ActionReceipt(
            schema_version="1.0.0",
            receipt_id=f"rcpt_{uuid.uuid4().hex}",
            proposal_id=proposal_id,
            account_id=principal.account_id,
            status="rejected",
            executed_at=now_iso,
        )
        _action_repo.save_receipt(conn, receipt)

    return {"status": "rejected"}


def clear_run_store() -> None:
    """Test utility to clear agentic state."""
    with open_app_state_db() as conn:
        conn.execute("DELETE FROM agentic_runs")
        conn.execute("DELETE FROM agentic_artifacts")
        conn.execute("DELETE FROM agentic_action_proposals")
        conn.execute("DELETE FROM agentic_action_receipts")
        conn.execute("DELETE FROM agentic_memory_proposals")
