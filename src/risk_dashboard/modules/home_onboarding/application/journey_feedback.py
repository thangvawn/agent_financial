from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from risk_dashboard.modules.home_onboarding.domain.journey_ports import (
    HomeCardRepository,
    HomeFeedbackRepository,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeJourneyFeedbackRequestV1,
    HomeJourneyFeedbackReceiptV1,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_feedback(
    *,
    account_id: str,
    card_id: str,
    request: HomeJourneyFeedbackRequestV1,
    feedback_repo: HomeFeedbackRepository,
    card_repo: HomeCardRepository,
    as_of: str | None = None,
) -> HomeJourneyFeedbackReceiptV1:
    now_iso = as_of or _utc_now_iso()

    # 1. Validate action and snooze parameters
    if request.action not in ("dismiss", "snooze", "complete"):
        raise ValueError(f"Invalid feedback action: {request.action}")

    snooze_until: str | None = None
    if request.action == "snooze":
        if request.snooze_hours not in (24, 72, 168):
            raise ValueError(
                f"Invalid snooze_hours: {request.snooze_hours}. Must be 24, 72, or 168."
            )
        try:
            base_dt = datetime.fromisoformat(now_iso)
            if base_dt.tzinfo is None:
                base_dt = base_dt.replace(tzinfo=timezone.utc)
        except Exception:
            base_dt = datetime.now(timezone.utc)
        snooze_until = (base_dt + timedelta(hours=request.snooze_hours)).isoformat()

    # 2. Check card existence & ownership
    card = card_repo.get_card_by_id(card_id=card_id, account_id=account_id)
    if card is None:
        return HomeJourneyFeedbackReceiptV1(
            receipt_id=f"receipt_{uuid.uuid4().hex[:16]}",
            card_id=card_id,
            status="not_found",
            recorded_at=now_iso,
        )

    # 3. Check card expiry
    if card.expires_at <= now_iso:
        return HomeJourneyFeedbackReceiptV1(
            receipt_id=f"receipt_{uuid.uuid4().hex[:16]}",
            card_id=card_id,
            status="expired",
            recorded_at=now_iso,
        )

    # 4. Record feedback with idempotency check
    receipt = HomeJourneyFeedbackReceiptV1(
        receipt_id=f"receipt_{uuid.uuid4().hex[:16]}",
        card_id=card_id,
        status="recorded",
        recorded_at=now_iso,
    )

    return feedback_repo.record_feedback(
        receipt=receipt,
        account_id=account_id,
        action=request.action,
        snooze_until=snooze_until,
        idempotency_key=request.idempotency_key,
    )

