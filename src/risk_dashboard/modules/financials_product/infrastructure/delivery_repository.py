"""SQLite repository for tracking per-report BCTC release delivery state."""

from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
from typing import Any

from risk_dashboard.platform.database import open_app_state_db


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS telegram_bctc_deliveries (
            delivery_key TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            report_period TEXT NOT NULL,
            report_type TEXT NOT NULL,
            source_version TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            delivered_at TEXT NOT NULL,
            telegram_message_id INTEGER
        )
        """
    )


class FinancialsDeliveryRepository:
    def __init__(self, db_factory: Any = open_app_state_db) -> None:
        self.db_factory = db_factory
        with self.db_factory() as conn:
            _init_db(conn)

    def is_delivered(
        self,
        ticker: str,
        report_period: str,
        report_type: str = "quarter",
        source_version: str = "v1",
        chat_id: str = "default_chat",
    ) -> bool:
        delivery_key = f"{ticker}:{report_period}:{report_type}:{source_version}:{chat_id}"
        with self.db_factory() as conn:
            row = conn.execute(
                "SELECT 1 FROM telegram_bctc_deliveries WHERE delivery_key = ?",
                (delivery_key,),
            ).fetchone()
            return row is not None

    def record_delivery(
        self,
        ticker: str,
        report_period: str,
        report_type: str = "quarter",
        source_version: str = "v1",
        chat_id: str = "default_chat",
        telegram_message_id: int | None = None,
    ) -> str:
        delivery_key = f"{ticker}:{report_period}:{report_type}:{source_version}:{chat_id}"
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db_factory() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO telegram_bctc_deliveries (
                    delivery_key, ticker, report_period, report_type, source_version, chat_id, delivered_at, telegram_message_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (delivery_key, ticker.upper(), report_period, report_type, source_version, str(chat_id), now_iso, telegram_message_id),
            )
        return delivery_key
