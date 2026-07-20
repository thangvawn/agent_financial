"""Northstar shared database module.

Canonical path: ``RISK_DASHBOARD_DB_PATH`` (default ``data/db/northstar.db``).

Public API keeps ``open_app_state_db`` for compatibility.
"""

from risk_dashboard.platform.database.app_state import open_app_state_db, reset_app_state_tables
from risk_dashboard.platform.database.config import clear_db_path_cache, get_db_path, project_root
from risk_dashboard.platform.database.connection import clear_migration_cache, connect_db, open_db
from risk_dashboard.platform.database.migrate import apply_migrations

__all__ = [
    "apply_migrations",
    "clear_db_path_cache",
    "clear_migration_cache",
    "connect_db",
    "get_db_path",
    "open_app_state_db",
    "open_db",
    "project_root",
    "reset_app_state_tables",
]
