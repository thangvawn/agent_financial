# 05 — BCTC / Financial Statement Agent Plan

> Domain owner: `modules/financials_product`
> Agent consumer: `modules/ai_tutor` và embedded BCTC workspace panel
> Dependencies: Agentic Core (doc 00), AI Runtime (doc 02), Identity/Trust (doc 01)
> Roadmap liên quan: AT1, AT5, EA2
> Trạng thái: **EXTEND thin module** — compute BCTC live qua REST; domain layer, schemas và agent tools chưa tồn tại.

## 0. Reality note

| Vùng | Hiện trạng verified | Hành động |
|---|---|---|
| Module shell | **EXISTS THIN** dưới `src/risk_dashboard/modules/financials_product/`: `api/public.py` (69.7K), `application/company_workspace.py`, `application/query_handler.py`, `infrastructure/delivery_repository.py`, `module.py` — **KHÔNG có `domain/`, KHÔNG có `schemas/`** | Giữ module là domain owner; thêm **NEW** `domain/` + `schemas/` + `agent_tools.py`; bọc compute hiện hữu, không viết lại nghiệp vụ |
| Financial data path | **LIVE REST** trong `api/public.py`: `_load_dataset_or_503()` (`api/public.py:769`) bọc `get_financial_dataset` (`data/financials.py`, import tại `api/public.py:15`); dataset shape là `FinancialDataset`/`FinancialPeriodData` (`schemas/financials.py:11-65`) | `bctc.resolve_report`/`resolve_line_item` là adapter **NEW** trên live loader; không tạo loader song song |
| Ratio/formula | `_calculated_ratio()` (`api/public.py:929`) trả `{value, formula_id, expression, calculation_status, inputs}` — **đã gần đúng provenance shape**; `_income_formulas()` (`api/public.py:1147`) = 7 formula hardcode (`gross_profit`, `gross_margin`, `operating_margin`, `net_margin`, `yoy_growth`, `qoq_growth`, `cost_to_revenue_ratio`), `_formula_by_id()` (`:1159`) lookup — **không version/unit/applicability** | `bctc.calculate_ratio` bọc `_calculated_ratio`; BCTC2 nâng `_income_formulas` thành versioned registry (thêm `unit`, `applicability`, `limitations`, `version`) |
| Telegram mock | `application/query_handler.py`: `MOCK_BCTC_DATABASE` (`:34-88`, hardcode FPT/HPG/VNM) + `FinancialsTelegramQueryHandler.handle()` (`:91-124`, lệnh `/bctc <ticker>`) | **KHÔNG** phải data path — đây là demo Telegram. Agent tools đọc live REST loader; mock chỉ được thay bằng tool call ở BCTC3 |
| Private upload | `/financials/upload` (`api/public.py:315`) + `/uploads/{upload_id}/analyze` (`api/public.py:387`) đọc env `RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR` (default `data/financial_uploads`); **chưa bind account** → IDOR risk | BCTC6 thêm ownership/account-scope + retention; model không được dereference `upload_id` tùy ý |
| Analysis engine | `analyze_financial_dataset()` (`engines/quant/financial_analysis.py`, import tại `api/public.py:17`); LLM-facing helper `_build_financial_context()` (`api/public.py:1297`) | Reuse làm compute; wrap output thành typed evidence; **không** expose SQL/dataframe tool cho model |
| Explain surface | `_line_item_explanations()` (`api/public.py:1165`) + routes `/api/bctc/income-statement/{overview,table,trends,margins,formulas,explain-line-item,insights,questions,student-notes,instructor-review}` (`api/public.py:515-721`) | Đây là UI surface hiện hữu; agent tools tái dùng cùng nguồn giải thích, không fork nội dung |
| Persistence | Shared DB dùng ordered `(migration_id, sql)` + additive `CREATE TABLE IF NOT EXISTS` (`platform/database/migrate.py`) | Bảng memo/artifact mới dùng migration additive theo convention; không schema ad-hoc trong tool |
| Module registration | `ModuleDefinition(id="financials_product", permission_scopes=("public:financials:read", "public:financials:write"), …)` (`modules/financials_product/module.py:4-12`) | BCTC0 mở rộng `permission_scopes` cho các scope `bctc:*` ở §5; giữ nguyên router mount hiện tại |

## 1. Capability

BCTC Agent giúp user đọc báo cáo tài chính bằng evidence: resolve line item, giải thích công thức, so sánh kỳ, nhận diện biến động, tạo quality-of-earnings/research memo và nêu câu hỏi cần kiểm tra tiếp. Mọi con số phải đến từ typed tool và gắn report revision, period, currency, unit, source.

Agent không đưa khuyến nghị mua/bán và không thay thế kiểm toán/chuyên gia tài chính. `financials_product` tiếp tục sở hữu dữ liệu và compute; agent chỉ điều phối đọc-hiểu có kiểm chứng.

## 2. Evidence từ codebase và khoảng trống

Module đã có REST compute (`api/public.py`), company workspace (`application/company_workspace.py`) và dataset loader (`data/financials.py`). Đây là nền deterministic đủ để bọc thành read-only tools.

Khoảng trống chính:

- chưa có common provenance/numeric-claim schema (dù `_calculated_ratio` đã gần đúng shape);
- chưa pin active report revision trong agent context — `FinancialDataset` chỉ có `source` + `fetched_at`, **không có `revision_id`**;
- `_income_formulas` chưa có version/unit/applicability → chưa phải formula registry;
- private upload chưa có account binding/retention boundary (IDOR risk);
- chưa có artifact lifecycle cho evidence memo;
- `query_handler.py` là Telegram mock, không được coi là data path.

## 3. User workflows

| Workflow | Trigger | Agent output | Write boundary |
|---|---|---|---|
| Explain line item | selected row trong income statement | definition, composition, caveat, source refs | read-only |
| Compare periods | company + metrics + periods | normalized comparison + drivers | read-only |
| Ratio walkthrough | formula pick từ registry | formula, substitution, unit, result, limitation | read-only |
| Earnings-quality review | selected reports | evidence table, hypotheses, red flags | artifact proposal only |
| Research checklist | company/report | unresolved questions + required evidence | read-only |
| Cross-link to Learn | concept/ratio | lesson recommendation (doc 04 `learning.recommend_next`) | no progress write |

## 4. Required surface context

- company/ticker và canonical company ID;
- report ID, reporting period và **active revision**;
- statement type và line-item reference;
- currency, display unit và scaling;
- `fetched_at`/published timestamp, source/license;
- selected comparison periods;
- ownership/access cho private report (upload);
- locale/accounting-standard context nếu có.

Client có thể gửi resource references, nhưng server phải resolve và verify report/revision thật. `AuthPrincipal` được resolve server-side qua `ResolveSession.execute(*, session_id) -> tuple[Account, AccountSession]` (`modules/auth/application/services.py:163-190`).

### 4.1 File layout đích

```text
src/risk_dashboard/modules/financials_product/
├── agent_tools.py                          # NEW: six typed Agentic Core tool adapters (§5)
├── skills/                                 # NEW: versioned bctc.* manifests/prompts
│   ├── manifests.py
│   └── prompts/
├── schemas/                                # NEW (thư mục chưa tồn tại)
│   ├── agent_tools.py                      # NEW: §5.1 Pydantic v2 contracts
│   └── evidence.py                         # NEW: NumericClaim/EvidenceRow/BCTCEvidenceMemo
├── domain/                                 # NEW (thư mục chưa tồn tại)
│   ├── formula_registry.py                 # NEW: versioned formula entries (nâng từ _income_formulas)
│   ├── provenance.py                       # NEW: revision pinning + freshness policy
│   ├── numeric_policy.py                   # NEW: claim→tool-evidence mapping rule
│   └── ports.py                            # NEW: ReportReader / UploadOwnershipPort
├── application/
│   ├── company_workspace.py                # REUSE: workspace composition
│   ├── query_handler.py                    # REUSE Telegram only — MOCK, không phải data path
│   ├── report_resolver.py                  # NEW: active-revision resolver trên _load_dataset_or_503
│   └── memo_service.py                     # NEW: evidence memo lifecycle + staleness
├── infrastructure/
│   ├── delivery_repository.py              # REUSE: Telegram delivery dedupe
│   ├── sqlite_memo_repository.py           # NEW: memo artifact persistence (additive migration)
│   └── upload_ownership_repository.py      # NEW: account binding cho private upload
├── api/
│   └── public.py                           # EXTEND: giữ REST hiện hữu; không thêm SQL/dataframe endpoint
└── module.py                               # EXTEND: thêm bctc:* permission_scopes
```

## 5. Domain tools

| Tool | Input schema | Output schema | Required scope | Risk-class |
|---|---|---|---|---|
| `bctc.resolve_report` | `ResolveReportInput` | `ResolveReportOutput` | `bctc:report:read` | `read` |
| `bctc.resolve_line_item` | `ResolveLineItemInput` | `ResolveLineItemOutput` | `bctc:report:read` | `read` |
| `bctc.compare_periods` | `ComparePeriodsInput` | `ComparePeriodsOutput` | `bctc:report:read` | `read` |
| `bctc.calculate_ratio` | `CalculateRatioInput` | `CalculateRatioOutput` | `bctc:formula:read` | `read` |
| `bctc.trace_provenance` | `TraceProvenanceInput` | `TraceProvenanceOutput` | `bctc:report:read` | `read` |
| `bctc.build_evidence_table` | `BuildEvidenceTableInput` | `BuildEvidenceTableOutput` | `bctc:evidence:read` | `read` |

Toàn bộ release đầu là `read` — **không** có `confirmed_write` trong phạm vi doc này. Memo artifact được tạo qua Agentic Core artifact path (doc 00), không qua tool ghi trực tiếp.

**Không expose general SQL/dataframe tool cho model.** Private report (upload) chỉ resolve được khi `AuthPrincipal.account_id` khớp owner của `upload_id`; model không truyền principal.

### 5.1 Tool I/O schemas

Contracts đặt tại `src/risk_dashboard/modules/financials_product/schemas/agent_tools.py`, Pydantic v2. ID trong input là resource references, không phải authority.

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CalculationStatus = Literal["ok", "insufficient_data"]


class ProvenanceRef(BaseModel):
    """Mọi con số model được nhìn thấy phải kèm ref này."""
    report_id: str
    revision_id: str
    period: str
    source: str
    fetched_at: str          # ISO-8601 UTC, từ FinancialDataset.fetched_at
    statement: Literal["income_statement", "balance_sheet", "cash_flow"] | None = None
    line_item: str | None = None


class NumericValue(BaseModel):
    value: float | None = None
    unit: Literal["VND", "VND_bn", "pct", "x", "ratio"]
    scale: int = Field(default=1, ge=1)
    calculation_status: CalculationStatus = "ok"
    provenance: ProvenanceRef


class ResolveReportInput(BaseModel):
    schema_version: str = "1.0.0"
    ticker: str = Field(min_length=1, max_length=20)
    period: str | None = None          # None → active/latest
    refresh: bool = False


class ResolveReportOutput(BaseModel):
    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    ticker: str
    company_name: str | None = None
    exchange: str | None = None
    available_periods: tuple[str, ...]
    active_period: str
    currency: Literal["VND"] = "VND"
    source: str
    fetched_at: str
    freshness_days: int = Field(ge=0)
    is_private_upload: bool = False


class ResolveLineItemInput(BaseModel):
    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    period: str
    line_item: str                     # khớp field của FinancialPeriodData


class ResolveLineItemOutput(BaseModel):
    schema_version: str = "1.0.0"
    line_item: str
    label_vi: str
    amount: NumericValue
    definition: str
    composition: tuple[str, ...] = ()
    caveats: tuple[str, ...] = ()


class ComparePeriodsInput(BaseModel):
    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    line_item: str
    periods: tuple[str, ...] = Field(min_length=2, max_length=8)


class PeriodDelta(BaseModel):
    from_period: str
    to_period: str
    absolute: NumericValue
    pct_change: NumericValue
    formula_id: str
    expression: str


class ComparePeriodsOutput(BaseModel):
    schema_version: str = "1.0.0"
    line_item: str
    observations: tuple[NumericValue, ...]
    deltas: tuple[PeriodDelta, ...]
    limitations: tuple[str, ...] = ()


class CalculateRatioInput(BaseModel):
    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    period: str
    formula_id: str                    # phải tồn tại trong formula registry
    formula_version: str | None = None # None → approved latest


class CalculateRatioOutput(BaseModel):
    schema_version: str = "1.0.0"
    formula_id: str
    formula_version: str
    expression: str
    inputs: tuple[NumericValue, ...]
    result: NumericValue
    applicability: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class TraceProvenanceInput(BaseModel):
    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    claim_ref: str                     # id của NumericValue/claim trong turn


class TransformStep(BaseModel):
    step: str
    detail: str


class TraceProvenanceOutput(BaseModel):
    schema_version: str = "1.0.0"
    claim_ref: str
    citations: tuple[ProvenanceRef, ...]
    transformation_chain: tuple[TransformStep, ...]
    license_note: str | None = None
    freshness_days: int = Field(ge=0)


class BuildEvidenceTableInput(BaseModel):
    schema_version: str = "1.0.0"
    report_id: str
    revision_id: str
    claim_refs: tuple[str, ...] = Field(min_length=1, max_length=50)


class EvidenceRow(BaseModel):
    claim: str
    kind: Literal["fact", "calculation"]
    value: NumericValue
    citation: ProvenanceRef


class BuildEvidenceTableOutput(BaseModel):
    schema_version: str = "1.0.0"
    rows: tuple[EvidenceRow, ...]
    unsupported_claims: tuple[str, ...] = ()
```

Invariant: **không** `NumericValue` nào được rời tool mà thiếu `provenance`. `unsupported_claims` không rỗng ⇒ numeric reviewer (BCTC4) chặn response.

### 5.2 Real-dependency mapping

| Contract/tool | Live code hôm nay | WP |
|---|---|---|
| `bctc.resolve_report` | `_load_dataset_or_503(ticker, *, refresh=False) -> FinancialDataset` (`api/public.py:769`) → `get_financial_dataset` (import `api/public.py:15`); shape `FinancialDataset` (`schemas/financials.py:48-65`) | BCTC0–BCTC1 |
| `bctc.resolve_line_item` | Field set `FinancialPeriodData` (`schemas/financials.py:11-45`); giải thích từ `_line_item_explanations()` (`api/public.py:1165`) và route `/api/bctc/income-statement/explain-line-item` (`api/public.py:515-721`) | BCTC1 |
| `bctc.compare_periods` | `_income_formulas()` entries `yoy_growth`/`qoq_growth` (`api/public.py:1147`); trends route `/api/bctc/income-statement/trends` (`api/public.py:515-721`) | BCTC1 |
| `bctc.calculate_ratio` | `_calculated_ratio(numerator, denominator, formula_id, expression) -> dict` (`api/public.py:929`) — trả `value/formula_id/expression/calculation_status/inputs`, `"insufficient_data"` khi numerator `None` hoặc denominator ∈ `(None, 0)`; lookup `_formula_by_id()` (`api/public.py:1159`) | BCTC1–BCTC2 |
| Formula registry | `_income_formulas()` 7 entries (`api/public.py:1147`) — cần thêm `version`, `unit`, `applicability`, `limitations`, approval state | BCTC2 |
| `bctc.trace_provenance` | `FinancialDataset.source` + `fetched_at` (`schemas/financials.py:50-51`), `provider_notes` (`:55`), `raw_statements` (`:57`); analysis chain `analyze_financial_dataset()` (import `api/public.py:17`) | BCTC0–BCTC1 |
| `bctc.build_evidence_table` | LLM context builder `_build_financial_context(dataset)` (`api/public.py:1297`) — hiện trả dict tự do; phải thay bằng typed rows | BCTC1, BCTC4 |
| Identity/ownership | `ResolveSession.execute(*, session_id)` (`modules/auth/application/services.py:163-190`), raise `SessionInvalid` khi thiếu/inactive/expired | BCTC0, BCTC6 |
| Private upload boundary | `/financials/upload` (`api/public.py:315`), `analyze_uploaded_file(upload_id)` (`api/public.py:387`), env `RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR` default `data/financial_uploads` | BCTC6 |
| Scope registration | `ModuleDefinition(... permission_scopes=("public:financials:read", "public:financials:write"))` (`modules/financials_product/module.py:4-12`) | BCTC0 |
| Migration | `platform/database/migrate.py` ordered `(migration_id, sql)` + additive `CREATE TABLE IF NOT EXISTS` | BCTC5 |

Lưu ý phản-trực-giác: `application/query_handler.py` **không** nằm trong dependency chain của bất kỳ tool nào. `MOCK_BCTC_DATABASE` (`:34-88`) là dữ liệu hardcode cho Telegram demo; `FinancialReportSnapshot` (`:16-31`) **không** phải report contract của agent.

## 6. Skills và orchestration

Skill manifests đầu tiên:

- `bctc.explain_line_item.v1`;
- `bctc.compare_periods.v1`;
- `bctc.ratio_walkthrough.v1`;
- `bctc.earnings_quality_review.v1`;
- `bctc.research_checklist.v1`.

```text
guard + report ownership (ResolveSession → account_id)
  → pin report_id/revision_id/period/currency/unit
  → classify explain | compare | ratio | review | checklist
  → call read-only bctc.* tools
  → quant specialist handoff nếu cần (engines/quant)
  → numeric + evidence reviewer (BCTC4)
  → teaching response hoặc reviewed memo artifact
```

Nếu reviewer không map được một numeric claim về tool result, claim phải bị loại hoặc gắn rõ là hypothetical example. Router ưu tiên deterministic match theo UI intent (row click → `explain_line_item`, formula pick → `ratio_walkthrough`).

## 7. Artifact contract

`BCTCEvidenceMemo` tại `schemas/evidence.py`:

| Field | Type | Ghi chú |
|---|---|---|
| `schema_version` | `str = "1.0.0"` | |
| `memo_id` | `str` | opaque, account-bound |
| `subject` | `str` | company/ticker |
| `report_refs` | `tuple[ProvenanceRef, ...]` | mọi revision đã dùng |
| `scope` | `str` | user question + phạm vi |
| `evidence_rows` | `tuple[EvidenceRow, ...]` | từ `bctc.build_evidence_table` |
| `calculations` | `tuple[CalculateRatioOutput, ...]` | có unit + limitation |
| `interpretations` | `tuple[str, ...]` | **tách khỏi** facts |
| `unresolved_questions` | `tuple[str, ...]` | |
| `limitations` | `tuple[str, ...]` | gồm freshness |
| `reviewer_status` | `Literal["pending","approved","rejected"]` | |
| `is_stale` | `bool` | `True` khi active `revision_id` đổi |
| `expires_at` | `str` | ISO-8601 UTC |

Memo là snapshot có source refs; không thay thế report và phải báo stale khi active revision thay đổi. Vì `FinancialDataset` hiện **không có** `revision_id`, BCTC0 phải derive revision deterministic (ví dụ hash của `source` + `fetched_at` + period set) rồi freeze contract.

## 8. Work packages

| ID | Work package | Deliverable | Exit evidence |
|---|---|---|---|
| BCTC0 | Data contract | report/revision/period/unit/provenance schemas + revision derivation | fixture review + contract tests |
| BCTC1 | Read tools | resolve_report, resolve_line_item, compare_periods, calculate_ratio, trace_provenance, build_evidence_table | golden calculation tests |
| BCTC2 | Formula registry | versioned formulas, units, applicability, limitations | domain expert sign-off |
| BCTC3 | Agent skills | explain, compare, ratio, quality review, checklist | route/evidence eval |
| BCTC4 | Numeric reviewer | claim→tool mapping + unsupported-claim block | adversarial numeric suite |
| BCTC5 | Artifact/UI | evidence memo, source drawer, stale indicator | E2E + accessibility |
| BCTC6 | Private data controls | ownership, retention, redaction, no raw memory copy | security/privacy tests |
| BCTC7 | Rollout/economics | flags, cohort, cost/time-to-insight metrics | pilot gate |
| BCTC8 | Numeric reviewer threshold | grounded-rate target, rejection threshold | threshold config review + adversarial pass |
| BCTC9 | Formula registry governance | approval workflow, versioning, units/applicability per formula | domain expert sign-off ≥5 ratios |

### 8.0 Thứ tự bắt buộc (dependency-ordered)

- `BCTC0` freeze `ProvenanceRef`/`NumericValue`/revision derivation và scope `bctc:*`; block mọi tool khác.
- `BCTC1` bọc sáu read tools sau BCTC0; chỉ gọi `_load_dataset_or_503` (`api/public.py:769`) và `_calculated_ratio` (`:929`), không viết loader mới.
- `BCTC2` + `BCTC9` đi cùng nhau: registry không có governance thì không approve formula; `calculate_ratio` chỉ nhận `formula_id` đã approved.
- `BCTC3` cần BCTC1 + AI Runtime/Agentic Core (docs 02/00); **không** import provider SDK trực tiếp.
- `BCTC4` + `BCTC8` cần BCTC1 (typed evidence) trước khi set threshold; reviewer chạy trước mọi response.
- `BCTC5` cần BCTC3 + BCTC4; memo table dùng additive migration.
- `BCTC6` phải xong **trước** khi bất kỳ private upload path lộ ra agent — đây là IDOR blocker, không phải hardening về sau.
- `BCTC7` chỉ bắt đầu khi BCTC2–BCTC6 pass gate và threshold BCTC8 đã chốt.

### 8.1 Acceptance test + Definition of Done per WP

| WP | Acceptance test | Definition of Done |
|---|---|---|
| BCTC0 | Mọi root schema round-trip với `schema_version="1.0.0"`; `NumericValue` thiếu `provenance` fail validation; cùng dataset → cùng `revision_id`, `fetched_at` đổi → `revision_id` đổi; client-supplied account authority bị từ chối | Contracts freeze tại `schemas/agent_tools.py` + `schemas/evidence.py`; revision derivation deterministic có test; `bctc:*` scopes thêm vào `module.py:4-12` |
| BCTC1 | Sáu adapters chạy trên fake + live dataset; `calculate_ratio` với denominator `0`/`None` trả `calculation_status="insufficient_data"` (khớp `api/public.py:929`); mọi output number có `ProvenanceRef`; không tool nào nhận SQL/expression tự do | `agent_tools.py` đăng ký scoped signatures §5; zero duplicate compute logic — tools delegate về `_load_dataset_or_503`/`_calculated_ratio`; p95 theo §13 |
| BCTC2 | 7 formula hiện hữu migrate đủ `version`/`unit`/`applicability`/`limitations`; `formula_id` không tồn tại hoặc chưa approved bị reject; unapproved version không resolve được | `domain/formula_registry.py` là single source; `_income_formulas()` (`api/public.py:1147`) đọc từ registry thay vì hardcode; ≥5 ratio approved |
| BCTC3 | Năm skill pass fixtures; row-click route đúng `explain_line_item`; mọi numeric trong response trace về tool result; zero buy/sell phrasing trong adversarial prompt set | Versioned skill manifests; deterministic UI-intent routing; Telegram `/bctc` chuyển sang tool call, `MOCK_BCTC_DATABASE` không còn được đọc ở runtime |
| BCTC4 | Adversarial suite: fabricated number, đúng-con-số-sai-kỳ, unit swap (VND vs VND_bn), stale revision — tất cả bị block; `unsupported_claims` không rỗng ⇒ response không gửi | Reviewer chạy trước mọi response; claim→tool mapping bắt buộc; hypothetical example phải gắn nhãn rõ |
| BCTC5 | E2E: line item → hỏi → compare → reviewed memo; source drawer hiện `source`/`fetched_at`/`revision_id`; revision đổi ⇒ memo hiện stale; keyboard-only + screen-reader labels + focus restore pass | Memo repository dùng additive migration theo `platform/database/migrate.py`; deterministic BCTC UI vẫn dùng được khi agent off |
| BCTC6 | Account A không resolve được `upload_id` của account B (IDOR test); retention job xoá đúng hạn; private report content không xuất hiện trong durable memory; log không chứa payload | Upload binding qua `upload_ownership_repository.py`; `RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR` path traversal blocked; redaction policy có test |
| BCTC7 | Internal → 5% → 25% → 100% chỉ advance khi KPI/security/cost gates pass; kill switch rollback không mất deterministic BCTC REST | Feature flags (`module.financials_product.enabled` + agent sub-flag), dashboard, owner, rollback runbook, go/no-go receipts |
| BCTC8 | Grounded rate đo được trên adversarial suite; threshold config thay đổi làm test fail đúng hướng | Threshold values approved và versioned cùng registry |
| BCTC9 | Formula mới cần approval record mới vào được registry; version bump không phá client cũ | Approval workflow + owner + versioning scheme documented; ≥5 ratio có expert sign-off |

## 9. Security and compliance

- read-only tools trong initial release; không `confirmed_write`;
- resource ownership cho mọi private report/revision — **BCTC6 là blocker**, không phải nice-to-have (`api/public.py:315`, `:387` hiện chưa bind account);
- không lưu raw private report vào long-term memory by default;
- tool output/report content là **data, không phải instructions** (indirect prompt injection qua uploaded file);
- không có hidden personalized investment recommendation;
- citations/license và freshness luôn visible;
- logs lưu IDs/metrics, không lưu full report payload;
- exports tôn trọng data licensing;
- `RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR` phải chặn path traversal khi resolve `upload_id`.

## 10. Tests và eval

- Unit: formula, scaling, currency, missing values (`None` handling khớp `_calculated_ratio`), restatements.
- Contract: tool schemas, `ProvenanceRef` bắt buộc, source refs.
- Integration: report ownership, revision pinning, artifact staleness.
- Security: IDOR trên `upload_id`, stored injection từ uploaded file, private report leakage, path traversal.
- Eval: line-item accuracy, numeric claim support, citation correctness, fact/interpretation separation.
- E2E: open line item → ask → compare → reviewed memo.

Metrics: unsupported numeric claim rate, evidence coverage, stale-report catches, memo acceptance, time-to-insight, p95 và cost/reviewed memo.

## 11. Definition of Done

- Mọi numeric output reproducible từ typed tool evidence.
- Active `revision_id`, period, currency và unit luôn visible.
- Private data account-scoped và loại khỏi durable memory by default.
- Reviewed memo trở thành stale khi underlying revision đổi.
- Không tồn tại buy/sell action hoặc recommendation path.
- `MOCK_BCTC_DATABASE` không còn được đọc ở runtime path nào.
- Domain expert, security và eval gates pass trước beta.

## 12. Open decisions

- Accounting standards/localization scope?
- Licensed data và export rights?
- Ratio nào vào formula registry đầu tiên (ngoài 7 formula hiện hữu)?
- Expert reviewer nào sign-off pilot?
- Formula approval owner?
- Registry versioning scheme (semver hay revision tag)?
- Numeric reviewer threshold final values?
- Revision derivation: hash-based hay provider-supplied khi có provider hỗ trợ?

## 13. Validation checkpoint

- Entry criteria: formula registry ≥5 ratios approved by domain expert; numeric reviewer threshold set; BCTC6 ownership test pass.
- Exit criteria (quantitative):
  - 100% numeric claims map về tool evidence;
  - ratio calc p50 <200ms / p95 <500ms;
  - evidence memo p50 <3s / p95 <8s, cost ≤$0.03/memo;
  - unsupported claims blocked by reviewer;
  - zero cross-account private report access.
- Validation gate: maps to VP-AT5 trong master §14A.3.
