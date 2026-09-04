# 03 — AI Tutor / Conversational Agent Plan

> Domain owner đích: `modules/ai_tutor`
> Agent consumer: `modules/ai_tutor` (self-owns conversation surface)
> Dependencies: Agentic Core (doc 00), AI Runtime (doc 02), Identity/Trust (doc 01)
> Roadmap liên quan: AT2, AT3, AT4, AT5
> Trạng thái: **GREENFIELD** — module chưa tồn tại; Tutor điều phối learning/BCTC/quant qua typed tools; không sở hữu domain state.

## 0. Reality note

| Vùng | Hiện trạng verified | Hành động |
|---|---|---|
| Module `ai_tutor` | **KHÔNG TỒN TẠI** — `src/risk_dashboard/modules/ai_tutor/` chưa có | GREENFIELD: tạo module theo hexagonal/DDD convention; `module.py` đăng ký `ModuleDefinition(id="ai_tutor", …)` |
| Identity/Auth | `ResolveSession.execute(*, session_id)` (`modules/auth/application/services.py:163-190`) trả `tuple[Account, AccountSession]`; raise `SessionInvalid` khi inactive/expired | Tutor dùng **REUSE** `ResolveSession` server-side; session_id từ request header, model không truyền principal |
| Learning adapter | `GetLearningLesson.execute()` (`modules/learning/application/query_handler.py:122-142`) → catalog + quiz; `GetLearningHome.execute()` (`:53-99`) → home payload | Tutor gọi `learning.*` tools; **không** import `query_handler` trực tiếp — chỉ qua tool adapters |
| BCTC adapter | REST compute live trong `modules/financials_product/api/public.py` (doc 05 §5.2); `_load_dataset_or_503(:769)`, `_calculated_ratio(:929)` | Tutor gọi `bctc.*` tools (doc 05 §5); **không** import financial modules trực tiếp |
| Agentic Core | `TrustedExecutionEnvelope`, `AgentRun`, `AgentStep`, `ToolCall` (doc 00 §5.2) | Tutor chạy trong envelope; tool calls được wrap `AgentStep` → `ToolCall` typed |
| AI Runtime | `LLMProvider` protocol, `GeminiAdapter` cố định `gemini-3.5-flash` (doc 02 §5) | Tutor gửi prompt qua runtime; không import provider SDK |
| Conversation persistence | **KHÔNG TỒN TẠI** — chưa có conversation/message store | GREENFIELD: SQLite repo theo convention `platform/database/migrate.py` additive migration |
| Module registration | `ModuleDefinition` frozen dataclass (`app/registry/module_definition.py:7-23`) với fields `id, slug, enabled_by_default, dependencies, feature_flags, permission_scopes, public_router, startup_hooks, job_handlers` | `module.py` mới đăng ký scopes `ai_tutor:conversation:read`, `ai_tutor:conversation:write`, `ai_tutor:feedback:write` |

## 1. Capability

AI Tutor là conversational product giúp user hỏi, học, kiểm tra hiểu biết và tiếp tục workflow trên Learn, BCTC, Simulation hoặc Quant. Tutor sở hữu conversation lifecycle và teaching interaction; specialist knowledge và tools vẫn thuộc domain.

MVP không phải chatbot tài chính đa năng. Nó là contextual finance-learning agent có evidence, memory có kiểm soát và bounded tool use.

## 2. Evidence từ codebase và khoảng trống

Không có module `ai_tutor` — mọi thứ là greenfield. Tuy nhiên, dependency anchors đã live:

- `ResolveSession` đã có auth flow (`modules/auth/application/services.py:163-190`);
- Learning query handler đã có lesson/progress/quiz flows (`modules/learning/application/query_handler.py`);
- Agentic Core envelope đã có typed tool call path (doc 00);
- AI Runtime có `GeminiAdapter` production dùng cố định `gemini-3.5-flash` (doc 02).

Khoảng trống chính:

- chưa có conversation/message persistence;
- chưa có tutor graph/router deterministic;
- chưa có streaming presentation contract (SSE);
- chưa có teaching policy enforced server-side;
- chưa có feedback lifecycle;
- chưa có skill manifests hay tool adapter registration;
- `ModuleDefinition` registration chưa tồn tại cho ai_tutor.

## 3. User workflows

| Workflow | Trigger | Agent output | Write boundary |
|---|---|---|---|
| Explain lesson | user chọn section trong lesson | definition + source refs | read-only (gọi `learning.get_context`) |
| Socratic hint | user hỏi đáp án quiz | staged hint, no answer leak | read-only (gọi `learning.get_quiz_item`) |
| Formula walkthrough | user chọn formula/block | variables, substitution, units | read-only (gọi `learning.get_context` + `bctc.calculate_ratio` nếu applicable) |
| BCTC analysis | user hỏi về financial data | evidence + comparison + limitations | read-only (gọi `bctc.*` tools) |
| Checkpoint | lesson milestone | deterministic question/result | **confirmed_write** qua `learning.grade_checkpoint` → `learning.update_progress` |
| Next lesson | reviewed progress | next-step card | read-only (gọi `learning.recommend_next`) |
| Feedback | user đánh giá response | feedback record | **confirmed_write** qua `feedback.submit` |
| Memory control | user xem/sửa/xóa memory | memory state update | **confirmed_write** qua `memory.update` / `memory.delete` |

## 4. Required surface context

- `conversation_id` và `message_id`;
- authenticated `account_id` (server-resolved từ `session_id`);
- current `lesson_id`/`report_id` nếu đang trong context;
- teaching preferences (locale, level, style) nếu user đã consent;
- conversation history (working memory, max N turns);
- tool grant policy (tools nào available trong session);
- streaming state (SSE connection id);
- idempotency key cho message submit.

Client có thể gửi resource references, nhưng server phải resolve và verify actual identity/context.

### 4.1 File layout đích

```text
src/risk_dashboard/modules/ai_tutor/
├── module.py                              # NEW: ModuleDefinition registration
├── agent_tools.py                         # NEW: typed Agentic Core tool adapters (§5)
├── skills/                                # NEW: versioned tutor.* manifests/prompts
│   ├── manifests.py
│   └── prompts/
├── schemas/                               # NEW (thư mục chưa tồn tại)
│   ├── agent_tools.py                     # NEW: §5.1 Pydantic v2 contracts
│   ├── conversation.py                    # NEW: conversation/message entities
│   ├── streaming.py                       # NEW: SSE event contracts
│   └── feedback.py                        # NEW: feedback entity
├── application/
│   ├── conversation_service.py            # NEW: conversation lifecycle CRUD
│   ├── graph.py                           # NEW: tutor intent router (deterministic)
│   ├── tutor_node.py                      # NEW: single-turn response composition
│   ├── response_composer.py               # NEW: streaming + non-streaming rendering
│   ├── feedback_service.py                # NEW: feedback validation + persistence
│   └── memory_service.py                  # NEW: durable memory read/propose/delete
├── domain/
│   ├── conversation.py                    # NEW: conversation/message entities
│   ├── teaching_policy.py                 # NEW: routing rules (ask vs answer vs hint)
│   ├── feedback.py                        # NEW: feedback entity + validation
│   └── ports.py                           # NEW: ConversationRepo, FeedbackRepo ports
├── infrastructure/
│   ├── sqlite_conversation_repository.py  # NEW: SQLite persistence (additive migration)
│   └── sqlite_feedback_repository.py      # NEW: feedback persistence
├── api/
│   ├── conversations.py                   # NEW: REST endpoints §5
│   └── events.py                          # NEW: SSE streaming endpoint
└── templates/                             # NEW: prompt templates (Jinja2)
    ├── system.py
    ├── explain.py
    ├── hint.py
    └── review.py
```

## 5. Domain tools

| Tool | Input schema | Output schema | Required scope | Risk-class |
|---|---|---|---|---|
| `tutor.create_conversation` | `CreateConversationInput` | `CreateConversationOutput` | `ai_tutor:conversation:write` | `confirmed_write` |
| `tutor.get_conversation` | `GetConversationInput` | `GetConversationOutput` | `ai_tutor:conversation:read` | `read` |
| `tutor.list_messages` | `ListMessagesInput` | `ListMessagesOutput` | `ai_tutor:conversation:read` | `read` |
| `tutor.send_message` | `SendMessageInput` | `SendMessageOutput` | `ai_tutor:conversation:write` | `confirmed_write` |
| `tutor.submit_feedback` | `SubmitFeedbackInput` | `SubmitFeedbackOutput` | `ai_tutor:feedback:write` | `confirmed_write` |

Release đầu: conversation CRUD + message send + feedback. Domain tools (learning/BCTC/quant) được gọi qua Agentic Core router, không phải tutor-owned. Tutor **không** sở hữu progress, mastery, hay financial data — chỉ điều phối qua scoped tools.

`AuthPrincipal` và `account_id` được server resolve trước tool call; model không truyền principal.

### 5.1 Tool I/O schemas

Contracts đặt tại `src/risk_dashboard/modules/ai_tutor/schemas/agent_tools.py`, Pydantic v2. ID trong input là resource references, không phải authority.

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreateConversationInput(BaseModel):
    schema_version: str = "1.0.0"
    surface: Literal["learn", "bctc", "quant", "general"] = "general"
    context_id: str | None = None        # lesson_id hoặc report_id nếu surface-scoped
    idempotency_key: str


class CreateConversationOutput(BaseModel):
    schema_version: str = "1.0.0"
    conversation_id: str
    created_at: str                      # ISO-8601 UTC
    surface: str
    status: Literal["active", "archived"] = "active"


class GetConversationInput(BaseModel):
    schema_version: str = "1.0.0"
    conversation_id: str


class GetConversationOutput(BaseModel):
    schema_version: str = "1.0.0"
    conversation_id: str
    surface: str
    status: Literal["active", "archived"]
    created_at: str
    updated_at: str
    message_count: int = Field(ge=0)
    context_id: str | None = None


class ListMessagesInput(BaseModel):
    schema_version: str = "1.0.0"
    conversation_id: str
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None


class Message(BaseModel):
    message_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str
    citations: tuple[CitationRef, ...] = ()
    tool_calls: tuple[ToolCallRef, ...] = ()


class CitationRef(BaseModel):
    source_type: Literal["lesson", "bctc", "formula"]
    source_id: str
    label: str


class ToolCallRef(BaseModel):
    tool_name: str
    status: Literal["success", "error", "skipped"]
    summary: str


class ListMessagesOutput(BaseModel):
    schema_version: str = "1.0.0"
    messages: tuple[Message, ...]
    next_cursor: str | None = None
    has_more: bool = False


class SendMessageInput(BaseModel):
    schema_version: str = "1.0.0"
    conversation_id: str
    content: str = Field(min_length=1, max_length=4000)
    current_surface_id: str | None = None  # lesson_id/report_id đang xem
    idempotency_key: str


class SendMessageOutput(BaseModel):
    schema_version: str = "1.0.0"
    message_id: str
    conversation_id: str
    created_at: str
    assistant_message_id: str
    streaming_token: str | None = None     # SSE connection ref
    tool_calls: tuple[ToolCallRef, ...] = ()


class SubmitFeedbackInput(BaseModel):
    schema_version: str = "1.0.0"
    message_id: str
    rating: Literal["helpful", "not_helpful", "partially_helpful"]
    comment: str | None = Field(default=None, max_length=2000)
    idempotency_key: str


class SubmitFeedbackOutput(BaseModel):
    schema_version: str = "1.0.0"
    feedback_id: str
    message_id: str
    created_at: str
```

Invariant: `Message.content` cho assistant response **không** chứa raw tool output — chỉ synthesized answer + citations. `tool_calls` là summary, không phải raw `ToolCall` object. Conversation history là working memory; durable memory chỉ qua `memory.update`/`memory.delete` (doc 00 §5.3).

### 5.2 Real-dependency mapping

| Contract/tool | Live code hôm nay | WP |
|---|---|---|
| `ResolveSession` (identity anchor) | `ResolveSession.__init__(accounts, sessions)` + `execute(*, session_id) -> tuple[Account, AccountSession]` (`modules/auth/application/services.py:163-190`); raises `SessionInvalid` | TUT0 |
| Learning context adapter | `GetLearningLesson.execute()` (`modules/learning/application/query_handler.py:122-142`) → `SqliteLearningCatalog.get_lesson()` (`infrastructure/catalog_reader.py:123-130`, `189-194`) | TUT2 (qua `learning.*` tools) |
| Learning home/recommend | `GetLearningHome.execute()` (`modules/learning/application/query_handler.py:53-99`) → catalog + progress | TUT2 (qua `learning.recommend_next`) |
| BCTC data adapter | `_load_dataset_or_503(ticker)` (`modules/financials_product/api/public.py:769`) → `get_financial_dataset` (`data/financials.py`); `_calculated_ratio()` (`:929`) | TUT2 (qua `bctc.*` tools) |
| ModuleDefinition | `ModuleDefinition(id, slug, enabled_by_default, dependencies, feature_flags, permission_scopes, public_router, …)` (`app/registry/module_definition.py:7-23`) | TUT0 |
| Agentic Core envelope | `TrustedExecutionEnvelope`, `AgentRun`, `AgentStep`, `ToolCall` (doc 00 §5.2) | TUT1 |
| AI Runtime | `LLMProvider` protocol, `GeminiAdapter` cố định `gemini-3.5-flash` (doc 02 §5) | TUT2 |
| Migration | `platform/database/migrate.py` ordered `(migration_id, sql)` + additive `CREATE TABLE IF NOT EXISTS` | TUT0 |

## 6. Skills và orchestration

Skill manifests đầu tiên:

- `tutor.explain.v1` — lesson context → explanation + citations;
- `tutor.socratic_hint.v1` — quiz context → staged hint;
- `tutor.formula_walkthrough.v1` — formula/block → substitution + units;
- `tutor.bctc_analysis.v1` — financial question → bctc.* tools → evidence;
- `tutor.checkpoint.v1` — lesson milestone → deterministic question;
- `tutor.next_step.v1` — progress review → recommended next lesson;
- `tutor.general.v1` — general finance question → bounded response.

```text
Guard + session auth (ResolveSession → account_id)
  → pin conversation_id/turn number
  → classify intent: explain | hint | formula | bctc | checkpoint | general
  → route to domain tools (learning.* / bctc.* / quant.*) qua Agentic Core
  → compose response (response_composer.py)
  → numeric/citation reviewer (doc 00 reviewer layer)
  → streaming presentation (SSE events)
  → optional feedback capture
```

Router ưu tiên deterministic match: UI intent (button click → specific skill), sau đó keyword/classifier fallback. Tutor graph (`graph.py`) là finite-state, không phải free-form LLM routing.

## 7. Knowledge và memory

- Conversation history (raw messages) là working memory — max N turns, bounded.
- Summaries được tạo mỗi K turns; giữ context window manageable.
- Durable memory (tutor-scoped) chỉ: explicit teaching preference, accepted learning goal, verified misconception.
- Memory disabled → working context vẫn hoạt động nhưng 0 durable write.
- Domain progress (learning mastery, BCTC artifacts) sống ở domain modules — tutor không duplicate.
- Summary phải dẫn nguồn content version; stale summary phải thua content mới.

## 8. Work packages

| ID | Work package | Deliverable | Exit evidence |
|---|---|---|---|
| TUT0 | Module + conversation contracts | `ModuleDefinition`, entities, SQLite repo, scope registration, migration | schema/security review |
| TUT1 | JSON vertical slice | create/list/message (JSON, no SSE) + fake graph | integration/E2E |
| TUT2 | Tutor graph + tool routing | deterministic router → learning/BCTC/quant tools | route accuracy eval |
| TUT3 | Teaching interactions | explain, hint, formula, checkpoint, next step | pedagogy review |
| TUT4 | Feedback/artifacts | feedback lifecycle, citations, limitations, artifact cards | UI/accessibility E2E |
| TUT5 | Memory controls | summaries + consented memory read/propose/delete | memory precision/privacy tests |
| TUT6 | SSE hardening | ordered events, reconnect, cancel, error recovery | streaming reliability tests |
| TUT7 | Persona definition | tone, Vietnamese register (anh/em), teaching style, forbidden phrasing | persona doc approved (master §14A.4) + sample transcript review |
| TUT8 | Teaching-style register | rule switching Socratic vs explanatory theo level/checkpoint/user | style switch tests + pedagogy review trên gold-set |

### 8.0 Thứ tự bắt buộc (dependency-ordered)

- `TUT0` freeze `ModuleDefinition`, conversation/message schemas `1.0.0`, ownership và scopes; block mọi tool.
- `TUT1` cần TUT0: JSON vertical slice chứng minh create → list → message flow; fake graph cho routing.
- `TUT2` cần TUT1: deterministic router thay thế fake graph; gọi `learning.*`/`bctc.*` tools qua Agentic Core; **không** import domain modules trực tiếp.
- `TUT3` cần TUT2 + AI Runtime (doc 02): teaching interactions chạy trên real LLM calls.
- `TUT4` cần TUT3: feedback lifecycle sau khi response quality đảm bảo.
- `TUT5` cần TUT0 + TUT3: durable memory chỉ sau conversation flow verified.
- `TUT6` cần TUT1: SSE hardening sau khi JSON flow stable.
- `TUT7` freeze trước TUT3: persona approved trước khi teaching interactions go live (master §14A.4).
- `TUT8` cần TUT7 + TUT3: style switch rules chạy trên approved persona.

### 8.1 Acceptance test + Definition of Done per WP

| WP | Acceptance test | Definition of Done |
|---|---|---|
| TUT0 | `ModuleDefinition` round-trip; `ResolveSession` reject inactive/expired session; cross-account conversation isolation; migration additive pass | Module registered; conversation/message tables created; scope `ai_tutor:conversation:read/write` + `ai_tutor:feedback:write` active |
| TUT1 | Create → list → get → send → list messages round-trip; idempotency key prevents duplicate; fake graph routes to correct surface | JSON flow E2E pass; zero SSE dependency; conversation persistence verified |
| TUT2 | 5 surfaces route correctly (learn/bctc/quant/general/checkpoint); unknown intent → general fallback; tool call summary trong `Message.tool_calls` | `graph.py` deterministic; route accuracy ≥90% trên fixtures; zero domain module imports trực tiếp |
| TUT3 | Explain/hint/formula/checkpoint/next-step pass pedagogy fixtures; hint leakage = 0; numeric claims có evidence; `learning.grade_checkpoint` gọi sau explicit confirm | Skills versioned; reviewer grounding/numeric chạy trước response; persona approved (TUT7) |
| TUT4 | Feedback submit → stored → readable; citation drawer hiện `CitationRef`; keyboard-only + screen-reader labels pass | Feedback repository additive migration; deterministic Learn/BCTC vẫn dùng được khi tutor off |
| TUT5 | Memory delete removes all durable rows; memory disabled = 0 durable write; preference/goal persists; conversation history unaffected | Durable memory chỉ explicit preference/goal/verified misconception; progress đọc live từ domain modules |
| TUT6 | Ordered SSE events; reconnect delivers missed events; cancel stops stream; error event has recoverable label; concurrent connections stable | SSE endpoint `/api/ai-tutor/conversations/{id}/events`; event ordering verified; graceful degradation JSON fallback |
| TUT7 | Persona doc approved (master §14A.4); sample transcripts pass tone/register review; forbidden phrasing rejected in adversarial set | `templates/system.py` persona prompt; Vietnamese register (anh/em) consistent; no buy/sell phrasing |
| TUT8 | Socratic vs explanatory style switch triggered correctly by level/checkpoint/user request; pedagogy review pass trên gold-set | Style rules in `teaching_policy.py`; gold-set eval ≥95% grounded rate |

## 9. Eval suite

Gold set phải bao phủ:

- lesson fact grounding và content version;
- financial claim evidence (BCTC tools);
- hint không lộ đáp án;
- beginner vs advanced explanation;
- ambiguous question và correct clarification;
- cross-user conversation isolation;
- persona register consistency (anh/em);
- stored injection qua conversation input;
- SSE event ordering;
- feedback idempotency.

Metrics: grounded citation rate, hint leakage = 0, persona register consistency, route accuracy, p95 TTFT/response latency, cost/session, feedback quality distribution.

## 10. Security and failure behavior

- `ResolveSession` reject inactive/expired; cross-user isolation enforced;
- conversation input sanitized trước display (stored injection);
- retrieved text là data, không phải instructions;
- quiz answer keys stay server-side (qua `learning.*` tools);
- if domain tool fails, tutor gives clearly labeled limitation, không fabricate;
- if SSE disconnect, client có thể reconnect với cursor;
- feedback không dùng làm training data nếu chưa có explicit consent;
- raw conversation có retention policy riêng; summaries không thay thế raw record về pháp lý;
- memory disabled = 0 durable write nhưng conversation scoped working context vẫn hoạt động.

## 11. Definition of Done

- Tutor operates end-to-end: conversation → tool evidence → reviewed response → feedback.
- Every external/numeric claim carries evidence or explicit limitation.
- Progress/mastery changes only through Learning service (qua `learning.update_progress`).
- Memory controls are visible and enforceable.
- JSON flow passes quality gates before SSE is enabled.
- Domain skills can be added without changing provider/runtime code.
- Persona approved và enforced (master §14A.4).
- Deterministic Learn/BCTC flows vẫn dùng được khi tutor off.

## 12. Open decisions

- Pilot syllabus và default teaching depth?
- Raw conversation retention period?
- Exact citation UX on mobile?
- When should Tutor ask clarifying question vs route directly?
- Persona refinement post-pilot?
- Socratic threshold (level/checkpoint state trigger)?
- Sequential-mode uplift bar (multi-agent bật khi nào)?
- Memory scope per surface (learn-only vs cross-surface)?

## 13. Validation checkpoint

Entry criteria:

- persona approved (master §14A.4);
- gold-set ≥100 câu ready;
- Learn Hub panel skeleton ready;
- BCTC agent tools (doc 05) ready.

Exit criteria (quantitative):

- grounded rate ≥95%;
- conversation create p50 < 200ms, p95 < 500ms;
- single-specialist response p50 < 3s, p95 < 6s, cost ≤ $0.02/session;
- zero cross-user conversation access;
- hint leakage = 0;
- multi-agent chỉ bật khi eval chứng minh uplift.

Validation gate: maps to VP-AT3.
