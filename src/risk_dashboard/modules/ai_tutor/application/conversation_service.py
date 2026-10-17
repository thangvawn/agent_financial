from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from risk_dashboard.modules.ai_tutor.application.tutor_graph import TutorGraph
from risk_dashboard.modules.ai_tutor.domain.teaching_policy import sanitize_conversation_input
from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_conversation_repository import (
    SqliteConversationRepository,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    ConversationEntity,
    MessageEntity,
)
from risk_dashboard.modules.ai_tutor.schemas.requests import (
    CreateConversationRequest,
    SendMessageRequest,
)
from risk_dashboard.modules.ai_tutor.schemas.responses import (
    ConversationResponse,
    MessageResponse,
    SendMessageResponse,
)


class ConversationNotFoundError(Exception):
    pass


class ConversationService:
    def __init__(
        self,
        repository: SqliteConversationRepository | None = None,
        graph: TutorGraph | None = None,
    ) -> None:
        self.repository = repository or SqliteConversationRepository()
        self.graph = graph or TutorGraph()

    def create_conversation(
        self, *, account_id: str, request: CreateConversationRequest
    ) -> ConversationResponse:
        existing = self.repository.get_by_idempotency(
            account_id=account_id, idempotency_key=request.idempotency_key
        )
        if existing:
            return self._to_conversation_response(existing, ())

        now_iso = datetime.now(timezone.utc).isoformat()
        conv_id = f"conv_{uuid4().hex[:12]}"
        entity = ConversationEntity(
            conversation_id=conv_id,
            account_id=account_id,
            surface=request.surface,
            context_id=request.context_id,
            status="active",
            title=f"Hội thoại {request.surface.capitalize()}",
            idempotency_key=request.idempotency_key,
            created_at=now_iso,
            updated_at=now_iso,
        )
        saved = self.repository.create_conversation(entity)
        return self._to_conversation_response(saved, ())

    def get_conversation(
        self, *, account_id: str, conversation_id: str
    ) -> ConversationResponse:
        conv = self.repository.get_conversation(
            conversation_id=conversation_id, account_id=account_id
        )
        if conv is None:
            raise ConversationNotFoundError("Không tìm thấy cuộc hội thoại.")
        messages = self.repository.list_messages(
            conversation_id=conversation_id, account_id=account_id
        )
        msg_responses = tuple(self._to_message_response(m) for m in messages)
        return self._to_conversation_response(conv, msg_responses)

    async def send_message(
        self, *, account_id: str, conversation_id: str, request: SendMessageRequest
    ) -> SendMessageResponse:
        conv = self.repository.get_conversation(
            conversation_id=conversation_id, account_id=account_id
        )
        if conv is None:
            raise ConversationNotFoundError("Không tìm thấy cuộc hội thoại.")

        now_iso = datetime.now(timezone.utc).isoformat()
        clean_content = sanitize_conversation_input(request.content)

        user_msg = MessageEntity(
            message_id=f"msg_{uuid4().hex[:12]}",
            conversation_id=conversation_id,
            role="user",
            content=clean_content,
            idempotency_key=f"user_{request.idempotency_key}",
            created_at=now_iso,
        )

        # Atomic idempotency claim
        won_race, existing_msg = self.repository.claim_idempotency(
            conversation_id=conversation_id,
            idempotency_key=request.idempotency_key,
            user_message=user_msg,
        )

        if not won_race:
            if existing_msg is not None and existing_msg.role == "assistant":
                return SendMessageResponse(
                    message_id=existing_msg.message_id,
                    conversation_id=existing_msg.conversation_id,
                    role="assistant",
                    answer=existing_msg.content,
                    citations=existing_msg.citations,
                    numeric_claims=existing_msg.numeric_claims,
                    assumptions=existing_msg.assumptions,
                    limitations=existing_msg.limitations,
                    check_question=existing_msg.check_question,
                    next_action=existing_msg.next_action,
                    trace_id=existing_msg.trace_id,
                    tool_calls=existing_msg.tool_calls,
                    created_at=existing_msg.created_at,
                )
            raise ValueError("Yêu cầu đang được xử lý, vui lòng thử lại sau.")

        # Execute graph with automatic claim release on failure
        try:
            response = await self.graph.execute(
                conversation_id=conversation_id,
                account_id=account_id,
                surface=request.surface or conv.surface,
                user_query=clean_content,
                resource_id=request.current_surface_id or conv.context_id,
                video_time_seconds=request.video_time_seconds,
            )

            # Save assistant message
            asst_msg = MessageEntity(
                message_id=response.message_id,
                conversation_id=conversation_id,
                role="assistant",
                content=response.answer,
                citations=response.citations,
                numeric_claims=response.numeric_claims,
                tool_calls=response.tool_calls,
                assumptions=response.assumptions,
                limitations=response.limitations,
                check_question=response.check_question,
                next_action=response.next_action,
                trace_id=response.trace_id,
                idempotency_key=request.idempotency_key,
                created_at=response.created_at,
            )
            self.repository.save_message(asst_msg)
            return response
        except Exception as exc:
            self.repository.release_claim(
                conversation_id=conversation_id,
                idempotency_key=request.idempotency_key,
            )
            raise exc

    def _to_conversation_response(
        self, conv: ConversationEntity, messages: tuple[MessageResponse, ...]
    ) -> ConversationResponse:
        return ConversationResponse(
            conversation_id=conv.conversation_id,
            surface=conv.surface,
            status=conv.status,
            context_id=conv.context_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(messages),
            messages=messages,
        )

    def _to_message_response(self, msg: MessageEntity) -> MessageResponse:
        return MessageResponse(
            message_id=msg.message_id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            intent=msg.intent,
            citations=msg.citations,
            numeric_claims=msg.numeric_claims,
            tool_calls=msg.tool_calls,
            assumptions=msg.assumptions,
            limitations=msg.limitations,
            check_question=msg.check_question,
            next_action=msg.next_action,
            trace_id=msg.trace_id,
            created_at=msg.created_at,
        )
