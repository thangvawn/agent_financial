from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import re

from pydantic import BaseModel, Field, field_validator


class FinancialPeriodData(BaseModel):
    period: str = Field(..., min_length=2)
    year: int | None = None
    quarter: int | None = None
    currency: str = "VND"
    revenue: float | None = None
    gross_profit: float | None = None
    operating_profit: float | None = None
    ebit: float | None = None
    ebitda: float | None = None
    net_income: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    equity: float | None = None
    cash: float | None = None
    short_term_investments: float | None = None
    debt: float | None = None
    short_term_debt: float | None = None
    long_term_debt: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    non_current_liabilities: float | None = None
    inventory: float | None = None
    receivables: float | None = None
    fixed_assets: float | None = None
    investment_properties: float | None = None
    long_term_investments: float | None = None
    other_assets: float | None = None
    accounts_payable: float | None = None
    retained_earnings: float | None = None
    minority_interest: float | None = None
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
    raw_statements: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        normalized = value.upper().strip()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,19}", normalized):
            raise ValueError("ticker must contain only letters, numbers, dot, underscore or hyphen")
        return normalized


class FinancialFlag(BaseModel):
    level: str
    title: str
    detail: str


class DuPontBreakdown(BaseModel):
    net_margin: float | None = None
    asset_turnover: float | None = None
    equity_multiplier: float | None = None
    roe_decomposed: float | None = None


class AltmanZScore(BaseModel):
    score: float | None = None
    zone: str | None = None  # "safe", "grey", "distress"
    components: dict[str, float | None] = Field(default_factory=dict)


class PiotroskiFScore(BaseModel):
    score: int | None = None  # 0-9
    details: dict[str, bool] = Field(default_factory=dict)


class FinancialMetricSnapshot(BaseModel):
    revenue: float | None = None
    revenue_growth_yoy_pct: float | None = None
    net_income: float | None = None
    net_income_growth_yoy_pct: float | None = None
    gross_margin_pct: float | None = None
    operating_margin_pct: float | None = None
    ebitda_margin_pct: float | None = None
    net_margin_pct: float | None = None
    roe_pct: float | None = None
    roa_pct: float | None = None
    roic_pct: float | None = None
    debt_to_equity: float | None = None
    net_debt_to_ebitda: float | None = None
    interest_coverage: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None
    cash_ratio: float | None = None
    ocf_to_net_income: float | None = None
    free_cash_flow: float | None = None
    fcf_margin_pct: float | None = None
    asset_turnover: float | None = None
    inventory_days: float | None = None
    receivable_days: float | None = None
    revenue_ttm: float | None = None
    net_income_ttm: float | None = None
    ocf_ttm: float | None = None
    dupont: DuPontBreakdown | None = None
    altman_z: AltmanZScore | None = None
    piotroski_f: PiotroskiFScore | None = None


class FinancialTrendPoint(BaseModel):
    period: str
    revenue: float | None = None
    net_income: float | None = None
    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None
    gross_margin_pct: float | None = None
    operating_margin_pct: float | None = None
    net_margin_pct: float | None = None
    roe_pct: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None


class FinancialChartFlag(BaseModel):
    severity: str
    code: str
    metric: str | None = None
    message: str


class MarginChartPoint(BaseModel):
    period: str
    year: int | None = None
    quarter: int | None = None
    revenue: float | None = None
    gross_profit: float | None = None
    operating_profit: float | None = None
    ebit: float | None = None
    net_income: float | None = None
    gross_margin_pct: float | None = None
    operating_margin_pct: float | None = None
    ebit_margin_pct: float | None = None
    net_margin_pct: float | None = None
    gross_margin_yoy_pp: float | None = None
    operating_margin_yoy_pp: float | None = None
    ebit_margin_yoy_pp: float | None = None
    net_margin_yoy_pp: float | None = None
    gross_margin_qoq_pp: float | None = None
    operating_margin_qoq_pp: float | None = None
    ebit_margin_qoq_pp: float | None = None
    net_margin_qoq_pp: float | None = None


class LatestMarginValues(BaseModel):
    gross_margin_pct: float | None = None
    operating_margin_pct: float | None = None
    ebit_margin_pct: float | None = None
    net_margin_pct: float | None = None
    net_margin_yoy_pp: float | None = None
    net_margin_qoq_pp: float | None = None


class MarginChartResponse(BaseModel):
    formulas: dict[str, str]
    points: list[MarginChartPoint] = Field(default_factory=list)
    latest: LatestMarginValues = Field(default_factory=LatestMarginValues)
    interpretation: str
    flags: list[FinancialChartFlag] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class CashFlowChartPoint(BaseModel):
    period: str
    year: int | None = None
    quarter: int | None = None
    revenue: float | None = None
    net_income: float | None = None
    cfo: float | None = None
    cfi: float | None = None
    cff: float | None = None
    capex: float | None = None
    fcf: float | None = None
    cfo_to_net_income: float | None = None
    cfo_margin_pct: float | None = None
    fcf_margin_pct: float | None = None
    receivables: float | None = None
    inventory: float | None = None
    revenue_yoy_pct: float | None = None
    receivables_yoy_pct: float | None = None
    inventory_yoy_pct: float | None = None


class CashFlowLatestMetrics(BaseModel):
    cfo: float | None = None
    cfi: float | None = None
    cff: float | None = None
    fcf: float | None = None
    cfo_to_net_income: float | None = None
    cfo_margin_pct: float | None = None
    fcf_margin_pct: float | None = None
    quality_score: float
    quality_label: str


class CashFlowChartResponse(BaseModel):
    formulas: dict[str, str]
    points: list[CashFlowChartPoint] = Field(default_factory=list)
    latest: CashFlowLatestMetrics
    interpretation: str
    flags: list[FinancialChartFlag] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class FinancialQualityChartsResponse(BaseModel):
    ticker: str
    source: str
    latest_period: str | None = None
    margin_analysis: MarginChartResponse
    cash_flow_quality: CashFlowChartResponse


class BalanceSheetCompositionItem(BaseModel):
    key: str
    label: str
    value: float
    percentage: float
    color_token: str
    display_order: int


class BalanceSheetRatios(BaseModel):
    liabilities_to_assets: float | None = None
    equity_ratio: float | None = None
    debt_to_assets: float | None = None
    debt_to_equity: float | None = None
    working_capital_ratio: float | None = None


class BalanceSheetInterpretation(BaseModel):
    summary: str
    strengths: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)


class BalanceSheetRedFlag(BaseModel):
    code: str
    severity: str
    metric: str
    message: str
    suggested_question: str


class BalanceSheetDataQuality(BaseModel):
    missing_fields: list[str] = Field(default_factory=list)
    estimated_fields: list[str] = Field(default_factory=list)
    consistency_warnings: list[str] = Field(default_factory=list)
    last_updated: str | None = None
    source: str


class BalanceSheetStrengthResponse(BaseModel):
    ticker: str
    period: str
    unit: str
    total_assets: float
    total_funding: float
    asset_items: list[BalanceSheetCompositionItem] = Field(default_factory=list)
    funding_items: list[BalanceSheetCompositionItem] = Field(default_factory=list)
    ratios: BalanceSheetRatios
    interpretation: BalanceSheetInterpretation
    red_flags: list[BalanceSheetRedFlag] = Field(default_factory=list)
    data_quality: BalanceSheetDataQuality


class HealthRadar(BaseModel):
    """0-100 scores for radar chart visualization."""
    profitability: float = 0
    growth: float = 0
    efficiency: float = 0
    liquidity: float = 0
    leverage: float = 0
    cash_quality: float = 0


class FinancialAnalysisResponse(BaseModel):
    ticker: str
    source: str
    fetched_at: datetime
    company_name: str | None = None
    exchange: str | None = None
    industry: str | None = None
    latest_period: str | None = None
    summary: FinancialMetricSnapshot
    health_radar: HealthRadar = Field(default_factory=HealthRadar)
    flags: list[FinancialFlag] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    provider_notes: list[str] = Field(default_factory=list)
    trends: list[FinancialTrendPoint] = Field(default_factory=list)
    periods: list[FinancialPeriodData] = Field(default_factory=list)


class FinancialImportRequest(BaseModel):
    dataset: FinancialDataset
