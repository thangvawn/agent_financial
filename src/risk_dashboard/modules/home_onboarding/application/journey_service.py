from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from risk_dashboard.modules.home_onboarding.application.journey_candidates import (
    create_candidates,
)
from risk_dashboard.modules.home_onboarding.application.journey_consent import (
    resolve_home_consent,
)
from risk_dashboard.modules.home_onboarding.application.journey_context import (
    build_home_journey_context,
)
from risk_dashboard.modules.home_onboarding.application.journey_ranker import (
    rank_candidates,
)
from risk_dashboard.modules.home_onboarding.domain.journey_ports import (
    HomeCardRepository,
    HomeFeedbackRepository,
    HomeSummaryReader,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeJourneyResponseV1,
    NextBestActionCardV1,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _calc_card_expires_at(summary_expires_at: str, now_iso: str) -> str:
    try:
        now_dt = _parse_iso(now_iso)
    except Exception:
        now_dt = datetime.now(timezone.utc)
    limit_24h = now_dt + timedelta(hours=24)
    try:
        sum_dt = _parse_iso(summary_expires_at)
        return min(sum_dt, limit_24h).isoformat()
    except Exception:
        return limit_24h.isoformat()


def _resolve_cta_label(surface: str, action_type: str) -> str:
    if surface == "learn":
        return "Bắt đầu bài học"
    if action_type == "refresh_artifact":
        return "Làm mới phân tích"
    if action_type == "view_research_memo":
        return "Xem báo cáo"
    return "Khám phá ngay"


async def get_home_journey(
    *,
    principal: Any,
    summary_readers: Sequence[HomeSummaryReader] = (),
    feedback_repo: HomeFeedbackRepository,
    card_repo: HomeCardRepository,
    refresh: bool = False,
    as_of: str | None = None,
    onboarding_state: str = "completed",
) -> HomeJourneyResponseV1:
    now_iso = as_of or _utc_now_iso()
    account_id = getattr(principal, "account_id", "")

    # 1. Resolve consent
    personalization_consented, memory_consented = resolve_home_consent(principal)
    if not personalization_consented:
        return HomeJourneyResponseV1(
            schema_version="1.0.0",
            generated_at=now_iso,
            mode="non_personalized",
            next_best_action=None,
            stale_sources_omitted=0,
            consent_required=True,
        )

    # 2. If not refresh, check active card
    if not refresh:
        active_card = card_repo.get_active_card(account_id=account_id, as_of=now_iso)
        if active_card is not None:
            # Verify card is not dismissed or snoozed
            if not feedback_repo.has_already_dismissed(
                account_id=account_id, candidate_id=active_card.candidate_id
            ) and not feedback_repo.is_snoozed(
                account_id=account_id,
                candidate_id=active_card.candidate_id,
                as_of=now_iso,
            ):
                return HomeJourneyResponseV1(
                    schema_version="1.0.0",
                    generated_at=now_iso,
                    mode="personalized",
                    next_best_action=active_card,
                    stale_sources_omitted=0,
                    consent_required=False,
                )

    # 3. Build journey context
    context = build_home_journey_context(
        principal=principal,
        consent=(personalization_consented, memory_consented),
        summary_readers=summary_readers,
        feedback_repo=feedback_repo,
        as_of=now_iso,
        onboarding_state=onboarding_state,
    )

    # Count stale summaries omitted
    stale_count = sum(1 for s in context.summaries if s.state == "stale")

    # 4. Generate candidates & rank
    candidates = create_candidates(context, as_of=now_iso)
    winner = rank_candidates(candidates)

    if winner is None:
        return HomeJourneyResponseV1(
            schema_version="1.0.0",
            generated_at=now_iso,
            mode="empty",
            next_best_action=None,
            stale_sources_omitted=stale_count,
            consent_required=False,
        )

    # 5. Build selected NextBestActionCardV1
    summary = winner["summary"]
    card_id = f"card_{uuid.uuid4().hex[:16]}"
    expires_at = _calc_card_expires_at(winner["expires_at"], now_iso)
    cta_label = _resolve_cta_label(winner["target_surface"], winner["action_type"])

    card = NextBestActionCardV1(
        schema_version="1.0.0",
        card_id=card_id,
        candidate_id=winner["candidate_id"],
        action_type=winner["action_type"],
        target_surface=winner["target_surface"],
        target_ref=summary.source_ref,
        title=winner["title"],
        why_now=winner["why_now"],
        source_summary_ids=(summary.summary_id,),
        estimated_minutes=15 if winner["target_surface"] == "learn" else None,
        limitations=(),
        cta_label=cta_label,
        cta_path=winner["cta_path"],
        created_at=now_iso,
        expires_at=expires_at,
        dismissible=True,
        snooze_options_hours=(24, 72, 168),
    )

    # 6. Save selected card
    card_repo.save_selected_card(
        card=card, account_id=account_id, policy_version="home-ranking-v1"
    )

    return HomeJourneyResponseV1(
        schema_version="1.0.0",
        generated_at=now_iso,
        mode="personalized",
        next_best_action=card,
        stale_sources_omitted=stale_count,
        consent_required=False,
    )
