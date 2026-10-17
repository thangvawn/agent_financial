"""Public REST API endpoints for agentic_core."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from risk_dashboard.modules.agentic_core.application.action_service import ActionExecutionError, ActionService
from risk_dashboard.modules.agentic_core.application.artifact_service import ArtifactService, ArtifactTransitionError
from risk_dashboard.modules.agentic_core.application.graph import run_graph
from risk_dashboard.modules.agentic_core.application.kill_switch import KillSwitchActiveError
from risk_dashboard.modules.agentic_core.application.memory_service import MemoryService
from risk_dashboard.modules.agentic_core.application.run_service import IdempotencyConflictError, RunService
from risk_dashboard.modules.agentic_core.infrastructure.repositories import AgenticActionRepository, AgenticArtifactRepository
from risk_dashboard.modules.agentic_core.schemas.artifact import AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.requests import AgentRunRequestV1, AgentRunResponseV1, EditMemoryRequest
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.platform.database import open_app_state_db

logger = logging.getLogger(__name__)

router = APIRouter()
_run_service, _artifact_service, _action_service = RunService(), ArtifactService(), ActionService()
_memory_service, _artifact_repo, _action_repo = MemoryService(), AgenticArtifactRepository(), AgenticActionRepository()

def _check_auth(principal: AuthPrincipal) -> None:
    if not principal.account_id or principal.is_anonymous:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

def _check_scope(principal: AuthPrincipal, required_scope: str) -> None:
    if required_scope not in principal.scopes and "*" not in principal.scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied: Missing required scope '{required_scope}'.")

@router.post("/runs", response_model=AgentRunResponseV1)
async def create_agentic_run(request: AgentRunRequestV1, principal: AuthPrincipal = Depends(resolve_principal)) -> AgentRunResponseV1:
    _check_auth(principal)
    try:
        return await _run_service.create_and_execute_run(request=request, principal=principal, run_graph_fn=run_graph)
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except KillSwitchActiveError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error running graph", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to execute agent run.") from exc

@router.get("/runs/{run_id}", response_model=AgentRunResponseV1)
def get_agentic_run(run_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> AgentRunResponseV1:
    _check_auth(principal)
    if (run := _run_service.get_run(run_id=run_id, account_id=principal.account_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    return run

@router.post("/runs/{run_id}:cancel")
def cancel_agentic_run(run_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, str]:
    _check_auth(principal)
    if (res := _run_service.cancel_run(run_id=run_id, account_id=principal.account_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    return res

@router.get("/runs/{run_id}/trace")
def get_run_trace(run_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, Any]:
    _check_auth(principal)
    if (trace := _run_service.get_run_trace(run_id=run_id, account_id=principal.account_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    return trace

@router.get("/artifacts/{artifact_id}", response_model=AgentArtifact)
def get_artifact(artifact_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> AgentArtifact:
    _check_auth(principal)
    with open_app_state_db() as conn:
        if (artifact := _artifact_repo.get(conn, artifact_id=artifact_id, account_id=principal.account_id)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found.")
        return artifact

@router.post("/artifacts/{artifact_id}:review", response_model=AgentArtifact)
def review_artifact(artifact_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> AgentArtifact:
    _check_auth(principal)
    try:
        return _artifact_service.submit_for_review(artifact_id=artifact_id, account_id=principal.account_id)
    except ArtifactTransitionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

@router.post("/artifacts/{artifact_id}:accept", response_model=AgentArtifact)
def accept_artifact(artifact_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> AgentArtifact:
    _check_auth(principal)
    try:
        return _artifact_service.accept(artifact_id=artifact_id, account_id=principal.account_id)
    except ArtifactTransitionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

@router.post("/artifacts/{artifact_id}:export")
def export_artifact(artifact_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, Any]:
    _check_auth(principal)
    try:
        return _artifact_service.export(artifact_id=artifact_id, account_id=principal.account_id)
    except ArtifactTransitionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

@router.post("/action-proposals/{proposal_id}:confirm")
def confirm_action_proposal(proposal_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, str]:
    _check_auth(principal)
    try:
        receipt = _action_service.confirm(proposal_id=proposal_id, account_id=principal.account_id)
        return {"status": "confirmed", "receipt_id": receipt.receipt_id}
    except ActionExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

@router.post("/action-proposals/{proposal_id}:reject")
def reject_action_proposal(proposal_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, str]:
    _check_auth(principal)
    try:
        receipt = _action_service.reject(proposal_id=proposal_id, account_id=principal.account_id)
        return {"status": "rejected", "receipt_id": receipt.receipt_id}
    except ActionExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

@router.get("/memories")
def list_user_memories(memory_type: str | None = None, principal: AuthPrincipal = Depends(resolve_principal)) -> list[dict[str, Any]]:
    _check_auth(principal)
    return [m.model_dump(mode="json") for m in _memory_service.list_memories(account_id=principal.account_id, memory_type=memory_type)]

@router.patch("/memories/{memory_id}")
def edit_user_memory(memory_id: str, payload: EditMemoryRequest, principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, Any]:
    _check_auth(principal)
    if (updated := _memory_service.edit_memory(account_id=principal.account_id, memory_id=memory_id, new_content=payload.content)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found or edit rejected.")
    return updated.model_dump(mode="json")

@router.delete("/memories/{memory_id}")
def delete_user_memory(memory_id: str, principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, bool]:
    _check_auth(principal)
    if not _memory_service.forget_memory(account_id=principal.account_id, memory_id=memory_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    return {"deleted": True}

@router.get("/memories:export")
def export_user_memories(principal: AuthPrincipal = Depends(resolve_principal)) -> dict[str, Any]:
    _check_auth(principal)
    return _memory_service.export_memories(account_id=principal.account_id)

def clear_run_store() -> None:
    """Test utility to clear agentic state."""
    tables = ("agentic_runs", "agentic_artifacts", "agentic_action_proposals", "agentic_action_receipts", "agentic_memory_proposals", "agentic_steps", "agentic_tool_calls", "agentic_memory_items")
    with open_app_state_db() as conn:
        for tbl in tables:
            conn.execute(f"DELETE FROM {tbl}")
