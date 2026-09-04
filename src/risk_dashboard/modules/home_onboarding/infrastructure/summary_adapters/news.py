from __future__ import annotations

import logging
from typing import Any

from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    SummarySourceRefV1,
)

logger = logging.getLogger(__name__)


class NewsSummaryReader:
    surface: str = "news"

    def __init__(self, repo: Any | None = None) -> None:
        self._repo = repo

    def _get_repo(self) -> Any | None:
        if self._repo is not None:
            return self._repo
        try:
            from risk_dashboard.modules.news_intelligence.infrastructure.brief_repository import (
                SqliteBriefRepository,
            )
            return SqliteBriefRepository()
        except Exception as exc:
            logger.warning(f"Failed to initialize SqliteBriefRepository: {exc}")
            return None

    def list_reviewed_summaries(
        self,
        *,
        account_id: str,
        scopes: tuple[str, ...],
        as_of: str,
        limit: int = 4,
    ) -> tuple[HomeDomainSummaryV1, ...]:
        repo = self._get_repo()
        if repo is None:
            return ()

        try:
            briefs = repo.list_by_account(account_id=account_id)
        except Exception as exc:
            logger.warning(
                f"Error fetching news briefs for account {account_id}: {exc}",
                exc_info=True,
            )
            return ()

        summaries: list[HomeDomainSummaryV1] = []
        for brief in briefs:
            rev_status = getattr(brief, "review_status", "")
            if rev_status not in ("reviewed", "accepted"):
                continue

            expires_at = getattr(brief, "expires_at", "") or ""
            if expires_at and expires_at <= as_of:
                continue

            brief_id = str(getattr(brief, "brief_id", ""))
            title = getattr(brief, "title", "") or f"Điểm tin {brief_id}"
            objective = getattr(brief, "objective", "") or title
            version = int(getattr(brief, "version", 1))
            created_at = getattr(brief, "created_at", "") or as_of

            source_ref = SummarySourceRefV1(
                surface="news",
                resource_type="news_brief",
                resource_id=brief_id,
                resource_version=version,
            )

            summaries.append(
                HomeDomainSummaryV1(
                    summary_id=f"summary:news:{account_id}:{brief_id}",
                    account_id=account_id,
                    surface="news",
                    kind="research_artifact",
                    title=f"Điểm tin: {title}"[:120],
                    compact_summary=objective[:500],
                    source_ref=source_ref,
                    review_status=rev_status,
                    review_policy_version="news-brief-v1",
                    allowed_action_type="read_news_brief",
                    allowed_cta_path=f"/news?brief_id={brief_id}",
                    state="ready",
                    created_at=created_at,
                    updated_at=created_at,
                    expires_at=expires_at or as_of,
                )
            )
            if len(summaries) >= limit:
                break

        return tuple(summaries)

