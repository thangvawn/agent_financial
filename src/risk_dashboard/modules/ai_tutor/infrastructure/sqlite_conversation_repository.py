from __future__ import annotations

import json
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    ConversationEntity,
    MessageEntity,
    NumericClaimRef,
    ToolCallRef,
)
from risk_dashboard.platform.database import open_app_state_db


class SqliteConversationRepository:
    def create_conversation(self, conversation: ConversationEntity) -> ConversationEntity:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO ai_conversation_sessions (
                    conversation_id, user_id, role, surface, context_id,
                    context_json, prompt_version, policy_version, status,
                    idempotency_key, created_at, updated_at
                )
                VALUES (?, ?, 'user', ?, ?, '{}', 'v1', 'v1', ?, ?, ?, ?)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    status = excluded.status
                """,
                (
                    conversation.conversation_id,
                    conversation.account_id,
                    conversation.surface,
                    conversation.context_id,
                    conversation.status,
                    conversation.idempotency_key,
                    conversation.created_at,
                    conversation.updated_at,
                ),
            )
        return conversation

    def get_conversation(self, *, conversation_id: str, account_id: str) -> ConversationEntity | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT conversation_id, user_id, surface, context_id, status,
                       idempotency_key, created_at, updated_at
                FROM ai_conversation_sessions
                WHERE conversation_id = ? AND user_id = ?
                """,
                (conversation_id, account_id),
            ).fetchone()
        if row is None:
            return None
        return ConversationEntity(
            conversation_id=row["conversation_id"],
            account_id=row["user_id"],
            surface=row["surface"],
            context_id=row["context_id"],
            status=row["status"],
            idempotency_key=row["idempotency_key"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_by_idempotency(self, *, account_id: str, idempotency_key: str) -> ConversationEntity | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT conversation_id, user_id, surface, context_id, status,
                       idempotency_key, created_at, updated_at
                FROM ai_conversation_sessions
                WHERE user_id = ? AND idempotency_key = ?
                """,
                (account_id, idempotency_key),
            ).fetchone()
        if row is None:
            return None
        return ConversationEntity(
            conversation_id=row["conversation_id"],
            account_id=row["user_id"],
            surface=row["surface"],
            context_id=row["context_id"],
            status=row["status"],
            idempotency_key=row["idempotency_key"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_message(self, message: MessageEntity) -> MessageEntity:
        citations_json = json.dumps([c.model_dump() for c in message.citations])
        numeric_json = json.dumps([n.model_dump() for n in message.numeric_claims])
        tools_json = json.dumps([t.model_dump() for t in message.tool_calls])
        struct_json = json.dumps(
            {
                "assumptions": list(message.assumptions),
                "limitations": list(message.limitations),
                "check_question": message.check_question,
                "next_action": message.next_action,
            }
        )
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO ai_messages (
                    message_id, conversation_id, sender, content, classified_intent,
                    risk_labels_json, structured_output_json, citations_json,
                    numeric_claims_json, tool_calls_json, trace_id,
                    idempotency_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, '[]', ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET content = excluded.content
                """,
                (
                    message.message_id,
                    message.conversation_id,
                    message.role,
                    message.content,
                    message.intent,
                    struct_json,
                    citations_json,
                    numeric_json,
                    tools_json,
                    message.trace_id,
                    message.idempotency_key,
                    message.created_at,
                ),
            )
            conn.execute(
                "UPDATE ai_conversation_sessions SET updated_at = ? WHERE conversation_id = ?",
                (message.created_at, message.conversation_id),
            )
        return message

    def get_message_by_idempotency(self, *, conversation_id: str, idempotency_key: str) -> MessageEntity | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT message_id, conversation_id, sender, content, classified_intent,
                       structured_output_json, citations_json, numeric_claims_json,
                       tool_calls_json, trace_id, idempotency_key, created_at
                FROM ai_messages
                WHERE conversation_id = ? AND idempotency_key = ?
                """,
                (conversation_id, idempotency_key),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_message(row)

    def list_messages(
        self, *, conversation_id: str, account_id: str, limit: int = 50, cursor: str | None = None
    ) -> tuple[MessageEntity, ...]:
        conv = self.get_conversation(conversation_id=conversation_id, account_id=account_id)
        if conv is None:
            return ()
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT message_id, conversation_id, sender, content, classified_intent,
                       structured_output_json, citations_json, numeric_claims_json,
                       tool_calls_json, trace_id, idempotency_key, created_at
                FROM ai_messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC, rowid ASC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return tuple(self._row_to_message(row) for row in rows)

    def _row_to_message(self, row) -> MessageEntity:
        citations = []
        if row["citations_json"]:
            try:
                citations = [CitationRef(**c) for c in json.loads(row["citations_json"])]
            except Exception:
                pass

        numeric_claims = []
        if row["numeric_claims_json"]:
            try:
                numeric_claims = [NumericClaimRef(**n) for n in json.loads(row["numeric_claims_json"])]
            except Exception:
                pass

        tool_calls = []
        if row["tool_calls_json"]:
            try:
                tool_calls = [ToolCallRef(**t) for t in json.loads(row["tool_calls_json"])]
            except Exception:
                pass

        assumptions = ()
        limitations = ()
        check_q = None
        next_act = None
        if row["structured_output_json"]:
            try:
                data = json.loads(row["structured_output_json"])
                assumptions = tuple(data.get("assumptions", ()))
                limitations = tuple(data.get("limitations", ()))
                check_q = data.get("check_question")
                next_act = data.get("next_action")
            except Exception:
                pass

        return MessageEntity(
            message_id=row["message_id"],
            conversation_id=row["conversation_id"],
            role="assistant" if row["sender"] == "assistant" else "user",
            content=row["content"],
            intent=row["classified_intent"],
            citations=tuple(citations),
            numeric_claims=tuple(numeric_claims),
            tool_calls=tuple(tool_calls),
            assumptions=assumptions,
            limitations=limitations,
            check_question=check_q,
            next_action=next_act,
            trace_id=row["trace_id"],
            idempotency_key=row["idempotency_key"],
            created_at=row["created_at"],
        )

    def get_message_with_ownership(
        self, *, message_id: str, account_id: str
    ) -> tuple[MessageEntity, ConversationEntity] | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT m.message_id, m.conversation_id, m.sender, m.content, m.classified_intent,
                       m.structured_output_json, m.citations_json, m.numeric_claims_json,
                       m.tool_calls_json, m.trace_id, m.idempotency_key, m.created_at,
                       s.conversation_id AS session_conversation_id, s.user_id, s.surface,
                       s.context_id, s.status AS session_status,
                       s.idempotency_key AS session_idempotency_key,
                       s.created_at AS session_created_at, s.updated_at AS session_updated_at
                FROM ai_messages m
                JOIN ai_conversation_sessions s ON m.conversation_id = s.conversation_id
                WHERE m.message_id = ? AND s.user_id = ?
                """,
                (message_id, account_id),
            ).fetchone()
        if row is None:
            return None
        msg = self._row_to_message(row)
        conv = ConversationEntity(
            conversation_id=row["session_conversation_id"],
            account_id=row["user_id"],
            surface=row["surface"],
            context_id=row["context_id"],
            status=row["session_status"],
            idempotency_key=row["session_idempotency_key"],
            created_at=row["session_created_at"],
            updated_at=row["session_updated_at"],
        )
        return msg, conv

    def release_claim(self, *, conversation_id: str, idempotency_key: str) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                DELETE FROM ai_messages
                WHERE conversation_id = ? AND idempotency_key = ?
                """,
                (conversation_id, f"claim_{idempotency_key}"),
            )

    def claim_idempotency(
        self, *, conversation_id: str, idempotency_key: str, user_message: MessageEntity
    ) -> tuple[bool, MessageEntity | None]:
        """Atomically claims idempotency slot. Returns (True, None) if won the race, or (False, existing_msg)."""
        existing_asst = self.get_message_by_idempotency(
            conversation_id=conversation_id, idempotency_key=idempotency_key
        )
        if existing_asst is not None:
            return False, existing_asst

        try:
            with open_app_state_db() as conn:
                conn.execute(
                    """
                    INSERT INTO ai_messages (
                        message_id, conversation_id, sender, content, classified_intent,
                        risk_labels_json, structured_output_json, citations_json,
                        numeric_claims_json, tool_calls_json, trace_id,
                        idempotency_key, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, '[]', '{}', '[]', '[]', '[]', ?, ?, ?)
                    """,
                    (
                        user_message.message_id,
                        user_message.conversation_id,
                        user_message.role,
                        user_message.content,
                        user_message.intent,
                        user_message.trace_id,
                        f"claim_{idempotency_key}",
                        user_message.created_at,
                    ),
                )
            return True, None
        except Exception:
            existing = self.get_message_by_idempotency(
                conversation_id=conversation_id, idempotency_key=idempotency_key
            )
            return False, existing

    def log_event(
        self,
        *,
        event_id: str,
        conversation_id: str,
        role: str,
        surface: str,
        intent: str,
        route_decision: str,
        guardrail_triggered: int = 0,
        tool_calls_json: str = "[]",
        latency_ms: int = 0,
        created_at: str,
    ) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO ai_event_logs (
                    event_id, conversation_id, role, surface, intent,
                    route_decision, guardrail_triggered, tool_calls_json,
                    latency_ms, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    conversation_id,
                    role,
                    surface,
                    intent,
                    route_decision,
                    guardrail_triggered,
                    tool_calls_json,
                    latency_ms,
                    created_at,
                ),
            )


