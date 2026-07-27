"""Unit tests for DeliveryRepository atomic lease locks, attempt numbers, Policy B superseding, safe table rebuild migrations, and state machine."""

from __future__ import annotations

import sqlite3
from risk_dashboard.modules.market_summary.infrastructure.delivery_repository import (
    DeliveryRepository,
    init_delivery_tables,
)


def test_delivery_lock_acquisition_and_dedup():
    conn = sqlite3.connect(":memory:")
    init_delivery_tables(conn)
    repo = DeliveryRepository(db=conn)

    report_date = "2026-07-27"
    chat_id = "123456789"
    mode = "analytical"

    # Worker 1 acquires lock
    del_id1, acquired1 = repo.acquire_delivery_lock(report_date, chat_id, mode, worker_id="worker_1")
    assert acquired1 is True

    # Worker 2 tries to acquire lock while active -> rejected!
    del_id2, acquired2 = repo.acquire_delivery_lock(report_date, chat_id, mode, worker_id="worker_2")
    assert acquired2 is False
    assert del_id1 == del_id2

    # Mark sent
    repo.update_delivery_status(del_id1, status="sent")

    # Worker 3 tries to re-send after sent -> rejected by dedup!
    del_id3, acquired3 = repo.acquire_delivery_lock(report_date, chat_id, mode, worker_id="worker_3")
    assert acquired3 is False


def test_policy_b_supersede_and_attempt_increment():
    conn = sqlite3.connect(":memory:")
    init_delivery_tables(conn)
    repo = DeliveryRepository(db=conn)

    report_date = "2026-07-27"
    chat_id = "123456789"
    mode = "analytical"

    # Attempt 1
    del_id1, acquired1 = repo.acquire_delivery_lock(report_date, chat_id, mode, worker_id="worker_1")
    assert acquired1 is True
    repo.record_chunk_sent(delivery_id=del_id1, chunk_index=0, telegram_message_id=1001)

    # Supersede attempt 1 due to payload hash change
    repo.update_delivery_status(del_id1, status="superseded", last_error="Payload hash changed")

    # Attempt 2 should acquire a NEW clean delivery_id with attempt_no=2 without UNIQUE constraint failure!
    del_id2, acquired2 = repo.acquire_delivery_lock(report_date, chat_id, mode, worker_id="worker_2")
    assert acquired2 is True
    assert del_id2 != del_id1

    # Verify attempt 1 chunks remain intact and isolated
    chunks_del1 = repo.get_sent_chunk_indices(del_id1)
    chunks_del2 = repo.get_sent_chunk_indices(del_id2)

    assert 0 in chunks_del1
    assert 0 not in chunks_del2  # fresh clean chunk state for attempt 2!


def test_table_rebuild_schema_migration():
    conn = sqlite3.connect(":memory:")
    # 1. Create table with legacy schema (UNIQUE on 3 columns)
    conn.execute(
        """
        CREATE TABLE telegram_market_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(report_date, chat_id, mode)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE telegram_market_delivery_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            delivery_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(delivery_id, chunk_index),
            FOREIGN KEY(delivery_id) REFERENCES telegram_market_deliveries(id) ON DELETE CASCADE
        );
        """
    )

    # 2. Insert legacy delivery and chunk records
    conn.execute(
        """
        INSERT INTO telegram_market_deliveries (report_date, chat_id, mode, status, created_at, updated_at)
        VALUES ('2026-07-27', '12345', 'fast', 'superseded', '2026-07-27T10:00:00', '2026-07-27T10:00:00');
        """
    )
    conn.execute(
        """
        INSERT INTO telegram_market_delivery_chunks (delivery_id, chunk_index, status, created_at, updated_at)
        VALUES (1, 0, 'sent', '2026-07-27T10:00:00', '2026-07-27T10:00:00');
        """
    )

    # 3. Execute migration rebuild via init_delivery_tables
    init_delivery_tables(conn)

    # 4. Verify attempt_no = 1 assigned to legacy delivery
    rows = conn.execute("SELECT id, report_date, attempt_no, status FROM telegram_market_deliveries WHERE id = 1").fetchall()
    assert len(rows) == 1
    assert rows[0][2] == 1  # attempt_no = 1

    # 5. Verify chunk foreign key points to delivery_id 1
    chunk_rows = conn.execute("SELECT delivery_id, chunk_index, status FROM telegram_market_delivery_chunks WHERE delivery_id = 1").fetchall()
    assert len(chunk_rows) == 1
    assert chunk_rows[0][0] == 1

    # 6. Verify PRAGMA foreign_key_check passes without errors
    fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
    assert len(fk_errors) == 0

    # 7. Verify PRAGMA foreign_key_list references telegram_market_deliveries
    fk_list = conn.execute("PRAGMA foreign_key_list('telegram_market_delivery_chunks');").fetchall()
    assert len(fk_list) == 1
    assert fk_list[0][2] == "telegram_market_deliveries"

    # 8. Verify attempt_no = 2 can be created on the migrated database without UNIQUE constraint failure!
    repo = DeliveryRepository(db=conn)
    del_id2, acquired2 = repo.acquire_delivery_lock("2026-07-27", "12345", "fast", worker_id="worker_migrated")
    assert acquired2 is True
    assert del_id2 != 1

    # 9. Verify unique index SQL contains attempt_no
    sql_def = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='telegram_market_deliveries'").fetchone()[0]
    assert "attempt_no" in sql_def
