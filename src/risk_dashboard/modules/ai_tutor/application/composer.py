from __future__ import annotations

from typing import Any
from uuid import uuid4

from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    NumericClaimRef,
    ToolCallRef,
)
from risk_dashboard.modules.ai_tutor.schemas.responses import SendMessageResponse


class FinalComposer:
    def compose(
        self,
        *,
        conversation_id: str,
        message_id: str | None = None,
        answer: str,
        citations: tuple[CitationRef, ...] = (),
        numeric_claims: tuple[NumericClaimRef, ...] = (),
        freshness: str = "latest",
        assumptions: tuple[str, ...] = (),
        limitations: tuple[str, ...] = (),
        check_question: str | None = None,
        next_action: str | None = None,
        tool_calls: tuple[ToolCallRef, ...] = (),
        trace_id: str | None = None,
        created_at: str,
    ) -> SendMessageResponse:
        mid = message_id or f"msg_{uuid4().hex[:12]}"
        tid = trace_id or f"trace_{uuid4().hex[:12]}"

        # Compose clean answer text with assumptions and limitations if applicable
        clean_answer = answer.strip()

        norm_assumptions = tuple(assumptions) if isinstance(assumptions, (list, tuple)) else ((assumptions,) if assumptions else ())
        norm_limitations = tuple(limitations) if isinstance(limitations, (list, tuple)) else ((limitations,) if limitations else ())
        norm_citations = tuple(citations) if isinstance(citations, (list, tuple)) else ()
        norm_numeric = tuple(numeric_claims) if isinstance(numeric_claims, (list, tuple)) else ()
        norm_tools = tuple(tool_calls) if isinstance(tool_calls, (list, tuple)) else ()

        return SendMessageResponse(
            message_id=mid,
            conversation_id=conversation_id,
            role="assistant",
            answer=clean_answer,
            citations=norm_citations,
            numeric_claims=norm_numeric,
            freshness=freshness,
            assumptions=norm_assumptions,
            limitations=norm_limitations,
            check_question=check_question,
            next_action=next_action,
            trace_id=tid,
            tool_calls=norm_tools,
            created_at=created_at,
        )
