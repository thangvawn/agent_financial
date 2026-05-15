# Risk Dashboard

Hệ thống phân tích rủi ro định lượng cho thị trường chứng khoán Việt Nam: **dữ liệu → quant engine (XGBoost/GARCH/HMM/SHAP/VAR) → multi-agent LLM → FastAPI → React**.

Tài liệu này giúp người mới **clone repo và chạy được** (Docker hoặc máy local).

---

## Mục lục

- [Yêu cầu](#yêu-cầu)
- [Clone repo](#clone-repo)
- [Cách 1 — Docker (khuyến nghị)](#cách-1--docker-khuyến-nghị)
- [Cách 2 — Chạy trên máy (Python + Node)](#cách-2--chạy-trên-máy-python--node)
- [Biến môi trường `.env`](#biến-môi-trường-env)
- [Nạp dữ liệu lần đầu](#nạp-dữ-liệu-lần-đầu)
- [URL sau khi chạy](#url-sau-khi-chạy)
- [Truy cập từ máy khác (LAN / ngrok)](#truy-cập-từ-máy-khác-lan--ngrok)
- [Lệnh thường dùng (Makefile)](#lệnh-thường-dùng-makefile)
- [Tests & chất lượng code](#tests--chất-lượng-code)
- [API & CLI (tham khảo)](#api--cli-tham-khảo)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)
- [Đẩy code lên Git (gợi ý)](#đẩy-code-lên-git-gợi-ý)

---

## Yêu cầu

| Thành phần | Ghi chú |
|------------|---------|
| **Git** | Để clone |
| **Docker Desktop** (cách 1) | Docker 24+, `docker compose` |
| **Python 3.10+** (cách 2) | Khuyến nghị 3.12 để gần với image Docker |
| **Node.js 20+** (cách 2, frontend dev) | Khi chạy Vite riêng |
| **Mạng** | Lần đầu cần internet để cài package và tải dữ liệu |

---

## Clone repo

```bash
git clone <URL-repo-của-bạn>.git
cd <tên-thư-mục-repo>
```

Ví dụ sau giả sử bạn đang đứng ở **thư mục gốc của repo** (nơi có `pyproject.toml`, `docker-compose.yml`).

---

## Cách 1 — Docker (khuyến nghị)

Phù hợp khi muốn **một lệnh có API + dashboard build sẵn** (port **8000**).

### 1. Tạo file môi trường

```bash
cp .env.example .env
```

Chỉnh tối thiểu `OPENAI_API_KEY` nếu cần chat AI (xem [Biến môi trường](#biến-môi-trường-env)).

### 2. Build và chạy

```bash
docker compose build
docker compose up -d
docker compose logs -f app frontend
```

Đợi log không còn lỗi import / uvicorn báo **Application startup complete** và service `frontend` bắt đầu watch build. Sau lần build đầu tiên, sửa UI trong `frontend/src` sẽ tự build lại `frontend/dist`; chỉ cần refresh `http://localhost:8000/`, không cần `docker compose build` hay `docker compose up` lại.

### 3. Nạp dữ liệu panel (bắt buộc để dashboard không 503)

Image Docker cài extra `auto` (macro tự động); lệnh crawl VN cần **`vnstock`** — cách đơn giản là chạy **một lần trên máy host** (dùng chung thư mục `./data` với container):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[vnstock,auto]"
risk-fetch-universe --start 2015-01-01 --end 2026-04-06 --macro auto --out ./data/cache
```

Sau đó restart app nếu cần:

```bash
docker compose restart app
```

### 4. Mở trình duyệt

| URL | Mô tả |
|-----|--------|
| [http://localhost:8000/dashboard](http://localhost:8000/dashboard) | Dashboard React (do backend phục vụ) |
| [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger |
| [http://localhost:8000/health](http://localhost:8000/health) | Health check |

Tắt stack:

```bash
docker compose down
```

`./data` được **mount** vào container — cache/model trong `data/` (theo `.gitignore`) vẫn nằm trên máy bạn.

---

## Cách 2 — Chạy trên máy (Python + Node)

### 1. Môi trường Python

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Cài backend + frontend

```bash
make install
# tương đương: pip install -e ".[dev,auto]" && cd frontend && npm ci
```

### 3. `.env`

```bash
cp .env.example .env
# sửa OPENAI_API_KEY và các key tùy chọn (mục dưới)
```

### 4. Nạp dữ liệu

```bash
pip install -e ".[vnstock,auto]"
risk-fetch-universe --start 2015-01-01 --end 2026-04-06 --macro auto --out ./data/cache
```

### 5. Chạy backend

```bash
make dev
# Backend: http://localhost:8000 (lắng nghe 0.0.0.0 — có thể mở bằng IP LAN)
```

### 6. (Tuỳ chọn) Frontend dev — Vite + proxy API

Terminal khác:

```bash
make dev-frontend
```

Mở URL mà Vite in ra (thường có thêm base path **`/dashboard-static/`**). API được proxy sang port **8000**.

### 7. (Tuỳ chọn) Chỉ build frontend, xem qua backend

```bash
make build
# Rồi mở http://localhost:8000/dashboard
```

Khi dùng Docker Compose mặc định, bước này thường không cần nữa vì service `frontend` đã chạy `npm run build -- --watch` và backend đã mount `./frontend/dist`.

---

## Biến môi trường `.env`

Copy từ [`.env.example`](.env.example). **Không commit** file `.env` lên Git (đã có trong `.gitignore`).

| Biến | Bắt buộc? | Mô tả |
|------|-----------|--------|
| `OPENAI_API_KEY` | Có nếu dùng chat / agent LLM | Key OpenAI |
| `AI_ASSISTANT_AGENT_ENABLED` | Không | `1` bật agent, `0` fallback không LLM |
| `AI_ASSISTANT_MODEL` | Không | Model chat (vd. `gpt-4o-mini`) |
| `TAVILY_API_KEY` | Không | Tin tức / news analyst nếu bật Tavily |
| `ELEVENLABS_*` | Không | Giọng ElevenLabs; để trống vẫn dùng voice local |
| `API_SECRET_KEY` | Không | Nếu đặt, gửi header `X-API-Key` cho API (trừ một số route công khai) |
| `FINNHUB_API_KEY` | Không | Lịch vĩ mô / quote (xem comment trong `.env.example`) |
| `LOG_LEVEL` | Không | `INFO`, `DEBUG`, … |

Chi tiết thêm: xem comment trong `.env.example`.

---

## Nạp dữ liệu lần đầu

- **Tự động VNINDEX + VN30 + macro:** cần `pip install -e ".[vnstock,auto]"` rồi `risk-fetch-universe ...` (như trên).
- **CSV tùy chỉnh:** `risk-eod-ingest` — mẫu cột trong `tests/fixtures/sample_*.csv`.
- **Macro chỉ tự động (yfinance/World Bank):** extra `auto`, dùng `risk-eod-ingest --macro-auto` (xem `risk-eod-ingest --help`).

Không có cache panel trong `data/cache/`, backend thường trả **503 / “panel not loaded”** trên các route dashboard.

---

## URL sau khi chạy

| Môi trường | Dashboard | API tài liệu |
|------------|-----------|----------------|
| Docker / `make dev` | `http://localhost:8000/dashboard` | `http://localhost:8000/docs` |
| `make dev-frontend` | URL **Network** do Vite in (cổng **5173**) + path base | Gọi qua proxy tới `:8000` |

---

## Truy cập từ máy khác (LAN / ngrok)

- **Cùng Wi‑Fi:** trên máy host lấy IP LAN (vd. `192.168.x.x`), máy khác mở `http://<IP-LAN>:8000/dashboard`. Backend Docker/`make dev` đã bind `0.0.0.0`.
- **Qua Internet:** dùng [ngrok](https://ngrok.com/) (hoặc Cloudflare Tunnel): `ngrok http 8000`, rồi mở URL `https://....` ngrok cấp + `/dashboard`.

---

## Lệnh thường dùng (Makefile)

```bash
make install        # Python [dev,auto] + frontend npm ci
make dev            # Uvicorn reload, host 0.0.0.0, port 8000
make dev-frontend   # Vite dev server
make build          # Build frontend vào frontend/dist
make test / make test-cov
make lint / make fmt
make docker-build   # docker compose build
make up / make down / make logs
make clean          # Xóa cache test / coverage local
```

---

## Tests & chất lượng code

```bash
make test
make test-cov
make lint
make fmt
```

---

## API & CLI (tham khảo)

- **API đầy đủ:** khi server chạy, mở Swagger tại `/docs`.
- **CLI chính:** `risk-fetch-universe`, `risk-eod-ingest`, `risk-train-model`, `risk-fetch-financials`, … (khai báo trong `pyproject.toml` → `[project.scripts]`).

Ví dụ `curl` nhanh:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/eod/run \
  -H "Content-Type: application/json" \
  -d '{"as_of": "2026-03-29"}'
```

---

## Cấu trúc thư mục

```
├── src/risk_dashboard/     # Backend Python package: API, modules, quant, agents, CLI
├── frontend/               # Frontend app riêng: React + Vite
├── tests/                  # Pytest test suite
├── scripts/                # Script vận hành / batch / smoke thủ công
├── docs/                   # Tài liệu dự án, research, proposal, notes
│   ├── project/            # Tài liệu quản lý dự án, ghi chú, worklog
│   └── research/word/      # Tài liệu Word (.docx): đề cương, proposal, định hướng
├── notebooks/              # Notebook nghiên cứu / phân tích thử nghiệm
├── data/                   # Runtime data/cache/model/local DB; không xem là source code
├── Dockerfile
├── docker-compose.yml    # app + Redis
├── Makefile
├── pyproject.toml
└── .env.example
```

Chi tiết quy ước đặt file xem [docs/STRUCTURE.md](docs/STRUCTURE.md).

---

## Xử lý lỗi thường gặp

| Hiện tượng | Hướng xử lý |
|------------|-------------|
| `Panel not loaded` / `503` | Chạy `risk-fetch-universe` (hoặc ingest khác) để có dữ liệu trong `data/cache/`, restart backend |
| `OPENAI_API_KEY not set` | Điền vào `.env` nếu cần chat LLM |
| `port 8000 already in use` | `lsof -i :8000` (macOS/Linux) rồi dừng process, hoặc đổi port uvicorn/Docker |
| Docker không lên | Bật Docker Desktop; `docker compose logs app` |
| Frontend trắng | Với chỉ backend: cần `make build` hoặc image Docker đã build frontend |
| `ModuleNotFoundError` | `pip install -e ".[dev,auto]"` trong đúng venv |
| `vnstock` / mạng lỗi | Thử lại sau; hoặc dùng CSV + `risk-eod-ingest` |

---

## Đẩy code lên Git (gợi ý)

1. **Không** commit `.env`, `node_modules/`, `data/cache/`, file model `.pkl` nhạy cảm (xem `.gitignore`).
2. Đảm bảo `.env.example` chỉ chứa **placeholder**, không dán key thật.
3. Tạo repo trên GitHub/GitLab → `git remote add origin <URL>` → `git push -u origin main` (hoặc nhánh bạn dùng).

Người khác clone về chỉ cần làm theo [Cách 1](#cách-1--docker-khuyến-nghị) hoặc [Cách 2](#cách-2--chạy-trên-máy-python--node) ở trên.

---

## Learn Hub — file media local (tùy chọn)

Đặt file thử vào:

- `data/learning_assets/videos/`, `audios/`, `books/`, `images/`

URL phục vụ tĩnh (khi backend chạy), ví dụ: `/learning-assets/videos/<tên-file>.mp4`. Chi tiết cấu trúc thư mục xem comment trong repo / `.gitignore` (`learning_assets`).
