# Database module — bước triển khai

**Mục tiêu:** một path DB transactional, một module quản lý connection + schema/migration.

## Bước

1. ✅ Path duy nhất `RISK_DASHBOARD_DB_PATH` (default `data/northstar.db`, compat `app_state.db`)
2. ✅ `platform/database/` — config, connection, migrate
3. ✅ Schema baseline + `schema_migrations` + ingest_runs trong cùng DB
4. ✅ Cắt `open_catalog_db` / registry path riêng → dùng DB chung
5. ✅ Docs + tests (`tests/test_database_module.py`)

## Không làm ngay

- Postgres / Redis
- Nhét parquet/pkl vào SQLite
- Xóa file `data/app_state.db` cũ (giữ làm fallback nếu chưa có northstar.db)
- Tách baseline.sql thành nhiều file domain (làm khi schema churn tăng)
