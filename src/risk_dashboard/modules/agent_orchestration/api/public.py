from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from risk_dashboard.agents.multi_agent import run_chat

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    as_of: date
    message: str = Field(..., min_length=1)


@router.post("/chat", tags=["Chat"])
def chat(req: ChatRequest):
    return run_chat(req.message)
