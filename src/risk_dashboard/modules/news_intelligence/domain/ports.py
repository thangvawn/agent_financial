from __future__ import annotations

from typing import Any, Protocol

from risk_dashboard.modules.news_intelligence.domain.source_health import SourceHealthRecord
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    NewsEvidenceBriefArtifact,
    SourceRef,
)


class SourceRegistryPort(Protocol):
    def get_source(self, source_id: str) -> SourceRef | None:
        ...

    def list_sources(self, **filters: Any) -> list[SourceRef]:
        ...

    def get_health(self, source_ids: tuple[str, ...] = ()) -> list[SourceHealthRecord]:
        ...

    def evaluate_coverage(self, source_ids: tuple[str, ...] = ()) -> bool:
        ...


class BriefRepositoryPort(Protocol):
    def save(self, brief: NewsEvidenceBriefArtifact) -> str:
        ...

    def get(self, brief_id: str, account_id: str) -> NewsEvidenceBriefArtifact | None:
        ...

    def list_by_account(self, account_id: str) -> list[NewsEvidenceBriefArtifact]:
        ...

