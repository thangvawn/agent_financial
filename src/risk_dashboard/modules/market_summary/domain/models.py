"""Domain models and data definitions for Market Summary."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field


class DataQuality(BaseModel):
    source: str = "vnstock"
    fetched_at: datetime
    market_date: date
    is_complete: bool = True
    is_stale: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class IndexMetrics(BaseModel):
    symbol: str  # e.g., VNINDEX, VN30, HNX
    close: float
    change_points: float
    change_pct: float
    volume: int
    value_vnd: float  # Value in VND
    vol_vs_prev_pct: float | None = None
    vol_vs_sma20_pct: float | None = None
    value_vs_prev_pct: float | None = None
    value_vs_sma20_pct: float | None = None


class MarketBreadth(BaseModel):
    universe: str = "HOSE"
    advancers: int
    decliners: int
    unchanged: int
    ceiling: int
    floor: int
    summary_assessment: str


class StockContribution(BaseModel):
    ticker: str
    points_impact: float
    percent_impact: float | None = None


class CapitalFlow(BaseModel):
    universe: str = "HOSE"
    is_available: bool = True
    leading_sectors: list[str] = Field(default_factory=list)
    weakening_sectors: list[str] = Field(default_factory=list)
    net_foreign_val_billion: float = 0.0  # in Billion VND
    top_foreign_buy: list[tuple[str, float]] = Field(default_factory=list)   # [(ticker, val_billion)]
    top_foreign_sell: list[tuple[str, float]] = Field(default_factory=list)  # [(ticker, val_billion)]


class TechnicalOverview(BaseModel):
    short_term_trend: Literal["BULLISH", "BEARISH", "NEUTRAL_SIDEWAYS"]
    support_zone: tuple[float, float]
    resistance_zone: tuple[float, float]
    volume_confirmation: Literal["HIGH", "NORMAL", "LOW"]
    watch_points: list[str] = Field(default_factory=list)


class ReportProvenance(BaseModel):
    schema_version: str = "1.0"
    metrics_version: str = "1.0"
    template_version: str = "1.0"
    provider_name: str = "vnstock"
    environment: str = "production"
    data_mode: Literal["live", "fixture"] = "live"
    provider_version: str | None = None
    prompt_version: str | None = None
    llm_model: str | None = None
    payload_hash: str | None = None


class MarketSummaryReport(BaseModel):
    report_date: date
    generated_at: datetime
    timezone: str = "Asia/Ho_Chi_Minh"
    indices: list[IndexMetrics]
    breadth: MarketBreadth | None = None
    capital_flow: CapitalFlow | None = None
    positive_movers: list[StockContribution] = Field(default_factory=list)
    negative_movers: list[StockContribution] = Field(default_factory=list)
    technical: TechnicalOverview | None = None
    quality: DataQuality
    provenance: ReportProvenance = Field(default_factory=ReportProvenance)
