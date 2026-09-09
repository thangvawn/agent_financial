from __future__ import annotations

from datetime import datetime, timezone, timedelta
import os
from typing import Any

from risk_dashboard.platform.feature_flags.decorator import feature_flag


def get_retention_ttl_days(memory_type: str) -> int | None:
    """Retrieve configured retention TTL in days for a memory type.
    Defaults to None (indefinite retention pending compliance/product approval).
    """
    env_var = f"RISK_AGENTIC__RETENTION__{memory_type.upper()}"
    val = os.environ.get(env_var)
    if val is None or not val.strip():
        return None
    try:
        return int(val.strip())
    except ValueError:
        return None


def calculate_expires_at(created_at: str | datetime, ttl_days: int | None) -> str | None:
    """Calculate ISO 8601 UTC expiration timestamp given created_at and ttl_days."""
    if ttl_days is None:
        return None
    if isinstance(created_at, str):
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    else:
        dt = created_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    expires = dt + timedelta(days=ttl_days)
    return expires.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@feature_flag("agentic.retention", default=True, fallback=0)
def purge_expired(conn: Any, account_id: str | None = None) -> int:
    """Purge expired records from agentic memory tables.
    Returns total count of deleted rows.
    """
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    total_deleted = 0
    tables = ["agentic_memory_items", "agentic_memory_proposals"]

    for table in tables:
        if account_id:
            cursor = conn.execute(
                f"DELETE FROM {table} WHERE account_id = ? AND expires_at IS NOT NULL AND expires_at < ?",
                (account_id, now_iso),
            )
        else:
            cursor = conn.execute(
                f"DELETE FROM {table} WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now_iso,),
            )
        total_deleted += cursor.rowcount

    conn.commit()
    return total_deleted


@feature_flag("agentic.retention", default=True, fallback=0)
def delete_account_data(conn: Any, account_id: str) -> int:
    """Delete all agentic memory data associated with an account (GDPR/right-to-be-forgotten cascade).
    Returns total count of deleted rows.
    """
    total_deleted = 0
    tables = [
        "agentic_memory_items",
        "agentic_memory_proposals",
    ]

    for table in tables:
        cursor = conn.execute(
            f"DELETE FROM {table} WHERE account_id = ?",
            (account_id,),
        )
        total_deleted += cursor.rowcount

    conn.commit()
    return total_deleted
