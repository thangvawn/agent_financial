from __future__ import annotations

from pydantic import BaseModel, Field


class ProLabBlueprintCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=8)
    name: str = Field(..., min_length=3, max_length=120)
    objective: str = Field(..., min_length=10, max_length=800)
    asset_universe: list[str] = Field(..., min_length=1, max_length=20)
    benchmark: str = Field(..., min_length=2, max_length=40)
    rebalance_frequency: str = Field(..., min_length=3, max_length=40)
    risk_constraints: str = Field(..., min_length=5, max_length=400)
    assumptions_note: str | None = Field(default=None, max_length=1000)


class ProLabScenarioRunRequest(BaseModel):
    user_id: str = Field(..., min_length=8)
    blueprint_id: str = Field(..., min_length=6)
    scenario_preset: str = Field(..., min_length=3, max_length=40)
    usd_vnd_rate: float | None = None
    sbv_interest_rate_pct: float | None = None


class ProLabBacktestRunRequest(BaseModel):
    user_id: str = Field(..., min_length=8)
    blueprint_id: str = Field(..., min_length=6)
    start_date: str = Field(..., min_length=8, max_length=20)
    end_date: str = Field(..., min_length=8, max_length=20)
    initial_capital: float = Field(..., ge=1000.0, le=1e15)


class ProLabBlueprintUpdateRequest(BaseModel):
    user_id: str = Field(..., min_length=8)
    name: str | None = Field(default=None, min_length=3, max_length=120)
    objective: str | None = Field(default=None, min_length=10, max_length=800)
    asset_universe: list[str] | None = Field(default=None, max_length=20)
    benchmark: str | None = Field(default=None, min_length=2, max_length=40)
    rebalance_frequency: str | None = Field(default=None, min_length=3, max_length=40)
    risk_constraints: str | None = Field(default=None, min_length=5, max_length=400)
    assumptions_note: str | None = Field(default=None, max_length=1000)


class ProLabAccessTokenRequest(BaseModel):
    session_id: str = Field(..., min_length=8)


class ProLabExperimentReviewRequest(BaseModel):
    review_status: str = Field(..., min_length=3, max_length=40)
    review_notes: str | None = Field(default=None, max_length=2000)


class ProLabCommandRunRequest(BaseModel):
    user_id: str = Field(..., min_length=8)
    provider_id: str = Field(..., min_length=3, max_length=80)
    command_id: str = Field(..., min_length=3, max_length=80)
    blueprint_id: str | None = Field(default=None, min_length=6)
    input_payload: dict[str, object] = Field(default_factory=dict)


class ProLabWorkspaceStateRequest(BaseModel):
    user_id: str = Field(..., min_length=8)
    active_page: str = Field(default="overview", min_length=2, max_length=80)
    open_panels: list[str] = Field(default_factory=list, max_length=20)
    selected_blueprint_id: str | None = Field(default=None, max_length=80)
    selected_experiment_id: str | None = Field(default=None, max_length=80)
    layout: dict[str, object] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=2000)
