"""SQLite repository for tracking Telegram inbound updates and offset state."""

from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
from typing import Any

from risk_dashboard.platform.database import open_app_state_db


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS telegram_bot_updates (
            update_id INTEGER PRIMARY KEY,
            chat_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            command TEXT,
            status TEXT NOT NULL,
            received_at TEXT NOT NULL,
            processed_at TEXT,
            error TEXT
        )
        """
    )


class TelegramUpdateRepository:
    def __init__(self, db_factory: Any = open_app_state_db) -> None:
        self.db_factory = db_factory
        with self.db_factory() as conn:
            _init_db(conn)

    def get_next_offset(self) -> int:
        """Returns next offset based on MAX update_id recorded in database."""
        with self.db_factory() as conn:
            row = conn.execute(
                "SELECT MAX(update_id) FROM telegram_bot_updates"
            ).fetchone()
            if row and row[0] is not None:
                return row[0] + 1
            return 0

    def is_processed(self, update_id: int) -> bool:
        with self.db_factory() as conn:
            row = conn.execute(
                "SELECT status FROM telegram_bot_updates WHERE update_id = ?",
                (update_id,),
            ).fetchone()
            if row and row[0] in {"processed", "processing", "access_denied", "ignored", "failed_terminal"}:
                return True
            return False

    def record_received(
        self,
        update_id: int,
        chat_id: str,
        user_id: str,
        command: str | None,
        status: str = "received",
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db_factory() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO telegram_bot_updates (
                    update_id, chat_id, user_id, command, status, received_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (update_id, str(chat_id), str(user_id), command, status, now_iso),
            )

    def mark_status(self, update_id: int, status: str, error: str | None = None) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db_factory() as conn:
            conn.execute(
                """
                UPDATE telegram_bot_updates
                SET status = ?, processed_at = ?, error = ?
                WHERE update_id = ?
                """,
                (status, now_iso, error, update_id),
            )
