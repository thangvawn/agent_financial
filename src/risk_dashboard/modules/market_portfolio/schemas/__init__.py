from __future__ import annotations

from risk_dashboard.modules.market_portfolio.schemas.legacy_requests import (
    CancelOrderRequest,
    PlaceOrderRequest,
    ResetPortfolioRequest,
    WatchlistAddRequest,
)
from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    ExplainFillInputV1,
    ExplainFillOutputV1,
    FreshnessStampV1,
    FreshnessState,
    GetExposureInputV1,
    GetExposureOutputV1,
    GetMarketSnapshotInputV1,
    GetMarketSnapshotOutputV1,
    GetPortfolioSnapshotInputV1,
    GetPortfolioSnapshotOutputV1,
    MarketSession,
    MoneyV1,
    PositionV1,
    PriceShockV1,
    RiskClass,
    RunScenarioInputV1,
    RunScenarioOutputV1,
    SCHEMA_VERSION,
    StrictModel,
)
from risk_dashboard.modules.market_portfolio.schemas.agent_api import (
    EvidenceRefV1,
    PortfolioReviewArtifactV1,
    StartPortfolioReviewRequestV1,
    StartPortfolioReviewResponseV1,
)
from risk_dashboard.modules.market_portfolio.schemas.rollout import (

    RolloutStage,
    RolloutStatusV1,
    SlaThresholdsV1,
)

__all__ = [
    # Legacy requests
    "WatchlistAddRequest",
    "PlaceOrderRequest",
    "CancelOrderRequest",
    "ResetPortfolioRequest",
    # Agent tools schemas
    "SCHEMA_VERSION",
    "RiskClass",
    "FreshnessState",
    "MarketSession",
    "StrictModel",
    "FreshnessStampV1",
    "MoneyV1",
    "PositionV1",
    "GetMarketSnapshotInputV1",
    "GetMarketSnapshotOutputV1",
    "GetPortfolioSnapshotInputV1",
    "GetPortfolioSnapshotOutputV1",
    "GetExposureInputV1",
    "GetExposureOutputV1",
    "PriceShockV1",
    "RunScenarioInputV1",
    "RunScenarioOutputV1",
    "ExplainFillInputV1",
    "ExplainFillOutputV1",
    # Agent API schemas
    "StartPortfolioReviewRequestV1",
    "EvidenceRefV1",
    "PortfolioReviewArtifactV1",
    "StartPortfolioReviewResponseV1",
    # Rollout schemas
    "RolloutStage",
    "RolloutStatusV1",
    "SlaThresholdsV1",
]


