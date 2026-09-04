# 06 — Simulation / Strategy Research Agent Plan

> Domain owner: registered facade `modules/simulation_lab`; current implementation `modules/pro_lab`
> Quant dependency: deterministic engines/tools
> Roadmap liên quan: AT1, AT6, EA3

## 0. Reality note

| Claim | Trạng thái thực tế (verified) | Hệ quả cho plan |
|---|---|---|
| `src/risk_dashboard/modules/simulation_lab/` | **Facade**, chỉ có `__init__.py` và `module.py`; module re-export `pro_lab` | Giữ facade tương thích; implementation tiếp tục ở `pro_lab` |
| `src/risk_dashboard/modules/pro_lab/` | **LIVE**: `api/{admin,ai,pro,public}.py`, `application/{backtest_studio,services}.py`, `domain/{entities,ports}.py`, `infrastructure/repositories/sqlite.py`, `providers/{contracts,registry}.py`, `schemas/{requests,responses,studio}.py`, `module.py` | Tái sử dụng assets thật; chỉ thêm contract/orchestration còn thiếu |
| Provider abstraction | `ProLabCommandDefinition`, `ProLabProviderDefinition`, `ProLabProviderResult` đã tồn tại (`providers/contracts.py:6-38`); `ProLabProviderRegistry` đăng ký và dispatch command deterministic (`providers/registry.py:49-414`) | Đây là **domain-command provider registry**, không phải model provider. Giữ nó và adapter vào tools; model call phải qua `platform/ai_runtime.LLMProvider` của doc 02 |
| AI call | `_invoke_openai()` dựng `ChatOpenAI` và gọi `.invoke()` trực tiếp (`api/ai.py:27-52`) | SIM2/SIM8 di dời qua shared AI Runtime; không đổi provider trước parity gate |
| “Swarm Committee” | **Một OpenAI prompt trả JSON role-play**, endpoint gọi `_invoke_openai()` đúng một lần (`api/ai.py:152-205`); không có graph state, handoff hay reviewer độc lập | Không được mô tả là multi-agent thật; SIM7 chỉ bật orchestration nhiều specialist nếu A/B chứng minh uplift |
| Tool đọc/chạy | Blueprint/run hiện có qua `SaveStrategyBlueprint`, `GetProLabRun`, `RunProLabCommand`, `RunBacktestLab` (`application/services.py:247-375,453-505,736-800`) và `RunBacktestStudio` (`application/backtest_studio.py:67-119`) | `get_strategy_spec`, `get_run`, `propose_run`/`execute_run` bọc luồng hiện hữu; proposal/confirmation là lớp mới |
| Tool còn thiếu | Không có contract riêng cho `validate_experiment`, `get_trade_summary` hoặc normalized `compare_runs` | SIM1 implement mới; không giả định backing hiện hữu |
| Persistence | Entity run đã có (`domain/entities.py:55-71`), SQLite save/get/list (`infrastructure/repositories/sqlite.py:267-361`) | SIM3/SIM5 thêm schema/migration additive qua `platform/database/migrate.py`; không thay repository bằng ORM |

## 1. Capability

Simulation Agent giúp user chuyển giả thuyết thành experiment có thể tái lập, đọc kết quả backtest, phát hiện lỗi phương pháp và đề xuất scenario tiếp theo. Agent phục vụ học tập/research trên paper environment; không đặt lệnh live và không cam kết lợi nhuận.

## 2. Current assets và vấn đề

`modules/simulation_lab` hiện re-export product module từ `modules/pro_lab` để giữ compatibility. `modules/pro_lab` có backtest studio, application services và AI endpoint. AI hiện tại mô phỏng “Swarm Committee” trong một model prompt/direct provider call; đó chưa phải multi-agent có state, typed handoff, reviewer và shared runtime.

Kế hoạch phải:

- extract deterministic backtest/context tools;
- migrate direct LLM call sang AI Runtime;
- thay role-play bằng bounded skills/specialists chỉ khi eval chứng minh giá trị;
- giữ reproducibility and no-trading boundary.

## 3. User workflows

| Workflow | Agent role | Output |
|---|---|---|
| Hypothesis builder | làm rõ thesis, universe, horizon, constraints | experiment spec draft |
| Strategy explainer | giải thích rule/parameter | formula/rule walkthrough |
| Backtest preflight | kiểm data window, leakage and assumptions | preflight checklist |
| Result critique | đọc metrics/trades/drawdown | evidence-based critique |
| Scenario compare | compare approved runs | normalized comparison |
| Next experiment | propose parameter/sensitivity test | ActionProposal to run simulation |

Simulation run có thể tốn chi phí nên execution cần entitlement/budget và explicit confirmation. Live order luôn forbidden.

## 4. Domain tools

| Tool | Input schema | Output schema | Required scope | Risk-class |
|---|---|---|---|---|
| `simulation.get_strategy_spec(blueprint_id: str)` | `StrategySpecQuery` | `StrategySpec` | `pro_lab:strategy:read` | `read` |
| `simulation.validate_experiment(manifest: ReproducibilityManifest)` | `ReproducibilityManifest` | `ExperimentValidation` | `pro_lab:experiment:read` | `read` |
| `simulation.get_run(run_id: str)` | `RunQuery` | `SimulationRunArtifact` | `pro_lab:run:read` | `read` |
| `simulation.get_trade_summary(run_id: str, detail: bool = False)` | `TradeSummaryQuery` | `TradeSummary` | `pro_lab:run:read`; detail cần `pro_lab:trade_detail:read` | `read` |
| `simulation.compare_runs(run_ids: tuple[str, ...])` | `CompareRunsQuery` | `RunComparison` | `pro_lab:run:read` trên mọi run | `read` |
| `simulation.propose_run(manifest: ReproducibilityManifest)` | `ReproducibilityManifest` | `ActionProposal` | `pro_lab:run:propose` | `proposal` |
| `simulation.execute_run(proposal_id: str, confirmation_token: str, idempotency_key: str)` | `ExecuteRunRequest` | `ActionReceipt` | `pro_lab:run:execute` | `confirmed_write` |
| bất kỳ broker/live-order path | Không được đăng ký | fail-closed error | không scope nào cấp được | `forbidden` |

`get_strategy_spec` bọc blueprint hiện hữu; `get_run` bọc `GetProLabRun.execute()` (`application/services.py:365-375`). `execute_run` cuối cùng gọi luồng deterministic `RunBacktestStudio.execute()` → `RunBacktestLab.execute()` (`application/backtest_studio.py:67-119`; `application/services.py:736-800`), nhưng chỉ sau confirmation. `validate_experiment`, trade aggregation và normalized run comparison là deliverable **NEW** của SIM1. Không expose shell, arbitrary Python, arbitrary code execution hoặc broker API cho model; live order luôn fail closed.

### 4.1 Real-dependency mapping

| Contract/tool | Live code today (file:line) | WP |
|---|---|---|
| strategy spec | `ProLabBlueprint` (`src/risk_dashboard/modules/pro_lab/domain/entities.py:11-24`); `SaveStrategyBlueprint.execute` (`src/risk_dashboard/modules/pro_lab/application/services.py:453-505`) | SIM1 adapter |
| `simulation.get_run` | `GetProLabRun.execute` ownership-check (`src/risk_dashboard/modules/pro_lab/application/services.py:365-375`); SQLite `get` (`src/risk_dashboard/modules/pro_lab/infrastructure/repositories/sqlite.py:308-318`) | SIM1 |
| command execution | `RunProLabCommand.execute` dispatch/persist/audit (`src/risk_dashboard/modules/pro_lab/application/services.py:247-362`) | SIM1/SIM5 |
| backtest execution | `RunBacktestStudio.execute` (`src/risk_dashboard/modules/pro_lab/application/backtest_studio.py:67-119`) → `RunBacktestLab.execute` (`src/risk_dashboard/modules/pro_lab/application/services.py:736-800`) | SIM1/SIM5 |
| run persistence | `ProLabExperimentRun` (`src/risk_dashboard/modules/pro_lab/domain/entities.py:55-71`); `SqliteProLabExperimentRunRepository` (`src/risk_dashboard/modules/pro_lab/infrastructure/repositories/sqlite.py:267-361`) | SIM3/SIM5 |
| domain provider contracts | definitions/results (`src/risk_dashboard/modules/pro_lab/providers/contracts.py:6-38`) | SIM1 reuse |
| domain provider registry | catalog, guardrails và deterministic dispatch (`src/risk_dashboard/modules/pro_lab/providers/registry.py:49-414`) | SIM1 adapter; không thay bằng `LLMProvider` |
| model provider | direct `ChatOpenAI(...).invoke(...)` (`src/risk_dashboard/modules/pro_lab/api/ai.py:27-52`) | SIM2/SIM8 migrate sang doc 02 `platform/ai_runtime.LLMProvider` |
| swarm behavior | một prompt + một `_invoke_openai` (`src/risk_dashboard/modules/pro_lab/api/ai.py:152-205`) | SIM0 baseline; SIM7 gated replacement |
| `validate_experiment`, trade summary, run comparison | chưa có contract/implementation tương ứng | SIM1 **NEW** |
| additive persistence migration | migration owner `src/risk_dashboard/platform/database/migrate.py` | SIM3/SIM5 |

## 5. Reproducibility contract

Mỗi run/artifact phải pin:

- strategy definition/version;
- dataset/source/version and time range;
- parameters, fees/slippage/benchmark;
- random seed if applicable;
- engine version and execution timestamp;
- warnings/data gaps;
- metrics calculation version.

Agent chỉ so sánh runs khi metric semantics compatible; nếu không phải nêu mismatch.

### 5.1 Contract schemas

Contracts mới dùng Pydantic v2 và sống tại `src/risk_dashboard/modules/pro_lab/schemas/simulation_agent.py`.

```python
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

class ReproducibilityManifest(BaseModel):
    schema_version: str = "1.0.0"
    strategy_id: str
    strategy_version: str
    dataset_source: str
    dataset_version: str
    data_start: str
    data_end: str
    parameters: dict[str, Any]
    commission_pct: float
    slippage_pct: float
    benchmark: str
    random_seed: int | None = None
    engine_version: str
    execution_timestamp: str
    metrics_calculation_version: str
    warnings: tuple[str, ...] = ()
    data_gaps: tuple[str, ...] = ()

class SimulationRunArtifact(BaseModel):
    schema_version: str = "1.0.0"
    artifact_id: str
    run_id: str
    account_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    manifest: ReproducibilityManifest
    metrics: dict[str, float | int | None]
    trade_summary: dict[str, Any]
    source_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    created_at: str
    completed_at: str | None = None

class ActionProposal(BaseModel):
    schema_version: str = "1.0.0"
    proposal_id: str
    run_id: str
    account_id: str
    operation: Literal["run_simulation"] = "run_simulation"
    manifest: ReproducibilityManifest
    estimated_cost: float
    risk_class: Literal["proposal"] = "proposal"
    requires_confirmation: bool = True
    policy_version: str
    created_at: str
    expires_at: str

class ExecuteRunRequest(BaseModel):
    schema_version: str = "1.0.0"
    proposal_id: str
    confirmation_token: str
    idempotency_key: str

class ActionReceipt(BaseModel):
    schema_version: str = "1.0.0"
    receipt_id: str
    proposal_id: str
    account_id: str
    status: Literal["executed", "failed", "rejected", "expired"]
    risk_class: Literal["confirmed_write"] = "confirmed_write"
    executed_at: str
    run_artifact_id: str | None = None
    error_code: str | None = None
```

Server resolve `account_id` và scopes; client không được dùng các field đó làm authority. Confirmation phải re-authenticate, re-check entitlement/budget/ownership/expiry, consume proposal một lần và dedupe bằng `idempotency_key`.

### 5.2 File layout target

```text
src/risk_dashboard/modules/simulation_lab/
├── __init__.py                              # REUSED facade
└── module.py                                # REUSED facade re-export pro_lab
src/risk_dashboard/modules/pro_lab/
├── api/
│   ├── ai.py                                # REUSED; SIM8 migrate direct model call
│   ├── admin.py                             # REUSED
│   ├── pro.py                               # REUSED
│   └── public.py                            # REUSED
├── application/
│   ├── backtest_studio.py                   # REUSED deterministic execution entry
│   ├── services.py                          # REUSED domain services
│   ├── simulation_tools.py                  # NEW typed tool adapters
│   └── simulation_actions.py                # NEW proposal/confirm/receipt service
├── domain/
│   ├── entities.py                          # REUSED; extend additive only
│   └── ports.py                             # REUSED; extend repository ports
├── infrastructure/repositories/
│   └── sqlite.py                            # REUSED; add scoped proposal/receipt persistence
├── providers/
│   ├── contracts.py                         # REUSED domain-command abstraction
│   └── registry.py                          # REUSED deterministic provider registry
├── schemas/
│   ├── requests.py                          # REUSED
│   ├── responses.py                         # REUSED
│   ├── studio.py                            # REUSED
│   └── simulation_agent.py                  # NEW §5.1 contracts
└── module.py                                # REUSED wiring; register new routes/services
```

Migrations additive thuộc `src/risk_dashboard/platform/database/migrate.py`. Shared model abstraction thuộc `src/risk_dashboard/platform/ai_runtime/` theo doc 02; không tạo model-provider abstraction thứ hai trong `pro_lab`.

## 6. Specialist design

MVP dùng một controller với skill packs:

- Research Designer;
- Quant/Risk Analyst;
- Evidence/Numeric Reviewer;
- Safety/Methodology Reviewer.

Default `single_specialist`; sequential Designer → Quant chỉ cho experiment design; parallel viewpoints tối đa hai nhánh ở controlled eval. Không cho agents tự sửa shared state hoặc gửi free-form chat cho nhau.

## 7. Work packages

| ID | Work package | Deliverable | Exit evidence |
|---|---|---|---|
| SIM0 | Inventory/parity | map current AI endpoint, prompts, backtest contracts | baseline fixtures |
| SIM1 | Deterministic tools | run/read/compare/preflight contracts | golden metrics tests |
| SIM2 | Runtime migration | direct provider call removed behind shared runtime | behavior/cost parity |
| SIM3 | Experiment artifact | versioned spec and reproducibility manifest | replay test |
| SIM4 | Critique skills | methodology/risk/evidence review | expert eval set |
| SIM5 | Confirmed run | proposal-preview-confirm-execute-receipt | auth/budget/idempotency tests |
| SIM6 | Embedded studio UX | critique, assumptions, compare, next experiment | E2E/accessibility |
| SIM7 | Multi-agent gate | sequential/parallel A/B against single specialist | uplift vs latency/cost review |
| SIM8 | Pro Lab → shared runtime migration | inventory existing behavior, migration steps, rollback plan | migration checklist reviewed, rollback tested |
| SIM9 | Behavior parity tests | existing Pro Lab output vs new runtime output comparison | parity tests pass (new runtime matches existing behavior) |

### 7.0 Thứ tự bắt buộc (dependency-ordered)

1. `SIM0` freeze baseline fixtures và inventory trước mọi migration.
2. `SIM1` freeze typed read/validation contracts; `SIM3` thêm manifest/artifact sau đó.
3. `SIM2` cần doc 02 `AIR0`/`AIR1`/`AIR2`; chưa cutover endpoint.
4. `SIM4` có thể phát triển trên fake runtime sau SIM1/SIM3.
5. `SIM5` cần SIM1 + SIM3 và persistence migration; `SIM6` chỉ tích hợp UX sau confirmed-run flow.
6. `SIM8` thực hiện migration call site, rồi `SIM9` chạy parity gate. **Không cutover trước khi SIM9 pass**; rollback về direct call path đã baseline nếu fail.
7. `SIM7` chạy cuối; multi-agent vẫn off nếu không đạt quality uplift trong latency/cost budget.

### 7.1 Acceptance test + Definition of Done per WP

| WP | Acceptance test | Definition of Done |
|---|---|---|
| SIM0 | Golden fixtures cover 3 AI endpoints và deterministic backtest path; ghi rõ swarm chỉ một model invocation | Inventory có symbol/file:line, request/output fixtures, latency/cost baseline và rollback baseline |
| SIM1 | Contract tests cho 7 tools; ownership deny cross-user; validation deterministic; incompatible metric version bị từ chối compare | Typed adapters bọc `services.py`/registry; NEW validator/trade-summary/compare implemented; 0 shell/Python/broker grant |
| SIM2 | `FakeProvider` chạy critique offline; Gemini adapter giữ required JSON/timeout/retry behavior | Module không import provider SDK; production cố định `gemini-3.5-flash`; migration chưa cutover trước behavior/eval parity |
| SIM3 | Manifest round-trip và replay cùng manifest cho kết quả deterministic trong tolerance; thiếu pin bắt buộc bị reject | `schema_version="1.0.0"`; mọi artifact pin đủ §5; migration additive qua `platform/database/migrate.py` |
| SIM4 | Eval set đo methodology issue recall/precision và numeric grounding; citation trỏ đúng run/metric | Skill prompts/version frozen; reviewer không sửa deterministic result; limitations luôn hiện diện |
| SIM5 | Expired/duplicate/cross-user confirmation bị reject; cùng idempotency key tạo tối đa một run và một receipt | Preview → explicit confirm → re-auth/re-check scope-budget → execute → immutable receipt; live order fail closed |
| SIM6 | E2E studio propose/confirm/run/critique/compare; keyboard + screen-reader path pass | UI hiển thị assumptions, data source/version, costs-not-applied warning và paper/research label |
| SIM7 | A/B single-specialist vs sequential/parallel trên cùng eval set; fail budget/uplift tự giữ mode off | Max hai nhánh, bounded steps/cost; không free-form shared state/handoff; decision log phê duyệt gate |
| SIM8 | Ba endpoint `api/ai.py` chạy qua shared runtime với feature-flag rollback; fault test timeout/malformed JSON | Xóa direct `ChatOpenAI` call khỏi call site sau gate; OpenAI/model/settings không silently đổi; rollback tested |
| SIM9 | Golden JSON/schema/safety/latency/cost comparison giữa baseline và runtime; drift nằm trong tolerance đã phê duyệt | Parity report pass là điều kiện cutover; fail thì rollback, không merge cutover |

## 8. Methodology/safety checks

- look-ahead bias and leakage;
- survivorship bias and selection bias;
- insufficient sample/window;
- overfitting and repeated parameter search;
- missing transaction costs/slippage;
- regime dependence and unstable metrics;
- risk-adjusted metrics and tail loss;
- benchmark mismatch;
- difference between simulated and actual execution.

Agent must label hypotheses and limitations, never present backtest as future guarantee.

## 9. Test và eval

- Unit: metric calculations, compatibility, cost estimate, run state.
- Contract: tools, proposal/receipt and version manifest.
- Integration: confirmed run, duplicate confirmation, budget failure, cancelled run.
- Security: arbitrary code/tool injection, entitlement bypass, broker endpoint denylist.
- Eval: methodology issue recall/precision, numeric grounding, experiment clarity.
- Performance: queue/run latency separated from model latency.

Metrics: reproducible run rate, issue-detection rate, experiment completion, invalid proposal rate, multi-agent uplift, cost/reviewed experiment.

## 10. Definition of Done

- Existing deterministic simulation remains source of truth.
- AI endpoint uses shared runtime and typed tools.
- Every critique pins run/data/engine versions and cited metrics.
- Execution requires exact preview, explicit confirmation and receipt.
- Live trading/broker/order actions fail closed.
- Multi-agent mode stays disabled unless it beats single-specialist quality within budget.

## 11. Open decisions

- Which strategy families and datasets are in pilot?
- Simulation cost/entitlement tiers?
- Reproducibility retention duration?
- Approved methodology rubric and domain reviewer?
- Migration cutover strategy (big-bang vs gradual)?
- Parity tolerance (mức chênh cho phép giữa Pro Lab và runtime mới)?
- Legacy Pro Lab deprecation timeline?

## 12. Validation checkpoint

- Entry criteria: migration checklist reviewed; parity tests written; reproducibility contract template approved.
- Exit criteria (quantitative):
  - zero direct provider calls ngoài shared runtime;
  - every critique pins run/data/engine versions;
  - parity tests pass (new runtime matches existing behavior);
  - run critique p50 <3s / p95 <8s, cost ≤$0.04/critique.
- Validation gate: maps to VP-AT6.
