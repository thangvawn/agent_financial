from __future__ import annotations

import json
from pathlib import Path

from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeJourneyFeedbackReceiptV1,
    NextBestActionCardV1,
)
from risk_dashboard.platform.database.connection import open_db


class SqliteHomeCardRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = db_path

    def save_selected_card(
        self,
        *,
        card: NextBestActionCardV1,
        account_id: str,
        policy_version: str = "home-ranking-v1",
    ) -> None:
        with open_db(self._db_path) as conn:
            refs = json.dumps([card.target_ref.model_dump()])
            conn.execute(
                """
                INSERT INTO home_journey_cards (
                    card_id, account_id, candidate_id, schema_version,
                    source_refs_json, action_json, policy_version,
                    created_at, expires_at, invalidated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(card_id) DO UPDATE SET
                    action_json = excluded.action_json,
                    expires_at = excluded.expires_at,
                    invalidated_at = NULL
                """,
                (
                    card.card_id, account_id, card.candidate_id, card.schema_version,
                    refs, card.model_dump_json(), policy_version, card.created_at, card.expires_at,
                ),
            )

    def get_active_card(self, *, account_id: str, as_of: str) -> NextBestActionCardV1 | None:
        with open_db(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT action_json FROM home_journey_cards
                WHERE account_id = ? AND invalidated_at IS NULL AND expires_at > ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (account_id, as_of),
            ).fetchone()
            return NextBestActionCardV1.model_validate_json(row["action_json"]) if row else None

    def get_card_by_id(self, *, card_id: str, account_id: str) -> NextBestActionCardV1 | None:
        with open_db(self._db_path) as conn:
            row = conn.execute(
                "SELECT action_json FROM home_journey_cards WHERE card_id = ? AND account_id = ?",
                (card_id, account_id),
            ).fetchone()
            return NextBestActionCardV1.model_validate_json(row["action_json"]) if row else None

    def invalidate_card(self, *, card_id: str, account_id: str, now_iso: str) -> None:
        with open_db(self._db_path) as conn:
            conn.execute(
                "UPDATE home_journey_cards SET invalidated_at = ? WHERE card_id = ? AND account_id = ?",
                (now_iso, card_id, account_id),
            )


class SqliteHomeFeedbackRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = db_path

    def has_already_dismissed(self, *, account_id: str, candidate_id: str) -> bool:
        with open_db(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT 1 FROM home_journey_feedback f JOIN home_journey_cards c ON f.card_id = c.card_id
                WHERE f.account_id = ? AND f.action = 'dismiss' AND c.candidate_id = ? LIMIT 1
                """,
                (account_id, candidate_id),
            ).fetchone()
            return row is not None

    def is_snoozed(self, *, account_id: str, candidate_id: str, as_of: str) -> bool:
        with open_db(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT 1 FROM home_journey_feedback f JOIN home_journey_cards c ON f.card_id = c.card_id
                WHERE f.account_id = ? AND f.action = 'snooze' AND f.snooze_until > ? AND c.candidate_id = ? LIMIT 1
                """,
                (account_id, as_of, candidate_id),
            ).fetchone()
            return row is not None

    def get_dismissed_candidate_ids(self, *, account_id: str) -> tuple[str, ...]:
        with open_db(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT c.candidate_id FROM home_journey_feedback f
                JOIN home_journey_cards c ON f.card_id = c.card_id
                WHERE f.account_id = ? AND f.action = 'dismiss'
                """,
                (account_id,),
            ).fetchall()
            return tuple(str(r[0]) for r in rows)

    def get_snoozed_candidates(self, *, account_id: str, as_of: str) -> dict[str, str]:
        with open_db(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT c.candidate_id, MAX(f.snooze_until) FROM home_journey_feedback f
                JOIN home_journey_cards c ON f.card_id = c.card_id
                WHERE f.account_id = ? AND f.action = 'snooze' AND f.snooze_until > ?
                GROUP BY c.candidate_id
                """,
                (account_id, as_of),
            ).fetchall()
            return {str(r[0]): str(r[1]) for r in rows}

    def record_feedback(
        self,
        *,
        receipt: HomeJourneyFeedbackReceiptV1,
        account_id: str,
        action: str,
        snooze_until: str | None = None,
        idempotency_key: str = "",
    ) -> HomeJourneyFeedbackReceiptV1:
        with open_db(self._db_path) as conn:
            existing = conn.execute(
                "SELECT receipt_id, card_id, created_at FROM home_journey_feedback WHERE account_id = ? AND idempotency_key = ?",
                (account_id, idempotency_key),
            ).fetchone()
            if existing is not None:
                return HomeJourneyFeedbackReceiptV1(
                    receipt_id=str(existing["receipt_id"]),
                    card_id=str(existing["card_id"]),
                    status="duplicate",
                    recorded_at=str(existing["created_at"]),
                )

            conn.execute(
                """
                INSERT INTO home_journey_feedback (
                    receipt_id, account_id, card_id, action,
                    snooze_until, idempotency_key, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_id, account_id, receipt.card_id,
                    action, snooze_until, idempotency_key, receipt.recorded_at,
                ),
            )
            return receipt

