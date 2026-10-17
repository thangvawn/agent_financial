from __future__ import annotations

import json
import sqlite3
from typing import Any

from risk_dashboard.platform.database import open_app_state_db


def _ensure_tables(conn: sqlite3.Connection) -> None:
    # Kept idempotent so a developer can use the feature against an older local
    # database before running the next migration.
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS learning_video_transcripts (
            lesson_id TEXT NOT NULL,
            source_key TEXT NOT NULL,
            status TEXT NOT NULL,
            source TEXT NOT NULL,
            language TEXT NOT NULL,
            transcript_hash TEXT NOT NULL,
            segments_json TEXT NOT NULL,
            duration_seconds REAL NOT NULL DEFAULT 0,
            warnings_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (lesson_id, source_key)
        );
        CREATE INDEX IF NOT EXISTS idx_learning_video_transcripts_hash
            ON learning_video_transcripts(transcript_hash);
        CREATE TABLE IF NOT EXISTS learning_video_quizzes (
            lesson_id TEXT NOT NULL,
            transcript_hash TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (lesson_id, transcript_hash)
        );
        CREATE TABLE IF NOT EXISTS learning_video_checkpoints (
            checkpoint_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            transcript_hash TEXT NOT NULL,
            question_json TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_learning_video_checkpoints_account
            ON learning_video_checkpoints(account_id, lesson_id);
        """
    )


class VideoAgentRepository:
    def _connect(self):
        conn = open_app_state_db()
        return conn

    def get_transcript(self, *, lesson_id: str, source_key: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            _ensure_tables(conn)
            row = conn.execute(
                "SELECT * FROM learning_video_transcripts WHERE lesson_id = ? AND source_key = ?",
                (lesson_id, source_key),
            ).fetchone()
        if row is None:
            return None
        return {
            "lesson_id": row["lesson_id"],
            "source_key": row["source_key"],
            "status": row["status"],
            "source": row["source"],
            "language": row["language"],
            "transcript_hash": row["transcript_hash"],
            "segments": json.loads(row["segments_json"]),
            "duration_seconds": float(row["duration_seconds"]),
            "warnings": tuple(json.loads(row["warnings_json"])),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def get_latest_transcript(self, *, lesson_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            _ensure_tables(conn)
            row = conn.execute(
                """
                SELECT * FROM learning_video_transcripts
                WHERE lesson_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (lesson_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "lesson_id": row["lesson_id"],
            "source_key": row["source_key"],
            "status": row["status"],
            "source": row["source"],
            "language": row["language"],
            "transcript_hash": row["transcript_hash"],
            "segments": json.loads(row["segments_json"]),
            "duration_seconds": float(row["duration_seconds"]),
            "warnings": tuple(json.loads(row["warnings_json"])),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def save_transcript(self, record: dict[str, Any]) -> None:
        with self._connect() as conn:
            _ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO learning_video_transcripts (
                    lesson_id, source_key, status, source, language, transcript_hash,
                    segments_json, duration_seconds, warnings_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lesson_id, source_key) DO UPDATE SET
                    status = excluded.status, source = excluded.source,
                    language = excluded.language, transcript_hash = excluded.transcript_hash,
                    segments_json = excluded.segments_json,
                    duration_seconds = excluded.duration_seconds,
                    warnings_json = excluded.warnings_json,
                    updated_at = excluded.updated_at
                """,
                (
                    record["lesson_id"], record["source_key"], record["status"], record["source"],
                    record["language"], record["transcript_hash"], json.dumps(record["segments"], ensure_ascii=False),
                    record["duration_seconds"], json.dumps(list(record.get("warnings", ())), ensure_ascii=False),
                    record["created_at"], record["updated_at"],
                ),
            )

    def get_quiz(self, *, lesson_id: str, transcript_hash: str) -> list[dict[str, Any]] | None:
        with self._connect() as conn:
            _ensure_tables(conn)
            row = conn.execute(
                "SELECT questions_json FROM learning_video_quizzes WHERE lesson_id = ? AND transcript_hash = ?",
                (lesson_id, transcript_hash),
            ).fetchone()
        return json.loads(row["questions_json"]) if row else None

    def save_quiz(self, *, lesson_id: str, transcript_hash: str, questions: list[dict[str, Any]], created_at: str) -> None:
        with self._connect() as conn:
            _ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO learning_video_quizzes (lesson_id, transcript_hash, questions_json, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(lesson_id, transcript_hash) DO UPDATE SET
                    questions_json = excluded.questions_json, created_at = excluded.created_at
                """,
                (lesson_id, transcript_hash, json.dumps(questions, ensure_ascii=False), created_at),
            )

    def save_checkpoint(self, record: dict[str, Any]) -> None:
        with self._connect() as conn:
            _ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO learning_video_checkpoints
                (checkpoint_id, account_id, lesson_id, transcript_hash, question_json, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["checkpoint_id"], record["account_id"], record["lesson_id"],
                    record["transcript_hash"], json.dumps(record["question"], ensure_ascii=False),
                    record["expires_at"], record["created_at"],
                ),
            )

    def get_checkpoint(self, *, checkpoint_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            _ensure_tables(conn)
            row = conn.execute(
                "SELECT * FROM learning_video_checkpoints WHERE checkpoint_id = ?",
                (checkpoint_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "checkpoint_id": row["checkpoint_id"],
            "account_id": row["account_id"],
            "lesson_id": row["lesson_id"],
            "transcript_hash": row["transcript_hash"],
            "question": json.loads(row["question_json"]),
            "expires_at": row["expires_at"],
            "created_at": row["created_at"],
        }
