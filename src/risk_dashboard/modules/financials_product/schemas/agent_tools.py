from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

CalculationStatus = Literal["ok", "insufficient_data"]


class ProvenanceRef(BaseModel):
    """Mọi con số model được nhìn thấy phải kèm ref này."""
    model_config = ConfigDict(frozen=True)

    report_id: str
    revision_id: str
    period: str
    source: str
    fetched_at: str  # ISO-8601 UTC
    statement: Literal["income_statement", "balance_sheet", "cash_flow"] | None = None
    line_item: str | None = None


class NumericValue(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: float | None = None
    unit: Literal["VND", "VND_bn", "pct", "x", "ratio"]
    scale: int = Field(default=1, ge=1)
    calculation_status: CalculationStatus = "ok"
    provenance: ProvenanceRef  # REQUIRED - Không Optional


class ResolveReportInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    ticker: str = Field(min_length=1, max_length=20)
    period: str | None = None  # None -> active/latest
    refresh: bool = False


class ResolveReportOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    ticker: str
    company_name: str | None = None
    exchange: str | None = None
    available_periods: tuple[str, ...] = ()
    active_period: str
    currency: Literal["VND"] = "VND"
    source: str
    fetched_at: str
    freshness_days: int = Field(ge=0)
    is_private_upload: bool = False


class ResolveLineItemInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    period: str
    line_item: str


class ResolveLineItemOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    line_item: str
    label_vi: str
    amount: NumericValue
    definition: str
    composition: tuple[str, ...] = ()
    caveats: tuple[str, ...] = ()


class PeriodDelta(BaseModel):
    model_config = ConfigDict(frozen=True)

    from_period: str
    to_period: str
    absolute: NumericValue
    pct_change: NumericValue
    formula_id: str
    expression: str


class ComparePeriodsInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    line_item: str
    periods: tuple[str, ...] = Field(min_length=2, max_length=8)


class ComparePeriodsOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    line_item: str
    observations: tuple[NumericValue, ...]
    deltas: tuple[PeriodDelta, ...]
    limitations: tuple[str, ...] = ()


class CalculateRatioInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    period: str
    formula_id: str
    formula_version: str | None = None  # None -> approved latest


class CalculateRatioOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    formula_id: str
    formula_version: str
    expression: str
    inputs: tuple[NumericValue, ...]
    result: NumericValue
    applicability: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class TransformStep(BaseModel):
    model_config = ConfigDict(frozen=True)

    step: str
    detail: str


class TraceProvenanceInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    claim_ref: str


class TraceProvenanceOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    claim_ref: str
    citations: tuple[ProvenanceRef, ...]
    transformation_chain: tuple[TransformStep, ...]
    license_note: str | None = None
    freshness_days: int = Field(ge=0)


class EvidenceRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim: str
    kind: Literal["fact", "calculation"]
    value: NumericValue
    citation: ProvenanceRef


class BuildEvidenceTableInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    claim_refs: tuple[str, ...] = Field(min_length=1, max_length=50)


class BuildEvidenceTableOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    rows: tuple[EvidenceRow, ...]
    unsupported_claims: tuple[str, ...] = ()

