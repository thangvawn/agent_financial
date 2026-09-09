"""Application service for agentic run lifecycle management and orchestration."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import logging
import time
from typing import Any, Callable
import uuid

from risk_dashboard.modules.agentic_core.application.graph import run_graph as default_run_graph
from risk_dashboard.modules.agentic_core.application.kill_switch import assert_agentic_available
from risk_dashboard.modules.agentic_core.application.skill_router import SkillRouter
from risk_dashboard.modules.agentic_core.infrastructure.repositories import (
    AgenticArtifactRepository,
    AgenticRunRepository,
)
from risk_dashboard.modules.agentic_core.schemas.artifact import AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.envelope import ConsentSnapshot, TrustedExecutionEnvelope
from risk_dashboard.modules.agentic_core.schemas.requests import AgentRunRequestV1, AgentRunResponseV1
from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun, AgentStep, ToolCallRecord
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.platform.ai_runtime.contracts import ModelTask
from risk_dashboard.platform.ai_runtime.factory import get_default_provider
from risk_dashboard.platform.database import open_app_state_db

logger = logging.getLogger(__name__)


from risk_dashboard.platform.feature_flags.decorator import feature_flag


class RunService:
    """Manages the creation, execution, cancellation, and tracing of agent runs."""

    def __init__(
        self,
        run_repo: AgenticRunRepository | None = None,
        artifact_repo: AgenticArtifactRepository | None = None,
    ) -> None:
        self._run_repo = run_repo or AgenticRunRepository()
        self._artifact_repo = artifact_repo or AgenticArtifactRepository()

    def build_envelope(
        self, request: AgentRunRequestV1, principal: AuthPrincipal, run_id: str | None = None, now_iso: str | None = None
    ) -> TrustedExecutionEnvelope:
        run_id = run_id or f"run_{uuid.uuid4().hex}"
        now_iso = now_iso or datetime.now(timezone.utc).isoformat()
        tool = SkillRouter.resolve_tool(surface=request.surface, operation=request.operation)
        required_caps = SkillRouter.get_required_capabilities(tool)
        allowed_caps = tuple(sorted(set(c for c in required_caps if c in principal.scopes or "*" in principal.scopes)))

        if principal.is_anonymous or principal.consent is None:
            consent = ConsentSnapshot(memory=False, analytics=False, consented_at=now_iso, policy_version="1.0.0")
        else:
            consent = ConsentSnapshot(
                memory=principal.consent.memory, analytics=principal.consent.analytics,
                consented_at=principal.consent.consented_at or now_iso, policy_version=principal.consent.policy_version,
            )

        return TrustedExecutionEnvelope(
            run_id=run_id, correlation_id=run_id, idempotency_key=run_id, account_id=principal.account_id,
            scopes=tuple(principal.scopes), surface=request.surface, resource_refs=tuple(request.resource_refs),
            locale=request.locale, allowed_capabilities=allowed_caps, policy_version="1.0.0",
            model_policy_version="1.0.0", consent=consent, created_at=now_iso,
        )

    @feature_flag("agentic.runs", default=True)
    async def create_and_execute_run(
        self,
        *,
        request: AgentRunRequestV1,
        principal: AuthPrincipal,
        run_graph_fn: Callable[..., Any] | None = None,
        provider: Any = None,
    ) -> AgentRunResponseV1:
        assert_agentic_available()
        run_id = f"run_{uuid.uuid4().hex}"
        now_iso = datetime.now(timezone.utc).isoformat()

        envelope = self.build_envelope(request, principal, run_id=run_id, now_iso=now_iso)
        tool = SkillRouter.resolve_tool(surface=request.surface, operation=request.operation)
        task = ModelTask(
            task_id=f"task_{uuid.uuid4().hex}", task_type="agentic_read", system_instructions_ref="default",
            messages=(), correlation_id=run_id,
        )
        if provider is None:
            try:
                provider = get_default_provider()
            except Exception:
                from risk_dashboard.platform.ai_runtime.testing.fake_provider import FakeProvider
                provider = FakeProvider()

        with open_app_state_db() as conn:
            self._run_repo.save(
                conn,
                AgentRun(
                    run_id=run_id, account_id=principal.account_id, surface=request.surface, status="running",
                    correlation_id=run_id, idempotency_key=run_id, created_at=now_iso, updated_at=now_iso,
                ),
            )

        runner = run_graph_fn or default_run_graph
        input_hash = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
        t0 = time.perf_counter()
        try:
            result = await runner(envelope, task, provider, tool)
            status_code = "completed" if result.get("status") == "success" else "failed"
            artifact = AgentArtifact(
                artifact_id=f"art_{uuid.uuid4().hex}", artifact_type="text", domain="general",
                account_id=principal.account_id, authoring_run_id=run_id, created_at=now_iso,
            )
            completed_iso = datetime.now(timezone.utc).isoformat()
            with open_app_state_db() as conn:
                self._artifact_repo.save(conn, artifact)
                self._run_repo.save(
                    conn,
                    AgentRun(
                        run_id=run_id, account_id=principal.account_id, surface=request.surface, status=status_code,
                        correlation_id=run_id, idempotency_key=run_id, result_payload={"result": result},
                        created_at=now_iso, updated_at=completed_iso,
                    ),
                )
                for idx, node_name in enumerate(result.get("trace", ())):
                    self._run_repo.save_step(
                        conn,
                        AgentStep(
                            schema_version="1.0.0", step_id=f"step_{run_id}_{idx}", run_id=run_id, step_index=idx,
                            agent_id="supervisor", node_name=node_name, status="completed", input_payload={},
                            output_payload={"code": result.get("code")} if node_name == "recovery" else {},
                            started_at=now_iso, completed_at=completed_iso,
                        ),
                    )
                if result.get("tool_calls_used", 0) > 0:
                    tool_name = tool.manifest.tool_id if hasattr(tool, "manifest") and tool.manifest is not None else getattr(tool, "name", "unknown_tool")
                    latency_ms = max(1, int((time.perf_counter() - t0) * 1000))
                    self._run_repo.save_tool_call(
                        conn,
                        ToolCallRecord(
                            schema_version="1.0.0", tool_call_id=f"tc_{run_id}_{uuid.uuid4().hex[:8]}", run_id=run_id,
                            account_id=principal.account_id, tool_name=tool_name, input_hash=input_hash,
                            status="success" if result.get("evidence") else "failed",
                            evidence=result.get("evidence") or {}, latency_ms=latency_ms, created_at=completed_iso,
                        ),
                    )
            return AgentRunResponseV1(run_id=run_id, status=status_code, artifact=artifact)
        except Exception as exc:
            failed_iso = datetime.now(timezone.utc).isoformat()
            with open_app_state_db() as conn:
                self._run_repo.save(conn, AgentRun(
                    run_id=run_id, account_id=principal.account_id, surface=request.surface, status="failed",
                    correlation_id=run_id, idempotency_key=run_id, created_at=now_iso, updated_at=failed_iso,
                ))
                self._run_repo.save_step(conn, AgentStep(
                    schema_version="1.0.0", step_id=f"step_{run_id}_failed", run_id=run_id, step_index=0,
                    agent_id="supervisor", node_name="failure", status="failed",
                    input_payload={"operation": request.operation, "surface": request.surface},
                    output_payload={"error": str(exc), "error_type": type(exc).__name__},
                    started_at=now_iso, completed_at=failed_iso,
                ))
            raise

    def get_run(self, *, run_id: str, account_id: str) -> AgentRunResponseV1 | None:
        with open_app_state_db() as conn:
            run = self._run_repo.get(conn, run_id=run_id, account_id=account_id)
            if run is None:
                return None
            artifacts = self._artifact_repo.list_by_run(conn, run_id=run_id, account_id=account_id)
            artifact = artifacts[0] if artifacts else None
        return AgentRunResponseV1(run_id=run.run_id, status=run.status, artifact=artifact)

    def cancel_run(self, *, run_id: str, account_id: str) -> dict[str, str] | None:
        with open_app_state_db() as conn:
            run = self._run_repo.get(conn, run_id=run_id, account_id=account_id)
            if run is None:
                return None
            if run.status in ["running", "accepted"]:
                self._run_repo.save(conn, AgentRun(
                    run_id=run.run_id, account_id=run.account_id, surface=run.surface, status="canceled",
                    correlation_id=run.correlation_id, idempotency_key=run.idempotency_key,
                    created_at=run.created_at, updated_at=datetime.now(timezone.utc).isoformat(),
                ))
        return {"status": "canceled"}

    def get_run_trace(self, *, run_id: str, account_id: str) -> dict[str, Any] | None:
        with open_app_state_db() as conn:
            run = self._run_repo.get(conn, run_id=run_id, account_id=account_id)
            if run is None:
                return None
            steps = self._run_repo.list_steps(conn, run_id=run_id)
            tool_calls = self._run_repo.list_tool_calls(conn, run_id=run_id, account_id=account_id)
        return {
            "run_id": run.run_id, "status": run.status, "surface": run.surface,
            "created_at": run.created_at, "updated_at": run.updated_at,
            "steps": [s.model_dump(mode="json") for s in steps],
            "tool_calls": [tc.model_dump(mode="json") for tc in tool_calls],
            "timeline": [s.node_name for s in steps],
        }
