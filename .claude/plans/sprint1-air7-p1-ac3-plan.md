# Sprint 1 — AIR7, P1 Migration, AC3 Plan

## Scope

1. AIR7 ADR: establish `platform/ai_runtime` as the single owner for remote LLM provider health; retain `platform/model_runtime` for local model-path health only.
2. P1 security migration: move `GET /auth/me` from query-string `session_id` to the existing server-side `resolve_principal` Bearer dependency.
3. AC3 offline graph shell: bounded deterministic execution with `FakeProvider` and a fake read-only tool. No Gemini/network, API router, domain agent, or frontend.

## Non-goals

- No Gemini invocation, OpenAI migration, Pro Lab cutover, real quant/domain tool, streaming, durable graph checkpoints, API endpoint for agentic runs, frontend, commit/push.
- Do not modify `.claude/settings.json` or `data/global_market_prices/global_market_snapshot.json`.

## Phase A — AIR7 ADR

### Files
- Create `docs/adr/ADR-001-ai-runtime-boundary.md`.

### Decision
- `risk_dashboard.platform.ai_runtime` owns remote LLM provider protocol, provider health, telemetry, redaction, retry, structured output.
- `risk_dashboard.platform.model_runtime` remains owner of local model runtime/path availability only.
- No health-check API merge or package rename in this phase.

### Verification
- ADR references real boundaries and no behavior change.

## Phase B — P1 authenticated `/auth/me` migration

### Files
- Modify `src/risk_dashboard/modules/auth/api/public.py`.
- Extend `tests/test_auth_google.py` or create focused `tests/test_auth_principal.py` endpoint cases.

### Implementation
- Replace `Query` identity input on `GET /auth/me` with `principal: AuthPrincipal = Depends(resolve_principal)`.
- Build `AuthMeResponse` from resolved principal/session account context. Since `/me` response only needs `session_id` and profile, fetch account from existing resolver dependency or expose principal plus account safely inside dependency.
- Remove `Query` and direct `ResolveSession` imports from endpoint module if orphaned.

### Security tests
- Valid `Authorization: Bearer <session_id>` returns 200 and own profile.
- Missing header gets FastAPI auth validation response; malformed/non-Bearer header gets 401.
- `?session_id=<valid>` without Authorization no longer authenticates.
- Revoked/expired session gets 401.

### Risk / rollback
- This is a breaking authenticated transport change. Rollback restores query-only endpoint; no session data mutation. Existing login response still returns `session_id`, so clients can build Bearer header.

## Phase C — AC3 offline graph shell

### Files
- Create `src/risk_dashboard/modules/agentic_core/application/graph.py`.
- Create `src/risk_dashboard/modules/agentic_core/domain/ports.py` for a narrow read-only tool protocol.
- Create `tests/test_agentic_graph.py`.

### Minimal design

Use `langgraph.graph.StateGraph` with explicit typed state and synchronous graph nodes. `LangGraph` supplies declarative node/edge orchestration only; LangChain model/tool wrappers are not needed because AC3 already receives an injected `LLMProvider` contract and read-only tool port.

`run_graph(envelope, task, provider, tool)` compiles and invokes a bounded graph with these transitions:

1. **guard**: reject exhausted/cancelled budget before provider/tool call.
2. **router**: deterministic route from `task.task_type`; unknown type takes recovery path without provider call.
3. **specialist**: invoke injected `FakeProvider.generate(task)` through the runtime retry boundary; only an approved `read` tool manifest can receive a grant.
4. **reviewer**: accept parsed/text provider result only if no failure; generate final `GraphResult` including stable trace steps.
5. **recovery**: convert typed `ModelError`, unknown intent, tool failure, cancellation, budget exhaustion into typed deterministic outcome.

State/result is in-memory, contains no raw prompt/secret, no DB write or checkpoint. Max steps uses `envelope.budget.max_steps`; tool calls uses `max_tool_calls`; wall deadline uses `max_wall_seconds`. Default direct/single-specialist path is one provider call and at most one injected synthetic read-only fake tool call. No generated UUID or current timestamp appears in replay-sensitive output.

### Tests
- Happy path: `FakeProvider` + fake read tool -> reviewed success; trace reproducible for identical scripted inputs.
- Forbidden tool: no tool execution/grant.
- Unknown task type: recovery result, no provider call.
- Provider `ModelError`: recovery result, no uncaught exception.
- `max_steps=0`/tool budget exhausted/cancelled: guard rejects before side effect.
- Fake provider proves no network dependency.

### Dependency and rollback
- Imports existing `TrustedExecutionEnvelope`, `ModelTask`, `ModelResult`, `LLMProvider`, `FakeProvider`, `resolve_grant` only.
- Does not import `engines/agents` or provider SDK.
- Rollback deletes new graph/ports/tests; no persisted state or migration.

## Execution order

A → B → C. Phase A documentation first; B security migration independently verifiable; C builds only after auth compatibility test passes.

## Success criteria

- ADR assigns exactly one remote provider-health owner.
- `/auth/me` cannot authenticate via URL query and accepts only valid Bearer session.
- AC3 graph runs fully offline with FakeProvider/fake tool; enforces grant/budget/recovery behavior.
- Targeted tests and prior Sprint 1 tests pass.
