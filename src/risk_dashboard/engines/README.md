# Engines

Computational core for Northstar — **not** product UI modules.

## Packages

| Package | Role |
|---------|------|
| `engines.quant` | Models, risk metrics, backtests, financial statement analytics, EOD pipeline |
| `engines.agents` | EOD narrative (LangGraph): narrative bundle, reviewer, intent router |

Product chatbots (`ai_assistant`, multi-agent chat, trading-lab chat) have been removed.

## Allowed dependencies

- `engines.quant` → data connectors / shared schemas / platform utils. **No** FastAPI, **no** `modules/*`.
- `engines.agents` → may call `engines.quant`, data connectors, shared schemas. **No** FastAPI, **no** `modules/*`.
- `modules/*/application` → **only** layer that should import engines for product features.

## Import path

Use `risk_dashboard.engines.quant.*` for computational modules and notebooks.
`risk_dashboard.quant.xgb_engine` remains only because stored pickle models
reference that historical module path. Other unused quant shims were removed.

## Non-goals

- Not a product domain (no user-facing chat routes).
- Not for storing product session state (that stays in module infrastructure / SQLite).
