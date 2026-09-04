from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
from typing import Any, Literal
from uuid import uuid4

from risk_dashboard.modules.agentic_core.schemas.envelope import (
    ConsentSnapshot,
    ExecutionBudget,
    TrustedExecutionEnvelope,
)
from risk_dashboard.modules.ai_tutor.application.composer import FinalComposer
from risk_dashboard.modules.ai_tutor.application.reviewers import (
    EvidenceAndNumericReviewer,
    SafetyAndPolicyReviewer,
)
from risk_dashboard.modules.ai_tutor.application.specialists.general_specialist import GeneralSpecialist
from risk_dashboard.modules.ai_tutor.application.specialists.learning_specialist import LearningSpecialist
from risk_dashboard.modules.ai_tutor.application.specialists.quant_specialist import QuantSpecialist
from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_conversation_repository import (
    SqliteConversationRepository,
)
from risk_dashboard.modules.ai_tutor.schemas.responses import SendMessageResponse


def classify_intent(surface: str, content: str) -> Literal["learn", "quant", "checkpoint", "general"]:
    lowered = content.lower()
    if surface == "checkpoint" or "checkpoint" in lowered or "kiểm tra kiến thức" in lowered:
        return "checkpoint"
    if surface == "quant" or any(kw in lowered for kw in ("var", "cvar", "monte carlo", "định lượng", "sharpe", "rủi ro đuôi", "mô hình")):
        return "quant"
    if surface == "learn" or any(kw in lowered for kw in ("bài học", "bài", "lesson", "giải thích", "roe", "cfo", "quiz", "gợi ý", "đáp án")):
        return "learn"
    return "general"


class TutorGraph:
    def __init__(
        self,
        learning_specialist: LearningSpecialist | None = None,
        quant_specialist: QuantSpecialist | None = None,
        general_specialist: GeneralSpecialist | None = None,
        evidence_reviewer: EvidenceAndNumericReviewer | None = None,
        safety_reviewer: SafetyAndPolicyReviewer | None = None,
        composer: FinalComposer | None = None,
        repo: SqliteConversationRepository | None = None,
    ) -> None:
        self.learning_specialist = learning_specialist or LearningSpecialist()
        self.quant_specialist = quant_specialist or QuantSpecialist()
        self.general_specialist = general_specialist or GeneralSpecialist()
        self.evidence_reviewer = evidence_reviewer or EvidenceAndNumericReviewer()
        self.safety_reviewer = safety_reviewer or SafetyAndPolicyReviewer()
        self.composer = composer or FinalComposer()
        self.repo = repo or SqliteConversationRepository()

    async def execute(
        self,
        *,
        conversation_id: str,
        account_id: str,
        surface: str,
        user_query: str,
        resource_id: str | None = None,
        trace_id: str | None = None,
    ) -> SendMessageResponse:
        start_time = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        tid = trace_id or f"trace_{uuid4().hex[:12]}"
        run_id = f"run_{uuid4().hex[:12]}"

        # Bind trusted execution envelope with caller identity and server-side capabilities
        envelope = TrustedExecutionEnvelope(
            run_id=run_id,
            correlation_id=tid,
            idempotency_key=tid,
            account_id=account_id,
            surface=surface,
            scopes=("learning:read", "quant:read", "ai_tutor:conversation:read", "ai_tutor:conversation:write"),
            allowed_capabilities=("learning:read", "quant:read"),
            budget=ExecutionBudget(
                max_steps=8,
                max_tool_calls=3,
                max_tokens=120000,
                max_wall_seconds=60.0,
                max_cost_usd=0.05,
            ),
            policy_version="v1",
            model_policy_version="v1",
            consent=ConsentSnapshot(policy_version="v1"),
            created_at=now_iso,
        )

        intent = classify_intent(surface, user_query)

        # 1. Specialist execution with server-side envelope grant enforcement
        if intent in {"learn", "checkpoint"}:
            raw_result = await self.learning_specialist.handle(
                intent=intent, user_query=user_query, resource_id=resource_id, envelope=envelope
            )
        elif intent == "quant":
            raw_result = await self.quant_specialist.handle(
                intent=intent, user_query=user_query, resource_id=resource_id, envelope=envelope
            )
        else:
            raw_result = await self.general_specialist.handle(user_query=user_query)

        # 2. Evidence & Numeric Review on BOTH metadata claims and prose numbers
        accepted_cites, accepted_numeric, verified_prose, numeric_rejections = self.evidence_reviewer.review(
            candidate_text=raw_result["answer"],
            evidence=raw_result.get("evidence"),
            citations=raw_result.get("citations", ()),
            numeric_claims=raw_result.get("numeric_claims", ()),
        )

        # 3. Safety & Policy Review
        is_safe, safe_text, policy_rejections, policy_notice = self.safety_reviewer.review(verified_prose)

        # 4. Synthesize limitations and guardrail flags
        limitations = list(raw_result.get("limitations", ()))
        if policy_notice and policy_notice not in limitations:
            limitations.append(policy_notice)
        if numeric_rejections:
            limitations.append("Một số số liệu không đủ bằng chứng đối soát đã được loại trừ.")

        guardrail_triggered = 1 if (not is_safe or bool(numeric_rejections)) else 0
        tool_calls = raw_result.get("tool_calls", ())
        tool_calls_json = json.dumps([t.model_dump() for t in tool_calls])
        latency_ms = int((time.time() - start_time) * 1000)

        # 5. Log audit event
        try:
            self.repo.log_event(
                event_id=f"evt_{uuid4().hex[:12]}",
                conversation_id=conversation_id,
                role="assistant",
                surface=surface,
                intent=intent,
                route_decision=intent,
                guardrail_triggered=guardrail_triggered,
                tool_calls_json=tool_calls_json,
                latency_ms=latency_ms,
                created_at=now_iso,
            )
        except Exception as exc:
            logger.error(
                "Failed to persist AI audit event for conversation %s (guardrail=%d): %s",
                conversation_id,
                guardrail_triggered,
                exc,
            )

        # 6. Final Compose
        return self.composer.compose(
            conversation_id=conversation_id,
            answer=safe_text,
            citations=accepted_cites,
            numeric_claims=accepted_numeric,
            freshness="latest",
            assumptions=raw_result.get("assumptions", ()),
            limitations=tuple(limitations),
            check_question=raw_result.get("check_question"),
            next_action=raw_result.get("next_action"),
            tool_calls=tool_calls,
            trace_id=tid,
            created_at=now_iso,
        )
