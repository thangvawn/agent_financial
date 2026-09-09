from __future__ import annotations

from datetime import datetime, timedelta, timezone
from risk_dashboard.modules.auth.infrastructure.sqlite import SqliteAccountSessionRepository
from risk_dashboard.platform.database import open_app_state_db


class RetentionService:
    """Service enforcing data retention windows and TTL cleanup."""

    def __init__(self, sessions: SqliteAccountSessionRepository | None = None) -> None:
        self._sessions = sessions or SqliteAccountSessionRepository()

    def purge_expired_sessions(self, before_iso: str | None = None) -> int:
        now_iso = before_iso or datetime.now(timezone.utc).isoformat()
        with open_app_state_db() as conn:
            cursor = conn.execute(
                """
                UPDATE account_sessions
                SET status = 'revoked'
                WHERE status = 'active' AND expires_at < ?
                """,
                (now_iso,),
            )
            conn.commit()
            return cursor.rowcount

    def purge_old_audit_logs(self, months: int = 12) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
        cutoff_iso = cutoff.isoformat()
        with open_app_state_db() as conn:
            cursor = conn.execute(
                "DELETE FROM audit_security_logs WHERE created_at < ?",
                (cutoff_iso,),
            )
            conn.commit()
            return cursor.rowcount

    def purge_expired_memories(self) -> int:
        now_iso = datetime.now(timezone.utc).isoformat()
        with open_app_state_db() as conn:
            cursor = conn.execute(
                "DELETE FROM agentic_memory_items WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now_iso,),
            )
            conn.commit()
            return cursor.rowcount

