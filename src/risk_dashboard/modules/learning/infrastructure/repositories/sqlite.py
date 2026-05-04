from __future__ import annotations

import json

from risk_dashboard.modules.learning.domain.entities import LearningCmsDocument, LearningHomeState, LearningProgress
from risk_dashboard.modules.learning.domain.ports import (
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


def reset_learning_state() -> None:
    reset_app_state_tables()
