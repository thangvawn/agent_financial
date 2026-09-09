from __future__ import annotations

import json
from typing import Any

from risk_dashboard.modules.agentic_core.infrastructure.migrations import ensure_agentic_tables
from risk_dashboard.modules.agentic_core.schemas.artifact import ActionProposal, ActionReceipt, AgentArtifact
from risk_dashboard.modules.agentic_core.schemas.memory import MemoryProposal
from risk_dashboard.modules.agentic_core.schemas.runs import AgentRun, AgentStep, ToolCallRecord


class AgenticRunRepository:
    def save(
        self,
        conn,
        run: AgentRun | None = None,
        *,
        run_id: str | None = None,
        account_id: str | None = None,
        surface: str | None = None,
        status: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        capability_id: str | None = None,
        task_input: dict[str, Any] | None = None,
        result_payload: dict[str, Any] | None = None,
        usage: dict[str, Any] | None = None,
    ) -> None:
        ensure_agentic_tables(conn)
        if run is not None:
            r_id = run.run_id
            acc_id = run.account_id
            surf = run.surface
            stat = run.status
            corr_id = run.correlation_id
            idem_key = run.idempotency_key
            cap_id = run.capability_id
            t_input = json.dumps(run.task_input)
            r_payload = json.dumps(run.result_payload) if run.result_payload is not None else None
            usg = json.dumps(run.usage)
            c_at = run.created_at
            u_at = run.updated_at
        else:
            r_id = run_id or ""
            acc_id = account_id or ""
            surf = surface or ""
            stat = status or ""
            corr_id = correlation_id
            idem_key = idempotency_key
            cap_id = capability_id
            t_input = json.dumps(task_input or {})
            r_payload = json.dumps(result_payload) if result_payload is not None else None
            usg = json.dumps(usage or {})
            c_at = created_at or ""
            u_at = updated_at or ""

        owner = conn.execute(
            "SELECT account_id FROM agentic_runs WHERE run_id = ?",
            (r_id,),
        ).fetchone()
        if owner is not None and owner["account_id"] != acc_id:
            raise ValueError("Run belongs to another account.")

        conn.execute(
            """
            INSERT INTO agentic_runs (
              run_id, account_id, surface, status, correlation_id, idempotency_key,
              capability_id, task_input_json, result_payload_json, usage_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
              status = excluded.status,
              result_payload_json = excluded.result_payload_json,
              usage_json = excluded.usage_json,
              updated_at = excluded.updated_at
            """,
            (r_id, acc_id, surf, stat, corr_id, idem_key, cap_id, t_input, r_payload, usg, c_at, u_at),
        )

    def get(self, conn, *, run_id: str, account_id: str) -> AgentRun | None:
        ensure_agentic_tables(conn)
        row = conn.execute(
            "SELECT * FROM agentic_runs WHERE run_id = ? AND account_id = ?",
            (run_id, account_id),
        ).fetchone()
        if row is None:
            return None
        return AgentRun(
            run_id=row["run_id"],
            account_id=row["account_id"],
            surface=row["surface"],
            status=row["status"],
            correlation_id=row["correlation_id"],
            idempotency_key=row["idempotency_key"],
            capability_id=row["capability_id"],
            task_input=json.loads(row["task_input_json"]) if row["task_input_json"] else {},
            result_payload=json.loads(row["result_payload_json"]) if row["result_payload_json"] else None,
            usage=json.loads(row["usage_json"]) if row["usage_json"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_by_idempotency(self, conn, *, account_id: str, idempotency_key: str) -> AgentRun | None:
        ensure_agentic_tables(conn)
        row = conn.execute(
            "SELECT * FROM agentic_runs WHERE account_id = ? AND idempotency_key = ? ORDER BY created_at DESC LIMIT 1",
            (account_id, idempotency_key),
        ).fetchone()
        if row is None:
            return None
        return AgentRun(
            run_id=row["run_id"],
            account_id=row["account_id"],
            surface=row["surface"],
            status=row["status"],
            correlation_id=row["correlation_id"],
            idempotency_key=row["idempotency_key"],
            capability_id=row["capability_id"],
            task_input=json.loads(row["task_input_json"]) if row["task_input_json"] else {},
            result_payload=json.loads(row["result_payload_json"]) if row["result_payload_json"] else None,
            usage=json.loads(row["usage_json"]) if row["usage_json"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_step(self, conn, step: AgentStep) -> None:
        ensure_agentic_tables(conn)
        conn.execute(
            """
            INSERT INTO agentic_steps (
              step_id, run_id, step_index, agent_id, node_name, status,
              input_payload_json, output_payload_json, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(step_id) DO UPDATE SET
              status = excluded.status,
              output_payload_json = excluded.output_payload_json,
              completed_at = excluded.completed_at
            """,
            (
                step.step_id,
                step.run_id,
                step.step_index,
                step.agent_id,
                step.node_name,
                step.status,
                json.dumps(step.input_payload),
                json.dumps(step.output_payload),
                step.started_at,
                step.completed_at,
            ),
        )

    def save_tool_call(self, conn, tool_call: ToolCallRecord) -> None:
        ensure_agentic_tables(conn)
        conn.execute(
            """
            INSERT INTO agentic_tool_calls (
              tool_call_id, run_id, account_id, tool_name, input_hash, status, evidence_json, latency_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tool_call_id) DO UPDATE SET
              status = excluded.status,
              evidence_json = excluded.evidence_json,
              latency_ms = excluded.latency_ms
            """,
            (
                tool_call.tool_call_id,
                tool_call.run_id,
                tool_call.account_id,
                tool_call.tool_name,
                tool_call.input_hash,
                tool_call.status,
                json.dumps(tool_call.evidence),
                tool_call.latency_ms,
                tool_call.created_at,
            ),
        )

    def list_steps(self, conn, *, run_id: str) -> list[AgentStep]:
        ensure_agentic_tables(conn)
        rows = conn.execute(
            """
            SELECT * FROM agentic_steps
            WHERE run_id = ?
            ORDER BY step_index ASC
            """,
            (run_id,),
        ).fetchall()
        return [
            AgentStep(
                schema_version="1.0.0",
                step_id=r["step_id"],
                run_id=r["run_id"],
                step_index=r["step_index"],
                agent_id=r["agent_id"],
                node_name=r["node_name"],
                status=r["status"],
                input_payload=json.loads(r["input_payload_json"]) if r["input_payload_json"] else {},
                output_payload=json.loads(r["output_payload_json"]) if r["output_payload_json"] else {},
                started_at=r["started_at"],
                completed_at=r["completed_at"],
            )
            for r in rows
        ]

    def list_tool_calls(self, conn, *, run_id: str, account_id: str) -> list[ToolCallRecord]:
        ensure_agentic_tables(conn)
        rows = conn.execute(
            """
            SELECT * FROM agentic_tool_calls
            WHERE run_id = ? AND account_id = ?
            ORDER BY created_at ASC
            """,
            (run_id, account_id),
        ).fetchall()
        return [
            ToolCallRecord(
                schema_version="1.0.0",
                tool_call_id=r["tool_call_id"],
                run_id=r["run_id"],
                account_id=r["account_id"],
                tool_name=r["tool_name"],
                input_hash=r["input_hash"],
                status=r["status"],
                evidence=json.loads(r["evidence_json"]) if r["evidence_json"] else {},
                latency_ms=r["latency_ms"],
                created_at=r["created_at"],
            )
            for r in rows
        ]


class AgenticArtifactRepository:
    def save(self, conn, artifact: AgentArtifact) -> None:
        ensure_agentic_tables(conn)
        owner = conn.execute(
            "SELECT account_id FROM agentic_artifacts WHERE artifact_id = ?",
            (artifact.artifact_id,),
        ).fetchone()
        if owner is not None and owner["account_id"] != artifact.account_id:
            raise ValueError("Artifact belongs to another account.")
        conn.execute(
            """
            INSERT INTO agentic_artifacts (
              artifact_id, account_id, authoring_run_id, artifact_type, domain,
              review_status, version, payload_json, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_id) DO UPDATE SET
              review_status = excluded.review_status, payload_json = excluded.payload_json
            """,
            (
                artifact.artifact_id,
                artifact.account_id,
                artifact.authoring_run_id,
                artifact.artifact_type,
                artifact.domain,
                artifact.review_status,
                artifact.version,
                json.dumps(artifact.model_dump(mode="json")),
                artifact.created_at,
                artifact.expires_at,
            ),
        )

    def get(self, conn, *, artifact_id: str, account_id: str) -> AgentArtifact | None:
        ensure_agentic_tables(conn)
        row = conn.execute(
            """
            SELECT payload_json FROM agentic_artifacts
            WHERE artifact_id = ? AND account_id = ?
            """,
            (artifact_id, account_id),
        ).fetchone()
        return None if row is None else AgentArtifact.model_validate_json(row["payload_json"])

    def list_by_run(self, conn, *, run_id: str, account_id: str) -> list[AgentArtifact]:
        ensure_agentic_tables(conn)
        rows = conn.execute(
            """
            SELECT payload_json FROM agentic_artifacts
            WHERE authoring_run_id = ? AND account_id = ?
            ORDER BY created_at DESC
            """,
            (run_id, account_id),
        ).fetchall()
        return [AgentArtifact.model_validate_json(r["payload_json"]) for r in rows]


class AgenticActionRepository:
    def save_proposal(self, conn, proposal: ActionProposal) -> None:
        ensure_agentic_tables(conn)
        owner = conn.execute(
            "SELECT account_id FROM agentic_action_proposals WHERE proposal_id = ?",
            (proposal.proposal_id,),
        ).fetchone()
        if owner is not None and owner["account_id"] != proposal.account_id:
            raise ValueError("Proposal belongs to another account.")
        conn.execute(
            """
            INSERT INTO agentic_action_proposals (
              proposal_id, run_id, account_id, operation, target_ref_json, payload_preview_json,
              risk_class, requires_confirmation, policy_version, status, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(proposal_id) DO UPDATE SET
              status = excluded.status
            """,
            (
                proposal.proposal_id,
                proposal.run_id,
                proposal.account_id,
                proposal.operation,
                json.dumps(proposal.target.model_dump(mode="json")),
                json.dumps(proposal.payload_preview),
                proposal.risk_class,
                1 if proposal.requires_confirmation else 0,
                proposal.policy_version,
                "proposed",
                proposal.created_at,
                proposal.expires_at,
            ),
        )

    def get_proposal(self, conn, *, proposal_id: str, account_id: str) -> ActionProposal | None:
        ensure_agentic_tables(conn)
        row = conn.execute(
            """
            SELECT * FROM agentic_action_proposals
            WHERE proposal_id = ? AND account_id = ?
            """,
            (proposal_id, account_id),
        ).fetchone()
        if row is None:
            return None
        from risk_dashboard.modules.agentic_core.schemas.envelope import ResourceRef

        return ActionProposal(
            schema_version="1.0.0",
            proposal_id=row["proposal_id"],
            run_id=row["run_id"],
            account_id=row["account_id"],
            operation=row["operation"],
            target=ResourceRef.model_validate_json(row["target_ref_json"]),
            payload_preview=json.loads(row["payload_preview_json"]),
            risk_class=row["risk_class"],
            requires_confirmation=bool(row["requires_confirmation"]),
            policy_version=row["policy_version"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )

    def update_proposal_status(self, conn, *, proposal_id: str, account_id: str, status: str) -> None:
        ensure_agentic_tables(conn)
        conn.execute(
            "UPDATE agentic_action_proposals SET status = ? WHERE proposal_id = ? AND account_id = ?",
            (status, proposal_id, account_id),
        )

    def save_receipt(self, conn, receipt: ActionReceipt) -> None:
        ensure_agentic_tables(conn)
        conn.execute(
            """
            INSERT INTO agentic_action_receipts (
              receipt_id, proposal_id, account_id, status, executed_at, result_ref_json, error_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(receipt_id) DO NOTHING
            """,
            (
                receipt.receipt_id,
                receipt.proposal_id,
                receipt.account_id,
                receipt.status,
                receipt.executed_at,
                json.dumps(receipt.result_ref.model_dump(mode="json")) if receipt.result_ref else None,
                receipt.error_code,
            ),
        )

    def get_receipt(self, conn, *, proposal_id: str, account_id: str) -> ActionReceipt | None:
        ensure_agentic_tables(conn)
        row = conn.execute(
            """
            SELECT * FROM agentic_action_receipts
            WHERE proposal_id = ? AND account_id = ?
            """,
            (proposal_id, account_id),
        ).fetchone()
        if row is None:
            return None
        from risk_dashboard.modules.agentic_core.schemas.envelope import ResourceRef

        res_ref = ResourceRef.model_validate_json(row["result_ref_json"]) if row["result_ref_json"] else None
        return ActionReceipt(
            schema_version="1.0.0",
            receipt_id=row["receipt_id"],
            proposal_id=row["proposal_id"],
            account_id=row["account_id"],
            status=row["status"],
            executed_at=row["executed_at"],
            result_ref=res_ref,
            error_code=row["error_code"],
        )


class AgenticMemoryRepository:
    def save_proposal(self, conn, proposal: MemoryProposal) -> None:
        ensure_agentic_tables(conn)
        owner = conn.execute(
            "SELECT account_id FROM agentic_memory_proposals WHERE proposal_id = ?",
            (proposal.proposal_id,),
        ).fetchone()
        if owner is not None and owner["account_id"] != proposal.account_id:
            raise ValueError("Memory proposal belongs to another account.")
        conn.execute(
            """
            INSERT INTO agentic_memory_proposals (
              proposal_id, run_id, account_id, memory_type, content, provenance,
              confidence, sensitivity, ttl_days, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(proposal_id) DO NOTHING
            """,
            (
                proposal.proposal_id,
                proposal.run_id,
                proposal.account_id,
                proposal.memory_type,
                proposal.content,
                proposal.provenance,
                proposal.confidence,
                proposal.sensitivity,
                proposal.ttl_days,
                "proposed",
                proposal.created_at,
            ),
        )

    def get_proposal(self, conn, *, proposal_id: str, account_id: str) -> MemoryProposal | None:
        ensure_agentic_tables(conn)
        row = conn.execute(
            """
            SELECT * FROM agentic_memory_proposals
            WHERE proposal_id = ? AND account_id = ?
            """,
            (proposal_id, account_id),
        ).fetchone()
        if row is None:
            return None
        return MemoryProposal(
            schema_version="1.0.0",
            proposal_id=row["proposal_id"],
            run_id=row["run_id"],
            account_id=row["account_id"],
            memory_type=row["memory_type"],
            content=row["content"],
            provenance=row["provenance"],
            confidence=row["confidence"],
            sensitivity=row["sensitivity"],
            ttl_days=row["ttl_days"],
            created_at=row["created_at"],
        )

    def list_proposals(self, conn, *, account_id: str) -> list[MemoryProposal]:
        ensure_agentic_tables(conn)
        rows = conn.execute(
            """
            SELECT * FROM agentic_memory_proposals
            WHERE account_id = ?
            ORDER BY created_at DESC
            """,
            (account_id,),
        ).fetchall()
        return [
            MemoryProposal(
                schema_version="1.0.0",
                proposal_id=r["proposal_id"],
                run_id=r["run_id"],
                account_id=r["account_id"],
                memory_type=r["memory_type"],
                content=r["content"],
                provenance=r["provenance"],
                confidence=r["confidence"],
                sensitivity=r["sensitivity"],
                ttl_days=r["ttl_days"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
