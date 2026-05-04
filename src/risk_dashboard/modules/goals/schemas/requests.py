from __future__ import annotations

from pydantic import BaseModel, Field


class GoalCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=100)
    goal_type: str = Field(..., min_length=3, max_length=50)
    goal_name: str = Field(..., min_length=3, max_length=120)
    deadline: str = Field(..., min_length=10, max_length=10)
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(0, ge=0)
    priority: str = Field(..., min_length=3, max_length=20)
    currency: str = Field(..., min_length=3, max_length=10)
    base_currency: str = Field(..., min_length=3, max_length=10)
    confidence_level: str = Field(..., min_length=3, max_length=20)


class GoalCheckInRequest(BaseModel):
    current_amount: float = Field(..., ge=0)
    note: str | None = Field(default=None, max_length=200)
