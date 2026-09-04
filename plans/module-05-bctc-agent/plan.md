# Module 05 — BCTC Agent (Financial Statement Agent)

> **Status:** Planning
> **Priority:** P1 (Wave V2)
> **Domain owner:** `modules/financials_product`
> **Dependencies:** Module 00 (Agentic Core), Module 01 (Identity/Trust), Module 02 (AI Runtime), Module 04 (Learn Agent — COMPLETED)
> **Source doc:** `docs/project/agentic-quantum/05_BCTC_AGENT_PLAN.md`

---

## Mục tiêu

BCTC Agent giúp user đọc báo cáo tài chính bằng evidence: resolve line item, giải thích công thức, so sánh kỳ, nhận diện biến động, tạo evidence memo và nêu câu hỏi cần kiểm tra tiếp. **Mọi con số phải đến từ typed tool và gắn report revision, period, currency, unit, source.**

Agent **không** đưa khuyến nghị mua/bán và **không** thay thế kiểm toán/chuyên gia tài chính.

---

## Hiện trạng codebase đã xác minh

| Thành phần | Trạng thái | File |
|---|---|---|
| Module shell | **EXISTS THIN** — có `api/public.py` (69.7K), `application/company_workspace.py`, `application/query_handler.py`, `infrastructure/delivery_repository.py`, `module.py` | `src/risk_dashboard/modules/financials_product/` |
| Domain layer | **KHÔNG TỒN TẠI** — chưa có `domain/`, `schemas/` | Cần tạo mới |
| Agent tools | **KHÔNG TỒN TẠI** — chưa có `agent_tools.py` | Cần tạo mới |
| Skills/Prompts | **KHÔNG TỒN TẠI** | Cần tạo mới |
| Data path | **LIVE REST** — `_load_dataset_or_503()` (`api/public.py:769`), `get_financial_dataset` (`data/financials.py`) | Reuse, không tạo loader mới |
| Ratio/formula | `_calculated_ratio()` (`api/public.py:929`), `_income_formulas()` (`api/public.py:1147`) — 7 formula hardcode | Wrap thành registry |
| Permission scopes | `("public:financials:read", "public:financials:write")` | Cần thêm `bctc:*` scopes |
| Existing tests | 5 test files (workspace, analysis, health, quality charts, telegram handler) | Giữ nguyên, thêm test mới |
| Frontend | `BctcAnalysisWorkspace.jsx`, `bctc-workspace.css`, `financialsApi.js` | Extend cho evidence UI |
| Migration | Additive via `platform/database/migrate.py` ordered `(migration_id, sql)` | Thêm migration mới |

---

## Phases (Dependency-Ordered)

| Phase | ID | Tên | Depends On | Deliverable |
|---|---|---|---|---|
| 1 | BCTC0 | Data Contract & Scopes | — | Schemas freeze + revision derivation + bctc:* scopes |
| 2 | BCTC1 | Read Tools (6 adapters) | BCTC0 | 6 tool adapters + ToolManifests |
| 3 | BCTC2 | Formula Registry | BCTC0 | Versioned formulas + governance |
| 4 | BCTC3 | Agent Skills (5 manifests) | BCTC1 | 5 skill manifests + prompt templates |
| 5 | BCTC4 | Numeric Reviewer | BCTC1 | Claim→tool mapping + unsupported-claim block |
| 6 | BCTC5 | Artifact/UI | BCTC3, BCTC4 | Evidence memo + source drawer + stale indicator |
| 7 | BCTC6 | Private Data Controls | BCTC0 | Upload ownership + retention + redaction |
| 8 | BCTC7 | Rollout/Economics | BCTC2-BCTC6 | Feature flags + cohort + metrics |
| 9 | BCTC8 | Eval & Gold Set | BCTC1 | Adversarial numeric suite + threshold config |

---

## Phase Details

→ See individual `phase-*.md` files for detailed implementation instructions.
