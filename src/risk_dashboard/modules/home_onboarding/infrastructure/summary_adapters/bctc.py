from __future__ import annotations

import logging
from typing import Any

from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    SummarySourceRefV1,
)

logger = logging.getLogger(__name__)


class BctcSummaryReader:
    surface: str = "bctc"

    def __init__(self, repo: Any | None = None) -> None:
        self._repo = repo

    def _get_repo(self) -> Any | None:
        if self._repo is not None:
            return self._repo
        try:
            from risk_dashboard.modules.financials_product.infrastructure.sqlite_memo_repository import (
                SqliteMemoRepository,
            )
            return SqliteMemoRepository()
        except Exception as exc:
            logger.warning(f"Failed to initialize SqliteMemoRepository: {exc}")
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
            memos = repo.list_memos_by_account(account_id=account_id)
        except Exception as exc:
            logger.warning(
                f"Error fetching BCTC memos for account {account_id}: {exc}",
                exc_info=True,
            )
            return ()

        summaries: list[HomeDomainSummaryV1] = []
        for memo in memos:
            rev_status = getattr(memo, "reviewer_status", "")
            if rev_status not in ("approved",):
                continue

            expires_at = getattr(memo, "expires_at", "") or ""
            if expires_at and expires_at <= as_of:
                continue

            memo_id = str(getattr(memo, "memo_id", ""))
            subject = getattr(memo, "subject", "") or memo_id
            interpretations = getattr(memo, "interpretations", ()) or ()
            summary_text = (
                interpretations[0] if interpretations else f"Phân tích tài chính {subject}"
            )
            unresolved = getattr(memo, "unresolved_questions", ()) or ()
            is_stale = bool(getattr(memo, "is_stale", False))

            if unresolved:
                state = "open_question"
            elif is_stale:
                state = "stale"
            else:
                state = "ready"

            created_at = getattr(memo, "created_at", "") or as_of
            updated_at = getattr(memo, "updated_at", "") or as_of

            # Map domain reviewer_status to HomeDomainSummaryV1 review_status Literal
            mapped_status = "reviewed" if rev_status == "approved" else rev_status

            source_ref = SummarySourceRefV1(
                surface="bctc",
                resource_type="research_memo",
                resource_id=memo_id,
                resource_version=1,
            )

            summaries.append(
                HomeDomainSummaryV1(
                    summary_id=f"summary:bctc:{account_id}:{memo_id}",
                    account_id=account_id,
                    surface="bctc",
                    kind="research_artifact",
                    title=f"BCTC: {subject}"[:120],
                    compact_summary=summary_text[:500],
                    source_ref=source_ref,
                    review_status=mapped_status,
                    review_policy_version="bctc-numeric-v1",
                    allowed_action_type="view_research_memo",
                    allowed_cta_path=f"/bctc?memo_id={memo_id}",
                    state=state,
                    created_at=created_at,
                    updated_at=updated_at,
                    expires_at=expires_at or as_of,
                )
            )
            if len(summaries) >= limit:
                break

        return tuple(summaries)

