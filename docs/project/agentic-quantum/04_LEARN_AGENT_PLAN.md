# 04 — Learn Agent Plan

> Domain owner: `modules/learning`
> Agent consumer: `modules/ai_tutor` và embedded Learn panel
> Roadmap liên quan: AT1, AT3, AT4A
> Trạng thái: **EXTEND live module** — Learning deterministic đã hoạt động; agent tools/skills chưa tồn tại.

## 0. Reality note

| Vùng | Hiện trạng verified | Hành động |
|---|---|---|
| Learning core | **LIVE**: `application/query_handler.py`, `application/services.py`, `domain/entities.py`, `domain/policies.py`, `domain/ports.py`, `infrastructure/catalog.py`, `infrastructure/catalog_reader.py`, `infrastructure/repositories/sqlite.py`, `schemas/requests.py`, `schemas/responses.py`, `api/public.py`, `api/admin.py`, `module.py` dưới `src/risk_dashboard/modules/learning/` | Giữ Learning là domain owner; bọc handler/port/repository hiện hữu thay vì viết lại nghiệp vụ |
| Context/catalog | `GetLearningLesson.execute()` đọc lesson + progress (`application/query_handler.py:122-142`); `SqliteLearningCatalog.get_lesson/list_lessons()` chỉ resolve published Content Ops (`infrastructure/catalog_reader.py:115-173`, `189-194`) | `learning.get_context` là adapter **NEW** trên live catalog/query handler; LEA1 thêm provenance/version contract |
| Progress | `LearningProgressRepository` có get/list/save (`domain/ports.py:49-60`); `SqliteLearningHomeRepository` triển khai account-scoped reads/writes (`infrastructure/repositories/sqlite.py:74-149`) | `get_progress` và `update_progress` là tool adapters **NEW**; write chỉ gọi policy/service deterministic |
| Quiz/checkpoint | Web flow `SubmitLearningQuiz.execute()` grade rồi ghi progress (`application/query_handler.py:145-196`). `quiz_handler.py` và `quiz_repository.py` là Telegram quiz/session riêng (`application/quiz_handler.py:17-52`, `55-154`; `infrastructure/quiz_repository.py:30-128`) | `get_quiz_item`/`grade_checkpoint` contracts là **NEW**; có thể tái dùng lesson question bank, nhưng không coi Telegram repository là mastery store |
| Recommendation | `GetLearningHome.execute()` dựng home payload (`application/query_handler.py:53-99`); catalog có path/course/lesson lists (`infrastructure/catalog_reader.py:123-173`) | `recommend_next` là deterministic adapter **NEW** kết hợp live catalog + progress trong LEA1 |
| Grading secrets | Entity hiện chứa `correct_answer` (`domain/entities.py:12-18`) và serializer nội bộ ghi field này (`infrastructure/catalog_reader.py:62-84`) | Grading key luôn ở server; không xuất `correct_answer`, key hay key handle có thể dereference trong bất kỳ model-facing output nào |
| Persistence | Shared DB dùng ordered `(migration_id, sql)` và additive `CREATE TABLE IF NOT EXISTS` (`platform/database/migrate.py:11-17`, `137-145`, `183-210`) | Mọi bảng mới của LEA dùng migration additive theo convention này; không tạo schema ad-hoc trong tool |

## 1. Capability

Learn Agent biến lesson thành một vòng học có kiểm chứng: hiểu context đang đọc, giải thích theo trình độ, gợi ý Socratic, minh họa công thức, phát hiện misconception, tạo checkpoint và đề xuất bài tiếp theo. Learning module tiếp tục sở hữu content, quiz và progress; agent chỉ điều phối trải nghiệm học.

## 2. Evidence từ codebase và khoảng trống

`modules/learning` đã có public/admin APIs, query handler, quiz handler, catalog/delivery repositories và progress-related services. Đây là nền deterministic tốt để bọc thành tools.

Khoảng trống chính:

- session/user identity chưa đủ chặt cho per-account memory;
- chưa có contextual tutor API/embedded panel;
- lesson content chưa có retrieval/provenance contract cho agent;
- chưa có skill manifests và learning-specific eval;
- không được để model tự đánh dấu user “đã hiểu”.

## 3. User workflows

| Workflow | Trigger | Agent output | Write boundary |
|---|---|---|---|
| Explain this | selected section/lesson | explanation + source refs | read-only |
| Socratic hint | quiz/problem context | staged hint, no answer leak | read-only |
| Formula walkthrough | formula/block | variables, substitution, units | read-only |
| Misconception check | user explanation | targeted question/check | memory proposal only after verified result |
| Checkpoint | lesson milestone | deterministic question/result | progress via Learning service |
| Next lesson | reviewed progress | next-step card | explicit accept/bookmark if supported |

## 4. Required surface context

- `course_id`, `path_id`, `lesson_id`;
- section/block reference and selected text identifier;
- locale and curriculum/content version;
- authenticated progress snapshot;
- current quiz/checkpoint state;
- user teaching preferences if consented;
- source freshness/publication status.

Client may send current resource references, but server must resolve and verify actual lesson/version.

### 4.1 File layout đích

```text
src/risk_dashboard/modules/learning/
├── agent_tools.py                         # NEW: six typed Agentic Core tool adapters
├── skills/                                # NEW: versioned learn.* manifests/prompts
│   ├── manifests.py
│   └── prompts/
├── schemas/
│   ├── agent_tools.py                     # NEW: §5.1 Pydantic v2 contracts
│   ├── requests.py                        # REUSE: public HTTP contracts
│   └── responses.py                       # REUSE: public HTTP contracts
├── application/
│   ├── query_handler.py                   # REUSE: lesson/home/quiz flows
│   ├── services.py                        # REUSE: current application services
│   └── checkpoint_service.py              # NEW: protected item selection/grading boundary
├── domain/
│   ├── entities.py                        # REUSE: lesson/question/progress entities
│   ├── policies.py                        # REUSE/EXTEND: deterministic progress policy
│   └── ports.py                           # EXTEND: protected checkpoint/recommendation ports
└── infrastructure/
    ├── catalog.py                         # REUSE: seeded deterministic content
    ├── catalog_reader.py                  # REUSE: published Content Ops catalog
    ├── repositories/sqlite.py             # REUSE: progress/home persistence
    ├── delivery_repository.py             # REUSE only for Telegram delivery, not progress
    └── quiz_repository.py                 # REUSE only for Telegram session semantics
```

## 5. Domain tools

| Tool | Input schema | Output schema | Required scope | Risk-class |
|---|---|---|---|---|
| `learning.get_context` | `GetContextInput` | `GetContextOutput` | `learn:content:read` | `read` |
| `learning.get_progress` | `GetProgressInput` | `GetProgressOutput` | `learn:progress:read` | `read` |
| `learning.get_quiz_item` | `GetQuizItemInput` | `GetQuizItemOutput` | `learn:checkpoint:read` | `read` |
| `learning.grade_checkpoint` | `GradeCheckpointInput` | `GradeCheckpointOutput` | `learn:checkpoint:grade` | `read` |
| `learning.update_progress` | `UpdateProgressInput` | `UpdateProgressOutput` | `learn:progress:write` | `confirmed_write` |
| `learning.recommend_next` | `RecommendNextInput` | `RecommendNextOutput` | `learn:recommendation:read` | `read` |

`AuthPrincipal` và `account_id` được server resolve trước tool call; model không truyền principal. `learning.update_progress` chỉ chạy sau explicit confirmation/verified checkpoint và idempotency check. Grading key không được đưa nguyên bản hoặc qua dereferenceable handle vào model context.

### 5.1 Tool I/O schemas

Contracts đặt tại `src/risk_dashboard/modules/learning/schemas/agent_tools.py`, dùng Pydantic v2. Các ID trong input là resource references, không phải authority.

```python
from typing import Literal
from pydantic import BaseModel, Field

class SourceRef(BaseModel):
    source_id: str
    content_version: str
    section_id: str | None = None

class ProgressItem(BaseModel):
    lesson_id: str
    status: str
    quiz_score: int | None = None
    attempt_count: int
    updated_at: str

class GetContextInput(BaseModel):
    schema_version: str = "1.0.0"
    lesson_id: str
    section_id: str | None = None
    locale: str = "vi-VN"

class GetContextOutput(BaseModel):
    schema_version: str = "1.0.0"
    lesson_id: str
    title: str
    canonical_content: tuple[str, ...]
    objectives: tuple[str, ...] = ()
    sources: tuple[SourceRef, ...]
    publication_status: Literal["published"]

class GetProgressInput(BaseModel):
    schema_version: str = "1.0.0"
    path_id: str
    lesson_id: str | None = None

class GetProgressOutput(BaseModel):
    schema_version: str = "1.0.0"
    path_id: str
    items: tuple[ProgressItem, ...]
    completion_pct: int = Field(ge=0, le=100)

class GetQuizItemInput(BaseModel):
    schema_version: str = "1.0.0"
    lesson_id: str
    difficulty: str | None = None

class GetQuizItemOutput(BaseModel):
    schema_version: str = "1.0.0"
    checkpoint_id: str
    lesson_id: str
    prompt: str
    options: tuple[str, ...]
    expires_at: str

class GradeCheckpointInput(BaseModel):
    schema_version: str = "1.0.0"
    checkpoint_id: str
    response: str

class GradeCheckpointOutput(BaseModel):
    schema_version: str = "1.0.0"
    checkpoint_id: str
    lesson_id: str
    passed: bool
    score: int = Field(ge=0, le=100)
    rubric_evidence: tuple[str, ...]
    misconceptions: tuple[str, ...] = ()
    verified_event_id: str

class UpdateProgressInput(BaseModel):
    schema_version: str = "1.0.0"
    verified_event_id: str
    idempotency_key: str
    confirmation_id: str

class UpdateProgressOutput(BaseModel):
    schema_version: str = "1.0.0"
    receipt_id: str
    lesson_id: str
    status: str
    quiz_score: int | None = None
    updated_at: str

class RecommendNextInput(BaseModel):
    schema_version: str = "1.0.0"
    path_id: str
    limit: int = Field(default=3, ge=1, le=10)

class RecommendedItem(BaseModel):
    lesson_id: str
    title: str
    rank: int = Field(ge=1)
    rationale: str

class RecommendNextOutput(BaseModel):
    schema_version: str = "1.0.0"
    path_id: str
    items: tuple[RecommendedItem, ...]
```

Invariant: `GetQuizItemOutput` và `GradeCheckpointOutput` **không có** `correct_answer`, grading key, rubric bí mật hoặc key handle. `checkpoint_id` là opaque, account-bound, TTL-bound token chỉ grading service server-side resolve.

### 5.2 Real-dependency mapping

| Contract/tool | Live code hôm nay | WP |
|---|---|---|
| `learning.get_context` | `GetLearningLesson.execute()` (`application/query_handler.py:122-142`) → `SqliteLearningCatalog.get_lesson()` (`infrastructure/catalog_reader.py:123-130`, `189-194`) | LEA0–LEA1 |
| `learning.get_progress` | `LearningProgressRepository.get_progress/list_by_path` (`domain/ports.py:49-60`) → `SqliteLearningHomeRepository` (`infrastructure/repositories/sqlite.py:74-120`) | LEA0–LEA1 |
| `learning.get_quiz_item` | Question shape `LearningQuizQuestion` (`domain/entities.py:12-18`); lesson resolver includes quiz questions (`infrastructure/catalog_reader.py:211-229`) | LEA4 — protected selector mới |
| `learning.grade_checkpoint` | Current combined grade/write flow `SubmitLearningQuiz.execute()` (`application/query_handler.py:145-196`); Telegram handler also grades in process (`application/quiz_handler.py:138-154`) | LEA4 — tách protected grading khỏi write |
| `learning.update_progress` | `quiz_progress()` được gọi trước `save_progress()` (`application/query_handler.py:158-171`); repository upsert (`infrastructure/repositories/sqlite.py:122-149`) | LEA4 — confirmed/idempotent adapter mới |
| `learning.recommend_next` | `GetLearningHome.execute()` combines catalog/progress (`application/query_handler.py:53-99`); catalog list/path APIs (`infrastructure/catalog_reader.py:123-173`) | LEA1 |

Lưu ý: `LearningDeliveryRepository` chỉ dedupe Telegram card delivery (`infrastructure/delivery_repository.py:27-60`), không lưu learning progress. `QuizSessionRepository` chỉ bảo vệ Telegram session ownership/expiry/atomic answer (`infrastructure/quiz_repository.py:30-128`), không phải checkpoint mastery repository.

## 6. Skills và orchestration

Skill manifests đầu tiên:

- `learn.explain.v1`;
- `learn.socratic_hint.v1`;
- `learn.formula_walkthrough.v1`;
- `learn.check_misconception.v1`;
- `learn.run_checkpoint.v1`;
- `learn.next_step.v1`.

Router ưu tiên deterministic match theo UI intent. Quant/Risk specialist chỉ được handoff khi lesson chứa công thức/risk concept cần tool; reviewer kiểm grounding và numeric claims trước response.

## 7. Knowledge và memory

- Published Learning/CMS content là source of truth.
- Knowledge index/FTS là derived cache có content/version/source IDs; MVP chưa cần vector DB.
- Working memory giữ current lesson, recent turns và unresolved question.
- Durable memory chỉ giữ explicit teaching preference, accepted goal, verified mastery/misconception.
- Progress không duplicate thành semantic memory; đọc live từ Learning repository.
- Summary cũ phải thua content version mới và live progress.

## 8. Work packages

| ID | Work package | Deliverable | Exit evidence |
|---|---|---|---|
| LEA0 | Identity/content contract | canonical principal and versioned context | ownership/version tests |
| LEA1 | Read tools | context, progress, catalog, sources | contract and latency tests |
| LEA2 | Retrieval | chunking/FTS, ACL, citations, freshness | retrieval gold set |
| LEA3 | Teaching skills | explain/hint/formula/misconception | pedagogy eval |
| LEA4 | Checkpoint path | protected grading, verified progress update | no-answer-leak + integration tests |
| LEA5 | Embedded UI | contextual panel, source, limitations, artifact card | accessible E2E |
| LEA6 | Memory/personalization | explicit preferences + verified mastery proposals | memory precision/privacy tests |
| LEA7 | Rollout | internal → 5% → 25% → 100% with flags | KPI and rollback review |
| LEA8 | Gold-set specification | size ≥100 câu, composition factual/numeric/reasoning/unsafe/tool-failure/injection, refresh cadence + owner | gold-set spec approved + baseline eval run |

### 8.0 Thứ tự bắt buộc (dependency-ordered)

- `LEA0` freeze identity, ownership và schema `1.0.0`; block mọi public agent tool.
- `LEA1` bọc read tools sau LEA0; `LEA2` bắt đầu khi provenance/version contract của `get_context` ổn định.
- `LEA3` cần LEA1 + AI Runtime/Agentic Core (docs 02/00); không được import provider SDK trực tiếp.
- `LEA4` cần LEA0, LEA1 và protected checkpoint store; phải tách grade khỏi write trước khi expose tool.
- `LEA5` cần LEA3 + LEA4; UI chỉ gọi scoped tools qua AI Tutor/Agentic Core.
- `LEA6` cần verified event từ LEA4; model output tự do không tạo mastery.
- `LEA8` freeze trước rollout; `LEA7` chỉ bắt đầu khi LEA3–LEA6 và baseline eval LEA8 đạt gate.

### 8.1 Acceptance test + Definition of Done per WP

| WP | Acceptance test | Definition of Done |
|---|---|---|
| LEA0 | Tool từ chối client-supplied account authority; cross-account resource refs không resolve; mọi root schema round-trip với `schema_version="1.0.0"` | `AuthPrincipal` server-resolved; contracts freeze tại `src/risk_dashboard/modules/learning/schemas/agent_tools.py`; ownership/version policy có contract tests |
| LEA1 | Sáu adapters chạy bằng fake/live repositories; read tools chỉ trả published content và account-scoped progress; p95 theo budget đã chốt | `agent_tools.py` đăng ký scoped signatures §5; không duplicate catalog/progress logic; real-dependency mapping được giữ đúng |
| LEA2 | Gold retrieval set kiểm đúng source/version; deleted/unpublished/stale content không xuất hiện; malicious content không thành instruction | Chunk/FTS derived cache rebuildable; ACL, citation và freshness enforced; không bắt buộc vector DB |
| LEA3 | Explain/hint/formula/misconception pass pedagogy fixtures; hint leakage = 0; numeric claims có evidence | Sáu versioned skill manifests; deterministic UI intent routing; reviewer grounding/numeric chạy trước response |
| LEA4 | `GetQuizItemOutput`/`GradeCheckpointOutput` không chứa answer key; wrong account/expired checkpoint bị từ chối; grade failure tạo 0 write; duplicate idempotency key tạo 1 receipt | Protected grading service server-side; grade và progress write tách biệt; `update_progress` confirmed + idempotent; migration additive theo `platform/database/migrate.py:137-145`, `183-210` |
| LEA5 | E2E lesson → panel → hint/checkpoint → receipt; keyboard-only, screen-reader labels, focus restore và source disclosure pass | Embedded panel có loading/error/limitations; CSP-safe rendering; deterministic Learn vẫn dùng được khi agent off |
| LEA6 | Chỉ verified checkpoint tạo mastery proposal; memory disabled tạo 0 durable row; delete/forget propagation pass | Durable memory chỉ explicit preference/goal/verified mastery; progress luôn đọc live, không duplicate semantic memory |
| LEA7 | Internal → 5% → 25% → 100% chỉ advance khi KPI/security/cost gates pass; kill switch rollback không mất deterministic Learn | Feature flags, dashboard, owner, rollback runbook và go/no-go receipts được phê duyệt |
| LEA8 | ≥100 cases chạy baseline, gồm factual/numeric/reasoning/unsafe/tool-failure/injection và two-account isolation | Dataset versioned; composition, expected evidence, owner, refresh cadence và threshold được phê duyệt |

## 9. Eval suite

Gold set phải bao phủ:

- lesson fact grounding và content version;
- công thức/units/substitution;
- hints không lộ đáp án;
- beginner vs advanced explanation;
- ambiguous question and correct clarification;
- misconception detection without overclaim;
- malicious lesson text/prompt injection;
- stale/deleted/unpublished lesson;
- two-account progress isolation.

Metrics: grounded citation rate, checkpoint uplift, completion, hint usefulness, answer leakage, retrieval precision, p95 latency và cost/verified session.

## 10. Security and failure behavior

- unpublished/admin content chỉ dùng với authorized principal;
- sanitize lesson Markdown/HTML before display;
- retrieved text là data, không phải instructions;
- quiz answer keys stay server-side;
- if retrieval fails, agent asks user to retry or gives clearly labeled general explanation;
- if grading fails, no progress write;
- idempotency prevents duplicate completion.

## 11. Definition of Done

- Learn vertical slice chạy từ lesson context đến checkpoint/progress receipt.
- Citation trỏ đúng content source/version.
- Mastery không thể tăng bằng free-form model output.
- Memory disabled path không ghi long-term profile.
- Security, pedagogy, retrieval, latency and cost gates pass.
- Learn remains usable without agent via deterministic existing flow.

## 12. Open decisions

- Pilot curriculum and language?
- Checkpoint bank ownership and review workflow?
- Exact mastery model and expiry/decay?
- Instructor visibility over aggregate progress?
- Gold-set size final là bao nhiêu?
- Ai owns gold-set curation?
- Refresh cadence của gold-set?

## 13. Validation checkpoint

Entry criteria:

- gold-set spec approved;
- checkpoint grading contract defined.

Exit criteria (quantitative):

- checkpoint grade p50 < 500ms, p95 < 1s;
- grading accuracy validated vs gold-set;
- ≥1 complete learning session E2E (lesson → checkpoint → progress → memory);
- numeric coverage 100% cho quantitative lessons.

Validation gate: maps to VP-AT3.

