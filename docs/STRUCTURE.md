# Repository Structure

Mục tiêu của cấu trúc repo là tách rõ source code, frontend app, tài liệu, runtime data và thử nghiệm.

## Root

- `README.md`: hướng dẫn chạy nhanh và tổng quan.
- `pyproject.toml`: package backend, pytest, ruff.
- `Makefile`: lệnh vận hành chung.
- `Dockerfile`, `docker-compose.yml`: build và chạy stack.
- `.env.example`: template biến môi trường. Không commit `.env`.

## Backend

- `src/risk_dashboard/`: Python package chính.
- `src/risk_dashboard/modules/`: bounded modules theo domain sản phẩm.
- `src/risk_dashboard/platform/`: database, security, runtime, feature flags.
- `src/risk_dashboard/quant/`: mô hình định lượng, backtest, analytics.
- `src/risk_dashboard/data/`: connector, ingest, ETL.
- `src/risk_dashboard/cli/`: command line entrypoints.

## Frontend

- `frontend/`: React + Vite app riêng.
- `frontend/src/app/`: shell, route mapping, app-level orchestration.
- `frontend/src/pages/`: page-level UI.
- `frontend/src/modules/`: frontend API/service/hooks theo domain.
- `frontend/src/shared/`: shared components, assistant, navigation, analytics.

Không đưa frontend source vào `src/`; giữ `frontend/` riêng để Node tooling, lockfile và build output không trộn với backend package.

## Documentation

- `docs/project/`: worklog, notes, tài liệu quản lý dự án.
- `docs/research/word/`: tài liệu Word nghiên cứu, đề cương, proposal.
- `docs/architecture/`: dùng cho ADR/sơ đồ nếu cần.
- `docs/operations/`: dùng cho runbook nếu cần.

## Data And Runtime

- `data/`: dữ liệu runtime, cache, SQLite local, model artifacts, learning assets.
- `tests/fixtures/`: dữ liệu nhỏ, ổn định, dùng cho test.
- `notebooks/`: phân tích thử nghiệm, không được coi là production code.
- `output/`: artifact sinh ra khi kiểm thử thủ công hoặc browser automation.

Quy tắc: dữ liệu có thể tái tạo hoặc thay đổi theo runtime không nên commit, trừ fixture nhỏ phục vụ test.

## Scripts

- `scripts/`: script batch hoặc thao tác vận hành có thể chạy lại.
- `scripts/manual/`: smoke script/thử nghiệm thủ công, không phải pytest.

## Khi Thêm Module Mới

1. Backend domain vào `src/risk_dashboard/modules/<module_name>/`.
2. Frontend page vào `frontend/src/pages/<module-name>/`.
3. Frontend service/hook vào `frontend/src/modules/<module-name>/`.
4. Test backend vào `tests/test_<module_name>.py`.
5. Tài liệu module vào `docs/project/` hoặc `docs/architecture/` tùy mục đích.
