# Architecture Overview

Hệ thống phân tích rủi ro và giáo dục tài chính cho thị trường Việt Nam.

Stack: **FastAPI (Python) → React (Vite) → SQLite + Redis**

---

## Tổng quan luồng dữ liệu

```
Nguồn dữ liệu                 Backend (src/)                Frontend (frontend/src/)
──────────────                 ──────────────                ────────────────────────
vnstock / yfinance  →  data/   →  pipeline/  →  engines/ →  api/  →  features/
CSV / Google Drive  →  data/   →  modules/   →  platform/ →  api/     shared/
BCTC upload                    →  (quant + agents trong engines/)
```

---

## Backend (`src/risk_dashboard/`)

### Sơ đồ package

```
src/risk_dashboard/
│
├── api/              HTTP layer
│   ├── main.py       FastAPI app, mount routers từ modules
│   └── middleware.py API key auth, request logging
│
├── app/              Application bootstrap
│   ├── bootstrap/    app_factory (tạo FastAPI app), lifecycle (startup/shutdown)
│   ├── config/       settings.py (pydantic-settings, đọc .env)
│   └── registry/     module_definition + registry (auto-mount feature modules)
│
├── modules/          feature modules (vertical slices)
│   ├── auth/
│   ├── home_onboarding/     HOME
│   ├── learning/            Learn Hub
│   ├── guided_investing/    BCTC surface (UI)
│   ├── news_intelligence/   News & Intelligence
│   ├── pro_lab/             Simulation Lab (backtest/scenario)
│   ├── financials_product/  BCTC upload + analysis API
│   ├── data_hub/            market data API
│   ├── market_portfolio/    facade /api/v1/market-portfolio (watchlist, mock orders, PnL)
│   ├── watchlist_product/   legacy price-cache helpers
│   ├── portfolio_product/   legacy backtest stub (410)
│   ├── watchlist_product/
│   ├── portfolio_product/
│   ├── ai_assistant/        multi-turn LLM chat (LangGraph)
│   ├── agent_orchestration/ HTTP routing layer cho agents
│   ├── quant_risk/          API endpoint cho quant engine
│   ├── analytics_monitoring/
│   ├── admin_cms/
│   ├── trust_safety/
│   ├── system_surface/
│   └── … (legacy: community/goals/financial_health — routers OFF by default)
│   Mỗi module có cấu trúc: api/ application/ domain/ infrastructure/ schemas/
│
│   Product map: app/registry/product_domains.py
│   Phase 4 slugs: home, simulation_lab (packages may remain home_onboarding/pro_lab)
│   Unmounted archive: community, goals, financial_health
│   Retired off-by-default: guided_investing (BCTC → financials_product)
│   Đã gỡ khỏi product surface: insights, Community UI,
│   Pro Lab research extras (Swarm/Copilot/Optimizer/Monte Carlo)
│
├── engines/          Computational core (Phase 5)
│   ├── README.md     ranh giới: quant vs agents; modules chỉ gọi qua application
│   ├── quant/        models, risk, backtest, BCTC analytics, EOD pipeline
│   └── agents/       LangGraph narrative / multi-agent / trading lab tools
│       (shims deprecated: risk_dashboard.quant.* / risk_dashboard.agents.*)
│
├── data/             Data connectors & ETL
│   ├── interfaces.py     abstract MacroSource, MarketSource
│   ├── market_connector.py  OHLCV từ CSV / vnstock
│   ├── macro_connector.py   vĩ mô từ CSV
│   ├── macro_auto.py        yfinance / World Bank
│   ├── macro_official.py    nguồn chính thức
│   ├── sector_connector.py
│   ├── financials.py        BCTC
│   ├── etl.py               align tần suất, build feature row
│   ├── ingest.py            orchestrate training panel
│   ├── universe_fetch.py    VN30/VNINDEX universe
│   ├── cross_asset_prices.py gold, USD, DXY...
│   ├── watchlist_prices.py
│   └── google_drive.py
│
├── pipeline/         ETL pipeline factories
│   ├── settings.py       đường dẫn mặc định
│   ├── market_factory.py chọn MarketSource
│   ├── macro_factory.py  chọn MacroSource
│   └── panel_materialize.py gộp + ghi Parquet
│
├── platform/         Cross-cutting infrastructure
│   ├── database/     SQLite connections (data/db/northstar.db)
│   ├── feature_flags/ feature flag service
│   ├── model_runtime/ model registry (pkl)
│   ├── runtime/      panel store (in-memory cache)
│   └── security/     access control
│
├── schemas/          Shared Pydantic schemas
│   ├── financials.py  FinancialDataset, FinancialAnalysisResponse...
│   └── snapshots.py   QuantEngineOutput, EODRunManifest, NarrativeBundle...
│
├── storage/          ETL registry
│   └── sqlite_store.py IngestRegistry (track ingest runs)
│
└── cli/              11 CLI entry points
    ├── ingest.py         risk-eod-ingest
    ├── fetch_market_universe.py  risk-fetch-universe
    ├── train_job.py      risk-train-model
    ├── fetch_financials.py
    └── ...
```

### Quy ước module

Mỗi feature module trong `modules/` có cấu trúc:
```
modules/{feature}/
├── module.py          ModuleDefinition (id, routers, feature flags)
├── api/
│   ├── public.py      router public (/api/v1/public/...)
│   └── pro.py         router pro (/api/v1/pro/...)  [nếu có]
├── application/       use cases, services
├── domain/            entities, policies, value objects
├── infrastructure/    repositories (SQLite), external adapters
└── schemas/           request/response Pydantic models cho module này
```

---

## Frontend (`frontend/src/`)

### Sơ đồ thư mục

```
frontend/src/
│
├── app/                    Application shell
│   ├── AppShell.jsx        Main layout, view switching, auth gate
│   ├── NavBar.jsx          Top navigation bar
│   └── domainRoutes.js     URL ↔ view name mapping
│
├── app/
│   ├── AppShell.jsx
│   ├── domainRoutes.js
│   └── productRegistry.js  # map 6 product domains ↔ routes/nav
│
├── features/               Product domains (pages + services + components)
│   ├── home/
│   ├── market-portfolio/
│   ├── learn-hub/
│   ├── bctc/
│   ├── news/
│   ├── simulation-lab/
│   └── auth/
│
├── shared/                 Cross-cutting UI (nav, assistant, analytics)
│
│ Legacy shims (không thêm code mới):
│   pages/index.js → re-export features
│   modules/README.md → deprecated
│
├── shared/                 Cross-cutting UI utilities
│   ├── assistant/          FloatingAssistant component + API
│   ├── analytics/          trackEvent (analytics event emitter)
│   ├── navigation/         ConnectedWorkspaceNav
│   ├── query/              React Query client + provider
│   └── Icons.jsx           Icon library
│
├── styles/                 Design system
│   ├── tokens.css          CSS variables (colors, spacing, typography)
│   ├── base-elements.css   Button, input, card base styles
│   ├── retail-surfaces.css Module-specific surface styles
│   └── app-shell.css       Layout shell styles
│
├── App.jsx                 Root component, URL → view state
├── main.jsx                React entry point
└── ErrorBoundary.jsx       Global error boundary
```

### Quy ước pages vs modules

| Thư mục | Vai trò | Ví dụ |
|---------|---------|-------|
| `pages/` | UI container — nhận props từ AppShell, render layout | `HomePage.jsx`, `InsightsPage.jsx` |
| `modules/` | Business logic — hooks, services (API calls), components tái dùng | `useHome()`, `fetchInsightsDashboard()` |
| `shared/` | Cross-cutting utilities dùng ở nhiều modules | `trackEvent`, `FloatingAssistant` |

Pages import từ modules, modules không import từ pages.

---

## Quan hệ BE ↔ FE

```
FE modules/{feature}/services/  →  HTTP  →  BE modules/{feature}/api/
FE shared/assistant/            →  HTTP  →  BE modules/ai_assistant/api/
FE pages/pro-lab/               →  HTTP  →  BE modules/pro_lab/api/
                                            BE agents/ (EOD, narrative)
                                            BE quant/ (XGBoost, VAR, SHAP)
```

---

## Môi trường

Xem `.env.example` và `README.md` để biết cách chạy.

- **Dev local**: `make dev` (backend) + `make dev-frontend` (Vite)
- **Docker**: `docker compose up -d`
- **Data**: cần chạy `risk-fetch-universe` lần đầu để có panel cache
