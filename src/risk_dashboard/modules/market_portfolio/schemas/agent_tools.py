from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"
RiskClass = Literal["read", "proposal", "confirmed_write", "forbidden"]
FreshnessState = Literal["fresh", "stale", "market_closed", "partial", "unavailable"]
MarketSession = Literal["pre_open", "open", "closed", "holiday", "unknown"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FreshnessStampV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    as_of: str
    source: str
    state: FreshnessState
    ttl_seconds: int = Field(ge=0)
    age_seconds: int = Field(ge=0)
    confidence_label: str
    stale_reason: str | None = None
    market_session: MarketSession


class MoneyV1(StrictModel):
    amount: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class PositionV1(StrictModel):
    symbol: str
    quantity: str
    avg_cost: MoneyV1
    mark_price: MoneyV1 | None = None
    market_value: MoneyV1 | None = None
    unrealized_pnl: MoneyV1 | None = None
    unrealized_pnl_pct: float | None = None
    weight_pct: float | None = Field(default=None, ge=0, le=100)
    freshness: FreshnessStampV1 | None = None


class GetMarketSnapshotInputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    market: Literal["VN"] = "VN"
    symbols: tuple[str, ...] = Field(default=(), max_length=100)


class GetMarketSnapshotOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    market: Literal["VN"]
    indices: tuple[dict[str, Any], ...]
    breadth: dict[str, Any] | None = None
    capital_flow: dict[str, Any] | None = None
    quotes: tuple[dict[str, Any], ...]
    freshness: FreshnessStampV1
    missing_symbols: tuple[str, ...] = ()


class GetPortfolioSnapshotInputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str


class GetPortfolioSnapshotOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    portfolio_kind: Literal["paper"] = "paper"
    snapshot_version: str
    cash: MoneyV1
    starting_cash: MoneyV1
    market_value: MoneyV1
    equity: MoneyV1
    total_pnl: MoneyV1
    total_pnl_pct: float
    positions: tuple[PositionV1, ...]
    missing_prices: tuple[str, ...] = ()
    freshness: FreshnessStampV1


class GetExposureInputV1(GetPortfolioSnapshotInputV1):
    benchmark: str | None = None


class GetExposureOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    snapshot_version: str
    invested_pct: float = Field(ge=0)
    cash_pct: float = Field(ge=0)
    largest_position_pct: float | None = None
    top3_concentration_pct: float | None = None
    hhi: float | None = Field(default=None, ge=0, le=1)
    weights_pct: dict[str, float]
    limitations: tuple[str, ...] = ()
    freshness: FreshnessStampV1


class PriceShockV1(StrictModel):
    symbol: str
    shock_pct: float = Field(ge=-50, le=50)


class RunScenarioInputV1(GetPortfolioSnapshotInputV1):
    shocks: tuple[PriceShockV1, ...] = Field(min_length=1, max_length=30)
    allow_stale: bool = False


class RunScenarioOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    base_snapshot_version: str
    assumptions: tuple[PriceShockV1, ...]
    base_equity: MoneyV1
    scenario_equity: MoneyV1
    pnl_delta: MoneyV1
    pnl_delta_pct: float
    position_deltas: dict[str, MoneyV1]
    deterministic_method: Literal["position_mark_price_shock_v1"]
    freshness: FreshnessStampV1
    limitations: tuple[str, ...]


class ExplainFillInputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    order_id: str


class ExplainFillOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    status: str
    filled_quantity: str
    filled_price: MoneyV1 | None = None
    limit_price: MoneyV1 | None = None
    created_at: str
    filled_at: str | None = None
    explanation_facts: tuple[str, ...]
    freshness: FreshnessStampV1

