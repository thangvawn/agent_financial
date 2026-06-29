# Architecture Overview

Hệ thống phân tích rủi ro và giáo dục tài chính cho thị trường Việt Nam.

Stack: **FastAPI (Python) → React (Vite) → SQLite + Redis**

---

## Tổng quan luồng dữ liệu

```
Nguồn dữ liệu                 Backend (src/)                Frontend (frontend/src/)
──────────────                 ──────────────                ────────────────────────
vnstock / yfinance  →  data/   →  pipeline/  →  quant/   →  api/  →  pages/
CSV / Google Drive  →  data/   →  agents/    →  modules/ →  api/     modules/
BCTC upload                    →  platform/  (cross-cutting)         shared/
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
├── modules/          22 feature modules (vertical slices)
│   ├── auth/
│   ├── home_onboarding/
│   ├── learning/
│   ├── guided_investing/
│   ├── insights/
│   ├── news_intelligence/
│   ├── pro_lab/
│   ├── community/
│   ├── ai_assistant/       multi-turn LLM chat (LangGraph)
│   ├── agent_orchestration/ HTTP routing layer cho agents
│   ├── quant_risk/         API endpoint cho quant engine
│   ├── financials_product/ BCTC upload + analysis API
│   ├── data_hub/           market data API
│   ├── watchlist_product/
│   ├── portfolio_product/
│   ├── financial_health/
│   ├── goals/
│   ├── analytics_monitoring/
│   ├── admin_cms/
│   ├── trust_safety/
│   ├── system_surface/
│   └── ...
│   Mỗi module có cấu trúc: api/ application/ domain/ infrastructure/ schemas/
│
├── agents/           EOD narrative agents (LangGraph)
│   │  Chú ý: tách biệt với modules/ai_assistant (chat) và
│   │         modules/agent_orchestration (HTTP routing)
│   ├── graph.py      LangGraph EOD graph
│   ├── narrative.py  build NarrativeBundle
│   ├── reviewer.py   verify narrative vs numbers
│   ├── router.py     intent routing
│   ├── multi_agent.py supervisor graph
│   └── tools/        LangChain tools (macro, fundamental, quant...)
│
├── quant/            Quantitative engines
│   ├── xgb_engine.py     XGBoost risk classifier
│   ├── var_engine.py     Vector AutoRegression
│   ├── shap_explain.py   SHAP feature attribution
│   ├── eod_pipeline.py   orchestrate train+predict
│   ├── backtest.py       rolling holdout
│   ├── scenario.py       macro override
│   ├── financial_analysis.py  ratio analysis
│   ├── financial_quality_charts.py
│   ├── balance_sheet_strength.py
│   ├── peer_compare.py
│   └── advanced_engine.py HMM regime detection
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
│   ├── database/     SQLite connections (app_state.db)
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
├── pages/                  Page-level components (UI containers)
│   ├── home-onboarding/    HomePage, OnboardingPage, MarketOverviewPage
│   ├── auth/               AuthPage
│   ├── learning/           LearningHomePage, EducationPlatformPage
│   ├── guided-investing/   GuidedInvestingPage
│   ├── insights/           InsightsPage
│   ├── community/          CommunityPage
│   ├── global-terminal/    GlobalTerminalPage, NewsPage, NewsEconCalendarPage
│   ├── pro-lab/            ProLabPage, ProLabBacktestStudioPage, ...
│   └── admin/              ContentOpsAdminPage, AnalyticsAdminPage,
│                           CommunityModerationPage, TrustSafetyAdminPage,
│                           ProLabAdminPage, LearningAdminPage
│
├── modules/                Feature modules (business logic)
│   ├── home-onboarding/    hooks, services, components, analytics
│   ├── auth/               useAuth hook
│   ├── learning/           hooks, services, components, content
│   ├── guided-investing/   services
│   ├── insights/           services
│   ├── community/          services
│   ├── data-hub/           services (market data, global terminal)
│   ├── financials/         services (BCTC upload/analysis)
│   ├── pro-lab/            services
│   ├── analytics-admin/    services
│   ├── content-ops-admin/  services
│   ├── trust-safety-admin/ services
│   ├── learning-admin/     services
│   └── pro-lab-admin/      services
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
