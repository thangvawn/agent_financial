from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_conversation_repository import (
    SqliteConversationRepository,
)
from risk_dashboard.modules.ai_tutor.infrastructure.sqlite_feedback_repository import (
    SqliteFeedbackRepository,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import FeedbackEntity
from risk_dashboard.modules.ai_tutor.schemas.requests import SubmitFeedbackRequest
from risk_dashboard.modules.ai_tutor.schemas.responses import FeedbackResponse


class MessageNotFoundError(Exception):
    """Raised when the message does not exist or does not belong to the requesting account."""


class FeedbackService:
    def __init__(
        self,
        repository: SqliteFeedbackRepository | None = None,
        conv_repository: SqliteConversationRepository | None = None,
    ) -> None:
        self.repository = repository or SqliteFeedbackRepository()
        self.conv_repository = conv_repository or SqliteConversationRepository()

    def submit_feedback(
        self, *, account_id: str, message_id: str, request: SubmitFeedbackRequest
    ) -> FeedbackResponse:
        # Verify ownership of message by principal account
        result = self.conv_repository.get_message_with_ownership(
            message_id=message_id, account_id=account_id
        )
        if result is None:
            raise MessageNotFoundError(
                "Không tìm thấy tin nhắn hoặc tin nhắn không thuộc quyền sở hữu của bạn."
            )

        msg, conv = result

        if request.idempotency_key:
            existing = self.repository.get_by_idempotency(
                message_id=message_id,
                idempotency_key=request.idempotency_key,
                account_id=account_id,
            )
            if existing:
                return FeedbackResponse(
                    feedback_id=existing.feedback_id,
                    message_id=existing.message_id,
                    status="recorded",
                    created_at=existing.created_at,
                )

        now_iso = datetime.now(timezone.utc).isoformat()
        feedback_id = f"fb_{uuid4().hex[:12]}"
        conv_id = conv.conversation_id

        entity = FeedbackEntity(
            feedback_id=feedback_id,
            conversation_id=conv_id,
            message_id=message_id,
            account_id=account_id,
            rating=request.rating,
            reason_code=request.reason_code,
            comment=request.comment,
            idempotency_key=request.idempotency_key,
            created_at=now_iso,
        )
        saved = self.repository.save_feedback(entity)
        return FeedbackResponse(
            feedback_id=saved.feedback_id,
            message_id=saved.message_id,
            status="recorded",
            created_at=saved.created_at,
        )
