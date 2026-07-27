"""SQLite repository for tracking per-chat/user learning card deliveries."""

from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
from typing import Any

from risk_dashboard.platform.database import open_app_state_db


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS telegram_learning_deliveries (
            delivery_key TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            card_id TEXT NOT NULL,
            delivered_at TEXT NOT NULL,
            telegram_message_id INTEGER
        )
        """
    )


class LearningDeliveryRepository:
    def __init__(self, db_factory: Any = open_app_state_db) -> None:
        self.db_factory = db_factory
        with self.db_factory() as conn:
            _init_db(conn)

    def is_delivered(self, chat_id: str, user_id: str, card_id: str) -> bool:
        delivery_key = f"{chat_id}:{user_id}:{card_id}"
        with self.db_factory() as conn:
            row = conn.execute(
                "SELECT 1 FROM telegram_learning_deliveries WHERE delivery_key = ?",
                (delivery_key,),
            ).fetchone()
            return row is not None

    def record_delivery(
        self,
        chat_id: str,
        user_id: str,
        card_id: str,
        telegram_message_id: int | None = None,
    ) -> str:
        delivery_key = f"{chat_id}:{user_id}:{card_id}"
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db_factory() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO telegram_learning_deliveries (
                    delivery_key, chat_id, user_id, card_id, delivered_at, telegram_message_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (delivery_key, str(chat_id), str(user_id), card_id, now_iso, telegram_message_id),
            )
        return delivery_key
