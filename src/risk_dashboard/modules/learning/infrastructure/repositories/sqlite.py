from __future__ import annotations

import json

from risk_dashboard.modules.learning.domain.entities import (
    CheckpointRecord,
    LearningCmsDocument,
    LearningHomeState,
    LearningProgress,
    ProgressReceiptRecord,
    VerifiedEventRecord,
)
from risk_dashboard.modules.learning.domain.ports import (
    LearningCheckpointRepository,
    LearningCmsRepository,
    LearningHomeReader,
    LearningHomeWriter,
    LearningProgressRepository,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


class SqliteLearningHomeRepository(LearningHomeReader, LearningHomeWriter, LearningProgressRepository):
    def get_home_state(self, *, user_id: str) -> LearningHomeState:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT user_id, path_id, path_label, next_lesson_id, next_lesson_title,
                       recommendation_summary, completed_lessons, completion_pct, updated_at
                FROM learning_home_states
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            raise ValueError("Learning home state not found.")
        return LearningHomeState(
            user_id=row["user_id"],
            path_id=row["path_id"],
            path_label=row["path_label"],
            next_lesson_id=row["next_lesson_id"],
            next_lesson_title=row["next_lesson_title"],
            recommendation_summary=row["recommendation_summary"],
            completed_lessons=row["completed_lessons"],
            completion_pct=row["completion_pct"],
            updated_at=row["updated_at"],
        )

    def save_home_state(self, state: LearningHomeState) -> LearningHomeState:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO learning_home_states (
                    user_id, path_id, path_label, next_lesson_id, next_lesson_title,
                    recommendation_summary, completed_lessons, completion_pct, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    path_id = excluded.path_id,
                    path_label = excluded.path_label,
                    next_lesson_id = excluded.next_lesson_id,
                    next_lesson_title = excluded.next_lesson_title,
                    recommendation_summary = excluded.recommendation_summary,
                    completed_lessons = excluded.completed_lessons,
                    completion_pct = excluded.completion_pct,
                    updated_at = excluded.updated_at
                """,
                (
                    state.user_id,
                    state.path_id,
                    state.path_label,
                    state.next_lesson_id,
                    state.next_lesson_title,
                    state.recommendation_summary,
                    state.completed_lessons,
                    state.completion_pct,
                    state.updated_at,
                ),
            )
            conn.commit()
        return state

    def get_progress(self, *, user_id: str, lesson_id: str) -> LearningProgress | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT user_id, path_id, lesson_id, status, quiz_score, attempt_count, completed_at, updated_at
                FROM learning_lesson_progress
                WHERE user_id = ? AND lesson_id = ?
                """,
                (user_id, lesson_id),
            ).fetchone()
        if row is None:
            return None
        return LearningProgress(
            user_id=row["user_id"],
            path_id=row["path_id"],
            lesson_id=row["lesson_id"],
            status=row["status"],
            quiz_score=row["quiz_score"],
            attempt_count=row["attempt_count"],
            completed_at=row["completed_at"],
            updated_at=row["updated_at"],
        )

    def list_by_path(self, *, user_id: str, path_id: str) -> list[LearningProgress]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT user_id, path_id, lesson_id, status, quiz_score, attempt_count, completed_at, updated_at
                FROM learning_lesson_progress
                WHERE user_id = ? AND path_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id, path_id),
            ).fetchall()
        return [
            LearningProgress(
                user_id=row["user_id"],
                path_id=row["path_id"],
                lesson_id=row["lesson_id"],
                status=row["status"],
                quiz_score=row["quiz_score"],
                attempt_count=row["attempt_count"],
                completed_at=row["completed_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def save_progress(self, progress: LearningProgress) -> LearningProgress:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO learning_lesson_progress (
                    user_id, path_id, lesson_id, status, quiz_score, attempt_count, completed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, lesson_id) DO UPDATE SET
                    path_id = excluded.path_id,
                    status = excluded.status,
                    quiz_score = excluded.quiz_score,
                    attempt_count = excluded.attempt_count,
                    completed_at = excluded.completed_at,
                    updated_at = excluded.updated_at
                """,
                (
                    progress.user_id,
                    progress.path_id,
                    progress.lesson_id,
                    progress.status,
                    progress.quiz_score,
                    progress.attempt_count,
                    progress.completed_at,
                    progress.updated_at,
                ),
            )
            conn.commit()
        return progress


class SqliteLearningCmsRepository(LearningCmsRepository):
    def get_document(self, *, doc_type: str, doc_id: str) -> LearningCmsDocument | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT doc_type, doc_id, status, payload_json, updated_at, published_at
                FROM learning_cms_documents
                WHERE doc_type = ? AND doc_id = ?
                """,
                (doc_type, doc_id),
            ).fetchone()
        if row is None:
            return None
        return LearningCmsDocument(
            doc_type=row["doc_type"],
            doc_id=row["doc_id"],
            status=row["status"],
            payload=json.loads(row["payload_json"]),
            updated_at=row["updated_at"],
            published_at=row["published_at"],
        )

    def list_documents(self, *, doc_type: str) -> list[LearningCmsDocument]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT doc_type, doc_id, status, payload_json, updated_at, published_at
                FROM learning_cms_documents
                WHERE doc_type = ?
                ORDER BY doc_id ASC
                """,
                (doc_type,),
            ).fetchall()
        return [
            LearningCmsDocument(
                doc_type=row["doc_type"],
                doc_id=row["doc_id"],
                status=row["status"],
                payload=json.loads(row["payload_json"]),
                updated_at=row["updated_at"],
                published_at=row["published_at"],
            )
            for row in rows
        ]

    def save_document(self, document: LearningCmsDocument) -> LearningCmsDocument:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO learning_cms_documents (
                    doc_type, doc_id, status, payload_json, updated_at, published_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_type, doc_id) DO UPDATE SET
                    status = excluded.status,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at,
                    published_at = excluded.published_at
                """,
                (
                    document.doc_type,
                    document.doc_id,
                    document.status,
                    json.dumps(document.payload),
                    document.updated_at,
                    document.published_at,
                ),
            )
            conn.commit()
        return document


class SqliteLearningCheckpointRepository(LearningCheckpointRepository):
    def save_checkpoint(self, checkpoint: CheckpointRecord) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO learning_agent_checkpoints (
                    checkpoint_id, account_id, lesson_id, question_id,
                    prompt, options_json, correct_answer, explanation,
                    expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(checkpoint_id) DO UPDATE SET
                    account_id = excluded.account_id,
                    lesson_id = excluded.lesson_id,
                    question_id = excluded.question_id,
                    prompt = excluded.prompt,
                    options_json = excluded.options_json,
                    correct_answer = excluded.correct_answer,
                    explanation = excluded.explanation,
                    expires_at = excluded.expires_at,
                    created_at = excluded.created_at
                """,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.account_id,
                    checkpoint.lesson_id,
                    checkpoint.question_id,
                    checkpoint.prompt,
                    json.dumps(list(checkpoint.options)),
                    checkpoint.correct_answer,
                    checkpoint.explanation,
                    checkpoint.expires_at,
                    checkpoint.created_at,
                ),
            )
            conn.commit()

    def get_checkpoint(self, *, checkpoint_id: str) -> CheckpointRecord | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT checkpoint_id, account_id, lesson_id, question_id,
                       prompt, options_json, correct_answer, explanation,
                       expires_at, created_at
                FROM learning_agent_checkpoints
                WHERE checkpoint_id = ?
                """,
                (checkpoint_id,),
            ).fetchone()
        if row is None:
            return None
        return CheckpointRecord(
            checkpoint_id=row["checkpoint_id"],
            account_id=row["account_id"],
            lesson_id=row["lesson_id"],
            question_id=row["question_id"],
            prompt=row["prompt"],
            options=tuple(json.loads(row["options_json"])),
            correct_answer=row["correct_answer"],
            explanation=row["explanation"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
        )

    def save_verified_event(self, event: VerifiedEventRecord) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO learning_verified_events (
                    event_id, account_id, checkpoint_id, lesson_id,
                    score, passed, rubric_evidence_json, misconceptions_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    account_id = excluded.account_id,
                    checkpoint_id = excluded.checkpoint_id,
                    lesson_id = excluded.lesson_id,
                    score = excluded.score,
                    passed = excluded.passed,
                    rubric_evidence_json = excluded.rubric_evidence_json,
                    misconceptions_json = excluded.misconceptions_json,
                    created_at = excluded.created_at
                """,
                (
                    event.event_id,
                    event.account_id,
                    event.checkpoint_id,
                    event.lesson_id,
                    event.score,
                    1 if event.passed else 0,
                    json.dumps(list(event.rubric_evidence)),
                    json.dumps(list(event.misconceptions)),
                    event.created_at,
                ),
            )
            conn.commit()

    def get_verified_event(self, *, event_id: str) -> VerifiedEventRecord | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT event_id, account_id, checkpoint_id, lesson_id,
                       score, passed, rubric_evidence_json, misconceptions_json,
                       created_at
                FROM learning_verified_events
                WHERE event_id = ?
                """,
                (event_id,),
            ).fetchone()
        if row is None:
            return None
        return VerifiedEventRecord(
            event_id=row["event_id"],
            account_id=row["account_id"],
            checkpoint_id=row["checkpoint_id"],
            lesson_id=row["lesson_id"],
            score=int(row["score"]),
            passed=bool(row["passed"]),
            rubric_evidence=tuple(json.loads(row["rubric_evidence_json"])),
            misconceptions=tuple(json.loads(row["misconceptions_json"])),
            created_at=row["created_at"],
        )

    def get_receipt_by_idempotency_key(self, *, account_id: str, idempotency_key: str) -> ProgressReceiptRecord | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT receipt_id, account_id, verified_event_id, idempotency_key,
                       confirmation_id, lesson_id, status, quiz_score, created_at
                FROM learning_progress_receipts
                WHERE account_id = ? AND idempotency_key = ?
                """,
                (account_id, idempotency_key),
            ).fetchone()
        if row is None:
            return None
        return ProgressReceiptRecord(
            receipt_id=row["receipt_id"],
            account_id=row["account_id"],
            verified_event_id=row["verified_event_id"],
            idempotency_key=row["idempotency_key"],
            confirmation_id=row["confirmation_id"],
            lesson_id=row["lesson_id"],
            status=row["status"],
            quiz_score=int(row["quiz_score"]) if row["quiz_score"] is not None else None,
            created_at=row["created_at"],
        )

    def save_receipt(self, receipt: ProgressReceiptRecord) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO learning_progress_receipts (
                    receipt_id, account_id, verified_event_id, idempotency_key,
                    confirmation_id, lesson_id, status, quiz_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id, idempotency_key) DO UPDATE SET
                    verified_event_id = excluded.verified_event_id,
                    confirmation_id = excluded.confirmation_id,
                    lesson_id = excluded.lesson_id,
                    status = excluded.status,
                    quiz_score = excluded.quiz_score,
                    created_at = excluded.created_at
                """,
                (
                    receipt.receipt_id,
                    receipt.account_id,
                    receipt.verified_event_id,
                    receipt.idempotency_key,
                    receipt.confirmation_id,
                    receipt.lesson_id,
                    receipt.status,
                    receipt.quiz_score,
                    receipt.created_at,
                ),
            )
            conn.commit()


def reset_learning_state() -> None:
    reset_app_state_tables()

