from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from risk_dashboard.modules.pro_lab.schemas.responses import ProLabExperimentResponse, ProLabWorkspaceResponse


class StudioRule(BaseModel):
    field: str = Field(..., min_length=2, max_length=40)
    operator: str = Field(..., min_length=1, max_length=20)
    value: float | str


class StudioStrategy(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    hypothesis: str = Field(..., min_length=10, max_length=800)
    universe: list[str] = Field(..., min_length=1, max_length=20)
    benchmark: str = Field(default="VNINDEX", min_length=2, max_length=40)
    entry_rules: list[StudioRule] = Field(default_factory=list, max_length=12)
    exit_rules: list[StudioRule] = Field(default_factory=list, max_length=12)
    rebalance_frequency: str = Field(default="monthly", min_length=2, max_length=40)


class StudioExecution(BaseModel):
    initial_capital: float = Field(default=100_000_000, ge=1_000, le=1e15)
    timeframe: str = Field(default="1d", pattern="^(1h|1d|1wk|1mo)$")
    commission_pct: float = Field(default=0.15, ge=0, le=20)
    slippage_pct: float = Field(default=0.05, ge=0, le=20)
    lot_size: int = Field(default=100, ge=1, le=10_000)
    settlement: str = Field(default="T+2", max_length=20)


class StudioRunRequest(BaseModel):
    user_id: str = Field(..., min_length=8)
    blueprint_id: str | None = Field(default=None, min_length=6)
    start_date: str = Field(..., min_length=8, max_length=20)
    end_date: str = Field(..., min_length=8, max_length=20)
    strategy: StudioStrategy
    execution: StudioExecution = Field(default_factory=StudioExecution)

    @model_validator(mode="after")
    def validate_rules(self) -> "StudioRunRequest":
        if not self.strategy.entry_rules:
            raise ValueError("Cần ít nhất một điều kiện vào lệnh.")
        return self


class StudioBootstrapResponse(BaseModel):
    workspace: ProLabWorkspaceResponse
    templates: list[dict[str, object]]
    data_status: dict[str, object]
    execution_profile: dict[str, object]
    supported_fields: list[dict[str, object]]


class StudioRunResponse(BaseModel):
    blueprint_id: str
    experiment: ProLabExperimentResponse
    fidelity: dict[str, object]
