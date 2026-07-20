"""Canonical database path resolution for Northstar."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def project_root() -> Path:
    # platform/database/config.py → parents[4] = repo root
    return Path(__file__).resolve().parents[4]


@lru_cache(maxsize=1)
def get_db_path() -> Path:
    """Single transactional SQLite path.

    Priority:
    1. RISK_DASHBOARD_DB_PATH (canonical)
    2. RISK_DASHBOARD_APP_STATE_DB (compat)
    3. RISK_DASHBOARD_SQLITE (compat ingest/pipeline)
    4. data/db/northstar.db, else legacy paths if present
    """
    for key in ("RISK_DASHBOARD_DB_PATH", "RISK_DASHBOARD_APP_STATE_DB", "RISK_DASHBOARD_SQLITE"):
        raw = os.getenv(key)
        if raw:
            return Path(raw).expanduser().resolve()

    root = project_root()
    candidates = (
        root / "data" / "db" / "northstar.db",
        root / "data" / "northstar.db",
        root / "data" / "app_state.db",
    )
    for path in candidates:
        if path.exists():
            return path.resolve()
    return candidates[0].resolve()


def clear_db_path_cache() -> None:
    get_db_path.cache_clear()
