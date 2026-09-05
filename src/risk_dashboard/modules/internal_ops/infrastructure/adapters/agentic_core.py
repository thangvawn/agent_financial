from __future__ import annotations

from datetime import datetime, timezone

from risk_dashboard.modules.internal_ops.application.policy import PurposeGrant
from risk_dashboard.modules.internal_ops.domain.contracts import EvidenceBatch


class AgenticCoreAdapter:
    """Agentic Core adapter is disabled until AC6 freezes application read services."""

    def __init__(self) -> None:
        self.is_enabled = False

    def get_run_trace(self, grant: PurposeGrant, run_id: str) -> EvidenceBatch:
        return EvidenceBatch(
            items=(),
            source_module="agentic_core",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="source_unavailable",
        )

    def get_skill_eval_diff(self, grant: PurposeGrant, skill_name: str) -> EvidenceBatch:
        return EvidenceBatch(
            items=(),
            source_module="agentic_core",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="source_unavailable",
        )

