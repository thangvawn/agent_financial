from __future__ import annotations

from typing import Any, Literal
from pydantic import Field

from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    SCHEMA_VERSION,
    StrictModel,
)

RolloutStage = Literal["disabled", "pilot_5pct", "cohort_25pct", "full_100pct"]


class SlaThresholdsV1(StrictModel):
    forbidden_executions: int = 0
    mp_mutations_allowed: int = 0
    cross_account_leakage: int = 0
    schema_validation_pct: float = 100.0
    freshness_presence_pct: float = 100.0
    cited_numeric_claims_pct: float = 100.0
    paper_disclaimer_pct: float = 100.0
    deterministic_p50_ms: int = 500
    deterministic_p95_ms: int = 2000
    reviewed_p50_ms: int = 2000
    reviewed_p95_ms: int = 6000
    max_cost_usd_per_review: float = 0.03
    kill_switch_max_sec: int = 30


class RolloutStatusV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    master_enabled: bool
    cohort_percentage: int = Field(ge=0, le=100)
    active_stage: RolloutStage
    allowlist_count: int = Field(ge=0)
    kill_switch_ready: bool = True
    sla_thresholds: SlaThresholdsV1 = Field(default_factory=SlaThresholdsV1)
    retention_policy: str = "short_lived_non_durable_24h"
    dependencies_status: dict[str, str] = Field(default_factory=dict)

