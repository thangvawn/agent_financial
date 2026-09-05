"""Request schemas for quant_research module."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuantResearchRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    operation: Literal["eod_analysis", "scenario_compare", "model_report"]
    question: str = Field(min_length=1, max_length=4000)
    as_of: date | None = None
    run_id: str | None = Field(default=None, max_length=128)
    usd_vnd_rate: float | None = Field(default=None, gt=0, le=1_000_000)
    sbv_interest_rate_pct: float | None = Field(default=None, ge=-10, le=100)

    @model_validator(mode="after")
    def validate_operation_invariants(self) -> QuantResearchRequestV1:
        if self.operation == "eod_analysis":
            if self.as_of is None:
                raise ValueError("Operation 'eod_analysis' requires 'as_of' date.")
        elif self.operation == "scenario_compare":
            if self.as_of is None:
                raise ValueError("Operation 'scenario_compare' requires 'as_of' date.")
            if self.usd_vnd_rate is None and self.sbv_interest_rate_pct is None:
                raise ValueError(
                    "Operation 'scenario_compare' requires at least one macro override "
                    "('usd_vnd_rate' or 'sbv_interest_rate_pct')."
                )
        elif self.operation == "model_report":
            if self.usd_vnd_rate is not None or self.sbv_interest_rate_pct is not None:
                raise ValueError(
                    "Operation 'model_report' does not accept macro overrides "
                    "('usd_vnd_rate' or 'sbv_interest_rate_pct')."
                )
        return self

