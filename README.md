# Risk Dashboard (pipeline)

Python package: `risk_dashboard` — luồng EOD: dữ liệu → định lượng (VAR/XGBoost/SHAP) → narrative có reviewer → API.

## Cài đặt

```bash
cd "/Users/mac/Documents/Dự án Agent Tài chính"
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Mặc định mô hình rủi ro dùng `sklearn.ensemble.GradientBoostingClassifier` (ổn định, không cần OpenMP như XGBoost). Tuỳ chọn: `pip install -e ".[xgboost]"` nếu đã cài `libomp` (macOS) và muốn thay backend sau này.

## Chạy test

```bash
pytest
```

## Chạy API (dev)

```bash
uvicorn risk_dashboard.api.main:app --reload --app-dir src
```

## Chạy UI React (dev)

UI dashboard đã được tách sang React tại `frontend/`.

```bash
cd frontend
npm install
npm run dev
```

Mặc định Vite chạy ở `http://localhost:5173` và đã proxy các API sang backend FastAPI ở `http://127.0.0.1:8000`.

## Build UI React để FastAPI phục vụ trực tiếp

```bash
cd frontend
npm run build
```

Sau khi build, route `GET /dashboard` sẽ ưu tiên trả về `frontend/dist/index.html`. Nếu chưa build frontend, API vẫn fallback về `src/risk_dashboard/api/dashboard.html`.

## Bước 1 — Ingest dữ liệu (thị trường + vĩ mô)

**Thị trường**

- **CSV**: cột thời gian (`tradingDate` / `date` / `time`) + `close` + `volume` (xem `tests/fixtures/sample_market.csv`).
- **vnstock** (tuỳ chọn): `pip install -e ".[vnstock]"`, sau đó `--market vnstock` (cần mạng, phụ thuộc API nguồn).

**Vĩ mô (tháng)**

- **Thủ công (CSV)**: `period_end`, `usd_vnd_rate`, `usd_vnd_1m_change_pct`, `sbv_interest_rate_pct`; tuỳ chọn `cpi_yoy_pct`, `fdi_disbursement_yoy_pct` (mẫu: `tests/fixtures/sample_macro.csv`) — phù hợp số liệu chính thức GSO/SBV.
- **Tự động (`AutoMacroSource` / `--macro-auto`)**: cài `pip install -e ".[auto]"` (có `yfinance`). Tỷ giá Yahoo (`USDVND=X`); CPI năm, lãi cho vay, **FDI YoY (proxy)** từ **World Bank** (`FP.CPI.TOTL.ZG`, `FR.INR.LEND`, `BX.KLT.DINV.CD.WD`) — **ước lượng**, không thay số GSO/SBV chính thức.
- **CSV “kiểu báo cáo” (`OfficialCsvMacroSource` / `--macro-official-csv`)**: tên cột tiếng Việt / alias (`cuoi_thang`, `ty_gia_usd`, `lai_suat_dieu_hanh`, …) — xem `read_official_macro_csv` và `tests/fixtures/sample_official_macro.csv`.

**Ngành (sector)**

- CSV: `month_end`, `sector_code`, `return_pct` — `load_sector_panel_csv`, `sector_winners_losers`. Gán `AgentState.sector_panel` để chat trả lời intent “nhóm ngành / lịch sử”.

**Universe crawl (dashboard + train raw)**

- CLI `risk-fetch-universe`: crawl `VNINDEX` + toàn bộ rổ `VN30` từ `vnstock`, lưu raw Parquet/CSV và sinh luôn một `training panel` market-level từ `VNINDEX` + macro.
- Dùng khi cần dữ liệu thị trường Việt Nam cho dashboard sau này, trong khi model hiện tại vẫn train trên panel market-level.

**Lưu trữ & job EOD**

- **SQLite registry**: `risk_dashboard.storage.IngestRegistry` — đăng ký đường dẫn Parquet sau ingest.
- **CLI** `risk-eod-job`: ingest + ghi registry (hoặc `--skip-ingest --parquet ...` để chỉ đăng ký file có sẵn).

**Chạy ingest → Parquet + manifest JSON**

```bash
# Vĩ mô từ CSV chuẩn cột
risk-eod-ingest --start 2024-01-01 --end 2024-12-31 \
  --market csv --market-csv path/to/market.csv \
  --macro-csv path/to/macro_monthly.csv \
  --output-dir ./data_outputs

# Vĩ mô tự động (cần mạng)
pip install -e ".[auto]"
risk-eod-ingest --start 2024-01-01 --end 2024-12-31 \
  --market csv --market-csv path/to/market.csv \
  --macro-auto --output-dir ./data_outputs

# Vĩ mô từ CSV xuất báo cáo (tên cột linh hoạt)
risk-eod-ingest ... --macro-official-csv path/to/macro_gso_style.csv

# Ingest + SQLite
risk-eod-job --start 2024-01-01 --end 2024-12-31 \
  --market csv --market-csv path/to/market.csv \
  --macro-csv path/to/macro.csv --output-dir ./data_outputs \
  --sqlite ./data/risk_dashboard.db

# Crawl VNINDEX + VN30 và sinh training panel
risk-fetch-universe --start 2015-01-01 --end 2026-03-29 \
  --macro auto --out ./data/cache
```

Trong code: `build_training_panel`, `AutoMacroSource`, `OfficialCsvMacroSource`, `CsvMacroSource`.
