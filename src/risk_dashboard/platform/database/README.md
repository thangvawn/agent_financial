# Database module

Transactional state for Northstar lives in **one SQLite file**, under `data/db/`.

## Path

| Priority | Source |
|----------|--------|
| 1 | `RISK_DASHBOARD_DB_PATH` (canonical) |
| 2 | `RISK_DASHBOARD_APP_STATE_DB` (compat) |
| 3 | `RISK_DASHBOARD_SQLITE` (compat pipeline) |
| 4 | `data/db/northstar.db` if present, else legacy `data/northstar.db` / `data/app_state.db`, else create `data/db/northstar.db` |

File caches (parquet, pkl, market JSON, uploads) stay under `data/` — only **metadata** belongs in SQLite.

## Layout

```text
data/db/
  northstar.db     # runtime (gitignored)
  README.md

platform/database/
  config.py          # get_db_path()
  connection.py      # connect_db / open_db
  migrate.py         # schema_migrations runner
  schema/baseline.sql
  app_state.py       # compat: open_app_state_db, reset, column patches
```

## Usage

```python
from risk_dashboard.platform.database import open_db, open_app_state_db, get_db_path

with open_db() as conn:
    conn.execute("SELECT 1")

# Existing repos keep working:
with open_app_state_db() as conn:
    ...
```

## Migrations

Tracked in `schema_migrations`. Current:

1. `001_baseline` — product + platform tables (from former monolithic SCHEMA)
2. `002_ingest_runs` — ingest registry (merged from former `risk_dashboard.db`)

Add new changes as `003_*.sql` / entries in `migrate.py` — do not edit applied migrations.

## Rebuild

```bash
export RISK_DASHBOARD_DB_PATH=/path/to/data/db/northstar.db
# First connect runs migrations.
```
