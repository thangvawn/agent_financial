from __future__ import annotations

from risk_dashboard.modules.ai_assistant.domain.contracts import (
    AssistantAction,
    AssistantContextPack,
    AssistantSource,
    IntentDecision,
    ModeDecision,
    SafetyDecision,
    StructuredAssistantPayload,
)
from risk_dashboard.modules.ai_assistant.domain.entities import AssistantReply


RESPONSE_COMPOSER_VERSION = "response_composer_v2_structured"


class AssistantResponseComposer:
    def compose(
        self,
        *,
        reply: AssistantReply,
        intent: IntentDecision,
        mode: ModeDecision,
        context: AssistantContextPack,
        safety: SafetyDecision,
    ) -> StructuredAssistantPayload:
        warnings = tuple(dict.fromkeys([*safety.warnings, *reply.guardrails]))
        actions = _actions(reply)
        learning = tuple(item for item in (reply.linked_lesson_id,) if item)
        return StructuredAssistantPayload(
            mode_used=reply.role,
            intent=intent.intent,
            intent_confidence=round(intent.confidence, 2),
            confidence_label=_confidence_label(intent=intent, mode=mode, safety=safety, context=context),
            data_freshness=context.freshness,
            warnings=warnings,
            next_actions=actions,
            suggested_modules=tuple(action.path for action in actions),
            learning_suggestions=learning,
            sources=_sources_for(reply=reply, context=context),
            response_blocks=(
                {"type": "summary", "content": reply.summary},
                {"type": "explanation", "content": reply.explanation},
                {"type": "next_step", "content": reply.next_step, "cta_path": reply.cta_path},
            ),
        )


def _actions(reply: AssistantReply) -> tuple[AssistantAction, ...]:
    if not reply.cta_path:
        return ()
    return (AssistantAction(label=reply.next_step or "Mở bước tiếp theo", path=reply.cta_path),)


def _sources_for(*, reply: AssistantReply, context: AssistantContextPack) -> tuple[AssistantSource, ...]:
    sources: list[AssistantSource] = [AssistantSource(label="Assistant policy", source_type="policy", freshness="fresh")]
    for signal in context.signals[:6]:
        sources.append(AssistantSource(label=signal.source, source_type="internal_state", freshness=signal.freshness))
    if reply.linked_lesson_id:
        sources.append(AssistantSource(label=reply.linked_lesson_id, source_type="learning_content", freshness="published"))
    return tuple(dict.fromkeys(sources))


def _confidence_label(*, intent: IntentDecision, mode: ModeDecision, safety: SafetyDecision, context: AssistantContextPack) -> str:
    if safety.action in {"block", "deescalate"}:
        return "guarded"
    if context.missing_context and intent.intent not in {"educational", "general_help"}:
        return "limited_context"
    if intent.confidence >= 0.82 and mode.confidence >= 0.82:
        return "high"
    if intent.confidence >= 0.65:
        return "moderate"
    return "low_needs_clarification"
