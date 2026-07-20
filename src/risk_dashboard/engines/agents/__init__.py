"""
EOD narrative agents (LangGraph) — xử lý quant output thành ngôn ngữ.

Product chatbots (ai_assistant / multi_agent / trading_lab) đã được gỡ.

- ``graph``: LangGraph graph chạy EOD run
- ``narrative``: build NarrativeBundle từ QuantEngineOutput
- ``reviewer``: verify narrative vs quant numbers
- ``router``: intent routing cho single-turn EOD queries
"""
from risk_dashboard.engines.agents.graph import AgentState, run_eod_narrative, run_intent
from risk_dashboard.engines.agents.narrative import build_narrative_bundle
from risk_dashboard.engines.agents.reviewer import verify_narrative_against_quant
from risk_dashboard.engines.agents.router import Intent, route_intent

__all__ = [
    "AgentState",
    "Intent",
    "build_narrative_bundle",
    "route_intent",
    "run_eod_narrative",
    "run_intent",
    "verify_narrative_against_quant",
]
