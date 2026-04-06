from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class FinancialPeriodData(BaseModel):
    period: str = Field(..., min_length=2)
    year: int | None = None
    quarter: int | None = None
    currency: str = "VND"
    revenue: float | None = None
    gross_profit: float | None = None
    operating_profit: float | None = None
    ebitda: float | None = None
    net_income: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    equity: float | None = None
    cash: float | None = None
    debt: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    inventory: float | None = None
    receivables: float | None = None
    operating_cash_flow: float | None = None
    investing_cash_flow: float | None = None
    financing_cash_flow: float | None = None
    capex: float | None = None


class FinancialDataset(BaseModel):
    ticker: str = Field(..., min_length=1)
    source: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    company_name: str | None = None
    exchange: str | None = None
    industry: str | None = None
    provider_notes: list[str] = Field(default_factory=list)
    periods: list[FinancialPeriodData] = Field(default_factory=list)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.upper().strip()


class FinancialFlag(BaseModel):
    level: str
    title: str
    detail: str


class FinancialMetricSnapshot(BaseModel):
    revenue: float | None = None
    revenue_growth_yoy_pct: float | None = None
    net_income: float | None = None
    net_income_growth_yoy_pct: float | None = None
    gross_margin_pct: float | None = None
    net_margin_pct: float | None = None
    roe_pct: float | None = None
    roa_pct: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None
    ocf_to_net_income: float | None = None
    free_cash_flow: float | None = None


class FinancialTrendPoint(BaseModel):
    period: str
    revenue: float | None = None
    net_income: float | None = None
    operating_cash_flow: float | None = None
    gross_margin_pct: float | None = None
    net_margin_pct: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None


class FinancialAnalysisResponse(BaseModel):
    ticker: str
    source: str
    fetched_at: datetime
    company_name: str | None = None
    exchange: str | None = None
    industry: str | None = None
    latest_period: str | None = None
    summary: FinancialMetricSnapshot
    flags: list[FinancialFlag] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    provider_notes: list[str] = Field(default_factory=list)
    trends: list[FinancialTrendPoint] = Field(default_factory=list)
    periods: list[FinancialPeriodData] = Field(default_factory=list)


class FinancialImportRequest(BaseModel):
    dataset: FinancialDataset
