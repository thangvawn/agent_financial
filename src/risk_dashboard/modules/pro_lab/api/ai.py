"""Live OpenAI-backed endpoints for Pro Lab.

Inspired by Vibe-Trading (https://github.com/HKUDS/Vibe-Trading) — turn natural-
language ideas into structured strategy blueprints, swarm reviews, and backtest
analyses. Uses the OpenAI API directly via langchain-openai.
"""
from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/pro-lab/ai", tags=["Pro Lab — AI"])


def _openai_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _model_name() -> str:
    return os.getenv("PRO_LAB_AI_MODEL", os.getenv("AI_ASSISTANT_MODEL", "gpt-4o-mini"))


def _invoke_openai(*, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
    """Call OpenAI through langchain-openai and parse JSON response."""
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=_model_name(),
        temperature=0.4,
        timeout=20,
        max_retries=1,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(user_payload, ensure_ascii=False)),
        ]
    )
    raw = str(response.content).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI trả về không phải JSON hợp lệ: {raw[:200]}",
        ) from exc


# ── Strategy Copilot ────────────────────────────────────────
class StrategyCopilotRequest(BaseModel):
    idea: str = Field(..., min_length=4, max_length=1500)
    market: str = Field(default="Vietnam equities")
    horizon: str = Field(default="monthly")
    risk_budget_pct: float = Field(default=2.0, ge=0.1, le=20.0)


class StrategyCopilotResponse(BaseModel):
    strategy_name: str
    market: str
    universe: list[str]
    signal_stack: list[str]
    risk_rules: list[str]
    validation_queue: list[str]
    rationale: str
    horizon: str
    confidence: str


_STRATEGY_SYSTEM_PROMPT = """Bạn là Strategy Copilot — chuyển ý tưởng giao dịch thành blueprint chiến lược có cấu trúc.

QUAN TRỌNG: Đây là môi trường research/sandbox, KHÔNG phải tín hiệu giao dịch thực.

Trả về JSON EXACT theo schema:
{
  "strategy_name": "tên ngắn gọn dưới 60 ký tự",
  "market": "thị trường mục tiêu",
  "universe": ["mã 1", "mã 2", "..."] (3-8 mã đại diện),
  "signal_stack": ["tín hiệu 1", "tín hiệu 2", "..."] (3-5 lớp tín hiệu),
  "risk_rules": ["quy tắc 1", "quy tắc 2", "..."] (3-5 quy tắc kiểm soát rủi ro),
  "validation_queue": ["bước validate 1", "..."] (3-5 bước kiểm chứng cần làm),
  "rationale": "1-2 câu giải thích logic chính",
  "horizon": "khung thời gian rebalance",
  "confidence": "low|medium|high"
}

Nguyên tắc: chặt chẽ về risk control, tránh hứa hẹn lợi nhuận, ưu tiên Việt hóa nội dung."""


@router.post("/strategy-copilot", response_model=StrategyCopilotResponse)
def strategy_copilot(
    req: StrategyCopilotRequest,
    x_pro_lab_test: str | None = Header(default=None, alias="X-Pro-Lab-Test"),
) -> StrategyCopilotResponse:
    if not _openai_enabled():
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY chưa được cấu hình trên server.",
        )
    payload = _invoke_openai(
        system_prompt=_STRATEGY_SYSTEM_PROMPT,
        user_payload={
            "idea": req.idea,
            "market": req.market,
            "horizon": req.horizon,
            "risk_budget_pct": req.risk_budget_pct,
        },
    )
    try:
        return StrategyCopilotResponse(
            strategy_name=str(payload.get("strategy_name", "Untitled strategy"))[:80],
            market=str(payload.get("market", req.market))[:80],
            universe=[str(item)[:20] for item in (payload.get("universe") or [])][:8],
            signal_stack=[str(item)[:200] for item in (payload.get("signal_stack") or [])][:6],
            risk_rules=[str(item)[:200] for item in (payload.get("risk_rules") or [])][:6],
            validation_queue=[str(item)[:200] for item in (payload.get("validation_queue") or [])][:6],
            rationale=str(payload.get("rationale", ""))[:500],
            horizon=str(payload.get("horizon", req.horizon))[:40],
            confidence=str(payload.get("confidence", "medium")).lower()[:10],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"AI payload không hợp lệ: {exc}") from exc


# ── Swarm Committee ────────────────────────────────────────
class SwarmCommitteeRequest(BaseModel):
    strategy_brief: str = Field(..., min_length=10, max_length=3000)
    review_focus: str = Field(default="overfit, liquidity, benchmark gap, execution assumptions")
    market: str = Field(default="Vietnam equities")


class SwarmAgentMemo(BaseModel):
    role: str
    stance: str
    memo: str
    key_concerns: list[str]


class SwarmCommitteeResponse(BaseModel):
    consensus: str
    confidence: str
    memos: list[SwarmAgentMemo]
    decision_summary: str
    next_actions: list[str]


_SWARM_SYSTEM_PROMPT = """Bạn là Swarm Committee — mô phỏng investment committee với 4 vai trò debate về 1 strategy:

1. Bull Researcher — tìm điểm mạnh, alpha source, lợi thế
2. Bear Risk Analyst — tìm rủi ro, overfit, regime risk, liquidity
3. Quant Engineer — đánh giá tính khả thi backtest, data quality
4. Portfolio Manager — final call, position sizing, sequencing

Trả về JSON EXACT:
{
  "consensus": "buy|hold|reject_or_revise",
  "confidence": "low|medium|high",
  "memos": [
    {"role": "Bull Researcher", "stance": "supportive|cautious|opposed", "memo": "1-3 câu", "key_concerns": ["..."]},
    {"role": "Bear Risk Analyst", "stance": "...", "memo": "...", "key_concerns": ["..."]},
    {"role": "Quant Engineer", "stance": "...", "memo": "...", "key_concerns": ["..."]},
    {"role": "Portfolio Manager", "stance": "...", "memo": "...", "key_concerns": ["..."]}
  ],
  "decision_summary": "1-2 câu kết luận PM",
  "next_actions": ["bước tiếp theo 1", "bước 2", "..."] (3-5 bước)
}"""


@router.post("/swarm-committee", response_model=SwarmCommitteeResponse)
def swarm_committee(req: SwarmCommitteeRequest) -> SwarmCommitteeResponse:
    if not _openai_enabled():
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY chưa được cấu hình.")
    payload = _invoke_openai(
        system_prompt=_SWARM_SYSTEM_PROMPT,
        user_payload={
            "strategy_brief": req.strategy_brief,
            "review_focus": req.review_focus,
            "market": req.market,
        },
    )
    try:
        memos_raw = payload.get("memos") or []
        memos = [
            SwarmAgentMemo(
                role=str(m.get("role", "Unknown"))[:50],
                stance=str(m.get("stance", "cautious"))[:30],
                memo=str(m.get("memo", ""))[:600],
                key_concerns=[str(c)[:200] for c in (m.get("key_concerns") or [])][:5],
            )
            for m in memos_raw[:4]
        ]
        return SwarmCommitteeResponse(
            consensus=str(payload.get("consensus", "hold"))[:30],
            confidence=str(payload.get("confidence", "medium"))[:10],
            memos=memos,
            decision_summary=str(payload.get("decision_summary", ""))[:500],
            next_actions=[str(a)[:200] for a in (payload.get("next_actions") or [])][:6],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"AI payload không hợp lệ: {exc}") from exc


# ── Backtest Critique ────────────────────────────────────────
class BacktestCritiqueRequest(BaseModel):
    strategy_name: str
    sharpe: float | None = None
    cagr_pct: float | None = None
    max_drawdown_pct: float | None = None
    win_rate_pct: float | None = None
    sample_size: int | None = None
    notes: str = Field(default="")


class BacktestCritiqueResponse(BaseModel):
    overall_grade: str
    red_flags: list[str]
    strengths: list[str]
    additional_validation: list[str]
    interpretation: str


_BACKTEST_SYSTEM_PROMPT = """Bạn là Backtest Critic. Đánh giá kết quả backtest qua lăng kính skeptical:
overfit risk, p-hacking, lookahead, sample size, robustness.

Trả về JSON:
{
  "overall_grade": "A|B|C|D|F",
  "red_flags": ["cờ đỏ 1", "..."] (0-5),
  "strengths": ["điểm mạnh 1", "..."] (0-5),
  "additional_validation": ["bước test bổ sung 1", "..."] (3-5),
  "interpretation": "đoạn 2-3 câu interpret kết quả 1 cách trung thực"
}"""


@router.post("/backtest-critique", response_model=BacktestCritiqueResponse)
def backtest_critique(req: BacktestCritiqueRequest) -> BacktestCritiqueResponse:
    if not _openai_enabled():
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY chưa được cấu hình.")
    payload = _invoke_openai(
        system_prompt=_BACKTEST_SYSTEM_PROMPT,
        user_payload=req.model_dump(),
    )
    try:
        return BacktestCritiqueResponse(
            overall_grade=str(payload.get("overall_grade", "C"))[:5],
            red_flags=[str(x)[:200] for x in (payload.get("red_flags") or [])][:6],
            strengths=[str(x)[:200] for x in (payload.get("strengths") or [])][:6],
            additional_validation=[str(x)[:200] for x in (payload.get("additional_validation") or [])][:6],
            interpretation=str(payload.get("interpretation", ""))[:600],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"AI payload không hợp lệ: {exc}") from exc


# ── Health probe ─────────────────────────────────────────────
class AIHealthResponse(BaseModel):
    openai_configured: bool
    model: str


@router.get("/health", response_model=AIHealthResponse)
def ai_health() -> AIHealthResponse:
    return AIHealthResponse(openai_configured=_openai_enabled(), model=_model_name())
