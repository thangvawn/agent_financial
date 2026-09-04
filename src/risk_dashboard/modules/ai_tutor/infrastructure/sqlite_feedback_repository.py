from __future__ import annotations

from risk_dashboard.modules.ai_tutor.schemas.conversation import FeedbackEntity
from risk_dashboard.platform.database import open_app_state_db


class SqliteFeedbackRepository:
    def save_feedback(self, feedback: FeedbackEntity) -> FeedbackEntity:
        """Atomically saves feedback using (message_id, idempotency_key) conflict target.

        Uses DO NOTHING to preserve the original side effect — the first writer wins.
        """
        with open_app_state_db() as conn:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_feedback_msg_idemp ON ai_feedback(message_id, idempotency_key)"
            )
            if feedback.idempotency_key:
                conn.execute(
                    """
                    INSERT INTO ai_feedback (
                        feedback_id, conversation_id, message_id, rating,
                        reason_code, free_text, idempotency_key, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(message_id, idempotency_key) DO NOTHING
                    """,
                    (
                        feedback.feedback_id,
                        feedback.conversation_id,
                        feedback.message_id,
                        1 if feedback.rating == "helpful" else (-1 if feedback.rating == "not_helpful" else 0),
                        feedback.reason_code,
                        feedback.comment,
                        feedback.idempotency_key,
                        feedback.created_at,
                    ),
                )
                # Always return the persisted record (first-writer-wins)
                persisted = self.get_by_idempotency(
                    message_id=feedback.message_id,
                    idempotency_key=feedback.idempotency_key,
                    account_id=feedback.account_id,
                )
                if persisted is not None:
                    return persisted
            else:
                conn.execute(
                    """
                    INSERT INTO ai_feedback (
                        feedback_id, conversation_id, message_id, rating,
                        reason_code, free_text, idempotency_key, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(feedback_id) DO NOTHING
                    """,
                    (
                        feedback.feedback_id,
                        feedback.conversation_id,
                        feedback.message_id,
                        1 if feedback.rating == "helpful" else (-1 if feedback.rating == "not_helpful" else 0),
                        feedback.reason_code,
                        feedback.comment,
                        feedback.idempotency_key,
                        feedback.created_at,
                    ),
                )
        return feedback

    def get_by_idempotency(
        self, *, message_id: str, idempotency_key: str, account_id: str | None = None
    ) -> FeedbackEntity | None:
        """Retrieves feedback by idempotency key with mandatory ownership scope if account_id is given."""
        with open_app_state_db() as conn:
            if account_id:
                row = conn.execute(
                    """
                    SELECT f.feedback_id, f.conversation_id, f.message_id, c.user_id,
                           f.rating, f.reason_code, f.free_text, f.idempotency_key, f.created_at
                    FROM ai_feedback f
                    JOIN ai_conversation_sessions c ON f.conversation_id = c.conversation_id
                    WHERE f.message_id = ? AND f.idempotency_key = ? AND c.user_id = ?
                    """,
                    (message_id, idempotency_key, account_id),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT f.feedback_id, f.conversation_id, f.message_id, c.user_id,
                           f.rating, f.reason_code, f.free_text, f.idempotency_key, f.created_at
                    FROM ai_feedback f
                    JOIN ai_conversation_sessions c ON f.conversation_id = c.conversation_id
                    WHERE f.message_id = ? AND f.idempotency_key = ?
                    """,
                    (message_id, idempotency_key),
                ).fetchone()
        if row is None:
            return None
        return self._row_to_feedback(row)

    def get_feedback(self, *, message_id: str, account_id: str) -> FeedbackEntity | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT f.feedback_id, f.conversation_id, f.message_id, c.user_id,
                       f.rating, f.reason_code, f.free_text, f.idempotency_key, f.created_at
                FROM ai_feedback f
                JOIN ai_conversation_sessions c ON f.conversation_id = c.conversation_id
                WHERE f.message_id = ? AND c.user_id = ?
                """,
                (message_id, account_id),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_feedback(row)

    def _row_to_feedback(self, row) -> FeedbackEntity:
        rating_val = row["rating"]
        rating = "helpful" if rating_val > 0 else ("not_helpful" if rating_val < 0 else "partially_helpful")
        return FeedbackEntity(
            feedback_id=row["feedback_id"],
            conversation_id=row["conversation_id"],
            message_id=row["message_id"],
            account_id=row["user_id"],
            rating=rating,
            reason_code=row["reason_code"],
            comment=row["free_text"],
            idempotency_key=row["idempotency_key"],
            created_at=row["created_at"],
        )
