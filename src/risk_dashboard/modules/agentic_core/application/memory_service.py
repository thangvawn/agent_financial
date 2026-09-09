from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from uuid import uuid4
from typing import Any

from risk_dashboard.modules.agentic_core.domain.memory import (
    MemoryItem,
    PROHIBITED_PATTERNS,
    VALID_MEMORY_TYPES,
    VALID_PROVENANCES,
)
from risk_dashboard.modules.agentic_core.infrastructure.sqlite_memory import SqliteMemoryRepository
from risk_dashboard.modules.agentic_core.schemas.memory import MemoryProposal
from risk_dashboard.platform.feature_flags.decorator import feature_flag

logger = logging.getLogger(__name__)


class MemoryGovernor:
    """Governor enforcing memory policies, consent, whitelist, and prohibitions."""

    @staticmethod
    def evaluate_proposal(
        *,
        account_id: str,
        run_id: str | None = None,
        memory_type: str,
        content: str,
        provenance: str,
        confidence: float = 1.0,
        sensitivity: str = "normal",
        ttl_days: int | None = None,
        consent_memory: bool = True,
        memory_mode: str = "on",
    ) -> MemoryProposal | None:
        if not consent_memory or memory_mode != "on":
            logger.info("Memory disabled by consent or mode for account %s; dropping proposal", account_id)
            return None

        if provenance not in VALID_PROVENANCES:
            logger.warning("Rejected memory with non-whitelisted provenance: %s", provenance)
            return None

        if memory_type not in VALID_MEMORY_TYPES:
            logger.warning("Rejected memory with invalid memory_type: %s", memory_type)
            return None

        for pattern in PROHIBITED_PATTERNS:
            if pattern.search(content):
                logger.warning("Prohibited pattern '%s' detected in memory content; blocking write", pattern.pattern)
                return None

        now_iso = datetime.now(timezone.utc).isoformat()
        return MemoryProposal(
            schema_version="1.0.0",
            proposal_id=f"mem_{uuid4().hex}",
            run_id=run_id or f"run_{uuid4().hex}",
            account_id=account_id,
            memory_type=memory_type,
            content=content.strip(),
            provenance=provenance,
            confidence=confidence,
            sensitivity=sensitivity,
            ttl_days=ttl_days,
            created_at=now_iso,
        )


class MemoryService:
    def __init__(self, repository: SqliteMemoryRepository | None = None) -> None:
        self._repo = repository or SqliteMemoryRepository()

    @feature_flag("agentic.memory", default=True, fallback=None)
    def record_memory(
        self,
        *,
        account_id: str,
        run_id: str | None = None,
        memory_type: str,
        content: str,
        provenance: str,
        confidence: float = 1.0,
        sensitivity: str = "normal",
        ttl_days: int | None = None,
        consent_memory: bool = True,
        memory_mode: str = "on",
    ) -> MemoryItem | None:
        proposal = MemoryGovernor.evaluate_proposal(
            account_id=account_id,
            run_id=run_id,
            memory_type=memory_type,
            content=content,
            provenance=provenance,
            confidence=confidence,
            sensitivity=sensitivity,
            ttl_days=ttl_days,
            consent_memory=consent_memory,
            memory_mode=memory_mode,
        )
        if proposal is None:
            return None

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        expires_at_iso = (
            (now + timedelta(days=proposal.ttl_days)).isoformat()
            if proposal.ttl_days is not None
            else None
        )
        item = MemoryItem(
            schema_version="1.0.0",
            memory_id=proposal.proposal_id,
            account_id=proposal.account_id,
            run_id=proposal.run_id,
            memory_type=proposal.memory_type,
            content=proposal.content,
            provenance=proposal.provenance,
            confidence=proposal.confidence,
            sensitivity=proposal.sensitivity,
            ttl_days=proposal.ttl_days,
            expires_at=expires_at_iso,
            created_at=now_iso,
            updated_at=now_iso,
        )
        self._repo.save(item)
        return item

    def get_memory(self, *, account_id: str, memory_id: str) -> MemoryItem | None:
        return self._repo.get(account_id=account_id, memory_id=memory_id)

    def list_memories(self, *, account_id: str, memory_type: str | None = None) -> list[MemoryItem]:
        return self._repo.list(account_id=account_id, memory_type=memory_type)

    def edit_memory(self, *, account_id: str, memory_id: str, new_content: str) -> MemoryItem | None:
        # Validate that new content doesn't violate denylist
        for pattern in PROHIBITED_PATTERNS:
            if pattern.search(new_content):
                logger.warning("Edit rejected due to prohibited pattern: %s", pattern.pattern)
                return None

        now_iso = datetime.now(timezone.utc).isoformat()
        success = self._repo.update_content(
            account_id=account_id,
            memory_id=memory_id,
            new_content=new_content.strip(),
            updated_at=now_iso,
        )
        if not success:
            return None
        return self._repo.get(account_id=account_id, memory_id=memory_id)

    def forget_memory(self, *, account_id: str, memory_id: str) -> bool:
        return self._repo.delete(account_id=account_id, memory_id=memory_id)

    def export_memories(self, *, account_id: str) -> dict[str, Any]:
        items = self._repo.list(account_id=account_id)
        return {
            "account_id": account_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total": len(items),
            "memories": [item.model_dump(mode="json") for item in items],
        }
