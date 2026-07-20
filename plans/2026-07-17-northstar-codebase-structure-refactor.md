# Northstar — Refactor cấu trúc codebase theo domain sản phẩm

**Mục tiêu:** Cấu trúc chuyên nghiệp, đặt tên theo 6 không gian sản phẩm, dễ mở rộng feature mới mà không lẫn legacy research.

**Nguyên tắc:** YAGNI / KISS / DRY · đổi tên theo domain · không big-bang rewrite logic · giữ route alias cũ.

---

## Target product domains

| Domain id | UI name | FE folder | BE module (target) | Hiện trạng |
|-----------|---------|-----------|--------------------|------------|
| `home` | Home | `features/home` | `home_onboarding` (slim) | FE intro OK |
| `market_portfolio` | Market & Portfolio | `features/market-portfolio` | gộp `data_hub` market + `watchlist_product` + `portfolio_product` | tên `global-terminal` |
| `learn_hub` | Learn Hub | `features/learn-hub` | `learning` | tên `learning` |
| `bctc` | BCTC Analysis | `features/bctc` | `financials_product` (+ deprecate `guided_investing` surface) | tên `guided-investing` |
| `news` | News & Intelligence | `features/news` | `news_intelligence` | nằm trong `global-terminal` |
| `simulation_lab` | Simulation Lab | `features/simulation-lab` | rename `pro_lab` → `simulation_lab` | tên `pro-lab` |
| `auth` | Auth | `features/auth` | `auth` | OK |

Platform (không phải product tab): `ai_assistant`, `trust_safety`, `analytics_monitoring`, `admin_cms`, `system_surface`, `quant_risk`.

Legacy (deprecate, không mở rộng): `community`, `goals`, `financial_health`, `insights` (đã xóa).

---

## Target tree

### Frontend

```
frontend/src/
├── app/                      # shell, routes, providers
│   ├── AppShell.jsx
│   ├── domainRoutes.js
│   ├── NavBar.jsx
│   └── productRegistry.js    # single source of product domains
├── features/                 # một folder = một product domain
│   ├── home/
│   │   ├── pages/
│   │   ├── api/ | services/
│   │   └── index.js
│   ├── market-portfolio/
│   ├── learn-hub/
│   ├── bctc/
│   ├── news/
│   ├── simulation-lab/
│   └── auth/
├── shared/                   # cross-cutting UI only
└── styles/
```

Quy ước mỗi feature:
- `pages/` — màn hình route
- `services/` — HTTP API
- `hooks/` — state hooks (khi cần)
- `components/` — UI chỉ dùng trong feature
- `index.js` — public export của feature

### Backend (giữ vertical slice, đổi tên theo domain)

```
src/risk_dashboard/
├── app/                 # bootstrap + registry
├── platform/            # db, flags, security
├── modules/             # product + platform modules
│   ├── home/
│   ├── market_portfolio/
│   ├── learn_hub/
│   ├── bctc/
│   ├── news/
│   ├── simulation_lab/
│   ├── auth/
│   └── _platform/…      # hoặc giữ tên platform modules
├── engines/             # (phase sau) chuyển quant/ + agents/
├── data/
└── api/
```

---

## Phases

### Phase 1 — FE domain rename (low risk)  ← làm trước
1. Thêm `app/productRegistry.js` (map domain ↔ route ↔ labels).
2. Đổi `pages/` + `modules/` → `features/<domain>/…` (hoặc rename folders giữ pages/modules song song rồi migrate).
3. Cập nhật imports, `pages/index.js` → `features` barrel.
4. Giữ URL cũ (`/global-terminal`, `/pro-lab`, `/guided-investing`) qua alias.
5. Cập nhật `docs/STRUCTURE.md` + `docs/ARCHITECTURE.md`.

### Phase 2 — BE product map (không đổi behavior) ✅
1. ✅ `app/registry/product_domains.py` map domain → module slugs + helpers.
2. ✅ Alias: `simulation_lab` → `pro_lab` (`resolve_module_slug`, flag alias).
3. ✅ Legacy `community` / `goals` / `financial_health`: `enabled_by_default=False`.
4. ✅ Home soft-decouple community snapshot (không crash khi legacy tắt).
5. ✅ Tests: `tests/test_product_domains_registry.py`.

### Phase 3 — Consolidate Market & Portfolio ✅
1. ✅ FE: tabs Markets / Watchlist / Trade / Portfolio trong `features/market-portfolio`.
2. ✅ BE facade `/api/v1/market-portfolio/…` (proxy data-hub + watchlist + mock MP/LO + portfolio PnL).
3. ✅ News API tách khỏi `dataHubApi` → `features/news/services/newsApi.js`.
4. ✅ SPA fallback `/market`, `/portfolio`.
5. ✅ Tests: `tests/test_market_portfolio_facade.py`.

### Phase 4 — Rename BE modules (có breaking) ✅
1. ✅ Slug `pro_lab` → `simulation_lab` (package `pro_lab` + HTTP `/pro-lab` giữ cho FE).
2. ✅ BCTC = `financials_product`; `guided_investing` retired (`enabled_by_default=False`).
3. ✅ Slug `home_onboarding` → `home` (package folder giữ).
4. ✅ Unmount `community` / `goals` / `financial_health` (+ ARCHIVE.md); cắt wiring Home.
5. ✅ AI context builder soft-load legacy readers.

### Phase 5 — Engines cleanup ✅
1. ✅ `quant/` + `agents/` → `engines/quant` + `engines/agents` (+ README ranh giới).
2. ✅ Consumers/tests import `risk_dashboard.engines.*`; shims cũ vẫn re-export.
3. ✅ Quy ước: product modules nên gọi engines qua application services (document trong README).

---

## Definition of Done (Phase 1)
- [x] Mọi product UI nằm dưới tên domain chuẩn
- [x] `npm run build` pass
- [x] Route cũ vẫn mở đúng surface
- [x] Docs STRUCTURE/ARCHITECTURE cập nhật
- [x] Có `productRegistry` làm nguồn tên/nav duy nhất

## Definition of Done (Phase 2)
- [x] `product_domains.py` map 6+ domains + aliases + LEGACY_MODULES
- [x] Registry: `get_module_by_slug`, domain buckets, `simulation_lab` flag alias → `pro_lab`
- [x] Legacy `community` / `goals` / `financial_health`: `enabled_by_default=False`
- [x] Home community snapshot soft-fail (`try/except` → `None`)
- [x] `tests/test_product_domains_registry.py` pass (venv)
- [x] Docs STRUCTURE ghi map / flags legacy

## Definition of Done (Phase 3)
- [x] Facade `/api/v1/market-portfolio` mounted
- [x] Watchlist CRUD + mock MP/LO + portfolio PnL (paper)
- [x] FE tabs Watchlist / Trade / Portfolio
- [x] News API decoupled from market-portfolio services
- [x] SPA `/market` + `/portfolio`
- [x] Facade tests pass

## Definition of Done (Phase 4)
- [x] Registered slugs: `home`, `simulation_lab`
- [x] Aliases: `home_onboarding`→`home`, `pro_lab`→`simulation_lab`
- [x] `guided_investing` retired (off by default); BCTC = `financials_product`
- [x] `community` / `goals` / `financial_health` unmounted + ARCHIVE.md
- [x] Home không hard-import / không wire legacy snapshots
- [x] Registry tests pass

## Definition of Done (Phase 5)
- [x] Canonical packages: `engines.quant`, `engines.agents`
- [x] README ranh giới trong `engines/README.md`
- [x] Consumers + tests dùng `engines.*`; shim `quant/` + `agents/` còn lại
- [x] Docs STRUCTURE/ARCHITECTURE cập nhật
- [x] Smoke import / subset tests pass

---

## Không làm trong Phase 1–5
- Matching engine / order book thật
- Physical delete SQLite tables / package folders legacy
- Rename HTTP `/pro-lab` → `/simulation-lab` (FE vẫn dùng path cũ)
- Refactor toàn bộ API → application facade cho mọi engine call (chỉ document rule)
