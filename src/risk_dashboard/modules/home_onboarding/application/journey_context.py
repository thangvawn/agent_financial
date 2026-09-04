from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Sequence

from risk_dashboard.modules.home_onboarding.domain.journey_ports import (
    HomeFeedbackRepository,
    HomeSummaryReader,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    ExplicitHomeMemoryV1,
    HomeDomainSummaryV1,
    JourneyContextV1,
    Surface,
)

logger = logging.getLogger(__name__)

MAX_SUMMARIES = 20
MAX_SUMMARY_PAYLOAD_BYTES = 32_000


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_home_journey_context(
    *,
    principal: Any,
    consent: tuple[bool, bool],
    summary_readers: Sequence[HomeSummaryReader] = (),
    feedback_repo: HomeFeedbackRepository | None = None,
    memory_store: Any | None = None,
    as_of: str | None = None,
    onboarding_state: str = "completed",
) -> JourneyContextV1:
    now_iso = as_of or _utc_now_iso()
    account_id = getattr(principal, "account_id", "")
    scopes = tuple(getattr(principal, "scopes", ()))
    personalization_consented, memory_consented = consent

    available_surfaces: list[Surface] = [
        r.surface for r in summary_readers if hasattr(r, "surface")
    ]

    # Invariant: Without personalization consent, do not read any domain summaries
    if not personalization_consented:
        return JourneyContextV1(
            account_id=account_id,
            principal_scopes=scopes,
            consent_policy_version="1.0.0",
            personalization_consented=False,
            memory_consented=False,
            locale="vi-VN",
            onboarding_state=onboarding_state,
            summaries=(),
            explicit_memories=(),
            dismissed_candidate_ids=(),
            snoozed_until_by_candidate={},
            available_surfaces=tuple(available_surfaces),
            built_at=now_iso,
        )

    # 1. Collect and validate domain summaries
    valid_summaries: list[HomeDomainSummaryV1] = []
    current_payload_size = 0

    for reader in summary_readers:
        try:
            summaries = reader.list_reviewed_summaries(
                account_id=account_id,
                scopes=scopes,
                as_of=now_iso,
                limit=4,
            )
        except Exception as exc:
            surface_name = getattr(reader, "surface", "unknown")
            logger.warning(
                f"Failed to read summaries from {surface_name} for account {account_id}: {exc}",
                exc_info=True,
            )
            continue

        for item in summaries:
            if not isinstance(item, HomeDomainSummaryV1):
                continue
            if item.schema_version != "1.0.0":
                continue
            # Enforce strict ownership
            if item.account_id != account_id:
                continue
            # Enforce review status
            if item.review_status not in ("reviewed", "accepted"):
                continue
            # Enforce expiry TTL
            if item.expires_at <= now_iso:
                continue

            summary_len = len(item.compact_summary)
            if len(valid_summaries) >= MAX_SUMMARIES:
                break
            if current_payload_size + summary_len > MAX_SUMMARY_PAYLOAD_BYTES:
                break

            valid_summaries.append(item)
            current_payload_size += summary_len

    # 2. Collect feedback / cooldown states
    dismissed_ids: tuple[str, ...] = ()
    snoozed_map: dict[str, str] = {}
    if feedback_repo is not None:
        try:
            dismissed_ids = feedback_repo.get_dismissed_candidate_ids(
                account_id=account_id
            )
            snoozed_map = feedback_repo.get_snoozed_candidates(
                account_id=account_id, as_of=now_iso
            )
        except Exception as exc:
            logger.warning(
                f"Failed to load feedback state for account {account_id}: {exc}",
                exc_info=True,
            )

    # 3. Collect explicit memories if memory consent is True
    explicit_memories: list[ExplicitHomeMemoryV1] = []
    if memory_consented and memory_store is not None:
        try:
            mems = memory_store.list_memories(account_id=account_id)
            for m in mems:
                if isinstance(m, ExplicitHomeMemoryV1) and m.verified:
                    explicit_memories.append(m)
        except Exception as exc:
            logger.warning(
                f"Failed to load explicit memories for account {account_id}: {exc}",
                exc_info=True,
            )

    return JourneyContextV1(
        account_id=account_id,
        principal_scopes=scopes,
        consent_policy_version="1.0.0",
        personalization_consented=True,
        memory_consented=memory_consented,
        locale="vi-VN",
        onboarding_state=onboarding_state,
        summaries=tuple(valid_summaries),
        explicit_memories=tuple(explicit_memories),
        dismissed_candidate_ids=tuple(dismissed_ids),
        snoozed_until_by_candidate=snoozed_map,
        available_surfaces=tuple(available_surfaces),
        built_at=now_iso,
    )

