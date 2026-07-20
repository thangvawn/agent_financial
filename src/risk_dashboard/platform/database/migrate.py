"""Ordered SQLite migrations for the shared Northstar DB."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

_PACKAGE = Path(__file__).resolve().parent
_SCHEMA_DIR = _PACKAGE / "schema"

# (migration_id, sql_text_or_path)
def _load_baseline() -> str:
    return (_SCHEMA_DIR / "baseline.sql").read_text(encoding="utf-8")


INGEST_RUNS_SQL = """
CREATE TABLE IF NOT EXISTS ingest_runs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  market_label TEXT,
  macro_label TEXT,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  parquet_path TEXT NOT NULL,
  manifest_path TEXT,
  n_rows INTEGER,
  meta_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_ingest_created ON ingest_runs(created_at DESC);
"""

COMMODITIES_SQL = """
CREATE TABLE IF NOT EXISTS commodity_instruments (
  symbol TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  provider_symbol TEXT,
  category TEXT NOT NULL,
  unit TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commodity_quotes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL REFERENCES commodity_instruments(symbol),
  as_of TEXT NOT NULL,
  price REAL,
  change REAL,
  change_pct REAL,
  high_24h REAL,
  low_24h REAL,
  volume_24h REAL,
  source TEXT NOT NULL,
  freshness TEXT NOT NULL,
  raw_json TEXT,
  UNIQUE(symbol, as_of)
);
CREATE INDEX IF NOT EXISTS idx_commodity_quotes_symbol_time ON commodity_quotes(symbol, as_of DESC);
"""

MIGRATIONS: list[tuple[str, str]] = [
    ("001_baseline", ""),  # filled at runtime from baseline.sql
    ("002_ingest_runs", INGEST_RUNS_SQL),
    ("003_commodities", COMMODITIES_SQL),
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_migrations_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          id TEXT PRIMARY KEY,
          applied_at TEXT NOT NULL
        )
        """
    )


def _applied_ids(conn) -> set[str]:
    rows = conn.execute("SELECT id FROM schema_migrations").fetchall()
    return {str(row[0]) for row in rows}


def _stamp_existing_baseline_if_needed(conn) -> None:
    """Existing app_state.db already has tables but no migration ledger."""
    applied = _applied_ids(conn)
    if "001_baseline" in applied:
        return
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='app_kv' LIMIT 1"
    ).fetchone()
    if row:
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (id, applied_at) VALUES (?, ?)",
            ("001_baseline", _now()),
        )


def apply_migrations(conn) -> list[str]:
    """Apply pending migrations. Returns list of newly applied ids."""
    ensure_migrations_table(conn)
    _stamp_existing_baseline_if_needed(conn)
    applied = _applied_ids(conn)
    newly: list[str] = []

    migrations = [
        ("001_baseline", _load_baseline()),
        ("002_ingest_runs", INGEST_RUNS_SQL),
        ("003_commodities", COMMODITIES_SQL),
    ]
    for mid, sql in migrations:
        if mid in applied:
            continue
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (id, applied_at) VALUES (?, ?)",
            (mid, _now()),
        )
        newly.append(mid)
        applied.add(mid)
    conn.commit()
    return newly
