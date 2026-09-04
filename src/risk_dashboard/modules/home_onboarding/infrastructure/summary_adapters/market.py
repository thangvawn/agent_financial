from __future__ import annotations

import logging
from typing import Any

from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    SummarySourceRefV1,
)

logger = logging.getLogger(__name__)


class MarketSummaryReader:
    surface: str = "market"

    def __init__(self, repo: Any | None = None) -> None:
        self._repo = repo

    def _get_repo(self) -> Any | None:
        if self._repo is not None:
            return self._repo
        try:
            from risk_dashboard.modules.market_portfolio.infrastructure.artifact_repository import (
                ArtifactRepository,
            )
            return ArtifactRepository()
        except Exception as exc:
            logger.warning(f"Failed to initialize ArtifactRepository: {exc}")
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
            artifacts = repo.list_by_account(account_id=account_id, limit=limit)
        except Exception as exc:
            logger.warning(
                f"Error fetching portfolio artifacts for account {account_id}: {exc}",
                exc_info=True,
            )
            return ()

        summaries: list[HomeDomainSummaryV1] = []
        for art in artifacts:
            expires_at = getattr(art, "expires_at", "") or ""
            if expires_at and expires_at <= as_of:
                continue

            art_id = str(getattr(art, "artifact_id", ""))
            portfolio_id = getattr(art, "portfolio_id", "default")
            summary_text = (
                getattr(art, "summary", "")
                or f"Đánh giá rủi ro danh mục {portfolio_id}."
            )
            created_at = getattr(art, "created_at", "") or as_of

            source_ref = SummarySourceRefV1(
                surface="market",
                resource_type="portfolio_review",
                resource_id=art_id,
                resource_version=1,
            )

            summaries.append(
                HomeDomainSummaryV1(
                    summary_id=f"summary:market:{account_id}:{art_id}",
                    account_id=account_id,
                    surface="market",
                    kind="market_education",
                    title=f"Thị trường: Đánh giá {portfolio_id}"[:120],
                    compact_summary=summary_text[:500],
                    source_ref=source_ref,
                    review_status="reviewed",
                    review_policy_version="market-portfolio-v1",
                    allowed_action_type="read_market_education",
                    allowed_cta_path=f"/market?artifact_id={art_id}",
                    state="ready",
                    created_at=created_at,
                    updated_at=created_at,
                    expires_at=expires_at or as_of,
                )
            )
            if len(summaries) >= limit:
                break

        return tuple(summaries)

