# SQLite (Northstar)

Một file transactional duy nhất:

| File | Vai trò |
|------|---------|
| `northstar.db` | App state + product tables + ingest registry |

Đường dẫn mặc định: `data/db/northstar.db`  
Override: `RISK_DASHBOARD_DB_PATH`

File cache (parquet, pkl, JSON market, uploads) nằm ngoài thư mục này — không phải database SQLite.
