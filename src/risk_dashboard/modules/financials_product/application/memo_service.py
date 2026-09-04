from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal, Sequence
import uuid

from risk_dashboard.modules.financials_product.domain.ports import MemoRepositoryPort
from risk_dashboard.modules.financials_product.infrastructure.sqlite_memo_repository import (
    SqliteMemoRepository,
)
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    CalculateRatioOutput,
    EvidenceRow,
    ProvenanceRef,
)
from risk_dashboard.modules.financials_product.schemas.evidence import BCTCEvidenceMemo


class MemoService:
    """Manages creation, retrieval, and staleness lifecycle for BCTC Evidence Memos."""

    def __init__(self, repo: MemoRepositoryPort | None = None) -> None:
        self.repo = repo or SqliteMemoRepository()

    def create_memo(
        self,
        *,
        account_id: str,
        subject: str,
        report_refs: Sequence[ProvenanceRef],
        scope: str,
        evidence_rows: Sequence[EvidenceRow],
        calculations: Sequence[CalculateRatioOutput] = (),
        interpretations: Sequence[str] = (),
        unresolved_questions: Sequence[str] = (),
        limitations: Sequence[str] = (),
        reviewer_status: Literal["pending", "approved", "rejected"] = "pending",
        expires_at: str | None = None,
    ) -> BCTCEvidenceMemo:
        if not account_id:
            raise ValueError("account_id is required to create a memo.")

        now_dt = datetime.now(timezone.utc)
        exp_dt = expires_at or (now_dt + timedelta(days=30)).isoformat()
        memo_id = f"memo_{uuid.uuid4().hex[:12]}"

        memo = BCTCEvidenceMemo(
            schema_version="1.0.0",
            memo_id=memo_id,
            subject=subject,
            report_refs=tuple(report_refs),
            scope=scope,
            evidence_rows=tuple(evidence_rows),
            calculations=tuple(calculations),
            interpretations=tuple(interpretations),
            unresolved_questions=tuple(unresolved_questions),
            limitations=tuple(limitations),
            reviewer_status=reviewer_status,
            is_stale=False,
            expires_at=exp_dt,
            created_at=now_dt.isoformat(),
            updated_at=now_dt.isoformat(),
        )
        self.repo.save_memo(memo, account_id)
        return memo

    def get_memo(self, *, account_id: str, memo_id: str) -> BCTCEvidenceMemo:
        memo = self.repo.get_memo(memo_id, account_id)
        if memo is None:
            raise KeyError(f"Memo '{memo_id}' not found for account '{account_id}'.")
        return memo

    def check_staleness(
        self,
        *,
        account_id: str,
        memo_id: str,
        current_revision_id: str,
    ) -> bool:
        memo = self.get_memo(account_id=account_id, memo_id=memo_id)
        is_stale = any(ref.revision_id != current_revision_id for ref in memo.report_refs)
        if is_stale and not memo.is_stale:
            self.repo.mark_stale(memo_id)
        return is_stale or memo.is_stale

    def mark_stale(self, *, memo_id: str) -> None:
        self.repo.mark_stale(memo_id)

    def archive_memo(self, *, account_id: str, memo_id: str) -> bool:
        if hasattr(self.repo, "delete_memo"):
            return getattr(self.repo, "delete_memo")(memo_id, account_id)
        return False

