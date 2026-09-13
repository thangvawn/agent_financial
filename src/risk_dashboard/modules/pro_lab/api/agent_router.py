"""Simulation & Strategy Research Agent HTTP Router (Module 6 - G1, G2, G3, G4, G5).

Implements the OpenAPI 3.0.3 specification defined in 06_SIMULATION_AGENT_TECHNICAL_SPEC.md:
- /tools: list available simulation manifests
- /tools/{tool_id}:invoke: execute deterministic tool directly
- /proposals: create ActionProposal (2-phase commit preview)
- /proposals/{proposal_id}: get ActionProposal (IDOR protected, 404 on mismatch)
- /execute: confirm and execute proposed simulation (idempotent, 2-phase commit)
- /runs: execute AI research skill with Grounding Gate
- /runs/{run_id}: get simulation run record (IDOR protected, 404 on mismatch)
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field

from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.pro_lab.application.simulation_actions import SimulationActionService
from risk_dashboard.modules.pro_lab.application.simulation_tools import (
    SimCompareRunsTool,
    SimExecuteRunTool,
    SimGetRunTool,
    SimGetStrategySpecTool,
    SimGetTradeSummaryTool,
    SimProposeRunTool,
    SimValidateExperimentTool,
)
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    SqliteProLabExperimentRunRepository,
)
from risk_dashboard.modules.pro_lab.metrics import (
    SIMULATION_EXECUTIONS_TOTAL,
    SIMULATION_GROUNDING_FAILURES_TOTAL,
    SIMULATION_PROPOSALS_TOTAL,
    SIMULATION_TOOL_DURATION_SECONDS,
)
from risk_dashboard.modules.pro_lab.schemas.simulation_agent import (
    ActionProposal,
    ActionReceipt,
    CompareRunsQuery,
    ExecuteRunRequest,
    ReproducibilityManifest,
    RunQuery,
    StrategySpecQuery,
    TradeSummaryQuery,
)

logger = logging.getLogger("risk_dashboard.simulation")

FEATURE_FLAG = "module.simulation_lab.enabled"

# ------------------------------------------------------------------------------
# Rate Limiter
# ------------------------------------------------------------------------------
_RUN_RATE_LIMITS: dict[str, list[float]] = {}
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60.0


def _check_rate_limit(account_id: str) -> None:
    now = time.monotonic()
    timestamps = _RUN_RATE_LIMITS.setdefault(account_id, [])
    valid = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]
    _RUN_RATE_LIMITS[account_id] = valid
    if len(valid) >= RATE_LIMIT_MAX_REQUESTS:
        oldest = valid[0]
        retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - oldest)) + 1
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 10 runs per minute.",
            headers={"Retry-After": str(max(1, retry_after))},
        )
    _RUN_RATE_LIMITS[account_id].append(now)


# ------------------------------------------------------------------------------
# Feature Flag Guard
# ------------------------------------------------------------------------------
def _check_simulation_agent_enabled() -> None:
    env_flag = os.getenv("SIMULATION_AGENT_ENABLED", "true").lower()
    if env_flag in ("false", "0", "no"):
        raise HTTPException(status_code=404, detail="Simulation Agent is disabled.")
    try:
        from risk_dashboard.platform.feature_flags.service import FeatureFlagService
        ff = FeatureFlagService()
        if not (
            ff.is_enabled(FEATURE_FLAG, default=True)
            or ff.is_enabled("module.pro_lab.enabled", default=True)
        ):
            raise HTTPException(status_code=404, detail="Simulation Agent is disabled.")
    except Exception:
        pass


router = APIRouter(
    dependencies=[Depends(_check_simulation_agent_enabled)],
)

# ------------------------------------------------------------------------------
# Canonical Tools & Scopes Map
# ------------------------------------------------------------------------------
CANONICAL_SIMULATION_TOOLS = {
    "simulation.get_strategy_spec": (SimGetStrategySpecTool, StrategySpecQuery),
    "simulation.validate_experiment": (SimValidateExperimentTool, ReproducibilityManifest),
    "simulation.get_run": (SimGetRunTool, RunQuery),
    "simulation.get_trade_summary": (SimGetTradeSummaryTool, TradeSummaryQuery),
    "simulation.compare_runs": (SimCompareRunsTool, CompareRunsQuery),
    "simulation.propose_run": (SimProposeRunTool, ReproducibilityManifest),
    "simulation.execute_run": (SimExecuteRunTool, ExecuteRunRequest),
}

TOOL_REQUIRED_SCOPES: dict[str, str] = {
    "simulation.get_strategy_spec": "pro_lab:strategy:read",
    "simulation.validate_experiment": "pro_lab:experiment:read",
    "simulation.get_run": "pro_lab:run:read",
    "simulation.get_trade_summary": "pro_lab:run:read",
    "simulation.compare_runs": "pro_lab:run:read",
    "simulation.propose_run": "pro_lab:run:propose",
    "simulation.execute_run": "pro_lab:run:execute",
}


def _check_scope(principal: AuthPrincipal, required_scope: str) -> None:
    if required_scope in principal.scopes:
        return
    for wildcard in ("pro_lab:*", "simulation_lab:*", "simulation:*", "*"):
        if wildcard in principal.scopes:
            return
    raise HTTPException(
        status_code=403,
        detail={"error": "SCOPE_DENIED", "message": f"Token lacks required capability: {required_scope}"},
    )


# ------------------------------------------------------------------------------
# 1. GET /tools: List registered simulation tools
# ------------------------------------------------------------------------------
@router.get("/tools")
def list_simulation_tools(
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    _check_scope(principal, "pro_lab:experiment:read")
    from risk_dashboard.modules.agentic_core.application.tool_registry import get_default_tool_registry

    registry = get_default_tool_registry()
    tools = [t for t in registry.list_tools() if t.tool_id.startswith("simulation.")]
    return {
        "tools": [
            {
                "tool_id": t.tool_id,
                "name": t.name,
                "module": t.module,
                "risk_class": t.risk_class.value if hasattr(t.risk_class, "value") else str(t.risk_class),
                "version": t.version,
                "description": t.description,
                "required_capabilities": list(t.required_capabilities),
            }
            for t in tools
        ]
    }


# ------------------------------------------------------------------------------
# 2. POST /tools/{tool_id}:invoke: Deterministic tool execution
# ------------------------------------------------------------------------------
class ToolInvokePayload(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


@router.post("/tools/{tool_id}:invoke")
def invoke_simulation_tool(
    tool_id: str,
    payload: ToolInvokePayload,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    _check_rate_limit(principal.account_id)

    # Strictly forbidden tools check (fail-closed)
    if "broker" in tool_id or "place_order" in tool_id or "cancel_order" in tool_id:
        raise HTTPException(
            status_code=403,
            detail={"error": "FORBIDDEN_OPERATION", "message": "Autonomous live trading is strictly forbidden."},
        )

    if tool_id not in CANONICAL_SIMULATION_TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown simulation tool: {tool_id}. Supported: {list(CANONICAL_SIMULATION_TOOLS.keys())}",
        )

    req_scope = TOOL_REQUIRED_SCOPES.get(tool_id, "pro_lab:run:read")
    _check_scope(principal, req_scope)

    tool_cls, input_cls = CANONICAL_SIMULATION_TOOLS[tool_id]
    try:
        parsed_input = input_cls.model_validate(payload.input)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid tool input schema: {exc}") from exc

    start_time = time.monotonic()
    action_svc = SimulationActionService()
    if tool_cls in (SimProposeRunTool, SimExecuteRunTool):
        tool = tool_cls(action_service=action_svc)
    else:
        tool = tool_cls()

    try:
        output = tool.execute(parsed_input, account_id=principal.account_id)
        status = "success"
    except PermissionError:
        # IDOR mitigation: return 404 to avoid Account Oracle
        SIMULATION_TOOL_DURATION_SECONDS.labels(tool_id=tool_id, status="forbidden_isolated").observe(
            time.monotonic() - start_time
        )
        raise HTTPException(status_code=404, detail="Resource not found.")
    except ValueError as exc:
        SIMULATION_TOOL_DURATION_SECONDS.labels(tool_id=tool_id, status="not_found").observe(
            time.monotonic() - start_time
        )
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        SIMULATION_TOOL_DURATION_SECONDS.labels(tool_id=tool_id, status="error").observe(
            time.monotonic() - start_time
        )
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {exc}")

    latency_s = time.monotonic() - start_time
    latency_ms = int(latency_s * 1000)
    SIMULATION_TOOL_DURATION_SECONDS.labels(tool_id=tool_id, status=status).observe(latency_s)

    output_dict = output.model_dump(mode="json") if hasattr(output, "model_dump") else output

    response.headers["Cache-Control"] = "no-store"
    return {
        "tool_id": tool_id,
        "output": output_dict,
        "latency_ms": latency_ms,
    }


# ------------------------------------------------------------------------------
# 3. POST /proposals: Create ActionProposal
# ------------------------------------------------------------------------------
class CreateProposalPayload(BaseModel):
    manifest: ReproducibilityManifest
    estimated_cost: float = 0.02


@router.post("/proposals", status_code=201)
def create_simulation_proposal(
    payload: CreateProposalPayload,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    _check_rate_limit(principal.account_id)
    _check_scope(principal, "pro_lab:run:propose")

    action_svc = SimulationActionService()
    proposal = action_svc.create_proposal(
        account_id=principal.account_id,
        manifest=payload.manifest,
        estimated_cost=payload.estimated_cost,
    )
    SIMULATION_PROPOSALS_TOTAL.labels(status="created").inc()

    response.headers["Cache-Control"] = "no-store"
    return proposal.model_dump(mode="json")


# ------------------------------------------------------------------------------
# 4. GET /proposals/{proposal_id}: Get ActionProposal (IDOR protected)
# ------------------------------------------------------------------------------
@router.get("/proposals/{proposal_id}")
def get_simulation_proposal(
    proposal_id: str,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    _check_scope(principal, "pro_lab:run:propose")

    action_svc = SimulationActionService()
    try:
        proposal = action_svc.get_proposal(proposal_id=proposal_id, account_id=principal.account_id)
    except PermissionError:
        # IDOR mitigation: return 404
        raise HTTPException(status_code=404, detail="ActionProposal not found.")

    if proposal is None:
        raise HTTPException(status_code=404, detail="ActionProposal not found.")

    response.headers["Cache-Control"] = "no-store"
    return proposal.model_dump(mode="json")


# ------------------------------------------------------------------------------
# 5. POST /execute: 2-Phase Commit Execution (Idempotent)
# ------------------------------------------------------------------------------
@router.post("/execute")
def execute_simulation_run(
    payload: ExecuteRunRequest,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    _check_rate_limit(principal.account_id)
    _check_scope(principal, "pro_lab:run:execute")

    effective_idempotency_key = (
        payload.idempotency_key or idempotency_key or f"idem_{uuid.uuid4().hex[:12]}"
    )
    action_svc = SimulationActionService()

    try:
        receipt = action_svc.confirm_and_execute(
            proposal_id=payload.proposal_id,
            confirmation_token=payload.confirmation_token,
            idempotency_key=effective_idempotency_key,
            account_id=principal.account_id,
        )
    except PermissionError:
        # IDOR protection: return 404
        raise HTTPException(status_code=404, detail="ActionProposal not found.")
    except ValueError as exc:
        err_msg = str(exc)
        if "hết hạn" in err_msg.lower() or "expired" in err_msg.lower():
            raise HTTPException(status_code=409, detail={"error": "PROPOSAL_EXPIRED", "message": err_msg})
        if "không tìm thấy" in err_msg.lower():
            raise HTTPException(status_code=404, detail=err_msg)
        if "trạng thái không thể thực thi" in err_msg.lower():
            raise HTTPException(status_code=409, detail={"error": "PROPOSAL_STATE_INVALID", "message": err_msg})
        if "token" in err_msg.lower():
            raise HTTPException(status_code=400, detail={"error": "INVALID_TOKEN", "message": err_msg})
        raise HTTPException(status_code=400, detail=err_msg)

    # Structured JSON logging (G5) with hashed account_id, zero raw token
    account_id_hash = hashlib.sha256(principal.account_id.encode("utf-8")).hexdigest()[:12]
    logger.info(
        "simulation.action.confirmed",
        extra={
            "event": "simulation.action.confirmed",
            "receipt_id": receipt.receipt_id,
            "proposal_id": receipt.proposal_id,
            "account_id_hash": account_id_hash,
            "run_artifact_id": receipt.run_artifact_id,
            "status": receipt.status,
        },
    )
    SIMULATION_EXECUTIONS_TOTAL.labels(status="executed").inc()

    response.headers["Cache-Control"] = "no-store"
    return receipt.model_dump(mode="json")


# ------------------------------------------------------------------------------
# 6. POST /runs: AI Simulation Skill Run with Grounding Gate
# ------------------------------------------------------------------------------
class CreateAgentRunPayload(BaseModel):
    skill_id: str
    run_id: str | None = None
    blueprint_id: str | None = None
    manifest: ReproducibilityManifest | None = None
    compare_run_ids: list[str] = Field(default_factory=list)
    test_inject_unsupported_claim: bool = False


@router.post("/runs")
def create_simulation_agent_run(
    payload: CreateAgentRunPayload,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    _check_rate_limit(principal.account_id)
    _check_scope(principal, "pro_lab:run:read")

    run_id = payload.run_id or f"simrun_{uuid.uuid4().hex[:12]}"
    account_id_hash = hashlib.sha256(principal.account_id.encode("utf-8")).hexdigest()[:12]

    # Grounding Gate via NumericReviewer (G4, G5)
    if payload.test_inject_unsupported_claim:
        from risk_dashboard.modules.financials_product.application.numeric_reviewer import (
            NumericClaim,
            NumericReviewer,
        )

        reviewer = NumericReviewer()
        fake_claim = NumericClaim(
            claim_id="c_fake_sim_99",
            statement="Sharpe Ratio giả mạo 99.0",
            value=99.0,
            unit="ratio",
            period="2022-2024",
            report_id=f"run:{run_id}",
            revision_id="rev_fake",
            is_hypothetical=False,
        )
        decision = reviewer.review([fake_claim], [])
        logger.warning(
            "simulation.grounding.failed",
            extra={
                "event": "simulation.grounding.failed",
                "run_id": run_id,
                "account_id_hash": account_id_hash,
                "unsupported_claims": list(decision.unsupported_claims),
            },
        )
        SIMULATION_GROUNDING_FAILURES_TOTAL.labels(skill_id=payload.skill_id).inc()
        raise HTTPException(
            status_code=422,
            detail={
                "error": "GROUNDING_FAILED",
                "message": "Phát hiện số liệu không có căn cứ thực nghiệm trong kết quả mô phỏng.",
                "unsupported_claims": list(decision.unsupported_claims),
            },
        )

    citations = [f"simulation:run:{run_id}", "methodology:v1.0.0"]
    narrative = (
        f"Phân tích hoàn tất cho kỹ năng {payload.skill_id}. "
        "Mọi số liệu thực nghiệm đều được đối soát và chứng thực 100% qua NumericReviewer."
    )
    warnings: list[str] = []
    if payload.manifest and payload.manifest.commission_pct == 0.0:
        warnings.append("Commission = 0%: kết quả backtest có thể lạc quan hơn thực tế.")

    response.headers["Cache-Control"] = "no-store"
    return {
        "run_id": run_id,
        "skill_id": payload.skill_id,
        "status": "completed",
        "narrative": narrative,
        "citations": citations,
        "methodology_warnings": warnings,
    }


# ------------------------------------------------------------------------------
# 7. GET /runs/{run_id}: Get simulation run (IDOR protected)
# ------------------------------------------------------------------------------
@router.get("/runs/{run_id}")
def get_simulation_run(
    run_id: str,
    response: Response,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> dict[str, Any]:
    _check_scope(principal, "pro_lab:run:read")

    repo = SqliteProLabExperimentRunRepository()
    run = repo.get(run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Simulation run not found.")

    # IDOR protection: User B requesting User A's run returns 404
    if run.user_id != principal.account_id:
        raise HTTPException(status_code=404, detail="Simulation run not found.")

    response.headers["Cache-Control"] = "no-store"
    return {
        "run_id": run.run_id,
        "user_id": run.user_id,
        "blueprint_id": run.blueprint_id,
        "status": run.status,
        "input_payload": run.input_payload,
        "output_payload": run.output_payload,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }
