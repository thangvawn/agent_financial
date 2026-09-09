"""Public REST API endpoints for agentic_core."""
from __future__ import annotations

from datetime import datetime, timezone
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from risk_dashboard.modules.agentic_core.application.action_service import ActionExecutionError, ActionService
from risk_dashboard.modules.agentic_core.application.artifact_service import ArtifactService, ArtifactTransitionError
from risk_dashboard.modules.agentic_core.application.graph import GraphResult, run_graph
from risk_dashboard.modules.agentic_core.application.kill_switch import (
    KillSwitchActiveError,
    assert_agentic_available,
    is_kill_switch_active,
)
from risk_dashboard.modules.agentic_core.application.memory_service import MemoryService
from risk_dashboard.modules.agentic_core.application.skill_router import SkillRouter
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
from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun, AgentStep, ToolCallRecord
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
    try:
        assert_agentic_available()
    except KillSwitchActiveError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc

    run_id = f"run_{uuid.uuid4().hex}"
    now_iso = datetime.now(timezone.utc).isoformat()

    tool = SkillRouter.resolve_tool(surface=request.surface, operation=request.operation)
    required_caps = SkillRouter.get_required_capabilities(tool)
    allowed_caps = tuple(set(("quant:read", *required_caps)))

    envelope = TrustedExecutionEnvelope(
        run_id=run_id,
        correlation_id=run_id,
        idempotency_key=run_id,
        account_id=principal.account_id,
        scopes=tuple(principal.scopes),
        surface=request.surface,
        resource_refs=tuple(request.resource_refs),
        locale=request.locale,
        allowed_capabilities=allowed_caps,
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

            # Persist step-level trace
            trace_nodes = result.get("trace", ())
            for idx, node_name in enumerate(trace_nodes):
                step_record = AgentStep(
                    schema_version="1.0.0",
                    step_id=f"step_{run_id}_{idx}",
                    run_id=run_id,
                    step_index=idx,
                    agent_id="supervisor",
                    node_name=node_name,
                    status="completed",
                    input_payload={},
                    output_payload={"code": result.get("code")} if node_name == "recovery" else {},
                    started_at=now_iso,
                    completed_at=completed_iso,
                )
                _run_repo.save_step(conn, step_record)

            if result.get("tool_calls_used", 0) > 0:
                tool_name = (
                    tool.manifest.tool_id
                    if hasattr(tool, "manifest") and tool.manifest is not None
                    else getattr(tool, "name", "unknown_tool")
                )
                tool_call = ToolCallRecord(
                    schema_version="1.0.0",
                    tool_call_id=f"tc_{run_id}_0",
                    run_id=run_id,
                    account_id=principal.account_id,
                    tool_name=tool_name,
                    input_hash="hash_placeholder",
                    status="success" if result.get("evidence") else "failed",
                    evidence=result.get("evidence") or {},
                    latency_ms=10,
                    created_at=completed_iso,
                )
                _run_repo.save_tool_call(conn, tool_call)

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


@router.get("/runs/{run_id}/trace")
def get_run_trace(
    run_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    """Get step-by-step trace and execution timeline for a run."""
    _check_auth(principal)

    with open_app_state_db() as conn:
        run = _run_repo.get(conn, run_id=run_id, account_id=principal.account_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

        steps = _run_repo.list_steps(conn, run_id=run_id)
        tool_calls = _run_repo.list_tool_calls(conn, run_id=run_id, account_id=principal.account_id)

    return {
        "run_id": run.run_id,
        "status": run.status,
        "surface": run.surface,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
        "steps": [s.model_dump(mode="json") for s in steps],
        "tool_calls": [tc.model_dump(mode="json") for tc in tool_calls],
        "timeline": [s.node_name for s in steps],
    }


_artifact_service = ArtifactService()
_action_service = ActionService()


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


@router.post("/artifacts/{artifact_id}:review", response_model=AgentArtifact)
def review_artifact(
    artifact_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> AgentArtifact:
    """Submit artifact for review (moves from draft to reviewed)."""
    _check_auth(principal)
    try:
        return _artifact_service.submit_for_review(artifact_id=artifact_id, account_id=principal.account_id)
    except ArtifactTransitionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/artifacts/{artifact_id}:accept", response_model=AgentArtifact)
def accept_artifact(
    artifact_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> AgentArtifact:
    """Accept reviewed artifact."""
    _check_auth(principal)
    try:
        return _artifact_service.accept(artifact_id=artifact_id, account_id=principal.account_id)
    except ArtifactTransitionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/artifacts/{artifact_id}:export")
def export_artifact(
    artifact_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    """Export reviewed/accepted artifact."""
    _check_auth(principal)
    try:
        return _artifact_service.export(artifact_id=artifact_id, account_id=principal.account_id)
    except ArtifactTransitionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/action-proposals/{proposal_id}:confirm")
def confirm_action_proposal(
    proposal_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, str]:
    """Confirm write action with idempotency, expiry, and forbidden checks."""
    _check_auth(principal)
    try:
        receipt = _action_service.confirm(proposal_id=proposal_id, account_id=principal.account_id)
        return {"status": "confirmed", "receipt_id": receipt.receipt_id}
    except ActionExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/action-proposals/{proposal_id}:reject")
def reject_action_proposal(
    proposal_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, str]:
    """Reject write action."""
    _check_auth(principal)
    try:
        receipt = _action_service.reject(proposal_id=proposal_id, account_id=principal.account_id)
        return {"status": "rejected", "receipt_id": receipt.receipt_id}
    except ActionExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc



class EditMemoryRequest(BaseModel):
    content: str = Field(min_length=1)


_memory_service = MemoryService()


@router.get("/memories")
def list_user_memories(
    memory_type: str | None = None,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> list[dict[str, Any]]:
    """List memory items for current user."""
    _check_auth(principal)
    memories = _memory_service.list_memories(account_id=principal.account_id, memory_type=memory_type)
    return [m.model_dump(mode="json") for m in memories]


@router.patch("/memories/{memory_id}")
def edit_user_memory(
    memory_id: str,
    payload: EditMemoryRequest,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    """Edit memory item content."""
    _check_auth(principal)
    updated = _memory_service.edit_memory(
        account_id=principal.account_id,
        memory_id=memory_id,
        new_content=payload.content,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found or edit rejected.")
    return updated.model_dump(mode="json")


@router.delete("/memories/{memory_id}")
def delete_user_memory(
    memory_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, bool]:
    """Delete a memory item for current user."""
    _check_auth(principal)
    deleted = _memory_service.forget_memory(account_id=principal.account_id, memory_id=memory_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")
    return {"deleted": True}


@router.get("/memories:export")
def export_user_memories(
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    """Export all memory items for current user."""
    _check_auth(principal)
    return _memory_service.export_memories(account_id=principal.account_id)


def clear_run_store() -> None:
    """Test utility to clear agentic state."""
    with open_app_state_db() as conn:
        conn.execute("DELETE FROM agentic_runs")
        conn.execute("DELETE FROM agentic_artifacts")
        conn.execute("DELETE FROM agentic_action_proposals")
        conn.execute("DELETE FROM agentic_action_receipts")
        conn.execute("DELETE FROM agentic_memory_proposals")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agentic_memory_items'")
        if cursor.fetchone() is not None:
            conn.execute("DELETE FROM agentic_memory_items")

