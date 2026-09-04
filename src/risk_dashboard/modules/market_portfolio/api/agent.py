from __future__ import annotations

import hashlib
import os
from fastapi import APIRouter, Depends, HTTPException

from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.market_portfolio.application.agent_service import MarketPortfolioAgentService
from risk_dashboard.modules.market_portfolio.domain.agent_policy import (
    ResourceNotFoundError,
    StaleDataBlockedError,
)
from risk_dashboard.modules.market_portfolio.schemas.agent_api import (
    PortfolioReviewArtifactV1,
    StartPortfolioReviewRequestV1,
    StartPortfolioReviewResponseV1,
)
from risk_dashboard.modules.market_portfolio.schemas.rollout import (
    RolloutStage,
    RolloutStatusV1,
    SlaThresholdsV1,
)
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

FEATURE_FLAG = "module.market_portfolio.agent.enabled"
COHORT_PERCENTAGE_ENV = "RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_PERCENTAGE"
COHORT_ALLOWLIST_ENV = "RISK_FLAG__MODULE__MARKET_PORTFOLIO__AGENT__COHORT_ALLOWLIST"


def get_cohort_percentage() -> int:
    raw = os.getenv(COHORT_PERCENTAGE_ENV)
    if raw is None:
        return 100
    try:
        val = int(raw.strip())
        return max(0, min(100, val))
    except ValueError:
        return 100


def get_cohort_allowlist() -> set[str]:
    raw = os.getenv(COHORT_ALLOWLIST_ENV, "")
    if not raw.strip():
        return set()
    return {x.strip() for x in raw.split(",") if x.strip()}


def is_account_in_cohort(account_id: str) -> bool:
    allowlist = get_cohort_allowlist()
    if account_id in allowlist:
        return True
    pct = get_cohort_percentage()
    if pct >= 100:
        return True
    if pct <= 0:
        return False
    # Deterministic account bucket hashing 0..99
    bucket = int(hashlib.sha256(f"mp_cohort:{account_id}".encode()).hexdigest(), 16) % 100
    return bucket < pct


def _check_agent_enabled() -> None:
    if not FeatureFlagService().is_enabled(FEATURE_FLAG, default=False):
        raise HTTPException(status_code=404, detail="Market portfolio agent is disabled.")


router = APIRouter(
    prefix="/market-portfolio/agent",
    tags=["Market & Portfolio Agent"],
    dependencies=[Depends(_check_agent_enabled)],
)

ops_router = APIRouter(
    prefix="/market-portfolio/agent/ops",
    tags=["Market & Portfolio Agent Ops"],
)


def get_agent_service() -> MarketPortfolioAgentService:
    return MarketPortfolioAgentService()


def _check_agent_scope(principal: AuthPrincipal) -> None:
    if not principal.account_id or principal.is_anonymous:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if "account:market_portfolio:read" not in principal.scopes:
        raise HTTPException(status_code=403, detail="Permission denied: Missing required scope.")
    if not is_account_in_cohort(principal.account_id):
        raise HTTPException(status_code=404, detail="Market portfolio agent is not enabled for this cohort.")


@router.post("/reviews", response_model=StartPortfolioReviewResponseV1)
async def start_portfolio_review(
    request: StartPortfolioReviewRequestV1,
    principal: AuthPrincipal = Depends(resolve_principal),
    service: MarketPortfolioAgentService = Depends(get_agent_service),
) -> StartPortfolioReviewResponseV1:
    _check_agent_scope(principal)

    try:
        return await service.start_review(request, principal)
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Resource not found.")
    except (StaleDataBlockedError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/reviews/{artifact_id}", response_model=PortfolioReviewArtifactV1)
def get_portfolio_review_artifact(
    artifact_id: str,
    principal: AuthPrincipal = Depends(resolve_principal),
    service: MarketPortfolioAgentService = Depends(get_agent_service),
) -> PortfolioReviewArtifactV1:
    _check_agent_scope(principal)
    artifact = service.get_artifact(principal, artifact_id)

    if artifact is None:
        raise HTTPException(status_code=404, detail="Resource not found.")
    return artifact


@ops_router.get("/rollout-status", response_model=RolloutStatusV1)
def get_rollout_status() -> RolloutStatusV1:
    master_enabled = FeatureFlagService().is_enabled(FEATURE_FLAG, default=False)
    pct = get_cohort_percentage()
    allowlist = get_cohort_allowlist()

    stage: RolloutStage
    if not master_enabled or pct <= 0:
        stage = "disabled"
    elif pct <= 5:
        stage = "pilot_5pct"
    elif pct <= 25:
        stage = "cohort_25pct"
    else:
        stage = "full_100pct"

    return RolloutStatusV1(
        schema_version="1.0.0",
        master_enabled=master_enabled,
        cohort_percentage=pct,
        active_stage=stage,
        allowlist_count=len(allowlist),
        kill_switch_ready=True,
        sla_thresholds=SlaThresholdsV1(),
        retention_policy="short_lived_non_durable_24h",
        dependencies_status={
            "doc_00_agentic_core": "ready",
            "doc_01_identity_trust": "ready",
            "doc_02_shared_ai_runtime": "ready",
            "data_owner_license_sla": "approved",
            "compliance_artifact_ttl": "approved",
        },
    )
