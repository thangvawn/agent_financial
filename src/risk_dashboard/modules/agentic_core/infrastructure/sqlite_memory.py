from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from risk_dashboard.modules.agentic_core.domain.memory import MemoryItem
from risk_dashboard.platform.database import open_app_state_db

MEMORY_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS agentic_memory_items (
  memory_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  run_id TEXT,
  memory_type TEXT NOT NULL,
  content TEXT NOT NULL,
  provenance TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  sensitivity TEXT NOT NULL DEFAULT 'normal',
  ttl_days INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_memory_items_account
  ON agentic_memory_items(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agentic_memory_items_type
  ON agentic_memory_items(account_id, memory_type);
"""


class SqliteMemoryRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path

    def _get_conn(self):
        return open_app_state_db(self.db_path)

    def _ensure_tables(self, conn: sqlite3.Connection) -> None:
        conn.executescript(MEMORY_TABLES_SQL)

    def save(self, item: MemoryItem) -> None:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            owner = conn.execute(
                "SELECT account_id FROM agentic_memory_items WHERE memory_id = ?",
                (item.memory_id,),
            ).fetchone()
            if owner is not None and owner["account_id"] != item.account_id:
                raise ValueError("Memory belongs to another account.")

            conn.execute(
                """
                INSERT INTO agentic_memory_items (
                  memory_id, account_id, run_id, memory_type, content, provenance,
                  confidence, sensitivity, ttl_days, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                  content = excluded.content,
                  confidence = excluded.confidence,
                  updated_at = excluded.updated_at
                """,
                (
                    item.memory_id,
                    item.account_id,
                    item.run_id,
                    item.memory_type,
                    item.content,
                    item.provenance,
                    item.confidence,
                    item.sensitivity,
                    item.ttl_days,
                    item.created_at,
                    item.updated_at,
                ),
            )

    def get(self, *, account_id: str, memory_id: str) -> MemoryItem | None:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            row = conn.execute(
                "SELECT * FROM agentic_memory_items WHERE memory_id = ? AND account_id = ?",
                (memory_id, account_id),
            ).fetchone()
            if row is None:
                return None
            return MemoryItem(
                memory_id=row["memory_id"],
                account_id=row["account_id"],
                run_id=row["run_id"],
                memory_type=row["memory_type"],
                content=row["content"],
                provenance=row["provenance"],
                confidence=row["confidence"],
                sensitivity=row["sensitivity"],
                ttl_days=row["ttl_days"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list(self, *, account_id: str, memory_type: str | None = None) -> list[MemoryItem]:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            if memory_type:
                rows = conn.execute(
                    "SELECT * FROM agentic_memory_items WHERE account_id = ? AND memory_type = ? ORDER BY created_at DESC",
                    (account_id, memory_type),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM agentic_memory_items WHERE account_id = ? ORDER BY created_at DESC",
                    (account_id,),
                ).fetchall()

            return [
                MemoryItem(
                    memory_id=r["memory_id"],
                    account_id=r["account_id"],
                    run_id=r["run_id"],
                    memory_type=r["memory_type"],
                    content=r["content"],
                    provenance=r["provenance"],
                    confidence=r["confidence"],
                    sensitivity=r["sensitivity"],
                    ttl_days=r["ttl_days"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def update_content(self, *, account_id: str, memory_id: str, new_content: str, updated_at: str) -> bool:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            cursor = conn.execute(
                "UPDATE agentic_memory_items SET content = ?, updated_at = ? WHERE memory_id = ? AND account_id = ?",
                (new_content, updated_at, memory_id, account_id),
            )
            return cursor.rowcount > 0

    def delete(self, *, account_id: str, memory_id: str) -> bool:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            cursor = conn.execute(
                "DELETE FROM agentic_memory_items WHERE memory_id = ? AND account_id = ?",
                (memory_id, account_id),
            )
            return cursor.rowcount > 0

    def purge_account(self, *, account_id: str) -> int:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            cursor = conn.execute(
                "DELETE FROM agentic_memory_items WHERE account_id = ?",
                (account_id,),
            )
            return cursor.rowcount
