from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from risk_dashboard.modules.home_onboarding.infrastructure.repositories.sqlite import SqliteOnboardingProfileRepository
from risk_dashboard.modules.pro_lab.application.services import GetProLabTeaser, IssueProLabAccessToken, is_pro_lab_local_test_open
from risk_dashboard.modules.pro_lab.schemas.requests import ProLabAccessTokenRequest
from risk_dashboard.modules.pro_lab.schemas.responses import ProLabAccessTokenResponse
from risk_dashboard.modules.pro_lab.schemas.responses import ProLabTeaserResponse
from risk_dashboard.platform.security.access_control import assign_role

router = APIRouter(prefix="/pro-lab", tags=["Pro Lab"])


@router.get("/teaser", response_model=ProLabTeaserResponse)
def pro_lab_teaser(session_id: str | None = Query(default=None)) -> ProLabTeaserResponse:
    return GetProLabTeaser().execute(session_id=session_id)


@router.post("/access-token", response_model=ProLabAccessTokenResponse)
def pro_lab_access_token(req: ProLabAccessTokenRequest) -> ProLabAccessTokenResponse:
    profile = SqliteOnboardingProfileRepository().get(req.session_id)
    local_test_open = is_pro_lab_local_test_open()
    if not local_test_open and (profile is None or not profile.pro_eligible):
        raise HTTPException(status_code=403, detail="User này chưa đủ điều kiện vào Pro Lab.")
    try:
        if local_test_open:
            assign_role(actor_id=req.session_id, role="pro_lab_user")
        return IssueProLabAccessToken().execute(actor_id=req.session_id, role="pro_lab_user")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
