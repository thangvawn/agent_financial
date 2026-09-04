# 00 — Agentic Core Plan

> Capability owner đích: `src/risk_dashboard/modules/agentic_core/`
> Roadmap liên quan: AT0, AT1, AT2, AT4, EA0
> Trạng thái: **100% greenfield** — module chưa tồn tại trong codebase (verified)

## 0. Reality note (đọc trước khi code)

| Claim | Trạng thái thực tế (verified) | Hệ quả cho plan |
|---|---|---|
| `modules/agentic_core/` | **Không tồn tại**. `src/risk_dashboard/schemas/` chỉ có `financials.py`, `snapshots.py` | Greenfield 100%. 8 contract (Envelope, AgentRun, AgentStep, ToolCall, AgentArtifact, ActionProposal, ActionReceipt, MemoryProposal) viết mới |
| `engines/agents/` (graph, router, narrative, reviewer) | **Demo deterministic, KHÔNG phải substrate**: router keyword-match (`engines/agents/router.py:13-21`), graph tuần tự cứng (`engines/agents/graph.py:35`), narrative template (`engines/agents/narrative.py:4-5`); `langgraph`=0 | Reference demo only. Agentic Core xây mới từ AT0; **không import** `engines/agents/`, chỉ đọc tham chiếu shape |
| `engines/quant/` | **Thật + LIVE** (14 module: `var_engine`, `xgb_engine`, `shap_explain`, `scenario`, `backtest`, `model_benchmark`, `eod_pipeline`…), 27 importer trong src | Tài sản thật. Bọc thành read-only tool, không viết lại |
| `src/risk_dashboard/quant/` (top-level) | Shim deprecated, **0 importer = dead** | Canonical = `engines/quant/`. Tool manifest chỉ trỏ `engines/quant/` |
| `FeatureFlagService.is_enabled()` | **Có thật** (`platform/feature_flags/service.py:6-12`), đọc env `RISK_FLAG__<FLAG>` | `@feature_flag()` decorator **chưa có** → AC7 implement decorator mỏng bọc `is_enabled()`, không thay cơ chế |
| Persistence | `platform/database/migrate.py` ordered `(migration_id, sql)` + `schema/baseline.sql`; repo dùng `open_app_state_db()` + raw SQL | AC1 thêm migration additive `CREATE TABLE IF NOT EXISTS`; không dựng ORM/Alembic |
| Test lớp agentic | `find src -name "test_*.py"`=0; chỉ `tests/test_agents.py` cover demo | Fake provider + fake tool harness là deliverable AC0/AC3 |

## 1. Capability

Agentic Core là product-level control plane cho mọi conversational và embedded agent. Module này quản lý run lifecycle, graph control, skill/tool selection, grants, handoff, artifacts, action proposals, memory policy và cross-surface budgets. Nó không sở hữu nội dung Learn, công thức BCTC, market data hay provider SDK.

Outcome: một workflow agent có thể được audit, replay, cancel và giới hạn quyền; domain teams tái sử dụng cùng primitives thay vì tự dựng agent loop.

## 2. Phạm vi và non-goals

Trong phạm vi:

- bounded supervisor graph;
- capability/skill manifest registry;
- typed Tool Registry và scoped Tool Grant;
- `AgentRun`, `AgentStep`, `ToolCall`, `Handoff`;
- `AgentArtifact`, `ActionProposal`, `ActionReceipt`;
- context builder và memory proposal policy;
- run budgets, feature flags, kill switch và shared telemetry.

Ngoài phạm vi:

- model adapter và prompt redaction thuộc AI Runtime (`platform/ai_runtime/`, doc 02);
- conversation UX/persona thuộc AI Tutor (doc 03);
- domain calculations/data writes thuộc domain module;
- shell, browser hoặc arbitrary MCP access;
- autonomous background swarm;
- order execution, admin publish hoặc hidden mutation.

## 3. Kiến trúc đích

```text
Request
  → Auth/Entitlement Guard        (modules/auth: ResolveSession → AuthPrincipal, doc 01)
  → Surface Context Resolver
  → Context + Memory Retrieval
  → Deterministic Router / Supervisor
  → Skill + Scoped Tool Grant
  → Specialist Node(s)            (platform/ai_runtime: LLMProvider, doc 02)
  → Evidence/Numeric/Safety Reviewer
  → Artifact or ActionProposal
  → Response / Explicit Confirmation
  → MemoryProposal + Telemetry
```

Execution mode mặc định là `direct` hoặc `single_specialist`. `sequential` chỉ dùng khi handoff tăng chất lượng; `parallel` tối đa hai nhánh và phải qua eval/cost gate.

### 3.1. Dependency thật (mapped vào import tồn tại, không aspirational)

| Agentic Core cần | Symbol/đích thực | Trạng thái |
|---|---|---|
| Identity | `risk_dashboard.modules.auth.application.services.ResolveSession` → `AuthPrincipal` | tồn tại (`services.py:163-187`), **extend** để trả `AuthPrincipal` (doc 01) |
| Model call | `risk_dashboard.platform.ai_runtime.provider.LLMProvider` | greenfield — AIR0/AIR1 (doc 02) xong trước AC3 |
| Feature flag | `risk_dashboard.platform.feature_flags.service.FeatureFlagService.is_enabled` | tồn tại (`service.py:6-12`) |
| DB | `risk_dashboard.platform.database.open_app_state_db`; migration ở `platform/database/migrate.py` | tồn tại |
| Domain tool (read-only) | `risk_dashboard.engines.quant.*` (canonical) | tồn tại — chỉ bọc |
| App wiring | `risk_dashboard.app.registry.module_definition.ModuleDefinition` + đăng ký `app/registry/registry.py::get_registered_modules()` | tồn tại — pattern ở `modules/pro_lab/module.py` |

Thứ tự bắt buộc: `AIR0+AIR1` (doc 02) và `ID1` (doc 01) merge **trước** `AC3`. AC0/AC1/AC2 song song được.

## 4. Cấu trúc package đề xuất

```text
modules/agentic_core/
├── api/
│   ├── runs.py
│   ├── artifacts.py
│   ├── actions.py
│   └── memory.py
├── application/
│   ├── run_service.py
│   ├── graph.py
│   ├── context_builder.py
│   ├── skill_router.py
│   ├── tool_grants.py
│   ├── artifact_service.py
│   ├── action_service.py
│   └── memory_service.py
├── domain/
│   ├── runs.py
│   ├── tools.py
│   ├── skills.py
│   ├── artifacts.py
│   ├── actions.py
│   ├── memory.py
│   ├── policies.py
│   └── ports.py
├── infrastructure/
│   ├── sqlite_runs.py
│   ├── sqlite_memory.py
│   └── skill_manifest_loader.py
└── schemas/
```

## 5. Core contracts

Contracts là Pydantic models sống tại `src/risk_dashboard/modules/agentic_core/schemas/` (style: `from __future__ import annotations`, `pydantic.BaseModel`/`Field`, giống `modules/auth/schemas/auth.py` và `schemas/financials.py`). Mỗi root contract mang `schema_version` để version hóa; AC0 freeze các schema này trước khi bất kỳ node nào được code.

### 5.1. Trusted execution envelope

`envelope.py`:

```python
class ResourceRef(BaseModel):
    kind: str                       # "report" | "run" | "artifact" | "simulation"
    resource_id: str
    module: str                     # slug của owning module

class ExecutionBudget(BaseModel):
    max_steps: int = 8
    max_tool_calls: int = 16
    max_tokens: int = 120_000
    max_wall_seconds: float = 60.0
    max_cost_usd: float = 0.50

class TrustedExecutionEnvelope(BaseModel):
    schema_version: str = "1.0.0"
    run_id: str
    correlation_id: str
    idempotency_key: str
    account_id: str                 # server-resolved từ AuthPrincipal (doc 01), KHÔNG nhận từ client
    scopes: tuple[str, ...]         # entitlements resolve server-side, format {tier}:{module}:{action}
    surface: str                    # "ai_tutor" | "pro_lab" | "bctc" | "news" | "market"
    resource_refs: tuple[ResourceRef, ...] = ()
    locale: str = "vi-VN"
    allowed_capabilities: tuple[str, ...]   # derived server-side từ scopes, KHÔNG từ client
    budget: ExecutionBudget
    policy_version: str
    model_policy_version: str
    skill_version: str | None = None
    consent: ConsentSnapshot        # từ doc 01 (memory/analytics/policy version)
    memory_mode: str = "ephemeral"  # "off" | "ephemeral" | "durable"
    created_at: str                 # ISO-8601 UTC
```

Invariant: client không được truyền `account_id`, `scopes`, memory namespace hoặc `allowed_capabilities` như authority; runtime dựng envelope từ `AuthPrincipal` (doc 01) rồi mới vào graph.

### 5.2. Artifact/action contract

`artifact.py` + `action.py`:

```python
class AgentArtifact(BaseModel):
    schema_version: str = "1.0.0"
    artifact_id: str
    artifact_type: str              # "analysis" | "chart_spec" | "lesson" | "backtest_report"
    domain: str                     # "finance" | "learning"
    account_id: str
    authoring_run_id: str
    source_refs: tuple[ResourceRef, ...] = ()
    claims: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    review_status: str = "draft"    # draft | reviewed | accepted | exported | expired
    version: int = 1
    created_at: str
    expires_at: str | None = None

class ActionProposal(BaseModel):
    schema_version: str = "1.0.0"
    proposal_id: str
    run_id: str
    account_id: str
    operation: str                  # "export_report" | "save_preference" | "run_simulation"
    target: ResourceRef
    payload_preview: dict[str, Any] # exact payload render cho user confirm
    risk_class: str                 # read | proposal | confirmed_write | forbidden
    requires_confirmation: bool = True
    policy_version: str
    created_at: str
    expires_at: str                 # short TTL, expired proposal bị từ chối

class ActionReceipt(BaseModel):     # immutable, append-only
    schema_version: str = "1.0.0"
    receipt_id: str
    proposal_id: str
    account_id: str
    status: str                     # executed | failed | rejected | expired
    executed_at: str
    result_ref: ResourceRef | None = None
    error_code: str | None = None
```

Khi confirm một `ActionProposal`: server phải re-authenticate, re-check ownership/entitlement trên `target`, kiểm tra proposal chưa expire/chưa dùng, rồi tạo immutable `ActionReceipt`. `forbidden` risk_class không bao giờ tạo proposal.

### 5.3. Memory contract

`memory.py` — LLM chỉ trả `MemoryProposal`, không bao giờ ghi trực tiếp:

```python
class MemoryProposal(BaseModel):
    schema_version: str = "1.0.0"
    proposal_id: str
    run_id: str
    account_id: str
    memory_type: str                # "preference" | "goal" | "plan" | "mastery" | "misconception"
    content: str
    provenance: str                 # "user_stated" | "user_approved_plan" | "deterministic_checkpoint"
    confidence: float = 1.0
    sensitivity: str = "normal"     # normal | sensitive
    ttl_days: int | None = None     # theo retention contract AC8
    created_at: str
```

`MemoryGovernor` (application layer) chấp nhận durable write chỉ khi `provenance` là một trong:

- `user_stated` — preference/goal user nói rõ;
- `user_approved_plan` — plan user đã chấp thuận;
- `deterministic_checkpoint` — mastery/misconception được checkpoint xác nhận (không phải LLM tự suy).

Cấm lưu: raw chain-of-thought, token, raw tool payload, private report nguyên bản, inferred sensitive finance state và buy/sell intent.

## 6. Work packages

| ID | Work package | Deliverable | Exit evidence |
|---|---|---|---|
| AC0 | Contracts freeze | Envelope, run, tool, claim, artifact, action, memory schemas | ADR + schema tests |
| AC1 | Persistence | Additive migrations and repositories | ownership/idempotency tests |
| AC2 | Registry/grants | Versioned manifests, risk classes, scoped grants | forbidden-tool suite |
| AC3 | Graph shell | Guard/router/tool/reviewer/recovery nodes with fakes | deterministic replay tests |
| AC4 | Context/memory | Budgeted context builder, proposal/write policy, user controls | poisoning/deletion tests |
| AC5 | Artifact/action | artifact review, preview-confirm-execute-receipt flow | stale/duplicate confirmation tests |
| AC6 | Operations | trace, budgets, flags, kill switch, run inspector | failure drill and dashboards |
| AC7 | Feature flag infra | Sub-feature flag decorator `@feature_flag()`, registry, audit, ≤30s refresh | flag toggle + graceful fallback tests |
| AC8 | Memory retention contract | TTL policy per memory type, deletion propagation SLA | TTL expiry + cascade deletion tests |
| AC9 | Threat model decomposition | ≥15 attack vectors với controls, reviewed by security owner | threat model doc + control mapping |

### 6.0. Thứ tự bắt buộc (dependency-ordered)

- `AC0` (contracts freeze) block tất cả — không code node nào trước khi schema `1.0.0` freeze.
- `AC1` + `AC2` song song được sau khi AC0 draft xong.
- `AC3` (graph shell) cần **`AIR0`+`AIR1`** (doc 02, fake provider) **và `ID1`** (doc 01, `AuthPrincipal`) merge trước.
- `AC4` → `AC5` → `AC6` tuần tự (context/memory → artifact/action → operations).
- `AC7`/`AC8`/`AC9` cross-cut, chạy sau AC3 (cần graph + envelope để có bề mặt test).

### 6.1. Acceptance test + Definition of Done per WP

| WP | Acceptance test | Definition of Done |
|---|---|---|
| AC0 | `TrustedExecutionEnvelope` round-trip serialize/deserialize; envelope **từ chối** client truyền `account_id`/`scopes`/`allowed_capabilities`; mọi root contract có `schema_version` | ADR contracts + toàn bộ schema `schema_version="1.0.0"` freeze tại `src/risk_dashboard/modules/agentic_core/schemas/` |
| AC1 | ownership scoping: query account A không đọc được row account B; duplicate `idempotency_key` → 1 side effect | migration additive `CREATE TABLE IF NOT EXISTS` qua `platform/database/migrate.py` + `schema/baseline.sql`; repo dùng `open_app_state_db()` |
| AC2 | forbidden-tool suite: tool `risk_class="forbidden"` không bao giờ resolve grant; grant scoped 1-run, expiry ngắn | manifest versioned + risk-class enum (`read\|proposal\|confirmed_write\|forbidden`); grant one-run/operation/resource-scoped |
| AC3 | deterministic replay với `FakeProvider` (doc 02); **0 import provider SDK** trong module; guard/router/tool/reviewer/recovery node chạy offline | graph shell replayable; max depth/fan-out/timeout/cancel enforce |
| AC4 | poisoning test: stored prompt injection coi là untrusted data, không escalate; deletion propagate qua view/index | context builder có budget; `MemoryGovernor` chỉ nhận provenance whitelisted |
| AC5 | stale/duplicate confirmation: proposal expired bị từ chối; confirm 2 lần → 1 `ActionReceipt` | preview → confirm (re-auth + re-check ownership) → execute → immutable receipt; `forbidden` không tạo proposal |
| AC6 | failure drill: provider timeout/partial tool failure → recovery; kill switch dừng run | trace + budget enforcement + run inspector + dashboards |
| AC7 | `@feature_flag("agentic.x")` off → graceful fallback (không crash); toggle ≤30s | thin decorator bọc `FeatureFlagService.is_enabled()` (`platform/feature_flags/service.py:6-12`), **không thay cơ chế** env `RISK_FLAG__*` |
| AC8 | TTL expiry: memory quá `ttl_days` bị purge; cascade deletion propagate qua memory/index/cache theo SLA | retention contract per `memory_type`; deletion SLA doc'd |
| AC9 | ≥15 attack vector có control mapping; reviewed by security owner | threat model doc + control-to-test mapping |

## 7. Data lifecycle

- Conversation store là product truth; graph checkpoint chỉ dùng resume.
- Run/step/tool events là append-only; summary/materialized view có thể rebuild.
- Memory item dùng event + current view, có provenance, confidence, sensitivity, TTL và superseding version.
- Artifact có lifecycle `draft → reviewed → accepted/exported/expired`.
- Action có lifecycle `proposed → confirmed/rejected/expired → executed/failed`.
- Deletion phải propagate qua memory/index/cache theo SLA; audit tối thiểu không được giữ payload nhạy cảm.

## 8. Security và reliability

- account/resource scoping trong mọi repository query;
- stored prompt injection được coi là untrusted data;
- schema-validation cả model output và tool output;
- max graph depth, max fan-out, timeout, cancellation và circuit breaker;
- no silent fallback làm mất citation/reviewer;
- tool grants one-run, operation/resource scoped và expiry ngắn;
- CSP-safe Markdown và output sanitization ở UI consumer.

## 9. Test và eval plan

- Unit: policies, state transitions, budget calculation, dedupe.
- Contract: every tool manifest and error envelope.
- Integration: auth → run → tool → reviewer → artifact.
- Security: IDOR, cross-user retrieval, prompt injection, grant escalation, replay.
- Resilience: provider timeout, partial tool failure, cancel, duplicate request.
- Eval: route accuracy, tool correctness, reviewer recall, memory precision.
- E2E: read-only run and confirmed safe action path.

## 10. SLO/KPI

- cross-user leakage: 0;
- duplicate side effect under idempotency: 0;
- forbidden action execution: 0;
- deterministic routing rate tăng dần theo known intents;
- run success, repair rate, tool error rate, p50/p95 latency;
- tokens/cost per successful outcome;
- artifact acceptance và action confirmation/rejection rate.

## 11. Definition of Done

- Fakes cho provider và tools chạy graph hoàn chỉnh không cần external API.
- Một domain read-only tool và verified Learning write hoặc test-only safe confirmed-write chạy end-to-end.
- Run có trace, cancellation, budget enforcement và replayable evidence.
- User memory có view/edit/forget/export; disabled mode không ghi durable memory.
- Security and eval gates đạt ngưỡng AT2/AT4 của master plan.
- Không domain business logic hoặc provider SDK bị đưa vào module.

## 12. Open decisions

Resolved (chốt trong wave này):

- `@feature_flag()` decorator: **thin decorator bọc `FeatureFlagService.is_enabled()`** (`platform/feature_flags/service.py:6-12`), **KHÔNG** tạo cơ chế mới. Decorator đọc cùng env `RISK_FLAG__*`, off → graceful fallback (không crash), refresh ≤30s. Registry + audit là phần thêm của AC7, không đổi hành vi `is_enabled()` hiện có.

Còn mở:

- LangGraph version + persistence adapter: cần lock trước AC3.
- Retention riêng cho run event, artifact, memory và receipt?
- Confirmation dùng one-time token hay signed challenge?
- Parallel mode budget theo entitlement nào?
- Flag refresh: polling vs push? (default polling ≤30s).
- Memory TTL values: cần product+compliance approve (xem master §14A.6).

## 13. Validation checkpoint

Entry criteria:

- architecture review done;
- ADR model/persistence/streaming locked;
- auth `ResolveSession` contract exist;
- threat model reviewed.

Exit criteria (quantitative):

- cross-user leakage = 0;
- duplicate side-effect under idempotency = 0;
- forbidden action execution = 0;
- fake provider + tools chạy full graph offline;
- ≥1 domain read-only tool + 1 verified write chạy E2E;
- run có trace/cancel/budget/replay;
- user memory view/edit/forget/export hoạt động.

Validation gate: maps to VP-AT2 trong master §14A.3.
