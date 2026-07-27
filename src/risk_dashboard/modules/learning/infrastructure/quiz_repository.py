"""SQLite repository for persistent Quiz Sessions in Learning domain."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
from typing import Any, Dict, Optional

from risk_dashboard.platform.database import open_app_state_db


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS telegram_quiz_sessions (
            session_id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            status TEXT NOT NULL,
            selected_choice_id TEXT,
            created_at TEXT NOT NULL,
            answered_at TEXT,
            expires_at TEXT NOT NULL
        )
        """
    )


class QuizSessionRepository:
    def __init__(self, db_factory: Any = open_app_state_db) -> None:
        self.db_factory = db_factory
        with self.db_factory() as conn:
            _init_db(conn)

    def create_session(
        self,
        session_id: str,
        chat_id: str,
        user_id: str,
        question_id: str,
        expires_in_seconds: int = 600,
    ) -> None:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=expires_in_seconds)
        with self.db_factory() as conn:
            conn.execute(
                """
                INSERT INTO telegram_quiz_sessions (
                    session_id, chat_id, user_id, question_id, status, created_at, expires_at
                ) VALUES (?, ?, ?, ?, 'active', ?, ?)
                """,
                (session_id, str(chat_id), str(user_id), question_id, now.isoformat(), expires.isoformat()),
            )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self.db_factory() as conn:
            row = conn.execute(
                """
                SELECT session_id, chat_id, user_id, question_id, status, selected_choice_id, created_at, answered_at, expires_at
                FROM telegram_quiz_sessions WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "session_id": row[0],
                "chat_id": row[1],
                "user_id": row[2],
                "question_id": row[3],
                "status": row[4],
                "selected_choice_id": row[5],
                "created_at": row[6],
                "answered_at": row[7],
                "expires_at": row[8],
            }

    def answer_session_atomically(self, session_id: str, user_id: str, choice_id: str) -> str:
        """Atomically validates and transitions active quiz session to answered."""
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        with self.db_factory() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT chat_id, user_id, status, expires_at FROM telegram_quiz_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()

            if not row:
                conn.commit()
                return "not_found"

            session_chat_id, session_user_id, status, expires_at_str = row

            if str(session_user_id).strip() != str(user_id).strip():
                conn.commit()
                return "wrong_user"

            if status == "answered":
                conn.commit()
                return "already_answered"

            try:
                expires_at_dt = datetime.fromisoformat(expires_at_str)
                if expires_at_dt.tzinfo is None:
                    expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)
                if now_dt > expires_at_dt:
                    conn.execute(
                        "UPDATE telegram_quiz_sessions SET status = 'expired' WHERE session_id = ?",
                        (session_id,),
                    )
                    conn.commit()
                    return "expired"
            except Exception:
                pass

            conn.execute(
                """
                UPDATE telegram_quiz_sessions
                SET status = 'answered', selected_choice_id = ?, answered_at = ?
                WHERE session_id = ? AND status = 'active'
                """,
                (choice_id, now_iso, session_id),
            )
            conn.commit()
            return "success"
