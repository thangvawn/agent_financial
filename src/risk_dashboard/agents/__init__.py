"""
EOD narrative agents (LangGraph) — xử lý quant output thành ngôn ngữ.

Tách biệt với modules/ai_assistant (multi-turn chat) và
modules/agent_orchestration (HTTP routing layer).

- ``graph``: LangGraph graph chạy EOD run
- ``narrative``: build NarrativeBundle từ QuantEngineOutput
- ``reviewer``: verify narrative vs quant numbers
- ``router``: intent routing cho single-turn queries
- ``multi_agent``: supervisor graph cho multi-agent chat
- ``tools/``: LangChain tools (fundamental, macro, portfolio, quant, sector)
"""
from risk_dashboard.agents.graph import AgentState, run_eod_narrative, run_intent
from risk_dashboard.agents.narrative import build_narrative_bundle
from risk_dashboard.agents.reviewer import verify_narrative_against_quant
from risk_dashboard.agents.router import Intent, route_intent

__all__ = [
    "AgentState",
    "Intent",
    "build_narrative_bundle",
    "route_intent",
    "run_eod_narrative",
    "run_intent",
    "verify_narrative_against_quant",
]
