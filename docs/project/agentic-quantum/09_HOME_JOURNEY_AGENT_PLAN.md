# 09 — Home Journey / Next-Best-Action Agent Plan

> Capability owner đích: `src/risk_dashboard/modules/home_onboarding/` (registered surface slug `home`)
> Dependencies: Identity/Trust (doc 01), Agentic Core (doc 00), Shared AI Runtime (doc 02), reviewed domain-summary producers
> Roadmap liên quan: EA5
> Trạng thái: **EXTEND, không greenfield** — Home/onboarding, SQLite repositories, deterministic route và `GET /api/v1/public/home/{session_id}` đã tồn tại; canonical principal, consent gate, versioned cross-surface summaries và journey artifact chưa tồn tại.

## 0. Reality note — đọc trước khi code

| Claim | Hiện trạng live đã verified | Hệ quả |
|---|---|---|
| Home surface | Package thật là `src/risk_dashboard/modules/home_onboarding/`; module đăng ký `id="home"`, mount `/api/v1/public`, phụ thuộc `learning` tại `src/risk_dashboard/modules/home_onboarding/module.py:3-22` | Extend package này; **không** tạo song song `modules/home/` trong MVP |
| Home API | `GET /home/{session_id}` nhận identity từ path và gọi `GetHomeState.execute(session_id=...)` tại `src/risk_dashboard/modules/home_onboarding/api/public.py:77-89` | Đây là compatibility endpoint có IDOR risk; HOME1 thêm authenticated `/api/v1/me/home-journey`, sau đó deprecate path identity theo ID1/ID5 |
| Current aggregation | `GetHomeState` đọc profile/state theo `session_id`, optional Learn reader, legacy health/goal readers tại `src/risk_dashboard/modules/home_onboarding/application/services.py:199-263` | Không coi đây là authorized cross-surface aggregation; thay bằng principal-scoped compact-summary ports |
| Current selection | Health/goal/Learn conditionals overwrite `next_best_action_*` theo thứ tự tại `src/risk_dashboard/modules/home_onboarding/application/services.py:236-262` | Có deterministic behavior nhưng chưa có candidate schema, explainability, cooldown, version pin hoặc audit |
| Current response | `HomeResponse` trả scalar `next_best_action_type/ref`, blocks và health/goal/community snapshots; chưa có `schema_version`, source refs, expiry, consent metadata tại `src/risk_dashboard/modules/home_onboarding/schemas/responses.py:73-85` | Giữ response cũ trong compatibility window; endpoint mới trả contract v1 bên dưới |
| Current preview | Nếu onboarding chưa xong, endpoint trả deterministic guest preview tại `src/risk_dashboard/modules/home_onboarding/api/public.py:86-89`; preview dựng default cautious persona tại `application/services.py:307-330` | Guest chỉ dùng static/onboarding state, không personal memory hoặc domain summary |
| Identity/consent | Canonical `AuthPrincipal`/`ConsentSnapshot` là deliverable ID1/ID3, chưa phải live contract (doc 01 §3.1) | HOME personalized path bị block bởi ID1+ID3; không dùng `session_id` client truyền làm authority |
| Agent substrate/runtime | `modules/agentic_core/` và `platform/ai_runtime/` là greenfield (doc 00 §0; doc 02 §0) | Ranking v1 không cần model. HOME6 explanation model chỉ mở sau AC0/AC2/AC6 + AIR0/AIR1/AIR3/AIR4 |
| Background autonomy | Không có approved bounded Home job substrate | MVP chỉ chạy khi authenticated Home load hoặc explicit refresh; **không daemon, cron, notification, mutation, simulation hoặc background agent run** |

## 1. Capability, scope, hard boundaries

Home Journey biến Home thành điểm tiếp tục hành trình bằng cách đọc **compact, reviewed, version-pinned summaries** sau canonical identity và explicit memory/personalization consent, rồi chọn **đúng một** next-best learning/research action.

Trong scope:

- resolve server-side `AuthPrincipal` và consent snapshot;
- đọc summary tối thiểu qua domain-owned ports, không raw tables/payloads;
- validate ownership, review status, schema version, TTL và entitlement;
- deterministic eligibility/ranking/cooldown;
- trả một `NextBestActionCardV1` có nguồn, lý do, hạn dùng, CTA và controls;
- dismiss/snooze/complete feedback do user chủ động;
- optional model rewrite của **rationale đã chọn**, không được đổi action.

Ngoài scope/cấm tuyệt đối:

- raw conversation, raw report, full portfolio/position, income/net-worth/health payload, hidden operator data;
- inference wealth, income, distress, risk tolerance, buy/sell intent hoặc sensitive financial state;
- investment recommendation, manipulative urgency, notification push;
- background autonomous action, domain mutation, simulation execution, order execution;
- model-generated candidate, arbitrary URL/tool, durable memory write trực tiếp;
- Home tự tính domain formula hoặc truy vấn raw domain repository.

## 2. Data flow và trust boundary

```text
Authenticated GET/explicit refresh
  → ResolveSession/AuthPrincipal (ID1; account_id/scopes server-resolved)
  → ConsentSnapshot (ID3; purpose="home_personalization", policy version current)
  → HomeJourneyContextBuilder
      → onboarding/profile repository (own account only)
      → DomainSummaryReader ports (compact reviewed summaries only)
      → recent feedback/cooldown repository (own account only)
  → schema/version + ownership + review + TTL + entitlement filters
  → deterministic CandidateFactory
  → deterministic Ranker (stable tie-break)
  → exactly one selected candidate or typed empty state
  → optional ExplanationComposer (selected fields only; HOME6 gate)
  → HomeJourneyResponseV1
  → user CTA navigates to owning domain; Home performs no domain action
```

| Component | Enters | Transform | Exits/failure |
|---|---|---|---|
| Auth/consent guard | credential/cookie | resolves account, scopes, consent purpose/version | `AuthPrincipal`; 401/403/consent-required, no summary read |
| Context builder | principal, locale, flags | account-scoped reads; max 20 summaries/32 KB | context; unavailable producer omitted with reason |
| Summary validator | compact summaries | schema, owner, review, TTL, entitlement | eligible summaries; safe rejection metric |
| Candidate factory | summaries + onboarding + feedback | maps allowlisted state to allowlisted CTA | candidate list; no free-form route |
| Ranker | candidates | priority → continuity → freshness → stable ID | exactly 0 or 1 candidate |
| Explanation | selected candidate only | template; optional constrained paraphrase | grounded rationale; template fallback |
| Feedback | card id + action | ownership/idempotency/expiry | event receipt; no inferred preference |

Consent invariant: without current `home_personalization=true`, return non-personalized onboarding/static Home. `memory=false` means no durable memory read/write. Revocation applies next request and invalidates account cards.

## 3. Concrete versioned schemas — v1.0.0

Schemas live at `src/risk_dashboard/modules/home_onboarding/schemas/journey.py`, Pydantic v2. Root contracts pin `schema_version="1.0.0"`; unknown major versions reject.

```python
from typing import Literal
from pydantic import BaseModel, Field

Surface = Literal["learn", "bctc", "simulation", "news", "market"]

class SummarySourceRefV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    surface: Surface
    resource_type: str
    resource_id: str
    resource_version: int = Field(ge=1)

class HomeDomainSummaryV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    summary_id: str
    account_id: str                    # internal, never serialized to client
    surface: Surface
    kind: Literal["learning_progress", "research_artifact", "stale_artifact", "market_education"]
    title: str = Field(max_length=120)
    compact_summary: str = Field(max_length=500)
    source_ref: SummarySourceRefV1
    review_status: Literal["reviewed", "accepted"]
    review_policy_version: str
    allowed_action_type: str
    allowed_cta_path: str
    state: Literal["incomplete", "open_question", "stale", "ready"]
    created_at: str
    updated_at: str
    expires_at: str

class ExplicitHomeMemoryV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    memory_id: str
    memory_type: Literal["preference", "goal", "mastery"]
    value: str = Field(max_length=200)
    provenance: Literal["user_stated", "user_approved_plan", "deterministic_checkpoint"]
    verified: bool
    consent_policy_version: str
    expires_at: str | None = None

class JourneyContextV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    account_id: str                    # internal only
    principal_scopes: tuple[str, ...]
    consent_policy_version: str
    personalization_consented: bool
    memory_consented: bool
    locale: str = "vi-VN"
    onboarding_state: str
    summaries: tuple[HomeDomainSummaryV1, ...] = ()
    explicit_memories: tuple[ExplicitHomeMemoryV1, ...] = ()
    dismissed_candidate_ids: tuple[str, ...] = ()
    snoozed_until_by_candidate: dict[str, str] = {}
    available_surfaces: tuple[Surface, ...] = ()
    built_at: str

class NextBestActionCardV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    card_id: str
    candidate_id: str
    action_type: str
    target_surface: Surface
    target_ref: SummarySourceRefV1
    title: str = Field(max_length=120)
    why_now: str = Field(max_length=300)
    source_summary_ids: tuple[str, ...]
    estimated_minutes: int | None = Field(default=None, ge=1, le=180)
    limitations: tuple[str, ...] = ()
    cta_label: str = Field(max_length=80)
    cta_path: str
    created_at: str
    expires_at: str
    dismissible: bool = True
    snooze_options_hours: tuple[int, ...] = (24, 72, 168)

class HomeJourneyResponseV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    generated_at: str
    mode: Literal["personalized", "non_personalized", "empty"]
    next_best_action: NextBestActionCardV1 | None
    stale_sources_omitted: int = 0
    consent_required: bool = False

class HomeJourneyFeedbackRequestV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    action: Literal["dismiss", "snooze", "complete"]
    snooze_hours: Literal[24, 72, 168] | None = None
    idempotency_key: str = Field(min_length=8, max_length=128)

class HomeJourneyFeedbackReceiptV1(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    receipt_id: str
    card_id: str
    status: Literal["recorded", "duplicate", "expired", "not_found"]
    recorded_at: str
```

Invariants: summary account must equal principal; only reviewed/accepted and non-expired enter ranking; action/CTA must match server registry; memory requires current personalization+memory consent and `verified=true`; response cardinality is 0..1; client never sends authority fields.

## 4. Exact package/file plan

```text
src/risk_dashboard/modules/home_onboarding/
├── api/public.py                         # legacy compatibility only
├── api/journey.py                        # authenticated journey + feedback
├── application/services.py               # preserve legacy services; wiring migration only
├── application/journey_context.py
├── application/journey_candidates.py
├── application/journey_ranker.py
├── application/journey_service.py
├── application/journey_feedback.py
├── application/journey_explanation.py
├── domain/journey.py
├── domain/journey_ports.py
├── domain/home_action_registry.py
├── schemas/journey.py
├── infrastructure/sqlite_journey.py
├── infrastructure/summary_adapters/{learning,bctc,simulation,news,market}.py
└── module.py

src/risk_dashboard/platform/database/migrate.py
src/risk_dashboard/platform/database/schema/baseline.sql
tests/unit/home_onboarding/test_journey_{schemas,ranker,consent}.py
tests/integration/home_onboarding/test_journey_{api,summaries}.py
tests/security/test_home_journey_isolation.py
tests/e2e/test_home_journey.py
```

File ownership: HOME0 schemas/ports/registry; HOME1 authenticated API; HOME2 adapters; HOME3 context; HOME4 candidates/ranker; HOME5 persistence/feedback/migrations; HOME6 explanation; HOME7 `module.py`, legacy integration and UI. Không hai WP song song sửa cùng file.

## 5. Endpoints, tool signatures, scopes, risk classes

| Method + path | Contract | Scope | Effect |
|---|---|---|---|
| `GET /api/v1/me/home-journey` | `refresh: bool=false` → `HomeJourneyResponseV1` | `me:home_journey:read` | bounded synchronous read; refresh is explicit, not background |
| `POST /api/v1/me/home-journey/cards/{card_id}/feedback` | request → receipt | `me:home_journey:feedback` | account-scoped idempotent event write |
| `DELETE /api/v1/me/home-journey/personalization` | 204 | `me:preferences:write` | delegates ID3 consent workflow; invalidates cards |
| `GET /api/v1/public/home/{session_id}` | existing `HomeResponse` | `public:home:read` | legacy only; no summaries/memory |

```python
class HomeSummaryReader(Protocol):
    surface: str
    def list_reviewed_summaries(
        self, *, account_id: str, scopes: tuple[str, ...], as_of: str, limit: int = 4
    ) -> tuple[HomeDomainSummaryV1, ...]: ...

async def get_home_journey_context(
    *, envelope: TrustedExecutionEnvelope
) -> JourneyContextV1: ...

async def select_home_next_best_action(
    *, envelope: TrustedExecutionEnvelope, context: JourneyContextV1
) -> NextBestActionCardV1 | None: ...
```

| Tool | Scope | Risk class | Constraint |
|---|---|---|---|
| `home.get_journey_context.v1` | `me:home_journey:read` | `read` | account from envelope; max 20/32 KB |
| `home.select_next_best_action.v1` | `me:home_journey:read` | `read` | deterministic, 0..1 action |
| `home.record_feedback.v1` | none | `forbidden` | feedback only via explicit REST control |
| mutation/simulation/order/notification | none | `forbidden` | no proposal in Home MVP |

## 6. Ranking v1

```text
consent → ownership → schema allowlist → reviewed/accepted → unexpired
→ entitlement → CTA registry → cooldown/dismiss → priority → continuity
→ freshness → stable candidate_id tie-break → select first only
```

Priority: verified incomplete Learn checkpoint; accepted research artifact with explicit open question; stale reviewed artifact with refresh CTA; explicit onboarding goal mapped to education; reviewed market education. Forbidden signals: inferred urgency, wealth/income, portfolio loss, inferred risk tolerance, sentiment, engagement addiction score, operator notes.

`candidate_id = sha256(surface + resource id/version + action_type + policy_version)`. Card TTL is `min(summary expiry, 24h)`. Policy version `home-ranking-v1`; changes require golden-test and product/privacy review.

## 7. Persistence, compatibility, rollback

Additive tables: `home_journey_cards(card_id PK, account_id, candidate_id, schema_version, source_refs_json, action_json, policy_version, created_at, expires_at, invalidated_at)` and `home_journey_feedback(receipt_id PK, account_id, card_id, action, snooze_until, idempotency_key, created_at, UNIQUE(account_id,idempotency_key))`. Store refs/rendered card only, never raw summary/memory/model response. Every query includes `account_id`.

Compatibility: keep existing response/endpoint unchanged; new endpoint behind `module.home_journey.v1.enabled=false`; authenticated UI prefers new endpoint and falls back to current static blocks, never path identity; no raw historical backfill; remove legacy authenticated usage only after ID1/ID5 and 30 zero-caller days.

Rollback per phase: HOME0–4 flag off; HOME5 disable writes and retain additive tables through rollback window; HOME6 disable rationale flag; HOME7 client reverts to current Home. Do not drop tables during incident rollback. Consent revoke/kill switch invalidates cards without cascading domain deletion.

## 8. Real dependency map

```text
ID1 AuthPrincipal + ID2 ownership + ID3 consent → HOME1 → HOME3
HOME0 → HOME1, HOME2, HOME4
HOME1 + HOME2 + HOME3 + HOME4 → HOME5 → HOME7
AC0+AC2+AC6 + AIR0+AIR1+AIR3+AIR4 + HOME4 → HOME6(optional) → HOME7
```

| Need | Live path/symbol | Status |
|---|---|---|
| orchestration | `GetHomeState`, `application/services.py:199-304` | extend/migrate with parity |
| route | `api/public.py:77-89` | legacy compatibility |
| Learn read | `application/services.py:225-230` | seed adapter; must become principal-scoped v1 summary |
| repository | `domain/ports.py:31-38` | session-scoped, insufficient for journey |
| module wiring | `module.py:4-22` | HOME7 integration; currently depends only Learn |
| identity/consent | doc 01 ID1/ID3 | blocker |
| grants/audit | doc 00 AC0/AC2/AC6 | blocker only for optional tool/model path |
| provider | doc 02 AIR0/AIR1/AIR3/AIR4 | blocker only for optional rationale |
| other summaries | no frozen v1 producers live | enable separately after contract/privacy review |

Pilot may be Learn-only. Không claim all-domain personalization before every enabled producer passes shared account-scoped contract suite.

## 9. Ordered WPs — acceptance, DoD, risk, rollback

| WP | Dependencies / owner files | Acceptance + measurable DoD | Risk and mitigation | Rollback |
|---|---|---|---|---|
| HOME0 contracts | none; schemas/ports/registry | round-trip; reject unknown major/expired/unreviewed/arbitrary CTA; v1 + policy reviewed | High×High sensitive leak; allowlist/max lengths/privacy review | revert, no data |
| HOME1 identity | HOME0, ID1–3; `api/journey.py` | spoofed identity fails; no consent means zero reader calls; endpoint typed, legacy unchanged | High×High IDOR; principal + two-account collision suite | flag off |
| HOME2 summaries | HOME0–1; adapters | each ≤4 compact reviewed own-account summaries; stale/deleted/revoked omitted; Learn first | High×High raw ingestion; per-surface allowlist/flag/review | disable surface |
| HOME3 context | HOME1–2; `journey_context.py` | revoke excludes data; memory off excludes memory; ≤20/32 KB; request-scoped | High×High cache/consent leak; no shared personal cache | non-personalized mode |
| HOME4 ranker | HOME0,3; candidates/ranker | stable winner across 1,000 shuffles; exactly 0..1; forbidden signals inert; compute p95 <50 ms | Medium×High irrelevant nudge; golden corpus/report control | prior policy/empty state |
| HOME5 feedback | HOME4; feedback/sqlite/migrations | duplicate→one receipt; A cannot mutate B; expired safe; no raw payload stored | High×High privacy/write duplication; unique key/account scope | disable writes, retain tables |
| HOME6 rationale | HOME4 + AC/AIR blockers; explanation | IDs/action/CTA unchanged; malformed/timeout fallback; zero invented action eval | High×Medium hallucination/egress; equality validator/redaction/separate flag | disable rationale |
| HOME7 pilot | HOME1–5; integration-owned files/UI | signed-in journey, CTA, dismiss/snooze/revoke, stale source, outage, legacy parity; Learn-only staged pilot | Medium×High critical Home regression; shadow/canary/kill switch | client/API flags off |

## 10. Test matrix and failure modes

| Layer | Required cases | Gate |
|---|---|---|
| Unit/schema/rank | versions, lengths, review/TTL, stable ties, cooldown, forbidden signals | 100% invariants; 0 multi-card |
| Auth/integration | expired credential, spoof, consent lifecycle, producer outage/malformed/deleted | 0 pre-consent reads; partial outage does not fail Home |
| Security/privacy | two accounts with colliding IDs, IDOR, prompt-injection text, log scan | zero leakage; zero raw/sensitive logs |
| Persistence | idempotency, ownership, expiry, invalidation | duplicate side effect 0; expired served 0 |
| Eval | grounding, action equality, urgency/advice | invented/changed action 0; forbidden advice 0 |
| E2E/a11y | onboarding/static→consent→card→CTA→completion; controls/revoke | critical desktop/mobile/keyboard journeys pass |
| Performance | 1/5 producers, warm/cold, concurrency | p50 <150 ms, p95 <800 ms; model-off cost $0 |

Failure behavior: auth ambiguity fails closed; missing consent returns static; producer timeout omits it under 100 ms reader budget; schema/account mismatch rejects and raises payload-free security metric; no candidate returns empty; duplicate feedback returns duplicate; model failure uses deterministic rationale; DB write failure does not trigger domain action; flags restore legacy/static Home.

Observability emits reason codes only (`summary_stale`, `consent_missing`, `candidate_selected`, `empty_state`, `feedback_recorded`), never title, summary, memory value or account ID.

## 11. Success criteria

- 100% new requests use server identity and current consent before personal reads.
- Zero raw conversation/report/portfolio data in context, persistence, logs or model.
- Zero cross-account leak/unauthorized feedback; zero sensitive inference/background action.
- Exactly 0 or 1 action; 100% actions registry/entitlement-valid.
- Ranking replay 100%; model altered/invented action 0.
- p95 API <800 ms without model; no Home render waits for multi-agent run.
- Pilot improves accepted/completed action against existing deterministic baseline without dismiss/report, latency or privacy regression; exact uplift threshold approved before experiment.

## 12. Open decisions

- Product/privacy approval for explicit `home_personalization` purpose/policy version.
- Which producers beyond Learn can emit v1 without sensitive fields.
- ID7/compliance approval for card/feedback retention; 24h is proposed only.
- UI consumer paths must be re-verified and assigned before HOME7; no guessed frontend paths.
- Product uplift threshold and experiment duration.
