from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.home_onboarding.application.journey_feedback import (
    record_feedback,
)
from risk_dashboard.modules.home_onboarding.application.journey_service import (
    get_home_journey,
)
from risk_dashboard.modules.home_onboarding.infrastructure.sqlite_journey import (
    SqliteHomeCardRepository,
    SqliteHomeFeedbackRepository,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters import (
    SURFACE_READERS,
)
from risk_dashboard.modules.home_onboarding.schemas.journey import (
    HomeJourneyFeedbackReceiptV1,
    HomeJourneyFeedbackRequestV1,
    HomeJourneyResponseV1,
)
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

FEATURE_FLAG = "module.home_onboarding.home_journey.v1.enabled"

router = APIRouter(prefix="/home-journey", tags=["Home Journey"])


def _check_journey_flag() -> None:
    if not FeatureFlagService().is_enabled(FEATURE_FLAG, default=False):
        raise HTTPException(status_code=404, detail="Home journey is disabled.")


def _check_read_scope(principal: AuthPrincipal) -> None:
    if not principal.account_id or principal.is_anonymous:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if "me:home_journey:read" not in principal.scopes:
        raise HTTPException(
            status_code=403, detail="Permission denied: Missing required scope."
        )


def _check_feedback_scope(principal: AuthPrincipal) -> None:
    if not principal.account_id or principal.is_anonymous:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if "me:home_journey:feedback" not in principal.scopes:
        raise HTTPException(
            status_code=403, detail="Permission denied: Missing required scope."
        )


def _card_repo() -> SqliteHomeCardRepository:
    return SqliteHomeCardRepository()


def _feedback_repo() -> SqliteHomeFeedbackRepository:
    return SqliteHomeFeedbackRepository()


@router.get("", response_model=HomeJourneyResponseV1)
async def get_journey(
    refresh: bool = Query(default=False),
    principal: AuthPrincipal = Depends(resolve_principal),
) -> HomeJourneyResponseV1:
    _check_journey_flag()
    _check_read_scope(principal)

    return await get_home_journey(
        principal=principal,
        summary_readers=tuple(SURFACE_READERS.values()),
        feedback_repo=_feedback_repo(),
        card_repo=_card_repo(),
        refresh=refresh,
    )


@router.post("/cards/{card_id}/feedback", response_model=HomeJourneyFeedbackReceiptV1)
async def submit_feedback(
    card_id: str,
    req: HomeJourneyFeedbackRequestV1,
    principal: AuthPrincipal = Depends(resolve_principal),
) -> HomeJourneyFeedbackReceiptV1:
    _check_journey_flag()
    _check_feedback_scope(principal)

    card_repo = _card_repo()
    feedback_repo = _feedback_repo()

    card = card_repo.get_card_by_id(card_id=card_id, account_id=principal.account_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found or access denied.")

    return record_feedback(
        account_id=principal.account_id,
        card_id=card_id,
        request=req,
        feedback_repo=feedback_repo,
        card_repo=card_repo,
    )

