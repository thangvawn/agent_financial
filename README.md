# Risk Dashboard

Hệ thống phân tích rủi ro định lượng cho thị trường chứng khoán Việt Nam.

Pipeline: **Dữ liệu → Quant Engine (XGBoost/GARCH/HMM/SHAP/VAR) → Multi-Agent LLM → FastAPI → React Dashboard**.

---

## Mục lục

- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt nhanh (local)](#cài-đặt-nhanh-local)
- [Chạy bằng Docker](#chạy-bằng-docker)
- [Nạp dữ liệu](#nạp-dữ-liệu)
- [Chạy phân tích](#chạy-phân-tích)
- [API Endpoints](#api-endpoints)
- [CLI Commands](#cli-commands)
- [Chạy tests](#chạy-tests)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Cấu hình](#cấu-hình)
- [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|------------|---------------------|
| Python | 3.10+ |
| Node.js | 20+ (cho frontend) |
| Docker | 24+ (nếu chạy Docker) |

---

## Cài đặt nhanh (local)

### Bước 1 — Clone repo

```bash
git clone https://github.com/thangvawn/agent_financial.git
cd agent_financial
```

### Bước 2 — Tạo môi trường Python

```bash
python -m venv .venv
source .venv/bin/activate    # macOS / Linux
# .venv\Scripts\activate     # Windows
```

### Bước 3 — Cài dependencies

```bash
# Cài tất cả (backend + dev tools + auto macro)
pip install -e ".[dev,auto]"

# Cài frontend
cd frontend && npm install && cd ..
```

Hoặc dùng Makefile:

```bash
make install
```

### Bước 4 — Cấu hình `.env`

```bash
cp .env.example .env
```

Mở file `.env` và điền:

```
OPENAI_API_KEY=sk-your-key-here    # Bắt buộc cho chat AI
API_SECRET_KEY=                     # Để trống = API public
LOG_LEVEL=INFO
```

### Bước 5 — Nạp dữ liệu lần đầu

```bash
# Tải VNINDEX + VN30 từ vnstock + macro tự động từ World Bank
pip install -e ".[vnstock,auto]"
risk-fetch-universe --start 2015-01-01 --end 2026-04-06 --macro auto --out ./data/cache
```

> Lệnh này cần mạng internet, mất khoảng 2-5 phút. Kết quả lưu vào `data/cache/`.

### Bước 6 — Chạy Backend API

```bash
make dev
# hoặc: uvicorn risk_dashboard.api.main:app --reload --app-dir src
```

Backend chạy tại `http://localhost:8000`.

### Bước 7 — Chạy Frontend (dev mode)

Mở terminal mới:

```bash
make dev-frontend
# hoặc: cd frontend && npm run dev
```

Frontend chạy tại `http://localhost:5173` (tự động proxy API sang port 8000).

### Bước 7 (thay thế) — Build frontend để backend serve trực tiếp

```bash
make build
# hoặc: cd frontend && npm run build
```

Sau khi build, truy cập `http://localhost:8000/dashboard` — backend serve trực tiếp React app.

---

## Chạy bằng Docker

### Bước 1 — Chuẩn bị `.env`

```bash
cp .env.example .env
# Sửa OPENAI_API_KEY trong .env
```

### Bước 2 — Build & chạy

```bash
# Build image
docker compose build

# Chạy nền
docker compose up -d

# Xem logs
docker compose logs -f app
```

Hoặc dùng Makefile:

```bash
make docker-build
make up
make logs
```

### Bước 3 — Truy cập

| URL | Mô tả |
|-----|-------|
| http://localhost:8000/dashboard | React Dashboard |
| http://localhost:8000/docs | Swagger API (tương tác) |
| http://localhost:8000/redoc | ReDoc API (đọc) |
| http://localhost:8000/health | Health check |

### Quản lý Docker

```bash
docker compose ps          # Xem trạng thái
docker compose restart app # Restart app
docker compose down        # Tắt tất cả
docker compose down -v     # Tắt + xóa volumes
docker compose up -d --build  # Rebuild khi code thay đổi
```

> Thư mục `./data` được mount vào container — dữ liệu không mất khi tắt/xóa container.

---

## Nạp dữ liệu

### Tự động (từ vnstock + World Bank)

```bash
# Cần cài trước: pip install -e ".[vnstock,auto]"
risk-fetch-universe --start 2015-01-01 --end 2026-04-06 \
  --macro auto --out ./data/cache
```

### Từ file CSV

**Dữ liệu thị trường** — cần cột: `tradingDate` (hoặc `date`), `close`, `volume`.

```bash
risk-eod-ingest --start 2024-01-01 --end 2024-12-31 \
  --market csv --market-csv path/to/market.csv \
  --macro-csv path/to/macro.csv \
  --output-dir ./data_outputs
```

**Dữ liệu vĩ mô (tháng)** — cần cột: `period_end`, `usd_vnd_rate`, `usd_vnd_1m_change_pct`, `sbv_interest_rate_pct`. Tùy chọn: `cpi_yoy_pct`, `fdi_disbursement_yoy_pct`.

Xem mẫu tại:
- `tests/fixtures/sample_market.csv`
- `tests/fixtures/sample_macro.csv`
- `tests/fixtures/sample_official_macro.csv`

### Vĩ mô tự động (không cần CSV)

```bash
pip install -e ".[auto]"
risk-eod-ingest --start 2024-01-01 --end 2024-12-31 \
  --market csv --market-csv path/to/market.csv \
  --macro-auto --output-dir ./data_outputs
```

Nguồn tự động: tỷ giá USD/VND từ Yahoo Finance, CPI/lãi suất/FDI từ World Bank API (ước lượng, không thay số liệu chính thức GSO/SBV).

---

## Chạy phân tích

### Trên giao diện Dashboard

1. Mở `http://localhost:8000/dashboard` (hoặc `http://localhost:5173` nếu dev mode)
2. Chọn **As Of Date** → bấm **Chạy Phân tích EOD**
3. Kết quả: Risk Score, Regime, SHAP, xác suất giảm điểm
4. Tab **Mô phỏng Kịch bản**: kéo slider tỷ giá / lãi suất → bấm **Chạy Mô phỏng**
5. Tab **Financial Analysis**: nhập ticker (VD: `FPT`) → bấm **Phân tích BCTC**
6. Nút chat 💬 góc phải: hỏi AI về rủi ro, stress test, danh mục

### Qua API

```bash
# Health check
curl http://localhost:8000/health

# Chạy EOD
curl -X POST http://localhost:8000/eod/run \
  -H "Content-Type: application/json" \
  -d '{"as_of": "2026-03-29"}'

# Mô phỏng kịch bản
curl -X POST http://localhost:8000/scenario/rerun \
  -H "Content-Type: application/json" \
  -d '{"as_of": "2026-03-29", "usd_vnd_rate": 25500}'

# Chat với AI
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"as_of": "2026-03-29", "message": "VN-INDEX hôm nay thế nào?"}'

# Phân tích BCTC
curl http://localhost:8000/financials/FPT/analysis
```

---

## API Endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/health` | Health check (panel + model status) |
| GET | `/dashboard` | React Dashboard UI |
| GET | `/dashboard/state` | Trạng thái panel dữ liệu |
| GET | `/dashboard/history` | Lịch sử Risk Score + VN-INDEX |
| GET | `/dashboard/live` | Dữ liệu realtime (DNSE) |
| GET | `/dashboard/money-flow` | Dòng tiền ngành |
| POST | `/eod/run` | Chạy phân tích EOD đầy đủ |
| POST | `/scenario/rerun` | Mô phỏng kịch bản vĩ mô |
| POST | `/chat` | Chat với Multi-Agent AI |
| GET | `/research/model-report` | Báo cáo model benchmark |
| GET | `/financials/{ticker}/analysis` | Phân tích BCTC theo ticker |
| POST | `/financials/import` | Import dataset BCTC từ JSON |
| POST | `/admin/load-panel` | Nạp panel thủ công |
| GET | `/docs` | Swagger UI (interactive) |
| GET | `/redoc` | ReDoc (read-only) |

> Nếu `API_SECRET_KEY` được đặt trong `.env`, tất cả request (trừ `/health`, `/docs`) phải gửi header `X-API-Key`.

---

## CLI Commands

| Lệnh | Chức năng |
|-------|-----------|
| `risk-fetch-universe` | Crawl VNINDEX + VN30, sinh training panel |
| `risk-eod-ingest` | Ingest dữ liệu thị trường + vĩ mô → Parquet |
| `risk-eod-job` | Ingest + đăng ký vào SQLite registry |
| `risk-fetch-data` | Tải dữ liệu thị trường |
| `risk-fetch-financials` | Tải BCTC doanh nghiệp |
| `risk-train-model` | Train model rủi ro offline |
| `risk-benchmark-models` | So sánh các thuật toán ML |
| `risk-benchmark-features` | So sánh các bộ features |
| `risk-model-report` | Sinh báo cáo model |

---

## Chạy tests

```bash
# Chạy tất cả tests
make test
# hoặc: pytest

# Chạy với coverage report
make test-cov
# hoặc: pytest --cov=risk_dashboard --cov-report=term-missing

# Chạy 1 file cụ thể
pytest tests/test_api.py -v

# Lint code
make lint
# hoặc: ruff check src/ tests/

# Format code
make fmt
```

---

## Cấu trúc dự án

```
agent_financial/
├── src/risk_dashboard/         # Package Python chính
│   ├── api/                    # FastAPI endpoints + middleware
│   │   ├── main.py             #   App, routes, panel management
│   │   └── middleware.py        #   API key auth + request logging
│   ├── agents/                 # Multi-Agent LLM system
│   │   ├── graph.py            #   EOD narrative pipeline
│   │   ├── multi_agent.py      #   LangGraph orchestrator (6 agents)
│   │   ├── narrative.py        #   Narrative generation
│   │   ├── reviewer.py         #   Compliance reviewer
│   │   ├── router.py           #   Intent routing
│   │   └── tools/              #   LangChain tools per domain
│   │       ├── macro.py        #     Macro indicators
│   │       ├── fundamental.py  #     Financial metrics
│   │       ├── quant.py        #     Risk score, stress test, VaR
│   │       ├── sector.py       #     Sector money flow
│   │       └── portfolio.py    #     Portfolio metrics
│   ├── quant/                  # Quantitative engine
│   │   ├── eod_pipeline.py     #   Main EOD flow
│   │   ├── xgb_engine.py       #   GradientBoosting risk model
│   │   ├── advanced_engine.py  #   HMM regime + GARCH volatility
│   │   ├── analytics.py        #   VaR, CVaR, stress test, Basel
│   │   ├── var_engine.py       #   Vector Autoregression
│   │   ├── shap_explain.py     #   SHAP feature attribution
│   │   ├── scenario.py         #   What-if macro simulation
│   │   └── model_benchmark.py  #   Model comparison framework
│   ├── data/                   # Data ingestion & connectors
│   │   ├── market_connector.py #   CSV / vnstock market data
│   │   ├── macro_connector.py  #   CSV macro data
│   │   ├── macro_auto.py       #   World Bank / yfinance auto
│   │   ├── macro_official.py   #   Official CSV (GSO format)
│   │   ├── financials.py       #   BCTC via vnstock
│   │   ├── ingest.py           #   Training panel builder
│   │   └── etl.py              #   Mixed-frequency alignment
│   ├── schemas/                # Pydantic models
│   ├── storage/                # SQLite registry
│   ├── pipeline/               # Panel materialization
│   └── cli/                    # 9 CLI entry points
├── frontend/                   # React + Vite dashboard
│   └── src/
│       ├── App.jsx             #   Main dashboard component
│       ├── ErrorBoundary.jsx   #   Error handling UI
│       └── App.css             #   Styles
├── tests/                      # 22 test modules + fixtures
├── data/                       # Runtime data (gitignored: .pkl, .parquet)
│   ├── models/                 #   Trained models + benchmarks
│   ├── cache/                  #   Parquet panel cache
│   └── financials/             #   BCTC cache
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # App + Redis
├── Makefile                    # Dev shortcuts
├── pyproject.toml              # Python dependencies + config
└── .github/workflows/ci.yml   # GitHub Actions CI
```

---

## Cấu hình

Tất cả cấu hình qua file `.env` (copy từ `.env.example`):

| Biến | Bắt buộc | Mô tả |
|------|----------|-------|
| `OPENAI_API_KEY` | Có (cho chat) | API key OpenAI, dùng cho multi-agent chat |
| `API_SECRET_KEY` | Không | Đặt giá trị để bật API key gate, để trống = public |
| `LOG_LEVEL` | Không | `DEBUG`, `INFO` (mặc định), `WARNING`, `ERROR` |

### Extras (pip)

| Extra | Lệnh cài | Mục đích |
|-------|----------|----------|
| `dev` | `pip install -e ".[dev]"` | pytest, ruff, httpx |
| `auto` | `pip install -e ".[auto]"` | yfinance (macro tự động) |
| `vnstock` | `pip install -e ".[vnstock]"` | vnstock (dữ liệu HOSE) |
| `xgboost` | `pip install -e ".[xgboost]"` | XGBoost (thay thế sklearn) |

---

## Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|-----|-------------|----------|
| `Panel not loaded` / `503` | Chưa nạp dữ liệu | Chạy `risk-fetch-universe` rồi restart backend |
| `OPENAI_API_KEY not set` | Thiếu key cho chat | Điền key vào `.env` |
| `port 8000 already in use` | Đang chạy process khác | `lsof -i :8000` rồi kill, hoặc dùng `--port 8001` |
| `ModuleNotFoundError` | Chưa cài package | `pip install -e ".[dev,auto]"` |
| `sklearn version mismatch` | Model train bằng version cũ | Xóa `data/models/latest_model.pkl`, restart để retrain |
| Docker `Cannot connect` | Docker Desktop chưa chạy | Mở Docker Desktop |
| Frontend trắng | Chưa build hoặc chưa chạy dev | `make build` hoặc `make dev-frontend` |
| `vnstock` lỗi mạng | API nguồn không ổn định | Dùng `--market csv` với file CSV thay thế |

---

## Makefile shortcuts

```bash
make install        # Cài tất cả dependencies
make dev            # Chạy backend (hot reload)
make dev-frontend   # Chạy frontend (hot reload)
make test           # Chạy tests
make test-cov       # Tests + coverage report
make lint           # Kiểm tra code style
make fmt            # Tự động format code
make build          # Build frontend production
make docker-build   # Build Docker image
make up             # Docker compose up
make down           # Docker compose down
make logs           # Xem logs container
make clean          # Xóa cache files
```
