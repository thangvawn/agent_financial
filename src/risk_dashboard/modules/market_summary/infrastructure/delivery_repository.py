"""SQLite repository for delivery and chunk state machine with lease locks, attempt numbers, and safe table rebuild migrations."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Any, Iterator
from risk_dashboard.platform.database import open_app_state_db


def init_delivery_tables(db: sqlite3.Connection) -> None:
    """Creates delivery state machine tables in SQLite app_state_db and safely rebuilds table constraints if migrating from legacy schemas."""
    # Check if legacy table exists
    row = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='telegram_market_deliveries'").fetchone()
    if row:
        sql_def = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='telegram_market_deliveries'").fetchone()[0]
        if sql_def and "UNIQUE(report_date, chat_id, mode)" in sql_def and "attempt_no" not in sql_def:
            # Table has old constraint UNIQUE(report_date, chat_id, mode). Rebuild safely!
            db.commit()
            db.execute("PRAGMA foreign_keys = OFF;")
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    """
                    CREATE TABLE telegram_market_deliveries_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_date TEXT NOT NULL,
                        chat_id TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        attempt_no INTEGER NOT NULL DEFAULT 1,
                        status TEXT NOT NULL,
                        locked_by TEXT,
                        lock_expires_at TEXT,
                        heartbeat_at TEXT,
                        payload_hash TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        sent_at TEXT,
                        last_error TEXT,
                        UNIQUE(report_date, chat_id, mode, attempt_no)
                    );
                    """
                )

                cols_legacy = [r[1] for r in db.execute("PRAGMA table_info(telegram_market_deliveries)").fetchall()]
                has_attempt_no = "attempt_no" in cols_legacy
                select_attempt = "attempt_no" if has_attempt_no else "1 AS attempt_no"

                db.execute(
                    f"""
                    INSERT INTO telegram_market_deliveries_new (
                        id, report_date, chat_id, mode, attempt_no, status, locked_by, lock_expires_at,
                        heartbeat_at, payload_hash, created_at, updated_at, sent_at, last_error
                    )
                    SELECT
                        id, report_date, chat_id, mode, {select_attempt}, status,
                        {"locked_by" if "locked_by" in cols_legacy else "NULL"},
                        {"lock_expires_at" if "lock_expires_at" in cols_legacy else "NULL"},
                        {"heartbeat_at" if "heartbeat_at" in cols_legacy else "NULL"},
                        {"payload_hash" if "payload_hash" in cols_legacy else "NULL"},
                        created_at, updated_at,
                        {"sent_at" if "sent_at" in cols_legacy else "NULL"},
                        {"last_error" if "last_error" in cols_legacy else "NULL"}
                    FROM telegram_market_deliveries;
                    """
                )

                db.execute("DROP TABLE telegram_market_deliveries;")
                db.execute("ALTER TABLE telegram_market_deliveries_new RENAME TO telegram_market_deliveries;")
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.execute("PRAGMA foreign_keys = ON;")

            # Foreign key check
            fk_errors = db.execute("PRAGMA foreign_key_check;").fetchall()
            if fk_errors:
                raise sqlite3.OperationalError(f"Foreign key check failed after table migration: {fk_errors}")

    with db:
        # Ensure base creation for fresh database
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_market_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                attempt_no INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL,
                locked_by TEXT,
                lock_expires_at TEXT,
                heartbeat_at TEXT,
                payload_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sent_at TEXT,
                last_error TEXT,
                UNIQUE(report_date, chat_id, mode, attempt_no)
            );
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_market_delivery_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                payload_hash TEXT,
                status TEXT NOT NULL,
                telegram_message_id INTEGER,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(delivery_id, chunk_index),
                FOREIGN KEY(delivery_id) REFERENCES telegram_market_deliveries(id) ON DELETE CASCADE
            );
            """
        )


class DeliveryRepository:
    def __init__(self, db: sqlite3.Connection | None = None) -> None:
        self._db = db

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if self._db is not None:
            yield self._db
        else:
            with open_app_state_db() as conn:
                init_delivery_tables(conn)
                yield conn

    def acquire_delivery_lock(
        self,
        report_date: str,
        chat_id: str,
        mode: str,
        worker_id: str = "default_worker",
        lease_seconds: int = 60,
    ) -> tuple[int, bool]:
        """Attempts to acquire atomic lease lock for active delivery (report_date, chat_id, mode).
        
        Returns (delivery_id, acquired_boolean).
        """
        now_utc = datetime.now(timezone.utc)
        now_str = now_utc.isoformat()
        expires_str = (now_utc + timedelta(seconds=lease_seconds)).isoformat()

        with self._connection() as db:
            db.commit()
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    """
                    SELECT id, status, lock_expires_at, attempt_no FROM telegram_market_deliveries
                    WHERE report_date = ? AND chat_id = ? AND mode = ? AND status != 'superseded'
                    ORDER BY attempt_no DESC LIMIT 1
                    """,
                    (report_date, chat_id, mode),
                ).fetchone()

                if row:
                    delivery_id, status, lock_expires_at, attempt_no = row[0], row[1], row[2], row[3]
                    if status == "sent":
                        db.commit()
                        return delivery_id, False  # Already delivered!

                    is_stale_lock = (lock_expires_at is None) or (lock_expires_at <= now_str)
                    if not is_stale_lock and status in ("generating", "sending"):
                        db.commit()
                        return delivery_id, False  # Lock active by another worker

                    db.execute(
                        """
                        UPDATE telegram_market_deliveries
                        SET status = 'generating', locked_by = ?, lock_expires_at = ?, heartbeat_at = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (worker_id, expires_str, now_str, now_str, delivery_id),
                    )
                    db.commit()
                    return delivery_id, True
                else:
                    max_att = db.execute(
                        """
                        SELECT COALESCE(MAX(attempt_no), 0) FROM telegram_market_deliveries
                        WHERE report_date = ? AND chat_id = ? AND mode = ?
                        """,
                        (report_date, chat_id, mode),
                    ).fetchone()[0]
                    new_attempt_no = max_att + 1

                    cursor = db.execute(
                        """
                        INSERT INTO telegram_market_deliveries (
                            report_date, chat_id, mode, attempt_no, status, locked_by, lock_expires_at, heartbeat_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'generating', ?, ?, ?, ?, ?)
                        """,
                        (report_date, chat_id, mode, new_attempt_no, worker_id, expires_str, now_str, now_str, now_str),
                    )
                    delivery_id = cursor.lastrowid
                    db.commit()
                    return delivery_id, True

            except sqlite3.IntegrityError:
                db.rollback()
                row_race = db.execute(
                    """
                    SELECT id, status FROM telegram_market_deliveries
                    WHERE report_date = ? AND chat_id = ? AND mode = ?
                    ORDER BY attempt_no DESC LIMIT 1
                    """,
                    (report_date, chat_id, mode),
                ).fetchone()
                if row_race:
                    return row_race[0], False
                raise
            except Exception:
                db.rollback()
                raise

    def get_delivery_payload_hash(self, delivery_id: int) -> str | None:
        """Retrieves the payload_hash stored for a delivery_id."""
        with self._connection() as db:
            row = db.execute(
                "SELECT payload_hash FROM telegram_market_deliveries WHERE id = ?",
                (delivery_id,),
            ).fetchone()
            return row[0] if row else None

    def get_sent_chunk_indices(self, delivery_id: int) -> set[int]:
        """Returns set of chunk indices already successfully sent for this delivery_id."""
        with self._connection() as db:
            rows = db.execute(
                "SELECT chunk_index FROM telegram_market_delivery_chunks WHERE delivery_id = ? AND status = 'sent'",
                (delivery_id,),
            ).fetchall()
            return {r[0] for r in rows}

    def update_delivery_status(
        self,
        delivery_id: int,
        status: str,
        last_error: str | None = None,
        payload_hash: str | None = None,
    ) -> None:
        now_str = datetime.now(timezone.utc).isoformat()
        sent_at = now_str if status == "sent" else None

        with self._connection() as db:
            db.execute(
                """
                UPDATE telegram_market_deliveries
                SET status = ?, last_error = ?, payload_hash = COALESCE(?, payload_hash),
                    sent_at = COALESCE(?, sent_at), updated_at = ?, lock_expires_at = NULL
                WHERE id = ?
                """,
                (status, last_error, payload_hash, sent_at, now_str, delivery_id),
            )

    def record_chunk_sent(
        self,
        delivery_id: int,
        chunk_index: int,
        telegram_message_id: int,
        payload_hash: str | None = None,
    ) -> None:
        now_str = datetime.now(timezone.utc).isoformat()

        with self._connection() as db:
            db.execute(
                """
                INSERT INTO telegram_market_delivery_chunks (
                    delivery_id, chunk_index, payload_hash, status, telegram_message_id, attempts, created_at, updated_at
                ) VALUES (?, ?, ?, 'sent', ?, 1, ?, ?)
                ON CONFLICT(delivery_id, chunk_index) DO UPDATE SET
                    status = 'sent', telegram_message_id = excluded.telegram_message_id,
                    attempts = attempts + 1, updated_at = excluded.updated_at
                """,
                (delivery_id, chunk_index, payload_hash, telegram_message_id, now_str, now_str),
            )

    def record_chunk_failed(
        self,
        delivery_id: int,
        chunk_index: int,
        last_error: str,
    ) -> None:
        now_str = datetime.now(timezone.utc).isoformat()

        with self._connection() as db:
            db.execute(
                """
                INSERT INTO telegram_market_delivery_chunks (
                    delivery_id, chunk_index, status, last_error, attempts, created_at, updated_at
                ) VALUES (?, ?, 'failed', ?, 1, ?, ?)
                ON CONFLICT(delivery_id, chunk_index) DO UPDATE SET
                    status = 'failed', last_error = excluded.last_error,
                    attempts = attempts + 1, updated_at = excluded.updated_at
                """,
                (delivery_id, chunk_index, last_error, now_str, now_str),
            )
