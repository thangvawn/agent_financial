"""Shared SQLite connection helper for Northstar.

Single-writer pattern: short-lived connections per call. Prefer one
transaction for multi-step writes (see market_portfolio.apply_fill_atomic).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from risk_dashboard.platform.database.config import get_db_path
from risk_dashboard.platform.database.migrate import apply_migrations

# Paths that already ran apply_migrations in this process.
_migrated_paths: set[str] = set()


def clear_migration_cache() -> None:
    _migrated_paths.clear()


def connect_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # timeout: wait on locks under concurrent FastAPI workers (single-writer SQLite).
    # check_same_thread=False: connection must not be shared across threads.
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=15)
    conn.row_factory = sqlite3.Row
    key = str(path.resolve())
    if key not in _migrated_paths:
        apply_migrations(conn)
        _migrated_paths.add(key)
    return conn


@contextmanager
def open_db(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open DB, apply migrations, commit on success, always close."""
    conn = connect_db(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
