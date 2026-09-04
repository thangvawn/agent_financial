from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any

from risk_dashboard.modules.market_portfolio.schemas.agent_api import PortfolioReviewArtifactV1
from risk_dashboard.platform.database import open_app_state_db

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ArtifactRepository:
    """Account-scoped storage for PortfolioReviewArtifactV1."""

    def __init__(self) -> None:
        self._ensure_table()

    def _ensure_table(self) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mp_portfolio_review_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    portfolio_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    review_type TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_mp_artifacts_acc_idemp
                ON mp_portfolio_review_artifacts (account_id, idempotency_key)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_mp_artifacts_acc_art
                ON mp_portfolio_review_artifacts (account_id, artifact_id)
                """
            )
            conn.commit()

    def get_by_idempotency_key(self, account_id: str, idempotency_key: str) -> PortfolioReviewArtifactV1 | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT schema_version, payload_json, expires_at
                FROM mp_portfolio_review_artifacts
                WHERE account_id = ? AND idempotency_key = ?
                """,
                (account_id, idempotency_key),
            ).fetchone()
            if not row:
                return None
            if row["expires_at"] <= _utc_now_iso():
                return None
            if row["schema_version"] != "1.0.0":
                logger.warning("Unsupported artifact schema_version %s", row["schema_version"])
                return None
            data = json.loads(row["payload_json"])
            return PortfolioReviewArtifactV1.model_validate(data)

    def get_artifact(self, account_id: str, artifact_id: str) -> PortfolioReviewArtifactV1 | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT schema_version, payload_json, expires_at
                FROM mp_portfolio_review_artifacts
                WHERE account_id = ? AND artifact_id = ?
                """,
                (account_id, artifact_id),
            ).fetchone()
            if not row:
                return None
            if row["expires_at"] <= _utc_now_iso():
                return None
            if row["schema_version"] != "1.0.0":
                logger.warning("Unsupported artifact schema_version %s", row["schema_version"])
                return None
            data = json.loads(row["payload_json"])
            return PortfolioReviewArtifactV1.model_validate(data)

    def list_by_account(self, account_id: str, limit: int = 10) -> list[PortfolioReviewArtifactV1]:
        now_iso = _utc_now_iso()
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT schema_version, payload_json, expires_at
                FROM mp_portfolio_review_artifacts
                WHERE account_id = ? AND expires_at > ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (account_id, now_iso, limit),
            ).fetchall()
            artifacts: list[PortfolioReviewArtifactV1] = []
            for row in rows:
                if row["schema_version"] != "1.0.0":
                    continue
                try:
                    data = json.loads(row["payload_json"])
                    artifacts.append(PortfolioReviewArtifactV1.model_validate(data))
                except Exception as exc:
                    logger.warning("Failed to deserialize artifact: %s", exc)
            return artifacts

    def save_artifact(self, artifact: PortfolioReviewArtifactV1, idempotency_key: str) -> PortfolioReviewArtifactV1:
        payload_json = json.dumps(artifact.model_dump())
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO mp_portfolio_review_artifacts (
                    artifact_id, account_id, portfolio_id, idempotency_key,
                    review_type, schema_version, payload_json, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id, idempotency_key) DO UPDATE SET
                    artifact_id = excluded.artifact_id,
                    payload_json = excluded.payload_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (
                    artifact.artifact_id,
                    artifact.account_id,
                    artifact.portfolio_id,
                    idempotency_key,
                    artifact.review_type,
                    artifact.schema_version,
                    payload_json,
                    artifact.created_at,
                    artifact.expires_at,
                ),
            )
            conn.commit()
        return artifact

    def purge_expired(self, now_iso: str | None = None) -> int:
        cutoff = now_iso or _utc_now_iso()
        with open_app_state_db() as conn:
            cur = conn.execute(
                "DELETE FROM mp_portfolio_review_artifacts WHERE expires_at <= ?",
                (cutoff,),
            )
            conn.commit()
            return cur.rowcount

