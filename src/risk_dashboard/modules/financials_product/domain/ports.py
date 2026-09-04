from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    ResolveReportOutput,
)
from risk_dashboard.modules.financials_product.schemas.evidence import (
    BCTCEvidenceMemo,
)


class ReportReader(ABC):
    @abstractmethod
    def resolve_report(
        self,
        ticker: str,
        period: str | None = None,
        refresh: bool = False,
    ) -> ResolveReportOutput:
        """Resolve a report and active revision for a ticker."""
        ...


class UploadOwnershipPort(ABC):
    @abstractmethod
    def check_ownership(self, upload_id: str, account_id: str) -> bool:
        """Verify that the upload belongs to the specified account."""
        ...

    @abstractmethod
    def bind_upload(
        self,
        upload_id: str,
        account_id: str,
        filename: str,
        upload_path: str,
        expires_at: str | None = None,
    ) -> None:
        """Bind an upload to an account."""
        ...


class MemoRepositoryPort(ABC):
    @abstractmethod
    def save_memo(self, memo: BCTCEvidenceMemo, account_id: str) -> None:
        """Persist an evidence memo."""
        ...

    @abstractmethod
    def get_memo(self, memo_id: str, account_id: str) -> BCTCEvidenceMemo | None:
        """Retrieve an evidence memo by ID and account_id."""
        ...

    @abstractmethod
    def list_memos_by_account(self, account_id: str) -> Sequence[BCTCEvidenceMemo]:
        """List all evidence memos for an account."""
        ...

    @abstractmethod
    def mark_stale(self, memo_id: str) -> None:
        """Mark a memo as stale."""
        ...

