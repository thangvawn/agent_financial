from __future__ import annotations

from typing import Literal
from pydantic import Field, model_validator

from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    FreshnessStampV1,
    PriceShockV1,
    RunScenarioInputV1,
    SCHEMA_VERSION,
    StrictModel,
)


class StartPortfolioReviewRequestV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str = Field(min_length=1)
    review_type: Literal["market_context", "exposure", "scenario", "fill"]
    scenario: RunScenarioInputV1 | None = None
    order_id: str | None = None
    locale: Literal["vi-VN", "en-US"] = "vi-VN"
    idempotency_key: str = Field(min_length=16, max_length=128)

    @model_validator(mode="after")
    def validate_request_integrity(self) -> StartPortfolioReviewRequestV1:
        if self.review_type == "scenario":
            if not self.scenario:
                raise ValueError("scenario is required when review_type is 'scenario'")
            symbols = [s.symbol for s in self.scenario.shocks]
            if len(symbols) != len(set(symbols)):
                raise ValueError("Scenario shocks cannot contain duplicate symbols")
        elif self.review_type == "fill":
            if not self.order_id:
                raise ValueError("order_id is required when review_type is 'fill'")
        return self


class EvidenceRefV1(StrictModel):
    tool_call_id: str
    tool_name: str
    output_schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    resource_id: str
    as_of: str


class PortfolioReviewArtifactV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    artifact_id: str
    account_id: str  # server-generated, never request input
    portfolio_id: str
    portfolio_kind: Literal["paper"] = "paper"
    snapshot_version: str
    review_type: str
    observed_facts: tuple[str, ...]
    calculations: dict[str, str | float | None]
    scenario_assumptions: tuple[PriceShockV1, ...] = ()
    narrative: str | None = None
    narrative_status: Literal["generated", "unavailable", "blocked"]
    evidence: tuple[EvidenceRefV1, ...]
    limitations: tuple[str, ...] = ()
    freshness: FreshnessStampV1
    review_status: Literal["reviewed", "rejected"]
    created_at: str
    expires_at: str


class StartPortfolioReviewResponseV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    run_id: str
    artifact: PortfolioReviewArtifactV1 | None = None
    error_code: str | None = None

