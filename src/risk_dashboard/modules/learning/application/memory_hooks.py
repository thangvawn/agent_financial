from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from risk_dashboard.modules.learning.domain.entities import VerifiedEventRecord, utc_now_iso
from risk_dashboard.platform.database import open_app_state_db

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MasteryMemoryProposal:
    proposal_id: str
    account_id: str
    lesson_id: str
    score: int
    verified_event_id: str
    topic: str
    created_at: str


@dataclass(frozen=True)
class TeachingPreferenceMemoryProposal:
    proposal_id: str
    account_id: str
    preference_key: str
    preference_value: str
    consent_explicit: bool
    created_at: str


class LearningMemoryGovernor:
    """Deterministic Memory Governor for Learning.

    Invariants:
    1. ONLY verified checkpoints generate mastery proposals. Free-form model output cannot create mastery.
    2. If user disabled memory, zero durable rows are written.
    3. User progress is always read live from learning_lesson_progress, not duplicated as semantic memory.
    4. Supports forget/delete propagation.
    """

    @staticmethod
    def propose_mastery(
        *,
        verified_event: VerifiedEventRecord,
        memory_enabled: bool = True,
    ) -> MasteryMemoryProposal | None:
        if not memory_enabled:
            logger.info("Memory is disabled for account; skipping mastery proposal.")
            return None

        if not verified_event.passed or verified_event.score < 80:
            logger.info(f"Checkpoint did not pass with mastery threshold (score={verified_event.score}); skipping.")
            return None

        from uuid import uuid4

        return MasteryMemoryProposal(
            proposal_id=f"mem_prop_{uuid4().hex}",
            account_id=verified_event.account_id,
            lesson_id=verified_event.lesson_id,
            score=verified_event.score,
            verified_event_id=verified_event.event_id,
            topic=f"mastery:{verified_event.lesson_id}",
            created_at=utc_now_iso(),
        )

    @staticmethod
    def record_mastery_proposal(
        *,
        verified_event: VerifiedEventRecord,
        memory_service: Any,
        memory_enabled: bool = True,
    ) -> Any | None:
        if not memory_enabled or not verified_event.passed or verified_event.score < 80:
            return None

        content = f"Mastered lesson '{verified_event.lesson_id}' with score {verified_event.score}"
        return memory_service.record_memory(
            account_id=verified_event.account_id,
            run_id=f"run_mastery_{verified_event.event_id}",
            memory_type="mastery",
            content=content,
            provenance="deterministic_checkpoint",
            confidence=1.0,
            sensitivity="normal",
            consent_memory=True,
            memory_mode="on",
        )

    @staticmethod
    def propose_preference(
        *,
        account_id: str,
        preference_key: str,
        preference_value: str,
        consent_explicit: bool,
        memory_enabled: bool = True,
    ) -> TeachingPreferenceMemoryProposal | None:
        if not memory_enabled or not consent_explicit:
            logger.info("Explicit consent missing or memory disabled; skipping preference proposal.")
            return None

        from uuid import uuid4

        return TeachingPreferenceMemoryProposal(
            proposal_id=f"pref_prop_{uuid4().hex}",
            account_id=account_id,
            preference_key=preference_key,
            preference_value=preference_value,
            consent_explicit=consent_explicit,
            created_at=utc_now_iso(),
        )

    @staticmethod
    def forget_account_memory(*, account_id: str) -> int:
        """Purge all durable learning memory proposals for an account upon forget request."""
        deleted_count = 0
        with open_app_state_db() as conn:
            # Check if durable agentic_memory_items table exists and purge account scoped records
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agentic_memory_items'")
            if cursor.fetchone():
                cur = conn.execute("DELETE FROM agentic_memory_items WHERE account_id = ?", (account_id,))
                deleted_count += cur.rowcount
            # Check legacy agentic_user_memory table if present
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agentic_user_memory'")
            if cursor.fetchone():
                cur = conn.execute("DELETE FROM agentic_user_memory WHERE user_id = ?", (account_id,))
                deleted_count += cur.rowcount
            conn.commit()
        return deleted_count


