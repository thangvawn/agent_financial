from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from risk_dashboard.modules.agentic_core.application.retention import calculate_expires_at
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
  expires_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agentic_memory_items_account
  ON agentic_memory_items(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agentic_memory_items_type
  ON agentic_memory_items(account_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_agentic_mem_items_expires
  ON agentic_memory_items(expires_at);
"""


class SqliteMemoryRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path

    def _get_conn(self):
        return open_app_state_db(self.db_path)

    def _ensure_tables(self, conn: sqlite3.Connection) -> None:
        conn.executescript(MEMORY_TABLES_SQL)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(agentic_memory_items)").fetchall()}
        if "expires_at" not in cols:
            conn.execute("ALTER TABLE agentic_memory_items ADD COLUMN expires_at TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agentic_mem_items_expires ON agentic_memory_items(expires_at)")

    @staticmethod
    def _row_to_item(row: Any) -> MemoryItem:
        expires_at = row["expires_at"] if "expires_at" in row.keys() else None
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
            expires_at=expires_at,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _save_with_conn(self, conn: sqlite3.Connection, item: MemoryItem) -> None:
        self._ensure_tables(conn)
        owner = conn.execute(
            "SELECT account_id FROM agentic_memory_items WHERE memory_id = ?",
            (item.memory_id,),
        ).fetchone()
        if owner is not None and owner["account_id"] != item.account_id:
            raise ValueError("Memory belongs to another account.")

        expires_at = item.expires_at
        if expires_at is None and item.ttl_days is not None:
            expires_at = calculate_expires_at(item.created_at, item.ttl_days)

        conn.execute(
            """
            INSERT INTO agentic_memory_items (
              memory_id, account_id, run_id, memory_type, content, provenance,
              confidence, sensitivity, ttl_days, expires_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(memory_id) DO UPDATE SET
              content = excluded.content,
              confidence = excluded.confidence,
              expires_at = excluded.expires_at,
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
                expires_at,
                item.created_at,
                item.updated_at,
            ),
        )

    def save(self, item: MemoryItem, conn: sqlite3.Connection | None = None) -> None:
        if conn is not None:
            self._save_with_conn(conn, item)
        else:
            with self._get_conn() as local_conn:
                self._save_with_conn(local_conn, item)

    def get(self, *, account_id: str, memory_id: str) -> MemoryItem | None:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            row = conn.execute(
                "SELECT * FROM agentic_memory_items WHERE memory_id = ? AND account_id = ?",
                (memory_id, account_id),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_item(row)

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

            return [self._row_to_item(r) for r in rows]

    def update_content(self, *, account_id: str, memory_id: str, new_content: str, updated_at: str) -> bool:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            cursor = conn.execute(
                "UPDATE agentic_memory_items SET content = ?, updated_at = ? WHERE memory_id = ? AND account_id = ?",
                (new_content, updated_at, memory_id, account_id),
            )
            return cursor.rowcount > 0

    def _delete_with_conn(self, conn: sqlite3.Connection, *, account_id: str, memory_id: str) -> bool:
        self._ensure_tables(conn)
        cursor = conn.execute(
            "DELETE FROM agentic_memory_items WHERE memory_id = ? AND account_id = ?",
            (memory_id, account_id),
        )
        return cursor.rowcount > 0

    def delete(self, *, account_id: str, memory_id: str, conn: sqlite3.Connection | None = None) -> bool:
        if conn is not None:
            return self._delete_with_conn(conn, account_id=account_id, memory_id=memory_id)
        with self._get_conn() as local_conn:
            return self._delete_with_conn(local_conn, account_id=account_id, memory_id=memory_id)

    def purge_account(self, *, account_id: str) -> int:
        with self._get_conn() as conn:
            self._ensure_tables(conn)
            cursor = conn.execute(
                "DELETE FROM agentic_memory_items WHERE account_id = ?",
                (account_id,),
            )
            return cursor.rowcount
