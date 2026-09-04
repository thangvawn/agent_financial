# Sprint 1 — Phase 0→3 Foundation Implementation Plan

## Scope

Three parallel lanes converging at Phase 3:
- **Lane 1 (Identity)**: ID0→ID1→ID2
- **Lane 2 (AI Runtime)**: AIR0→AIR1→AIR2→AIR3→AIR4
- **Lane 3 (Agentic Core)**: AC0→AC1→AC2

**Fixed constraints:**
- Production model: `gemini-3.5-flash` (no OpenAI fallback)
- No domain agents, no frontend, no commit/push
- Do NOT touch `.claude/settings.json` or `data/global_market_prices/global_market_snapshot.json`

---

## Phase 0 — Baseline Setup

### P0.1: Add `google-genai` dependency
- **File**: `pyproject.toml`
- **Action**: Add `google-genai>=1.0` to `[project.dependencies]`
- **Rationale**: Required for `GeminiAdapter` (AIR2). Currently 0 lines of google SDK in codebase.

### P0.2: Create package skeletons
- **Files**: Create `__init__.py` for:
  - `src/risk_dashboard/platform/ai_runtime/`
  - `src/risk_dashboard/platform/ai_runtime/providers/`
  - `src/risk_dashboard/platform/ai_runtime/testing/`
  - `src/risk_dashboard/modules/agentic_core/`
  - `src/risk_dashboard/modules/agentic_core/schemas/`
  - `src/risk_dashboard/modules/auth/schemas/` (if not exists)
- **Action**: Empty `__init__.py` files only. No logic.

### P0.3: Model policy env documentation
- **File**: `src/risk_dashboard/platform/ai_runtime/README.md`
- **Content**: Document env vars: `AI_PROVIDER=google`, `AI_MODEL=gemini-3.5-flash`, `AI_FALLBACK_ENABLED=0`, `GEMINI_API_KEY=`

---

## Phase 1 — Identity (ID0→ID1→ID2)

### P1.1: ID0 — Identity inventory (documentation only)
- **No code change**. Inventory already documented in `01_IDENTITY_TRUST_FOUNDATION_PLAN.md` §2.
- Anti-pattern flagged: `modules/auth/api/public.py:95-96` (`session_id` from client Query param).

### P1.2: ID1 — AuthPrincipal + ConsentSnapshot schemas
- **File**: `src/risk_dashboard/modules/auth/schemas/principal.py`
- **Content**: Exact schemas from plan doc 01 §3.1:
  - `ConsentSnapshot(BaseModel)`: schema_version, memory, analytics, policy_version, consented_at
  - `AuthPrincipal(BaseModel)`: schema_version, account_id, session_id, assurance, scopes, is_anonymous, consent, resolved_at
- **Style**: `from __future__ import annotations`, Pydantic v2, match existing `modules/auth/schemas/auth.py`
- **Exit**: Round-trip serialize/deserialize test

### P1.3: ID1 — FastAPI dependency (resolve_principal)
- **File**: `src/risk_dashboard/modules/auth/application/dependencies.py`
- **Content**: FastAPI `Depends` function wrapping `ResolveSession.execute()` → emit `AuthPrincipal`
- **Extends**: `services.py:163-187` (`ResolveSession`). Does NOT modify `ResolveSession` itself.
- **Logic**: Call `ResolveSession.execute(session_id=...)` → map `Account`+`AccountSession` → `AuthPrincipal`

### P1.4: ID2 — Ownership/entitlement policy stubs
- **File**: `src/risk_dashboard/modules/auth/domain/policies.py` (or add to existing)
- **Content**: Pure functions for scope checking:
  - `has_scope(principal: AuthPrincipal, required: str) -> bool`
  - `check_ownership(principal: AuthPrincipal, resource_account_id: str) -> bool`
- **No DB, no side effects.** Policy functions only.

---

## Phase 2 — AI Runtime (AIR0→AIR1→AIR2→AIR3→AIR4)

### P2.1: AIR0 — Contracts
- **File**: `src/risk_dashboard/platform/ai_runtime/contracts.py`
- **Content**: Exact contracts from plan doc 02 §3:
  - `Role` literal type
  - `ModelMessage`, `ModelSettings`, `ModelTask`, `TokenUsage`, `ModelResult`, `ModelError`
  - All with `schema_version="1.0.0"`, Pydantic v2
- **Invariant**: 0 provider SDK imports in this file.

### P2.2: AIR0 — Provider protocol
- **File**: `src/risk_dashboard/platform/ai_runtime/provider.py`
- **Content**: `LLMProvider(Protocol)` with `name: str`, `async generate(task) -> ModelResult`, `async health() -> bool`
- **Invariant**: Provider-neutral, 0 SDK imports.

### P2.3: AIR1 — FakeProvider
- **File**: `src/risk_dashboard/platform/ai_runtime/testing/fake_provider.py`
- **Content**: Deterministic scripted provider:
  - Accepts `list[ModelResult]` or `dict[str, ModelResult]` as script
  - `generate()` returns next scripted result (by task_type key or FIFO)
  - Supports injecting `ModelError` and artificial delay
  - `health()` always True
- **Exit**: Can run orchestration tests without network.

### P2.4: AIR2 — GeminiAdapter
- **File**: `src/risk_dashboard/platform/ai_runtime/providers/google_gemini.py`
- **Content**:
  - Import `google.genai` (google-genai SDK)
  - Fixed model: `gemini-3.5-flash` (read from env `AI_MODEL`, default `gemini-3.5-flash`)
  - `generate()`: build request from `ModelTask`, call Gemini, map response → `ModelResult`
  - `health()`: lightweight API ping
  - Auth from env `GEMINI_API_KEY` (startup validation, never log)
  - Honor `deadline_seconds` as timeout
  - Map Gemini errors → typed `ModelError` codes per doc 02 §7
- **Invariant**: Model fixed, no user-selectable model, no fallback.

### P2.5: AIR3 — Guardrails
- **File**: `src/risk_dashboard/platform/ai_runtime/retry.py`
- **Content**:
  - `with_retry(provider, task) -> ModelResult`: bounded retry honoring `deadline_seconds`
  - Retry only on `retryable=True` errors
  - Max 2 retries, exponential backoff, respect overall deadline
- **File**: `src/risk_dashboard/platform/ai_runtime/redaction.py`
- **Content**:
  - `redact_for_provider(task: ModelTask) -> ModelTask`: strip/mask known secret patterns before sending
  - Defense-in-depth, not primary auth mechanism

### P2.6: AIR4 — Telemetry
- **File**: `src/risk_dashboard/platform/ai_runtime/telemetry.py`
- **Content**:
  - `record_call(task, result, latency_ms)`: log token usage, cost estimate, finish_reason
  - Structured logging (dict/JSON), no raw prompts in output
  - `get_usage_summary() -> dict`: aggregate stats
- **File**: `src/risk_dashboard/platform/ai_runtime/health.py`
- **Content**:
  - `async check_provider_health(provider: LLMProvider) -> dict`: health status wrapper
  - Distinct from `platform/model_runtime` (local model health). This is provider health.

### P2.7: AIR — Structured output helper
- **File**: `src/risk_dashboard/platform/ai_runtime/structured.py`
- **Content**:
  - `parse_structured(text: str, schema: dict) -> dict | None`: validate model output against JSON Schema
  - Repair budget: retry parse with minor fixes (strip markdown fences, etc.) up to 2 attempts
  - Return parsed dict or raise `ModelError(code="schema_invalid")`

---

## Phase 3 — Agentic Core (AC0→AC1→AC2)

### P3.1: AC0 — Contract schemas freeze
- **File**: `src/risk_dashboard/modules/agentic_core/schemas/envelope.py`
  - `ResourceRef`, `ExecutionBudget`, `TrustedExecutionEnvelope` — exact from doc 00 §5.1
  - `TrustedExecutionEnvelope.consent` type = `ConsentSnapshot` from Phase 1
- **File**: `src/risk_dashboard/modules/agentic_core/schemas/artifact.py`
  - `AgentArtifact`, `ActionProposal`, `ActionReceipt` — exact from doc 00 §5.2
- **File**: `src/risk_dashboard/modules/agentic_core/schemas/memory.py`
  - `MemoryProposal` — exact from doc 00 §5.3
- **All schemas**: `schema_version="1.0.0"`, `from __future__ import annotations`, Pydantic v2
- **Invariant**: 0 provider SDK imports. Client cannot supply `account_id`/`scopes`/`allowed_capabilities`.

### P3.2: AC1 — Persistence (SQLite migrations + repositories)
- **File**: `src/risk_dashboard/modules/agentic_core/infrastructure/migrations.py`
- **Content**:
  - `ensure_agentic_tables(conn)`: additive `CREATE TABLE IF NOT EXISTS` for:
    - `agentic_runs` (run_id PK, account_id, surface, status, created_at, updated_at)
    - `agentic_artifacts` (artifact_id PK, account_id, run_id, artifact_type, domain, review_status, created_at)
    - `agentic_action_receipts` (receipt_id PK, proposal_id, account_id, status, executed_at)
    - `agentic_memory_proposals` (proposal_id PK, run_id, account_id, memory_type, provenance, status, created_at)
  - Pattern: match `open_app_state_db()` additive migration style (ALTER TABLE ADD COLUMN IF NOT EXISTS via PRAGMA table_info)
- **File**: `src/risk_dashboard/modules/agentic_core/infrastructure/repositories.py`
- **Content**:
  - `AgenticRunRepository`: CRUD for runs, scoped by `account_id`
  - `AgenticArtifactRepository`: CRUD for artifacts, scoped by `account_id`
  - All queries enforce `WHERE account_id = ?` — ownership scoping mandatory
  - Uses `open_app_state_db()` connection

### P3.3: AC2 — Tool registry + grants
- **File**: `src/risk_dashboard/modules/agentic_core/domain/tools.py`
- **Content**:
  - `RiskClass` enum: `read`, `proposal`, `confirmed_write`, `forbidden`
  - `ToolManifest(BaseModel)`: tool_id, name, module, risk_class, version, description
  - `ToolGrant(BaseModel)`: grant_id, run_id, tool_id, scopes, expires_at
- **File**: `src/risk_dashboard/modules/agentic_core/application/tool_grants.py`
- **Content**:
  - `resolve_grant(envelope, tool_manifest) -> ToolGrant | None`
  - `forbidden` risk_class → always None (never grant)
  - Grant scoped to single run, short expiry
  - Check `envelope.allowed_capabilities` against tool requirements

---

## Tests

### Test files to create:
1. `tests/test_auth_principal.py` — AuthPrincipal/ConsentSnapshot round-trip, reject client-supplied fields
2. `tests/test_ai_runtime_contracts.py` — ModelTask/ModelResult/ModelError round-trip, 0 provider imports
3. `tests/test_fake_provider.py` — FakeProvider scripted responses, error injection, delay
4. `tests/test_agentic_core_schemas.py` — Envelope/Artifact/Action/Memory schema round-trip
5. `tests/test_agentic_persistence.py` — SQLite migrations, ownership scoping (account A ≠ account B)
6. `tests/test_tool_grants.py` — forbidden never grants, grant scoping, expiry

### Test invariants:
- 0 network calls in any test (FakeProvider only)
- Cross-account isolation verified
- `forbidden` risk_class never resolves grant
- All schemas validate `schema_version="1.0.0"`

---

## File ownership matrix

| File | Owner | Phase |
|------|-------|-------|
| `pyproject.toml` | shared | P0 |
| `modules/auth/schemas/principal.py` | Identity lane | P1 |
| `modules/auth/application/dependencies.py` | Identity lane | P1 |
| `modules/auth/domain/policies.py` | Identity lane | P1 |
| `platform/ai_runtime/*` | AI Runtime lane | P2 |
| `modules/agentic_core/schemas/*` | Agentic Core lane | P3 |
| `modules/agentic_core/infrastructure/*` | Agentic Core lane | P3 |
| `modules/agentic_core/domain/tools.py` | Agentic Core lane | P3 |
| `modules/agentic_core/application/tool_grants.py` | Agentic Core lane | P3 |

## Execution order

```
P0 (baseline) → P1 (identity) + P2 (AI runtime) parallel → P3 (agentic core, depends on P1 ConsentSnapshot)
```

P1 and P2 are independent. P3 imports `ConsentSnapshot` from P1, so P1 must complete first.

## Risks

1. `google-genai` SDK API may differ from assumed interface → mitigate with Context7 docs lookup before coding AIR2
2. Existing `modules/auth/schemas/` dir may not exist → P0.2 creates it
3. `ResolveSession` return type may need verification → already verified at `services.py:163-187`

## Success criteria

- All 6 test files pass
- `python -c "from risk_dashboard.platform.ai_runtime.contracts import ModelTask"` succeeds
- `python -c "from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope"` succeeds
- `python -c "from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal"` succeeds
- 0 provider SDK imports in contracts/schemas
- 0 OpenAI production fallback code
- Model fixed to `gemini-3.5-flash`
