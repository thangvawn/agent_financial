from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from risk_dashboard.modules.home_onboarding.domain.home_action_registry import (
    is_action_allowed,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeDomainSummaryV1,
    JourneyContextV1,
)

POLICY_VERSION = "home-ranking-v1"


def _compute_candidate_id(summary: HomeDomainSummaryV1) -> str:
    raw = (
        f"{summary.surface}:"
        f"{summary.source_ref.resource_id}:"
        f"{summary.source_ref.resource_version}:"
        f"{summary.allowed_action_type}:"
        f"{POLICY_VERSION}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _resolve_priority(summary: HomeDomainSummaryV1) -> int:
    # 1. verified incomplete Learn checkpoint = 100
    if summary.surface == "learn" and summary.kind == "learning_progress" and summary.state == "incomplete":
        return 100
    # 2. accepted research artifact with explicit open question = 80
    if summary.kind == "research_artifact" and summary.state == "open_question":
        return 80
    # 3. stale reviewed artifact with refresh CTA = 60
    if summary.kind == "stale_artifact" or summary.state == "stale":
        return 60
    # 4. onboarding goal mapped to education = 40
    if summary.kind == "learning_progress":
        return 40
    # 5. reviewed market education = 20
    if summary.kind == "market_education":
        return 20
    return 10


def create_candidates(
    context: JourneyContextV1,
    *,
    as_of: str | None = None,
) -> list[dict[str, Any]]:
    now_iso = as_of or datetime.now(timezone.utc).isoformat()
    candidates: list[dict[str, Any]] = []

    for summary in context.summaries:
        # Validate action and CTA path
        if not is_action_allowed(summary.allowed_action_type, summary.allowed_cta_path):
            continue

        candidate_id = _compute_candidate_id(summary)

        # Skip dismissed
        if candidate_id in context.dismissed_candidate_ids:
            continue

        # Skip active snoozes
        snoozed_until = context.snoozed_until_by_candidate.get(candidate_id)
        if snoozed_until and snoozed_until > now_iso:
            continue

        priority = _resolve_priority(summary)

        candidates.append({
            "candidate_id": candidate_id,
            "summary": summary,
            "priority": priority,
            "action_type": summary.allowed_action_type,
            "cta_path": summary.allowed_cta_path,
            "target_surface": summary.surface,
            "title": summary.title,
            "why_now": summary.compact_summary[:300],
            "created_at": summary.created_at,
            "updated_at": summary.updated_at,
            "expires_at": summary.expires_at,
        })

    return candidates

