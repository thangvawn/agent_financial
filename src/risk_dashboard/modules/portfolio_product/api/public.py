from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["Backtest"])


class BacktestStrategyRuleRequest(BaseModel):
    enabled: bool = False
    volume_spike_multiplier: float = Field(2.0, ge=1.0, le=20.0)
    btc_daily_change_min_pct: float = Field(3.0, ge=-50.0, le=50.0)
    stop_loss_pct: float = Field(4.0, ge=0.1, le=50.0)


class BacktestRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, max_length=30)
    start_date: date
    end_date: date
    initial_capital: float = Field(100_000_000.0, ge=1_000.0, le=1e15)
    equal_weight: bool = True
    weights: dict[str, float] | None = None
    include_benchmark: bool = True
    strategy: BacktestStrategyRuleRequest | None = None


@router.post("/backtest/run", tags=["Backtest"])
def backtest_run(req: BacktestRequest):
    raise HTTPException(
        status_code=410,
        detail=(
            "Public backtest legacy đã được retire. "
            "Hãy dùng Pro / Research / Trading Lab để chạy scenario, backtest và report export."
        ),
        headers={"X-Legacy-Portfolio-Backtest": "retired", "X-Primary-Surface": "pro_lab"},
    )
