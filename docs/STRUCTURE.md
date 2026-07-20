# Repository Structure

Mục tiêu: tách rõ source code, frontend app, tài liệu, runtime data; frontend tổ chức theo **product domain**.

## Root

- `README.md`, `pyproject.toml`, `Makefile`, `Dockerfile`, `docker-compose.yml`
- `.env.example` — không commit `.env`
- `plans/` — kế hoạch triển khai (gồm refactor cấu trúc)

## Backend (`src/risk_dashboard/`)

- `modules/` — vertical slice theo domain (API + application + domain + infrastructure)
- `platform/` — database, security, feature flags
  - **Database module:** `platform/database/` — một SQLite transactional
    (`RISK_DASHBOARD_DB_PATH`, default `data/db/northstar.db`; xem `platform/database/README.md`)
- `engines/` — `quant` + `agents` (xem `engines/README.md`); shims `quant/` + `agents/` vẫn re-export
- `data/` — connectors / cache / uploads (parquet, pkl, JSON — không nhét vào SQLite)
- `app/registry/` — mount modules

Product domains: `home`, `market_portfolio`, `learn_hub`, `bctc`, `news`, `simulation_lab`, `auth`.

- Map + alias: `src/risk_dashboard/app/registry/product_domains.py`
- Registry helpers: `get_module_by_slug`, `get_enabled_modules_by_domain`, `resolve_module_slug`
- Registered product slugs (Phase 4): `home`, `simulation_lab`, `market_portfolio`, …
  - Package folders may still be `home_onboarding` / `pro_lab` (HTTP `/pro-lab` kept)
- Market & Portfolio facade: `/api/v1/market-portfolio`
- Unmounted (archived packages): `community`, `goals`, `financial_health`
- Retired off-by-default: `guided_investing` (BCTC = `financials_product`)
- Alias flags: `RISK_FLAG__MODULE__PRO_LAB__ENABLED` → `simulation_lab`;
  `RISK_FLAG__MODULE__HOME_ONBOARDING__ENABLED` → `home`

Chi tiết roadmap: `plans/2026-07-17-northstar-codebase-structure-refactor.md`.

## Frontend (`frontend/src/`)

```
app/                 # AppShell, routes, productRegistry
features/            # một folder = một product domain
  home/
  market-portfolio/
  learn-hub/
  bctc/
  news/
  simulation-lab/
  auth/
shared/              # navigation, assistant, analytics
styles/
```

Mỗi feature thường có:

- `pages/` — màn hình route
- `services/` — HTTP API
- `components/` / `hooks/` — nội bộ feature
- `index.js` — public export

`pages/` và `modules/` cũ chỉ còn shim/README — không thêm code mới vào đó.

Nguồn tên domain / nav: `frontend/src/app/productRegistry.js`.

## Documentation / Data

- `docs/` — architecture, specs, project notes
- `data/` — runtime cache/SQLite (không commit secrets)
- `tests/` — pytest
- `output/` — artifact trình bày (excalidraw…)

## Khi thêm feature mới

1. Tạo `frontend/src/features/<domain>/…`
2. Đăng ký trong `productRegistry.js` + `domainRoutes.js`
3. Backend module trong `src/risk_dashboard/modules/<domain>/`
4. Test `tests/test_<domain>.py`
5. Không đặt logic domain vào `shared/`
