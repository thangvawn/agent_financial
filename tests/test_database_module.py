from __future__ import annotations

from pathlib import Path

from risk_dashboard.platform.database import (
    clear_db_path_cache,
    connect_db,
    get_db_path,
    open_app_state_db,
    open_db,
)
from risk_dashboard.platform.database.migrate import apply_migrations
from risk_dashboard.storage.sqlite_store import IngestRegistry


def test_get_db_path_respects_canonical_env(tmp_path: Path, monkeypatch):
    target = tmp_path / "northstar.db"
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(target))
    monkeypatch.delenv("RISK_DASHBOARD_APP_STATE_DB", raising=False)
    monkeypatch.delenv("RISK_DASHBOARD_SQLITE", raising=False)
    clear_db_path_cache()
    assert get_db_path() == target.resolve()


def test_migrations_create_baseline_and_ingest(tmp_path: Path, monkeypatch):
    target = tmp_path / "fresh.db"
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(target))
    clear_db_path_cache()

    with open_db() as conn:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        applied = {
            row[0] for row in conn.execute("SELECT id FROM schema_migrations ORDER BY id").fetchall()
        }

    assert "schema_migrations" in tables
    assert "app_kv" in tables
    assert "mp_orders" in tables
    assert "ingest_runs" in tables
    assert "learning_topics" in tables
    assert applied >= {"001_baseline", "002_ingest_runs"}


def test_open_app_state_db_compat_alias(tmp_path: Path, monkeypatch):
    target = tmp_path / "compat.db"
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(target))
    clear_db_path_cache()
    with open_app_state_db() as conn:
        conn.execute("INSERT INTO app_kv(key, value) VALUES (?, ?)", ("db_module", "ok"))
    with open_db() as conn:
        row = conn.execute("SELECT value FROM app_kv WHERE key = ?", ("db_module",)).fetchone()
    assert row["value"] == "ok"


def test_ingest_registry_uses_shared_db(tmp_path: Path, monkeypatch):
    target = tmp_path / "ingest.db"
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(target))
    clear_db_path_cache()

    registry = IngestRegistry()
    try:
        rid = registry.register(
            parquet_path=tmp_path / "panel.parquet",
            start_date="2024-01-01",
            end_date="2024-12-31",
            n_rows=10,
        )
        latest = registry.latest()
    finally:
        registry.close()

    assert latest is not None
    assert latest.id == rid
    assert latest.n_rows == 10


def test_apply_migrations_is_idempotent(tmp_path: Path, monkeypatch):
    target = tmp_path / "idem.db"
    monkeypatch.setenv("RISK_DASHBOARD_DB_PATH", str(target))
    clear_db_path_cache()
    conn = connect_db()
    assert apply_migrations(conn) == []
    assert apply_migrations(conn) == []
    conn.close()
