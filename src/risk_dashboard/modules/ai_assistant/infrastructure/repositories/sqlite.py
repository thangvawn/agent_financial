from __future__ import annotations

import json
import uuid

from risk_dashboard.modules.ai_assistant.domain.entities import (
    AssistantConversationSession,
    AssistantEventLog,
    AssistantFeedback,
    AssistantMessage,
)
from risk_dashboard.modules.ai_assistant.domain.ports import AssistantConversationRepository
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


def new_conversation_id() -> str:
    return f"aic_{uuid.uuid4().hex[:16]}"


def new_message_id() -> str:
    return f"aim_{uuid.uuid4().hex[:16]}"


def new_feedback_id() -> str:
    return f"aif_{uuid.uuid4().hex[:16]}"


def new_event_id() -> str:
    return f"aie_{uuid.uuid4().hex[:16]}"


class SqliteAssistantConversationRepository(AssistantConversationRepository):
    def save_session(self, session: AssistantConversationSession) -> AssistantConversationSession:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO ai_conversation_sessions (
                  conversation_id, user_id, role, surface, context_json,
                  prompt_version, policy_version, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(conversation_id) DO UPDATE SET
                  role = excluded.role,
                  surface = excluded.surface,
                  context_json = excluded.context_json,
                  prompt_version = excluded.prompt_version,
                  policy_version = excluded.policy_version,
                  status = excluded.status,
                  updated_at = excluded.updated_at
                """,
                (
                    session.conversation_id,
                    session.user_id,
                    session.role,
                    session.surface,
                    json.dumps(session.context, ensure_ascii=False),
                    session.prompt_version,
                    session.policy_version,
                    session.status,
                    session.created_at,
                    session.updated_at,
                ),
            )
            conn.commit()
        return session

    def get_session(self, *, conversation_id: str) -> AssistantConversationSession | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT conversation_id, user_id, role, surface, context_json,
                       prompt_version, policy_version, status, created_at, updated_at
                FROM ai_conversation_sessions
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()
        if row is None:
            return None
        return AssistantConversationSession(
            conversation_id=row["conversation_id"],
            user_id=row["user_id"],
            role=row["role"],
            surface=row["surface"],
            context=json.loads(row["context_json"] or "{}"),
            prompt_version=row["prompt_version"],
            policy_version=row["policy_version"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_recent_messages(self, *, conversation_id: str, limit: int = 8) -> tuple[AssistantMessage, ...]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT message_id, conversation_id, sender, content, classified_intent,
                       risk_labels_json, structured_output_json, created_at
                FROM ai_messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (conversation_id, max(1, min(limit, 20))),
            ).fetchall()
        messages: list[AssistantMessage] = []
        for row in reversed(rows):
            messages.append(
                AssistantMessage(
                    message_id=row["message_id"],
                    conversation_id=row["conversation_id"],
                    sender=row["sender"],
                    content=row["content"],
                    classified_intent=row["classified_intent"],
                    risk_labels=tuple(json.loads(row["risk_labels_json"] or "[]")),
                    structured_output=json.loads(row["structured_output_json"] or "{}"),
                    created_at=row["created_at"],
                )
            )
        return tuple(messages)

    def save_message(self, message: AssistantMessage) -> AssistantMessage:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO ai_messages (
                  message_id, conversation_id, sender, content, classified_intent,
                  risk_labels_json, structured_output_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.message_id,
                    message.conversation_id,
                    message.sender,
                    message.content,
                    message.classified_intent,
                    json.dumps(list(message.risk_labels), ensure_ascii=False),
                    json.dumps(message.structured_output, ensure_ascii=False),
                    message.created_at,
                ),
            )
            conn.commit()
        return message

    def save_feedback(self, feedback: AssistantFeedback) -> AssistantFeedback:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO ai_feedback (
                  feedback_id, conversation_id, message_id, rating, reason_code, free_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.feedback_id,
                    feedback.conversation_id,
                    feedback.message_id,
                    feedback.rating,
                    feedback.reason_code,
                    feedback.free_text,
                    feedback.created_at,
                ),
            )
            conn.commit()
        return feedback

    def save_event(self, event: AssistantEventLog) -> AssistantEventLog:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO ai_event_logs (
                  event_id, conversation_id, role, surface, intent, route_decision,
                  guardrail_triggered, tool_calls_json, latency_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.conversation_id,
                    event.role,
                    event.surface,
                    event.intent,
                    event.route_decision,
                    int(event.guardrail_triggered),
                    json.dumps(list(event.tool_calls), ensure_ascii=False),
                    event.latency_ms,
                    event.created_at,
                ),
            )
            conn.commit()
        return event


def reset_ai_assistant_state() -> None:
    reset_app_state_tables()
