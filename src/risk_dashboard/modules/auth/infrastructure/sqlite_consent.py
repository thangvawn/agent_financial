from __future__ import annotations

import logging
from datetime import datetime, timezone

from risk_dashboard.modules.auth.schemas.principal import ConsentSnapshot
from risk_dashboard.platform.database import open_app_state_db

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SqliteAccountConsentRepository:
    def __init__(self) -> None:
        self._ensure_table()

    def _ensure_table(self) -> None:
        try:
            with open_app_state_db() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS account_consents (
                        account_id TEXT PRIMARY KEY,
                        memory INTEGER NOT NULL DEFAULT 1,
                        analytics INTEGER NOT NULL DEFAULT 1,
                        policy_version TEXT NOT NULL DEFAULT '1.0.0',
                        consented_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
        except Exception as exc:
            logger.warning("Failed to ensure account_consents table: %s", exc)

    def get(self, *, account_id: str) -> ConsentSnapshot | None:
        try:
            with open_app_state_db() as conn:
                row = conn.execute(
                    """
                    SELECT memory, analytics, policy_version, consented_at
                    FROM account_consents WHERE account_id = ?
                    """,
                    (account_id,),
                ).fetchone()
            if row is None:
                return None
            return ConsentSnapshot(
                schema_version="1.0.0",
                memory=bool(row["memory"]),
                analytics=bool(row["analytics"]),
                policy_version=str(row["policy_version"]),
                consented_at=row["consented_at"],
            )
        except Exception as exc:
            logger.warning(
                "Failed to get consent for account %s: %s", account_id, exc, exc_info=True
            )
            return None

    def save(self, *, account_id: str, consent: ConsentSnapshot) -> ConsentSnapshot:
        now = _utc_now_iso()
        consented_at = consent.consented_at or now
        try:
            with open_app_state_db() as conn:
                conn.execute(
                    """
                    INSERT INTO account_consents (
                        account_id, memory, analytics, policy_version, consented_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(account_id) DO UPDATE SET
                        memory = excluded.memory,
                        analytics = excluded.analytics,
                        policy_version = excluded.policy_version,
                        consented_at = excluded.consented_at,
                        updated_at = excluded.updated_at
                    """,
                    (
                        account_id,
                        1 if consent.memory else 0,
                        1 if consent.analytics else 0,
                        consent.policy_version,
                        consented_at,
                        now,
                        now,
                    ),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(
                "Failed to save consent for account %s: %s", account_id, exc, exc_info=True
            )
        return consent

    def revoke(self, *, account_id: str) -> None:
        now = _utc_now_iso()
        try:
            with open_app_state_db() as conn:
                conn.execute(
                    """
                    UPDATE account_consents
                    SET memory = 0, analytics = 0, updated_at = ?
                    WHERE account_id = ?
                    """,
                    (now, account_id),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(
                "Failed to revoke consent for account %s: %s", account_id, exc, exc_info=True
            )
