"""Baseline fixtures and inventory for Pro Lab AI endpoints (SIM0).

Documents:
1. strategy_copilot (pro_lab/api/ai.py:50-58)
2. backtest_critique (pro_lab/api/ai.py:136-168)
3. swarm_committee (pro_lab/api/ai.py:82-134)
   * Note: swarm_committee is a SINGLE model invocation with role-play prompt returning JSON,
     not a distributed multi-agent graph with shared memory or independent reviewers.
"""
from __future__ import annotations

from typing import Any

BASELINE_INVENTORY: dict[str, dict[str, Any]] = {
    "strategy_copilot": {
        "endpoint": "/pro-lab/ai/strategy-copilot",
        "file_line": "src/risk_dashboard/modules/pro_lab/api/ai.py:50",
        "handler": "execute_strategy_copilot",
        "request_schema": "StrategyCopilotRequest",
        "response_schema": "StrategyCopilotResponse",
        "model_invocation_count": 1,
        "latency_baseline_p50_ms": 1200,
        "latency_baseline_p95_ms": 3500,
        "cost_baseline_usd": 0.005,
        "rollback_path": "Revert to direct LLMProvider call with STRATEGY_SYSTEM_PROMPT",
    },
    "backtest_critique": {
        "endpoint": "/pro-lab/ai/backtest-critique",
        "file_line": "src/risk_dashboard/modules/pro_lab/api/ai.py:136",
        "handler": "execute_backtest_critique",
        "request_schema": "BacktestCritiqueRequest",
        "response_schema": "BacktestCritiqueResponse",
        "model_invocation_count": 1,
        "latency_baseline_p50_ms": 1500,
        "latency_baseline_p95_ms": 4000,
        "cost_baseline_usd": 0.008,
        "rollback_path": "Revert to direct LLMProvider call with BACKTEST_SYSTEM_PROMPT",
    },
    "swarm_committee": {
        "endpoint": "/pro-lab/ai/swarm-committee",
        "file_line": "src/risk_dashboard/modules/pro_lab/api/ai.py:82",
        "handler": "execute_swarm_committee",
        "request_schema": "SwarmCommitteeRequest",
        "response_schema": "SwarmCommitteeResponse",
        "model_invocation_count": 1,  # NOT a multi-agent graph; single role-play prompt
        "architecture_note": "Single OpenAI/Gemini prompt returning structured role-play memos",
        "latency_baseline_p50_ms": 1800,
        "latency_baseline_p95_ms": 4800,
        "cost_baseline_usd": 0.012,
        "rollback_path": "Revert to direct LLMProvider call with SWARM_SYSTEM_PROMPT",
    },
}

GOLDEN_STRATEGY_COPILOT_INPUT = {
    "idea": "Breakout trend following on VN30 stocks using 20-day high and 2x ATR stop loss",
    "market": "HOSE",
    "horizon": "medium_term",
    "risk_budget_pct": 2.0,
}

GOLDEN_STRATEGY_COPILOT_OUTPUT = {
    "strategy_name": "VN30 20D Donchian Breakout with ATR Stop",
    "market": "HOSE",
    "universe": ["FPT", "MWG", "MBB", "TCB", "HPG", "VHM"],
    "signal_stack": [
        "Entry: Price breaks above 20-day high with volume > 1.5x 20-day SMA volume",
        "Exit: Trailing stop at 2x 14-day ATR from highest high since entry",
    ],
    "risk_rules": [
        "Max 2% portfolio risk per trade",
        "Max 5 concurrent open positions",
        "Daily loss limit 4% portfolio stop-all",
    ],
    "validation_queue": [
        "Walk-forward optimization across 2020-2024",
        "Slippage stress test with 0.2% and 0.4%",
    ],
    "rationale": "Captures sustained momentum on liquid VN30 large caps while capping tail risk via volatility trailing stops.",
    "horizon": "medium_term",
    "confidence": "high",
}

GOLDEN_BACKTEST_CRITIQUE_INPUT = {
    "strategy_name": "VN30 Breakout",
    "metrics": {
        "total_return_pct": 45.2,
        "cagr_pct": 18.5,
        "sharpe_ratio": 1.42,
        "sortino_ratio": 1.88,
        "max_drawdown_pct": 12.4,
        "win_rate_pct": 52.0,
        "profit_factor": 1.65,
        "total_trades": 84,
    },
    "trade_log_sample": [
        {"ticker": "FPT", "entry": "2023-03-01", "exit": "2023-04-15", "pnl_pct": 14.2},
        {"ticker": "MWG", "entry": "2023-05-10", "exit": "2023-05-28", "pnl_pct": -3.8},
    ],
    "focus_area": "drawdown_and_regime_stability",
}

GOLDEN_BACKTEST_CRITIQUE_OUTPUT = {
    "overall_grade": "B+",
    "red_flags": [
        "Trade sample size (84 trades) is slightly low for 3-year statistical significance",
        "Missing explicit slippage assumption in trade log execution",
    ],
    "strengths": [
        "Favorable profit factor (1.65) and healthy Sharpe (1.42)",
        "Controlled max drawdown of 12.4% during 2022-2023 market corrections",
    ],
    "additional_validation": [
        "Perform Monte Carlo trade shuffling to verify path independence",
        "Test on midcap universe (VNMidcap) to check robustness against liquidity drop",
    ],
    "interpretation": "Strategy demonstrates solid risk-adjusted returns but requires slippage stress testing before live deployment.",
}

GOLDEN_SWARM_COMMITTEE_INPUT = {
    "strategy_brief": "Trend following on liquid VN30 stocks with ATR trailing stop",
    "review_focus": "Risk and methodology verification",
    "market": "HOSE",
}

GOLDEN_SWARM_COMMITTEE_OUTPUT = {
    "consensus": "approve_with_conditions",
    "confidence": "high",
    "memos": [
        {
            "role": "Quant Researcher",
            "stance": "positive",
            "memo": "Parameters are standard and avoid acute curve-fitting. Sample period needs extension.",
            "key_concerns": ["Lookback window sensitivity", "Market regime change in 2022"],
        },
        {
            "role": "Risk Manager",
            "stance": "cautious",
            "memo": "Trailing ATR stop provides adequate tail protection but position sizing must account for market gaps.",
            "key_concerns": ["Overnight gap risk on VN Index", "Liquidity constraints on exits"],
        },
        {
            "role": "Execution Specialist",
            "stance": "cautious",
            "memo": "HOSE matching engine constraints and ATC auction dynamics could cause slippage spikes.",
            "key_concerns": ["ATC price execution variance", "Transaction fees eating low-edge trades"],
        },
    ],
    "decision_summary": "Committee supports paper deployment conditional on adding 0.2% slippage and running walk-forward testing.",
    "next_actions": [
        "Add commission (0.15%) and slippage (0.2%) to backtest parameters",
        "Run 5-fold walk-forward validation across bull/bear cycles",
    ],
}

