# 11 — Quantitative Finance Research Agent Plan

> Owner đích: `src/risk_dashboard/modules/quant_research/`
> Canonical live assets: `src/risk_dashboard/engines/quant/`
> Dependencies: Agentic Core (doc 00), Identity/Trust (doc 01), AI Runtime (doc 02)
> Status: module/agent greenfield; engines và REST wrapper LIVE

## 0. Fixed decision và reality note

Trong phạm vi này, **“Quantum” = quantitative finance (“quant”), KHÔNG quantum computing**.

- Runtime/dependency count cho `qiskit`, `cirq`, qubit, circuit, QUBO, QAOA/VQE, simulator, hardware = **0**.
- Quantum hardware, “quantum advantage” và quantum-computing roadmap explicitly **out of scope**; không được xuất hiện như future product expectation.
- `src/risk_dashboard/engines/quant/` là canonical, thật và LIVE; phải bọc read-only, không viết lại (`docs/project/agentic-quantum/00_AGENTIC_CORE_PLAN.md:12-13,71`).
- `src/risk_dashboard/quant/` là deprecated compatibility shim; package root re-export canonical package (`src/risk_dashboard/quant/__init__.py:1-2`). Plan này không quyết định xóa shim và không thêm importer mới vào shim.
- Live wrapper hiện hữu: `POST /eod/run` (`src/risk_dashboard/modules/quant_risk/api/public.py:26-33`), `POST /scenario/rerun` (`:36-60`), `GET /research/model-report` (`:63-70`). Nó gọi `run_eod_narrative`, `rerun_with_macro_override`, `build_model_research_report` (`:7-10`). Wrapper này là compatibility baseline, không phải Agentic Core tool substrate.
- `QuantEngineOutput` và nested models tồn tại tại `src/risk_dashboard/schemas/snapshots.py:30-99`, chưa versioned. Agent contract sẽ wrap/composition, không sửa engine schema trong MVP.
- Live module đã khai báo feature flag và scope `public:quant_risk:read` (`src/risk_dashboard/modules/quant_risk/module.py:2-9`). Module mới không thay router cũ trong compatibility window.

## 1. Capability và boundaries

Agent trả nghiên cứu định lượng có provenance: EOD market-risk analysis, macro scenario comparison, model/backtest report; sau đó giải thích mà không thay đổi số.

Không thuộc scope: trading/order/portfolio mutation, financial recommendation, arbitrary Python/shell/notebook, training model từ prompt, refactor engines, durable memory trước consent, quantum computing, xóa deprecated shim.

## 2. Dependency graph và thứ tự

```text
Doc 01 ID1 AuthPrincipal ───────────────┐
Doc 00 AC0 contracts + AC2 Tool Grants ─┼─> QF0 contracts
Doc 02 AIR0 + AIR1 fake provider ───────┘       │
engines/quant + snapshots schemas ──────────────┤
                                                v
                         QF1 adapters/tools -> QF2 service/reviewer
                                                    │
                         QF3 API/module <────────────┘
                                                    │
                         QF4 compatibility rollout <─┘
```

Hard blockers: QF0 starts after Agentic Core schema/grant freeze and ID1. Doc 00 requires AIR0+AIR1 and ID1 before orchestration (`00_AGENTIC_CORE_PLAN.md:63-75`). QF1 requires QF0; QF2 requires QF1 + fake provider; QF3 requires Agentic Core run/artifact API; QF4 requires QF1-QF3.

## 3. Explicit data flows

### 3.1 EOD

1. Client sends `QuantResearchRequestV1(as_of, question, run_id?)`; never sends account/scopes/tools.
2. Server resolves `AuthPrincipal`; Agentic Core creates trusted envelope server-side (`00_AGENTIC_CORE_PLAN.md:131-151`).
3. Grant authorizes `quant.eod_analysis.v1` with `quant_research:analysis:read`.
4. Adapter loads panel, calls canonical EOD path; engine transforms panel → features/model → `QuantEngineOutput` (score, regime, horizons, SHAP, VAR, backtest, provenance: `snapshots.py:76-99`).
5. Adapter emits versioned result with source refs/freshness. Reviewer exact-compares narrative metrics against typed payload.
6. Service returns versioned artifact; no write/action proposal.

### 3.2 Scenario

1. Request supplies `as_of` and one/two bounded overrides: USD/VND, SBV rate.
2. Grant authorizes `quant.scenario_compare.v1`.
3. Adapter calls `risk_dashboard.engines.quant.scenario.rerun_with_macro_override`, matching live invocation (`modules/quant_risk/api/public.py:43-49`).
4. Baseline and scenario use same date/panel; adapter emits deltas, assumptions, provenance.
5. Missing baseline, stale panel, NaN/Inf, mismatch => blocked artifact, never fabricated fallback.

### 3.3 Model report

1. Tool accepts only trusted `model_ref="latest"`, not filesystem paths.
2. Adapter maps it server-side to `data/models` and calls `build_model_research_report`, matching live route (`modules/quant_risk/api/public.py:63-70`).
3. Output excludes pickle/raw model/path data; evidence classified `available|partial|unavailable`.

## 4. Concrete versioned schemas

Paths: `src/risk_dashboard/modules/quant_research/schemas/{requests.py,tools.py,artifacts.py}`. Pydantic v2, `extra="forbid"`, root `schema_version="1.0.0"`.

```python
# requests.py
class QuantResearchRequestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    operation: Literal["eod_analysis", "scenario_compare", "model_report"]
    question: str = Field(min_length=1, max_length=4000)
    as_of: date | None = None
    run_id: str | None = Field(default=None, max_length=128)
    usd_vnd_rate: float | None = Field(default=None, gt=0, le=1_000_000)
    sbv_interest_rate_pct: float | None = Field(default=None, ge=-10, le=100)
```

Validators: EOD requires date; scenario requires date + >=1 override; model report rejects overrides. Client schema has no `account_id`, `scopes`, tool name, `model_dir`, path.

```python
# tools.py
class QuantSourceRefV1(BaseModel):
    source_id: str
    source_type: Literal["panel", "model", "benchmark", "engine"]
    version: str
    as_of: datetime | None = None

class QuantToolResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    tool_name: str
    status: Literal["ok", "partial", "unavailable"]
    payload: dict[str, Any]
    source_refs: tuple[QuantSourceRefV1, ...]
    warnings: tuple[str, ...] = ()
    generated_at: datetime
```

```python
# artifacts.py
class QuantResearchArtifactV1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    artifact_type: Literal["quant_research"] = "quant_research"
    run_id: str
    operation: Literal["eod_analysis", "scenario_compare", "model_report"]
    headline: str
    findings: tuple[str, ...]
    metrics: dict[str, float | int | str | None]
    source_refs: tuple[QuantSourceRefV1, ...]
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...]
    review_status: Literal["verified", "blocked"]
    generated_at: datetime
```

Compatibility: wrap existing `QuantEngineOutput`; no field change in `snapshots.py`. Additive fields => 1.1.0; breaking changes => parallel V2, dual-read/emit window, migrate consumers, then retire V1 separately.

## 5. Exact paths và real imports

```text
src/risk_dashboard/modules/quant_research/
├── __init__.py
├── module.py
├── api/public.py
├── application/{service.py,reviewer.py}
├── domain/ports.py
├── infrastructure/engine_adapter.py
├── tools/manifests.py
└── schemas/{requests.py,tools.py,artifacts.py}

tests/modules/quant_research/
├── test_schemas.py
├── test_engine_adapter.py
├── test_tool_grants.py
├── test_service.py
├── test_api.py
└── test_compatibility.py
```

Required imports:

```python
from risk_dashboard.engines.quant.eod_pipeline import run_quant_eod
from risk_dashboard.engines.quant.scenario import rerun_with_macro_override
from risk_dashboard.engines.quant.research_report import build_model_research_report
from risk_dashboard.platform.runtime.panel_store import PanelUnavailableError, get_panel
from risk_dashboard.schemas.snapshots import QuantEngineOutput
```

`run_quant_eod` and scenario are already live imports (`src/risk_dashboard/modules/guided_investing/application/services.py:54,57`). No new import may start with `risk_dashboard.quant`.

EOD boundary phải tách rõ hai lớp: existing compatibility route gọi `run_eod_narrative`, còn QF1 adapter gọi canonical `run_quant_eod`. QF1 không giả định hai function có cùng wrapper shape; parity fixture phải cùng panel/date, unwrap narrative về core `QuantEngineOutput`, rồi exact-compare core fields, provenance và typed error mapping. Existing wrapper giữ nguyên trong compatibility window.

## 6. Endpoints, tools, scopes, risk classes

| Endpoint | Contract | Required scope | Effect |
|---|---|---|---|
| `POST /api/quant-research/runs` | request V1 → run + artifact V1 | `quant_research:analysis:read` | read |
| `GET /api/quant-research/runs/{run_id}` | run/artifact status | same + ownership | read |

Principal is server-resolved per doc 01 (`01_IDENTITY_TRUST_FOUNDATION_PLAN.md:23-42,93-106`). Existing three router-local paths `/eod/run`, `/scenario/rerun`, `/research/model-report` stay unchanged. Effective mounted URLs phải lấy từ `quant_risk` module/registry prefix trong QF3 compatibility test; plan không hard-code prefix chưa verify.

```python
async def run_eod_analysis(*, as_of: date, run_id: str | None = None) -> QuantToolResultV1: ...
async def compare_macro_scenario(*, as_of: date, usd_vnd_rate: float | None = None, sbv_interest_rate_pct: float | None = None) -> QuantToolResultV1: ...
async def get_model_research_report(*, model_ref: Literal["latest"] = "latest") -> QuantToolResultV1: ...
```

| Manifest ID | Scope | Risk class | Limits |
|---|---|---|---|
| `quant.eod_analysis.v1` | `quant_research:analysis:read` | `read` | one panel read; deadline; no training flag |
| `quant.scenario_compare.v1` | `quant_research:scenario:read` | `read` | <=2 overrides; baseline required |
| `quant.model_report.v1` | `quant_research:model_report:read` | `read` | trusted `latest`; no arbitrary path/raw model |

Taxonomy follows doc 00 (`read|proposal|confirmed_write|forbidden`, `00_AGENTIC_CORE_PLAN.md:173-198`). Errors: `invalid_input`, `panel_unavailable`, `date_out_of_range`, `model_unavailable`, `engine_failure`, `deadline_exceeded`, `numeric_review_failed`. Retry only transient availability, max once within envelope deadline.

## 7. Ordered WPs, ownership, acceptance và DoD

| # | WP | Exclusive files | Blockers | Acceptance | DoD |
|---|---|---|---|---|---|
| 1 | QF0 contracts | `schemas/*`, `domain/ports.py`, `test_schemas.py` | AC0/AC2, ID1 | V1 round-trip; invalid combinations/authority/path rejected | schema 1.0.0 frozen; type/schema tests green |
| 2 | QF1 adapters/tools | `engine_adapter.py`, `manifests.py`, adapter/grant tests | QF0 | fixture equals direct engine; missing scope denied; 0 new shim imports | 3 tools, typed errors, bounded calls; no engine edits |
| 3 | QF2 service/reviewer | `service.py`, `reviewer.py`, `test_service.py` | QF1, AIR fake | mismatch/missing provenance/NaN blocks; deterministic fake-provider E2E | narrative cannot alter metrics; limitations mandatory; 0 QC/advice claims |
| 4 | QF3 API/module | `__init__.py`, `module.py`, `api/public.py`, app registry entry, `test_api.py` | QF2, run API | auth/scope/ownership denial; exact OpenAPI; stable 400/503 | feature flag, telemetry, no private payload logs |
| 5 | QF4 rollout | `test_compatibility.py`, rollout config only | QF3 | old wrapper vs adapter core output parity; canary gates | old routes unchanged; reversible flag; no shim deletion |

QF0 first. QF1 and QF2 fixture design may parallelize without shared files; QF2 code waits QF1. QF3 alone owns app registry. QF3→QF4 sequential.

## 8. Risks/failure modes

| Phase | Failure | L×I | Mitigation |
|---|---|---|---|
| QF0 | schema drifts from engine | M×H | composition + golden serialization |
| QF1 | deprecated import/calculation change | M×H | import allowlist; parity test; no engine edit |
| QF1 | missing/stale panel/date | H×M | typed failure + available range; no fallback fabrication |
| QF1 | training/cache side effect | M×H | approved read entrypoints; assert no model write; budgets |
| QF2 | LLM changes numbers/overstates evidence | M×H | exact numeric reviewer; blocked artifact; provenance/limitations |
| QF2 | output becomes advice | M×H | no action tools; policy/disclaimer/evals |
| QF3 | spoofed identity/scope | L×H | principal + grant + ownership; two-account IDOR matrix |
| QF3 | model/path/private data leaks | M×H | trusted ref, redaction, log assertions |
| QF4 | diverges from live wrapper | M×H | compatibility fixture, canary flag, retain fallback |
| All | “Quantum” interpreted as QC | M×H | product/tool names say Quantitative Finance; forbidden-claim eval |

All High-impact mitigations release-block. Sanitize exceptions; no raw stack trace to model/client.

## 9. Test matrix

- Unit: validators, scenario invariants, refs, reviewer exactness, NaN/Inf, errors, manifest metadata.
- Contract: JSON-schema snapshots; Agentic Core ToolCall/result; `QuantEngineOutput` adapter; version compatibility.
- Integration: deterministic panel/model, unavailable panel, date range, baseline/deltas, model-ref allowlist, path injection.
- Security: two accounts, scope deny, shell/training/trade/QC prompts, oversized question, logs/secrets.
- Resilience: missing/corrupt model metadata, timeout, engine exception, partial provenance, retry exhaustion.
- E2E: principal → envelope → grant → canonical engine → reviewer → artifact for all operations; old/new compatibility.
- Performance: p50/p95, deadline, concurrency, cache behavior.

Lifetime rule: adapters/services stateless per request. Treat engine model cache as process-shared; never store principal/question. Before adding mutable state, enumerate every constructor/instantiation site.

## 10. Migration và rollback

1. Add V1 behind `module.quant_research.enabled=false`.
2. Offline golden parity against canonical engine and live wrapper.
3. Enable internal then canary accounts; old endpoints remain fallback.
4. Enable read-only traffic after numeric/error/latency gates.
5. Do not redirect/remove old routes or delete shims in this plan.

Rollback: QF0 remove unconsumed package; QF1/QF2 disable tool manifests; QF3 disable module flag; QF4 route canary back to existing wrapper. Engines/routes unchanged. No quant-specific DB migration; Agentic Core owns run/artifact persistence, avoiding cascading rollback.

## 11. Measurable success criteria

- 100% manifests import `risk_dashboard.engines.quant`; 0 new `risk_dashboard.quant` imports.
- 3 tool contracts + 2 endpoints pass schema/OpenAPI snapshots.
- Golden fixtures: exact core `QuantEngineOutput` equality direct vs adapter.
- 100% artifacts have source refs + limitations; injected numeric mismatch block rate 100%.
- Unauthorized/cross-account successful access = 0.
- Active QC dependencies/claims (`qiskit`, `cirq`, QAOA, hardware, advantage) = 0.
- Existing 3 live endpoints behavior-compatible throughout rollout.
- Canary meets p95/error thresholds fixed before QF4 (not guessed in code).

## 12. Explicit out-of-scope và unresolved questions

Out of scope: QAOA/VQE, circuits, simulators, hardware, quantum credentials/advantage/roadmap, arbitrary execution, trading actions, shim deletion.

Unresolved questions:

1. Final route prefix must follow app assembly: `/api/quant-research/*` or registry-provided prefix?
2. Stable EOD adapter boundary: `run_quant_eod` or existing `run_eod_narrative` composition? QF1 review must choose one; calculations remain in `engines/quant/`.
3. Canary p95/error thresholds and quant research product owner chưa được chỉ định.
