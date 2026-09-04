from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class ReproducibilityManifest(BaseModel):
    """Pin đầy đủ 17 fields để tái lập hoàn toàn 1 kết quả simulation."""
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    strategy_id: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    dataset_source: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    data_start: str = Field(min_length=1)
    data_end: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    commission_pct: float = Field(ge=0.0)
    slippage_pct: float = Field(ge=0.0)
    benchmark: str = Field(min_length=1)
    random_seed: int | None = None
    engine_version: str = Field(min_length=1)
    execution_timestamp: str = Field(min_length=1)
    metrics_calculation_version: str = Field(min_length=1)
    warnings: tuple[str, ...] = ()
    data_gaps: tuple[str, ...] = ()


class SimulationRunArtifact(BaseModel):
    """Artifact hoàn chỉnh của một simulation run."""
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    artifact_id: str
    run_id: str
    account_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    manifest: ReproducibilityManifest
    metrics: dict[str, float | int | None] = Field(default_factory=dict)
    trade_summary: dict[str, Any] = Field(default_factory=dict)
    source_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    created_at: str
    completed_at: str | None = None


class ActionProposal(BaseModel):
    """Đề xuất thực thi simulation run có chi phí tài nguyên, cần preview & confirm."""
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    proposal_id: str
    run_id: str
    account_id: str
    operation: Literal["run_simulation"] = "run_simulation"
    manifest: ReproducibilityManifest
    estimated_cost: float = Field(ge=0.0)
    risk_class: Literal["proposal"] = "proposal"
    requires_confirmation: bool = True
    policy_version: str = "1.0.0"
    created_at: str
    expires_at: str


class ExecuteRunRequest(BaseModel):
    """Yêu cầu thực thi simulation sau khi user đã confirm proposal."""
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    proposal_id: str = Field(min_length=1)
    confirmation_token: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)


class ActionReceipt(BaseModel):
    """Biên nhận kết quả sau khi thực thi confirmed action."""
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    receipt_id: str
    proposal_id: str
    account_id: str
    status: Literal["executed", "failed", "rejected", "expired"]
    risk_class: Literal["confirmed_write"] = "confirmed_write"
    executed_at: str
    run_artifact_id: str | None = None
    error_code: str | None = None


# Domain Tool Queries and Outputs

class StrategySpecQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    blueprint_id: str = Field(min_length=1)


class StrategySpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    blueprint_id: str
    name: str
    objective: str
    asset_universe: tuple[str, ...]
    benchmark: str
    rebalance_frequency: str
    risk_constraints: str
    assumptions_note: str | None = None
    version: str = "1.0.0"
    status: str = "draft"
    created_at: str
    updated_at: str


class ExperimentValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    is_valid: bool
    missing_fields: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    data_gap_notes: tuple[str, ...] = ()
    validation_status: Literal["passed", "warning", "rejected"]


class RunQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    run_id: str = Field(min_length=1)


class TradeSummaryQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    run_id: str = Field(min_length=1)
    detail: bool = False


class TradeSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    run_id: str
    total_trades: int = Field(ge=0)
    win_trades: int = Field(ge=0)
    loss_trades: int = Field(ge=0)
    win_rate_pct: float = Field(ge=0.0, le=100.0)
    profit_factor: float | None = None
    max_drawdown_pct: float = Field(ge=0.0, le=100.0)
    total_return_pct: float
    avg_trade_return_pct: float
    sharpe_ratio: float | None = None
    detail_trades: tuple[dict[str, Any], ...] = ()


class CompareRunsQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    run_ids: tuple[str, ...] = Field(min_length=2, max_length=10)


class RunComparisonItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    strategy_id: str
    strategy_version: str
    metrics_calculation_version: str
    total_return_pct: float
    sharpe_ratio: float | None
    max_drawdown_pct: float
    win_rate_pct: float
    trade_count: int


class RunComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = "1.0.0"
    runs: tuple[RunComparisonItem, ...]
    is_compatible: bool
    incompatible_reasons: tuple[str, ...] = ()
    best_sharpe_run_id: str | None = None
    lowest_drawdown_run_id: str | None = None
    comparison_notes: tuple[str, ...] = ()

