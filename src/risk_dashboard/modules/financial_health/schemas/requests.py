from __future__ import annotations

from pydantic import BaseModel, Field


class FinancialHealthAssessmentRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    monthly_income_range: str = Field(..., min_length=1, max_length=50)
    income_stability_level: str = Field(..., min_length=1, max_length=50)
    expense_discipline_level: str = Field(..., min_length=1, max_length=50)
    emergency_fund_months_band: str = Field(..., min_length=1, max_length=50)
    monthly_debt_payment_ratio_band: str = Field(..., min_length=1, max_length=50)
    savings_rate_band: str = Field(..., min_length=1, max_length=50)
    liquidity_stress_level: str = Field(..., min_length=1, max_length=50)
    has_basic_insurance: bool
    has_high_interest_debt: bool
    wants_to_start_investing: bool
