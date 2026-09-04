from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    SummarySourceRefV1,
)

logger = logging.getLogger(__name__)


def _calc_expires_at(updated_at_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(updated_at_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception as exc:
        logger.warning(f"Error parsing date {updated_at_iso}: {exc}")
        dt = datetime.now(timezone.utc)
    return (dt + timedelta(days=30)).isoformat()


class LearningSummaryReader:
    surface: str = "learn"

    def __init__(self, reader: Any | None = None) -> None:
        self._reader = reader

    def _get_reader(self) -> Any | None:
        if self._reader is not None:
            return self._reader
        try:
            from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import (
                SqliteLearningHomeRepository,
            )
            return SqliteLearningHomeRepository()
        except Exception as exc:
            logger.warning(f"Failed to initialize SqliteLearningHomeRepository: {exc}")
            return None

    def list_reviewed_summaries(
        self,
        *,
        account_id: str,
        scopes: tuple[str, ...],
        as_of: str,
        limit: int = 4,
    ) -> tuple[HomeDomainSummaryV1, ...]:
        reader = self._get_reader()
        if reader is None:
            return ()
        try:
            state = reader.get_home_state(user_id=account_id)
        except Exception as exc:
            logger.warning(
                f"Error retrieving learning home state for account {account_id}: {exc}",
                exc_info=True,
            )
            return ()

        if not state or not getattr(state, "next_lesson_id", None):
            return ()

        lesson_id = str(state.next_lesson_id)
        lesson_title = getattr(state, "next_lesson_title", "") or f"Bài học {lesson_id}"
        path_label = getattr(state, "path_label", "Lộ trình học tập")
        recommendation = getattr(state, "recommendation_summary", "")
        summary_text = (
            recommendation
            or f"Tiếp tục bài học {lesson_title} trên lộ trình {path_label}."
        )
        updated_at = getattr(state, "updated_at", "") or as_of
        expires_at = _calc_expires_at(updated_at)

        source_ref = SummarySourceRefV1(
            surface="learn",
            resource_type="lesson",
            resource_id=lesson_id,
            resource_version=1,
        )

        summary = HomeDomainSummaryV1(
            summary_id=f"summary:learn:{account_id}:{lesson_id}",
            account_id=account_id,
            surface="learn",
            kind="learning_progress",
            title=lesson_title[:120],
            compact_summary=summary_text[:500],
            source_ref=source_ref,
            review_status="reviewed",
            review_policy_version="learn-checkpoint-v1",
            allowed_action_type="open_lesson",
            allowed_cta_path=f"/learn?lesson={lesson_id}",
            state="incomplete",
            created_at=updated_at,
            updated_at=updated_at,
            expires_at=expires_at,
        )
        return (summary,)

