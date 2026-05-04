from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AssistantConversationSession:
    conversation_id: str
    user_id: str
    role: str
    surface: str
    context: dict[str, object]
    prompt_version: str
    policy_version: str
    status: str = "active"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class AssistantMessage:
    message_id: str
    conversation_id: str
    sender: str
    content: str
    classified_intent: str | None
    risk_labels: tuple[str, ...]
    structured_output: dict[str, object]
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class AssistantFeedback:
    feedback_id: str
    conversation_id: str
    message_id: str
    rating: int
    reason_code: str
    free_text: str | None = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class AssistantEventLog:
    event_id: str
    conversation_id: str
    role: str
    surface: str
    intent: str
    route_decision: str
    guardrail_triggered: bool
    tool_calls: tuple[str, ...]
    latency_ms: int
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class AssistantReply:
    role: str
    allowed: bool
    route_decision: str
    title: str
    summary: str
    explanation: str
    next_step: str
    cta_path: str
    guardrails: tuple[str, ...]
    confidence_note: str
    check_question: str | None = None
    linked_lesson_id: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None
    risk_labels: tuple[str, ...] = ()
