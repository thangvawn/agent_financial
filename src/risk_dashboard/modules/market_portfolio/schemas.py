from __future__ import annotations

from pydantic import BaseModel, Field


class WatchlistAddRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=120)
    symbol: str = Field(..., min_length=1, max_length=16)
    label: str = Field(default="", max_length=80)


class PlaceOrderRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=120)
    symbol: str = Field(..., min_length=1, max_length=16)
    side: str = Field(..., pattern="^(BUY|SELL)$")
    order_type: str = Field(..., pattern="^(MP|LO)$")
    quantity: float = Field(..., gt=0, le=1_000_000)
    limit_price: float | None = Field(default=None, gt=0)


class CancelOrderRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=120)


class ResetPortfolioRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=120)
