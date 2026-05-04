from __future__ import annotations

from typing import Protocol

from risk_dashboard.modules.ai_assistant.domain.entities import (
    AssistantConversationSession,
    AssistantEventLog,
    AssistantFeedback,
    AssistantMessage,
)


class AssistantConversationRepository(Protocol):
    def save_session(self, session: AssistantConversationSession) -> AssistantConversationSession: ...

    def get_session(self, *, conversation_id: str) -> AssistantConversationSession | None: ...

    def list_recent_messages(self, *, conversation_id: str, limit: int = 8) -> tuple[AssistantMessage, ...]: ...

    def save_message(self, message: AssistantMessage) -> AssistantMessage: ...

    def save_feedback(self, feedback: AssistantFeedback) -> AssistantFeedback: ...

    def save_event(self, event: AssistantEventLog) -> AssistantEventLog: ...
