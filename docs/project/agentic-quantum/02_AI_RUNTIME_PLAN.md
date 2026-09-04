# 02 — Shared AI Runtime Plan

> Capability owner đích: `src/risk_dashboard/platform/ai_runtime/`
> Roadmap liên quan: AT2, AT4B, AT6
> Trạng thái: package đích chưa tồn tại (greenfield); runtime bọc live `ChatOpenAI` đang chạy tại `src/risk_dashboard/modules/pro_lab/api/ai.py:32-44`.
> Provider = abstraction: production dùng `GeminiAdapter` với model cố định `gemini-3.5-flash`; `FakeProvider` chỉ dùng cho test.

## 0. Reality note (đọc trước khi code)

| Vùng | Hiện trạng (verified) | Hành động |
|---|---|---|
| `platform/ai_runtime/` | Không tồn tại. Chỉ có `platform/model_runtime/registry.py:6-11` với `model_runtime_health()` (11 dòng, check local model path) | Greenfield; AIR0 tạo contracts |
| LLM provider | OpenAI live (`gpt-4o-mini` qua `langchain-openai`); `google.generativeai` = 0 dòng | Chốt `LLMProvider`; production target cố định Gemini `gemini-3.5-flash`; migrate live OpenAI calls sau parity |
| Live call site | `_invoke_openai` / `_model_name` / `_openai_enabled` tại `pro_lab/api/ai.py:19-52` gọi `ChatOpenAI(...).invoke(...)` trực tiếp | AIR6 migrate sang `GeminiAdapter`; cutover chỉ sau behavior/eval parity |
| `platform/model_runtime` | Domain khác (local model health), không phải LLM provider runtime | AIR7 ADR tách owner, tránh 2 runtime cùng sở hữu provider health |
| Pro Lab "swarm 4 agents" | 1 prompt OpenAI trả JSON roleplay (`ai.py:152-205`), không phải 4 agent/tool thật | Ghi rõ reality; substrate thật ở doc 00/03 |

## 1. Capability

AI Runtime cung cấp một đường gọi model thống nhất, có structured output, timeout, retry, cancellation, redaction, health và telemetry. Runtime là hạ tầng; nó không quyết định persona, skill, tool authority, finance formula hoặc memory write.

Codebase hiện có `platform/model_runtime`, nhưng package này đang phục vụ health/availability của local model path chứ chưa phải LLM provider runtime mô tả ở đây. AT0 phải ra ADR chọn một trong hai hướng: mở rộng/đổi tên package hiện hữu hoặc tạo `platform/ai_runtime` song song với boundary rõ; không để hai runtime cùng sở hữu provider health mơ hồ.

## 2. Scope và boundary

Runtime sở hữu:

- provider protocol and request/response types;
- production `GeminiAdapter` cố định `gemini-3.5-flash`; legacy OpenAI call sites chỉ là migration source;
- structured generation/function-call parsing;
- streaming adapter sau khi JSON path ổn định;
- timeout, bounded retry, cancellation and circuit breaker;
- token/cost/latency/finish-reason telemetry;
- prompt/context redaction and size limits;
- fake provider for deterministic tests;
- startup validation and health status.

Runtime không sở hữu:

- graph state/router/reviewer;
- tool registry/grants;
- prompts chuyên môn hoặc skill manifests;
- user memory/context retrieval;
- cross-provider automatic fallback trong MVP;
- domain response caching có personal data.

## 3. Proposed interfaces

Contracts sống ở `src/risk_dashboard/platform/ai_runtime/contracts.py` (Pydantic v2) và `provider.py` (Protocol). Provider-neutral, `schema_version` cho forward-compat.

```python
# src/risk_dashboard/platform/ai_runtime/contracts.py
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]

class ModelMessage(BaseModel):
    role: Role
    content: str

class ModelSettings(BaseModel):
    temperature: float = 0.4                     # khớp ai.py:34
    max_output_tokens: int = 4096
    response_format: Literal["text", "json_object"] = "json_object"

class ModelTask(BaseModel):
    schema_version: str = "1.0.0"
    task_type: str                               # vd "strategy_copilot", "tutor_answer"
    system_instructions_ref: str                 # id/khóa prompt, KHÔNG nhúng raw prompt tùy tiện
    messages: tuple[ModelMessage, ...]
    tool_schemas: tuple[dict[str, Any], ...] = ()
    output_schema: dict[str, Any] | None = None  # JSON Schema cho structured output
    settings: ModelSettings = Field(default_factory=ModelSettings)
    correlation_id: str
    deadline_seconds: float = 20.0               # khớp timeout=20 ở ai.py:35
    max_cost_usd: float = 0.10

class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0

class ModelResult(BaseModel):
    schema_version: str = "1.0.0"
    parsed: dict[str, Any] | None                # structured output đã validate
    text: str
    tool_calls: tuple[dict[str, Any], ...] = ()
    usage: TokenUsage = Field(default_factory=TokenUsage)
    provider: str                                # "openai" | "gemini" | "fake"
    model: str
    latency_ms: int
    finish_reason: str
    repair_attempts: int = 0

class ModelError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code                         # xem §7 error model
        self.retryable = retryable
```

```python
# src/risk_dashboard/platform/ai_runtime/provider.py
from typing import Protocol
from .contracts import ModelTask, ModelResult

class LLMProvider(Protocol):
    name: str
    async def generate(self, task: ModelTask) -> ModelResult: ...
    async def health(self) -> bool: ...
```

Runtime chỉ nhận context đã được caller authorize. Nó vẫn redacts defense-in-depth trước khi gửi provider.

### 3.1 Real-dependency mapping (không aspirational)

| Contract/concept | Live code hôm nay | WP |
|---|---|---|
| `LLMProvider.generate` | `ChatOpenAI(...).invoke([...])` tại `pro_lab/api/ai.py:32-44` | AIR2 bọc, AIR6 di dời |
| `ModelTask.settings` | `temperature=0.4, timeout=20, max_retries=1, response_format=json_object` `ai.py:32-38` | AIR2 |
| model resolution | `_model_name()` `ai.py:23-24` (`PRO_LAB_AI_MODEL`→`AI_ASSISTANT_MODEL`→`gpt-4o-mini`) | AIR2 |
| provider enabled | `_openai_enabled()` `ai.py:19-20` (`OPENAI_API_KEY`) | AIR2 |
| `health()` (local model) | `model_runtime_health()` `platform/model_runtime/registry.py:6-11` | AIR7 (tách owner) |
| bật/tắt runtime | `FeatureFlagService.is_enabled` `platform/feature_flags/service.py:6-12` | AIR6 gate |

## 4. Package đề xuất

```text
src/risk_dashboard/platform/ai_runtime/
├── contracts.py              # ModelTask/ModelResult/ModelError/ModelSettings (§3)
├── provider.py               # LLMProvider Protocol (§3)
├── structured.py             # parse + validate output_schema, repair budget
├── streaming.py              # AIR5, sau khi JSON path ổn
├── retry.py                  # bounded retry, honor deadline (§7)
├── redaction.py              # redact secret/PII trước provider & traces (§9)
├── telemetry.py              # token/cost/latency/finish_reason (§8)
├── health.py                 # provider health (KHÁC model_runtime local health — §0, AIR7)
├── providers/
│   └── google_gemini.py      # AIR2 production, cố định gemini-3.5-flash
└── testing/fake_provider.py  # AIR1 deterministic scripted provider
```

## 5. Model policy

- Provider-neutral contract; production model cố định = Gemini `gemini-3.5-flash`. Existing OpenAI `gpt-4o-mini` call site là migration source, không phải target policy.
- Model/provider/config chỉ lấy từ trusted server configuration.
- Không cho user chọn arbitrary model.
- Temperature/limits đặt theo task class, không tự do theo endpoint.
- Repair attempt tối đa có budget; schema failure sau budget trả typed error.
- Fallback disabled ở MVP; khi thêm phải có ADR, eval parity và disclosure.

## 6. Work packages

| ID | Work package | Deliverable | Exit evidence |
|---|---|---|---|
| AIR0 | Contracts | `LLMProvider` + `ModelTask/ModelResult/ModelError` (`schema_version` 1.0.0) | type/schema review |
| AIR1 | Fake runtime | deterministic scripted provider (`testing/fake_provider.py`) | orchestration tests độc lập network |
| AIR2 | Gemini production adapter | `google_gemini.py` cố định `gemini-3.5-flash`; auth, generate, function calls, usage | integration test isolated env + model-policy assertion |
| AIR3 | Guardrails | deadline, retry, cancel, size limit, redaction | fault-injection tests |
| AIR4 | Observability | traces, token/cost/latency, health | dashboards và alert rules |
| AIR5 | Streaming | ordered events, cancel/disconnect handling | SSE contract/E2E |
| AIR6 | Pro Lab migration | di dời call site `ai.py` vào shared runtime và chuyển sang `GeminiAdapter` | behavior/eval parity trước cutover |
| AIR7 | Runtime naming ADR | extend `platform/model_runtime` vs tạo mới `platform/ai_runtime` + boundary + migration | ADR approved + single owner provider health |

### 6.0 Thứ tự

AIR0 → AIR1 → AIR7 (ADR chốt path package, blocks tạo file) → AIR2 → AIR3 → AIR4 → AIR6 (behavior/eval parity gate trước Gemini cutover) → AIR5.

### 6.1 Acceptance test + Definition of Done

- **AIR0**: import `contracts`/`provider` OK; round-trip `ModelTask`/`ModelResult` qua Pydantic; `ModelError.code` ∈ §7. DoD: type check pass, 0 provider SDK import trong contracts.
- **AIR1**: `FakeProvider.generate` trả `ModelResult` scripted theo `task_type`; hỗ trợ inject error + delay. DoD: orchestration test chạy không cần network.
- **AIR2**: `GeminiAdapter.generate` dùng cố định `gemini-3.5-flash`; golden fixtures đối chiếu behavior cần giữ từ `_invoke_openai` trên 3 endpoint Pro Lab. DoD: parity JSON, `usage` populated, `deadline_seconds`/timeout=20 honored.
- **AIR3**: fault-injection (timeout, 429, malformed JSON, cancel) → typed `ModelError` đúng `retryable`. DoD: retry honor `deadline_seconds`, size limit enforced.
- **AIR4**: mỗi call phát telemetry token/cost/latency/finish_reason, redacted. DoD: dashboard + alert rule, 0 secret/raw prompt trong traces.
- **AIR5**: streaming ordered, cancel/disconnect → abort upstream. DoD: SSE contract test + E2E.
- **AIR6**: `ai.py` 3 endpoint gọi qua runtime và cut over sang Gemini `gemini-3.5-flash` sau behavior/eval parity. DoD: parity gate pass, không có OpenAI production fallback.
- **AIR7**: ADR chốt package path, single owner provider health. DoD: ADR approved, không 2 runtime tranh chấp provider health.

## 7. Error model

Typed errors tối thiểu:

- `configuration_error`;
- `provider_auth_error`;
- `rate_limited`;
- `deadline_exceeded`;
- `cancelled`;
- `schema_invalid`;
- `safety_blocked`;
- `provider_unavailable`;
- `budget_exceeded`.

Error trả caller không chứa secret, raw provider payload hoặc private prompt. Retry chỉ áp dụng transient error và phải honor overall deadline/idempotency.

## 8. Performance và cost controls

- hard context/token limits theo task class;
- p50/p95 TTFT and total latency;
- cost attributed by surface, skill, run and outcome;
- model call count and repair count per run;
- shared/versioned knowledge cache only; no cross-user answer cache;
- cancel upstream request khi user disconnect nếu không còn side effect cần hoàn tất;
- concurrency limits per account and service.

## 9. Security

- secret từ environment/secret manager, startup validation, không log;
- redact token, PII và forbidden fields trước model/traces;
- provider payload minimization;
- TLS and verified SDK configuration;
- dependency pinning and vulnerability scan;
- prompt injection không được “giải” ở runtime bằng heuristic duy nhất; authority vẫn ở Tool Grant.

## 10. Test plan

- Unit: redaction, budgeting, schema parse, retry decisions.
- Contract: fake and Gemini adapters obey same protocol.
- Integration: structured result, function calls, safety block, rate limit.
- Resilience: timeout, malformed stream, disconnect, provider partial response.
- Security: secret/log scan and oversized input.
- Performance: concurrency, TTFT, total latency and cost aggregation.

## 11. Definition of Done

- Agentic Core và AI Tutor không import provider SDK trực tiếp.
- Runtime trả structured typed result hoặc typed error ở mọi path.
- Fake provider covers graph, retry, cancellation and streaming tests.
- Telemetry không chứa raw secret/private context.
- Budget and deadline propagate end-to-end.
- Pro Lab migration chỉ thực hiện sau parity gate, không silently đổi hành vi.

## 12. Open decisions

- SDK/version pin and exact streaming protocol?
- Token/cost estimator khi provider usage thiếu?
- Regional data handling requirements?
- Model deployment health và rollout strategy?
- ~~`ai_runtime` là new package hay extend `model_runtime`?~~ → chốt tại AIR7 ADR (blocks tạo package path).
- Provider fallback order nào được dùng khi có?

## 13. Validation checkpoint

Entry criteria:

- ADR `ai_runtime` vs `model_runtime` decided;
- fake provider ready.

Exit criteria (quantitative):

- Agentic Core + AI Tutor không import provider SDK trực tiếp;
- model call p50 < 100ms, p95 < 300ms excluding network;
- fake provider covers retry/cancel/streaming/timeout;
- schema validation trên mọi model output.

Validation gate: maps to VP-AT2.
