# Risk Dashboard

Hệ thống phân tích rủi ro định lượng cho thị trường chứng khoán Việt Nam: **dữ liệu → quant engine (XGBoost/GARCH/HMM/SHAP/VAR) → multi-agent LLM → FastAPI → React**.

Tài liệu này giúp người mới **clone repo và chạy được** (Docker hoặc máy local).

Tab **News → Social** và collector YouTube/Reddit tùy chọn: [cách chạy, phạm vi và giới hạn nguồn](docs/project/engineering/SOCIAL.md).

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
- [Video Learning Agent](#video-learning-agent)
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
Đặt `API_SECRET_KEY` cho API dùng chung; nếu cần nạp panel qua endpoint quản trị trong
môi trường local không bật API key, đặt thêm `ADMIN_SYSTEM_KEY`.

### 2. Build và chạy

```bash
docker compose build
docker compose up -d
docker compose logs -f app frontend
```

Đợi log không còn lỗi import / uvicorn báo **Application startup complete** và service `frontend` bắt đầu watch build. Sau lần build đầu tiên, sửa UI trong `frontend/src` sẽ tự build lại `frontend/dist`; chỉ cần refresh `http://localhost:8000/`, không cần `docker compose build` hay `docker compose up` lại.

Nếu build báo `ReadTimeoutError` khi tải gói từ `files.pythonhosted.org`, chạy lại
`docker compose build app` để tận dụng cache. Dockerfile dùng pip 26.2.2, timeout
120 giây, 10 lần thử kết nối và 10 lần tiếp tục tải dở. Mạng chậm hơn có thể tăng
các giới hạn này khi build:

```bash
docker compose build --build-arg PIP_TIMEOUT=300 --build-arg PIP_RETRIES=15 --build-arg PIP_RESUME_RETRIES=15 app
```

Không cần xóa cache hoặc dùng `--no-cache` cho lỗi tải gói. Thông báo có bản pip
mới không phải traceback gây dừng build. Xem [cấu hình timeout/retry của pip](https://pip.pypa.io/en/stable/cli/pip/)
và [cơ chế tiếp tục tải từ pip 25.2](https://pip.pypa.io/en/stable/news/#v25-2).

### 3. Nạp dữ liệu panel (bắt buộc để dashboard không 503)

Image Docker cài extra `auto` (macro tự động). DataHub market feed trong container
không phụ thuộc `vnstock`: nó ưu tiên `vnstock` nếu có và tự fallback sang HTTP
public của VCI để lấy listing/order book. Lệnh crawl panel lịch sử vẫn cần
**`vnstock`**, nên chạy **một lần trên máy host** (dùng chung thư mục `./data` với container):

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
| [http://localhost:8000/ready](http://localhost:8000/ready) | Readiness (503 khi panel/model chưa sẵn sàng) |

Tắt stack:

```bash
docker compose down
```

### Dữ liệu thị trường VN realtime

VN market feed chạy nền khi backend khởi động. Trong giờ giao dịch, quote board
được làm mới mặc định mỗi 12 giây; ngoài giờ, chu kỳ mặc định là 5 phút. Listing
được làm mới mỗi 6 giờ và các lịch sử phổ biến được prefetch theo chu kỳ riêng.

API `/api/v1/public/data-hub/vn-market/snapshot` dùng chiến lược
stale-while-revalidate: nếu cache vừa hết TTL, API trả snapshot thành công gần
nhất ngay lập tức và thực hiện refresh nền, tránh để request người dùng chờ
provider. Trong Docker, provider fallback là VCI HTTP; nếu máy đã cài vnstock,
vnstock được ưu tiên. Cache JSON được ghi theo cơ chế atomic replace nên process
đang đọc không thấy file nửa chừng.

Trang Global Terminal tự đọc snapshot mỗi 15 giây khi tab đang mở, tự backoff khi
API lỗi, dừng polling khi tab bị ẩn và đồng bộ ngay khi quay lại. Nút làm mới gửi
`refresh=true` để yêu cầu một refresh nền không khóa request. API trả thêm
`last_success_at`, `age_seconds`, `freshness`, `market_session` và
`refresh_interval_seconds` để giao diện không gắn nhãn live cho cache cũ.

Có thể điều chỉnh bằng các biến `VN_MARKET_INTERVAL_FAST_SEC`,
`VN_MARKET_INTERVAL_SLOW_SEC`, `VN_MARKET_UNIVERSE_INTERVAL_SEC`,
`VN_MARKET_PREFETCH_INTERVAL_SEC` và `GLOBAL_MARKET_INTERVAL_SEC` trong `.env`.
Cross-asset trên Global Terminal (vàng, dầu, chỉ số và FX) dùng quote intraday
5 phút từ Yahoo Finance khi provider có dữ liệu; crypto dùng spot 24 giờ từ
CoinGecko. `GLOBAL_MARKET_INTERVAL_SEC` mặc định là 60 giây và
`GLOBAL_MARKET_CACHE_TTL_SEC` mặc định là 75 giây. Mỗi item giữ
`updated_at`, `data_interval` và `source` riêng để UI phân biệt quote mới,
quote trễ và cache fallback. Đây là near-realtime theo độ trễ của provider
miễn phí, không phải tick-by-tick exchange feed; muốn tick realtime cần thay
provider bằng WebSocket/paid market-data feed.
Đặt
`ENABLE_VN_MARKET_SCHEDULER=0` khi chạy worker chỉ phục vụ test hoặc khi có
worker ingest riêng.

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
| `TELEGRAM_BOT_TOKEN` | Có nếu gửi News qua Telegram | Token do BotFather cấp; không commit vào Git |
| `TELEGRAM_CHAT_ID` | Có nếu gửi News qua Telegram | ID người nhận, group hoặc channel |
| `TELEGRAM_TRANSLATION_MODEL` | Không | Model dịch/tóm tắt tiếng Việt; mặc định `gpt-4o-mini` |
| `ENABLE_TELEGRAM_NEWS_SCHEDULER` | Không | `1` bật lịch gửi ngày/tuần/tháng |
| `LOG_LEVEL` | Không | `INFO`, `DEBUG`, … |

Chi tiết thêm: xem comment trong `.env.example`.

Kiểm tra Telegram sau khi cấu hình:

```bash
risk-telegram-news test
risk-telegram-news day --force
```

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

### BCTC Practice Lab

Tab **Thực hành chỉ số** mô phỏng đường đi có thể kiểm chứng từ khoản mục raw
đến trường dẫn xuất, insight và xếp hạng nhiều doanh nghiệp. API nhận mã đã có
trong cache/provider hoặc nhận trực tiếp một hay nhiều `FinancialDataset` để
chạy bài tập tái lập:

```bash
curl -X POST http://localhost:8000/financials/practice-lab \
  -H "Content-Type: application/json" \
  -d '{"tickers":["FPT","HPG"],"period_mode":"quarter","limit":12}'
```

Kết quả gồm `raw_inputs`, `calculated_fields` (công thức và dependencies),
`insights`, `categories`, `ranking`, `comparison.metrics` và `data_quality`.
Trường thiếu được giữ là `null`, loại khỏi điểm và hạ `confidence`; hệ thống
không tự bù số ước lượng. Điểm tổng hợp là heuristic giáo dục có trọng số
(sinh lời 20%, tăng trưởng 15%, hiệu quả 15%, thanh khoản 15%, đòn bẩy 15%,
chất lượng dòng tiền 20%). Khi có nhiều mã, hệ thống tự chọn kỳ chung mới
nhất; nếu không có kỳ chung, response trả `warnings` để người học biết cần
kiểm tra mốc thời gian. Kết quả không phải khuyến nghị đầu tư.

Ví dụ `curl` nhanh:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/eod/run \
  -H "Content-Type: application/json" \
  -d '{"as_of": "2026-03-29"}'
```

### Agent runs: input, bằng chứng và retry an toàn

Agent nhận nội dung công việc qua `task_input` (hoặc alias tương thích
`input_parameters`) và các `resource_refs`. Dữ liệu này được cách ly trước khi
gửi tới model; tool read-only được cấp grant theo scope và reviewer chỉ phát
hành claim có `evidence_refs` hợp lệ. Có thể dùng `idempotency_key` dài tối
thiểu 8 ký tự để retry mà không chạy graph/tool lần hai:

```bash
curl -X POST http://localhost:8000/api/v1/public/agentic/runs \
  -H "Authorization: Bearer <session_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "bctc.resolve_line_item",
    "surface": "bctc_workspace",
    "task_input": {"symbol": "VCB", "line_item": "revenue"},
    "idempotency_key": "vcb-revenue-2026-01"
  }'
```

Provider giả chỉ được dùng khi đặt `AGENTIC_ALLOW_FAKE_PROVIDER=1` trong môi
trường phát triển offline. Nếu thiếu `GEMINI_API_KEY` ở môi trường thật, run
được ghi nhận là failed thay vì âm thầm trả dữ liệu giả.

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
| `Panel not loaded` / `/ready` trả `503` | Chạy `risk-fetch-universe` (hoặc ingest khác) để có dữ liệu trong `data/cache/`, sau đó kiểm tra lại `/health` và `/ready` |
| `POST /admin/load-panel` trả `401/503` | Gửi `X-API-Key` nếu đã đặt `API_SECRET_KEY`, hoặc gửi `X-Admin-System-Key` sau khi đặt `ADMIN_SYSTEM_KEY` |
| `OPENAI_API_KEY not set` | Điền vào `.env` nếu cần chat LLM |
| `port 8000 already in use` | `lsof -i :8000` (macOS/Linux) rồi dừng process, hoặc đổi port uvicorn/Docker |
| Docker không lên | Bật Docker Desktop; `docker compose logs app` |
| Build lỗi `ReadTimeoutError` từ `files.pythonhosted.org` | Chạy lại `docker compose build app`; xem cấu hình timeout/retry ở phần Docker, giữ cache tải gói |
| Frontend trắng | Với chỉ backend: cần `make build` hoặc image Docker đã build frontend |
| `ModuleNotFoundError` | `pip install -e ".[dev,auto]"` trong đúng venv |
| `vnstock` / VCI / mạng lỗi | API vẫn trả snapshot cache kèm `freshness=stale`; kiểm tra `stale_reason`, thử lại sau, hoặc dùng CSV + `risk-eod-ingest` |

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

## Video Learning Agent

Trong màn hình trình phát bài học, tab **Video Agent** chuẩn bị transcript, tạo checkpoint trắc nghiệm và trả lời câu hỏi theo mốc video. Agent ưu tiên phụ đề YouTube công khai; nếu video không có phụ đề, hệ thống dùng transcript do Content Ops/người dạy cung cấp hoặc nội dung bài học đã xuất bản làm fallback. Transcript và ngân hàng câu hỏi được cache theo `lesson_id` + hash nội dung để không gọi lại provider không cần thiết.

Các endpoint công khai (đều nhận `session_id` hoặc Bearer session giống Learning API):

```text
POST /api/v1/public/learning/lessons/{lesson_id}/video-agent/prepare
GET  /api/v1/public/learning/lessons/{lesson_id}/video-agent
GET  /api/v1/public/learning/lessons/{lesson_id}/video-agent/checkpoint
POST /api/v1/public/learning/lessons/{lesson_id}/video-agent/checkpoint/grade
POST /api/v1/public/learning/lessons/{lesson_id}/video-agent/ask
```

Ví dụ chuẩn bị bằng transcript do giảng viên cung cấp:

```bash
curl -X POST http://localhost:8000/api/v1/public/learning/lessons/money-basics-101/video-agent/prepare \
  -H 'Content-Type: application/json' \
  -d '{"transcript_text":"Dòng tiền là phần còn lại sau chi tiêu. Quỹ dự phòng giúp giảm áp lực thanh khoản."}'
```

Checkpoint chỉ trả prompt và các lựa chọn; `correct_answer`/đáp án nội bộ không bao giờ được serialize trước khi chấm. Khi chấm, checkpoint được ràng buộc với tài khoản và hết hạn sau 15 phút. Câu trả lời ngoài transcript sẽ được từ chối có giải thích thay vì suy đoán. Vì phụ đề YouTube phụ thuộc quyền truy cập của video, nên video không có captions cần được nhập transcript qua Content Ops hoặc request `prepare`.
