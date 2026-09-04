# 07 — News Intelligence Agent Plan

> Domain owner đích: `modules/news_intelligence` (LIVE — extend, không greenfield)
> Shared lib: `modules/market_summary` (KHÔNG có `module.py` — thư viện dùng chung, không phải registered module)
> Phụ thuộc doc: 00 (Agentic Core envelope), 01 (auth/consent/scope), 02 (AI Runtime `LLMProvider`)
> Roadmap: AT1, EA4 — Validation gate VP-AT7
> Trạng thái: **EXTEND LIVE** — ingestion/clustering/enrichment/scoring/safety đã chạy production

## 0. Reality note

| Vùng | Hiện trạng verified | Hành động |
|---|---|---|
| Module registration | `modules/news_intelligence/module.py` — slug `news_intelligence`, dep `("system_surface",)`, flag `module.news_intelligence.enabled`, scope `("public:news:read",)`, mount `/api/v1/public` | REUSE — thêm agent scope, không tạo module mới |
| REST surface | `api/public.py` — `/feed`:22, `/highlights`:51, `/articles/{id}`:60, `/clusters`:72, `/pulse`:99, POST `/articles/{id}/save`:127, DELETE :134, `/saved`:141, `/desk/finnhub`:155, `/source-health`:174 | REUSE làm evidence surface; agent KHÔNG gọi REST, gọi application layer |
| Entities | `domain/entities.py` — `utc_now_iso()`:8, `NewsSource`:12 (frozen), `NewsArticle`:24, `NewsArticle.to_dict()`:59 | REUSE làm nguồn field contract §5.1 |
| Clustering | `application/clustering.py` — `NewsCluster`:29, `cluster_articles(articles, *, limit=20)`:59, `_jaccard`:97, `_velocity`:113 | REUSE cho `news.get_cluster` |
| Enrichment | `application/enrichment.py` — `enrich_article(article)`:45, `_threat`:135, `_content_hash`:144 | REUSE cho `news.get_enrichment` |
| Scoring | `domain/scoring.py` — `calculate_importance(...)`:80, `ImportanceResult`:40, `ImportanceBreakdown`:20; weights 0.35/0.20/0.15/0.10/0.10/0.10 | REUSE — score là **domain output**, agent chỉ giải thích, không tự tính lại |
| Impact mapping | `domain/impact.py` — `map_impact(*, headline, summary, category)`:99, `ImpactMapping`:17, `_MARKET_KEYWORDS` (FX/Rates/VN Equity/US Equity) | REUSE cho affected markets/sectors/monitors/learn links |
| Safety | `safety/news_policy.py` — `SAFETY_BLOCK`, `is_unsafe_query(text)`:44, `build_safety_block()`:49, `build_data_quality_block(...)`:56, `build_analyst_redirect()`:81 | EXTEND — thêm untrusted-content boundary (WP NEWS2) |
| Market context | `modules/market_summary/domain/metrics.py:14 calculate_index_metrics`, `:78 calculate_market_breadth`, `:110 calculate_capital_flow`; `domain/models.py:80 MarketSummaryReport`, `:67 ReportProvenance`, `:10 DataQuality` | REUSE deterministic — shared lib, không phải module |
| Schemas package | **KHÔNG tồn tại** `modules/news_intelligence/schemas/` | NEW — tạo package cho agent tool contracts |
| Brief artifact | Chưa có reviewed brief store | NEW — `NewsEvidenceBrief` + additive migration |

Kết luận reality: News Agent là **explanation layer bọc pipeline đã chạy production**, không greenfield. Mọi số liệu importance/impact/threat do domain code sinh; LLM chỉ diễn giải và trích nguồn.

## 1. Capability

News Agent biến cụm tin thành brief có nguồn: tóm tắt sự kiện, phân tách fact/claim/hypothesis, so sánh nguồn, nêu dữ kiện còn thiếu, liên kết tới lesson/BCTC/market context.

Agent **không** được: dự đoán chắc chắn giá, biến sentiment thành buy/sell recommendation, tự fetch URL tùy ý, tự tính lại importance score, hay coi nội dung article là instruction.

## 2. Evidence từ codebase và khoảng trống

Evidence pipeline có sẵn (tốt hơn để model tự browse):

- ingestion: `application/rss_producer.py`, `application/finnhub_desk.py`;
- clustering: `application/clustering.py` (Jaccard token similarity + velocity);
- enrichment: `application/enrichment.py` (language, priority, sentiment, impact, category refine, tickers, threat, content hash);
- scoring: `domain/scoring.py` (6-factor weighted importance);
- impact: `domain/impact.py` (markets/sectors/monitors/learn links/entities);
- highlights: `application/highlights.py`;
- translation: `application/translation.py`;
- delivery: `application/telegram_digest.py`, `application/telegram_scheduler.py`, `application/query_handler.py:19 NewsTelegramQueryHandler`, `:64 format_news_query_sections`;
- safety: `safety/news_policy.py`.

Khoảng trống phải đóng trong plan này:

| Gap | Chi tiết | WP |
|---|---|---|
| Source contract chưa thống nhất cho agent | `NewsSource` có `tier`/`flag`/`region`/`category` nhưng chưa có license/freshness/health schema versioned | NEWS0 |
| Anonymous identity path chưa tách | chưa phân biệt ephemeral run vs personalized read | NEWS0 |
| Indirect prompt injection chưa threat-model | article text đi thẳng vào prompt, chưa có content boundary | NEWS2 |
| Impact score bị hiểu sai | score là domain output, không phải "sự thật do LLM xác nhận" | NEWS1, NEWS3 |
| Chưa có reviewed brief artifact | không có store/expiry/reviewer status | NEWS4 |
| `schemas/` package không tồn tại | agent tool contracts chưa có nơi freeze | NEWS1 |
| `market_summary` ownership mờ | không có `module.py` → là shared lib | NEWS5 (đã chốt ở §0) |

## 3. User workflows

| Workflow | Input | Output | Write boundary |
|---|---|---|---|
| Explain event | cluster_id / article_id | facts + source links + event/publish timestamp | read-only |
| Compare sources | cluster_id | agreement/disagreement matrix có evidence rows | read-only |
| Impact hypothesis | event + authorized market context | mechanisms/scenarios **labeled hypothesis** | read-only |
| Evidence gap | draft brief | missing facts + stale/low-quality source list | read-only |
| Learning bridge | topic/category | lesson/concept card từ `impact.learn_links` | read-only |
| Research brief | selected cluster(s) | `NewsEvidenceBrief` artifact có expiry | **confirmed_write** (user xác nhận mới lưu) |

Chỉ workflow cuối tạo persistence. Năm workflow đầu chạy hoàn toàn read-only trên evidence có sẵn.

## 4. Required surface context

Mỗi agent turn cần envelope từ Agentic Core (doc 00) gồm: `run_id`, `AuthPrincipal` server-resolved (doc 01), locale, `is_anonymous`, active cluster/article nếu UI đang mở, và feature-flag state `module.news_intelligence.agent.enabled`.

Context KHÔNG được chứa: raw article HTML chưa sanitize, secret của source API, hay bất kỳ client-supplied account authority.

### 4.1 File layout đích

```text
src/risk_dashboard/modules/news_intelligence/
├── module.py                          # EXTEND — thêm agent scope + flag
├── api/
│   └── public.py                      # REUSE — REST surface không đổi
├── application/
│   ├── clustering.py                  # REUSE
│   ├── enrichment.py                  # REUSE
│   ├── highlights.py                  # REUSE
│   ├── translation.py                 # REUSE
│   ├── query_handler.py               # REUSE
│   ├── agent_tools.py                 # NEW — 6 tool adapters (read) + 1 confirmed_write
│   └── brief_builder.py               # NEW — dựng NewsEvidenceBrief từ evidence rows
├── domain/
│   ├── entities.py                    # REUSE — NewsSource/NewsArticle
│   ├── enums.py                        # REUSE
│   ├── scoring.py                     # REUSE — importance là domain output
│   ├── impact.py                      # REUSE — map_impact
│   ├── source_health.py               # NEW — license/freshness/health value objects
│   └── ports.py                       # NEW — BriefRepository, SourceRegistry protocols
├── infrastructure/                    # NEW dir
│   ├── brief_repository.py            # NEW — sqlite NewsEvidenceBrief store
│   └── source_registry.py             # NEW — license/attribution inventory reader
├── safety/
│   ├── news_policy.py                 # EXTEND — untrusted content boundary
│   └── content_boundary.py            # NEW — sanitize + label article text
└── schemas/                           # NEW package (chưa tồn tại)
    ├── __init__.py                    # NEW
    └── agent_tools.py                 # NEW — Pydantic v2 tool I/O contracts
```

## 5. Domain tools

| Tool | Input schema | Output schema | Required scope | Risk-class |
|---|---|---|---|---|
| `news.get_cluster` | `GetClusterInput` | `GetClusterOutput` | `public:news:read` | read |
| `news.get_source_health` | `GetSourceHealthInput` | `GetSourceHealthOutput` | `public:news:read` | read |
| `news.get_enrichment` | `GetEnrichmentInput` | `GetEnrichmentOutput` | `public:news:read` | read |
| `news.compare_sources` | `CompareSourcesInput` | `CompareSourcesOutput` | `public:news:read` | read |
| `news.get_market_context` | `GetMarketContextInput` | `GetMarketContextOutput` | `public:market_summary:read` | read |
| `news.build_brief_evidence` | `BuildBriefEvidenceInput` | `BuildBriefEvidenceOutput` | `public:news:read` | read |
| `news.save_brief` | `SaveBriefInput` | `SaveBriefOutput` | `public:news:write` | confirmed_write |
| *(mọi HTTP fetch tùy ý)* | — | — | — | **forbidden** |

Ràng buộc bắt buộc: model không có network tool trong MVP. Article content là **untrusted data**; nội dung article không thể mở rộng tool permission, không thể thay đổi instruction, không thể yêu cầu thêm scope.

### 5.1 Tool I/O schemas

`src/risk_dashboard/modules/news_intelligence/schemas/agent_tools.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0.0"

ImportanceLabel = Literal["critical", "high", "medium", "low", "noise"]
Sentiment = Literal["positive", "neutral", "negative"]
Impact = Literal["high", "medium", "low"]
ThreatLevel = Literal["normal", "watch", "elevated", "critical"]
ClaimKind = Literal["fact", "source_claim", "hypothesis"]


class SourceRef(BaseModel):
    schema_version: str = SCHEMA_VERSION
    source_id: str
    name: str
    url: str
    tier: int = Field(ge=1, le=5)
    region: str
    category: str
    license_class: Literal["open", "attribution_required", "licensed", "restricted"]
    attribution_text: str | None = None
```

```python
class ArticleRef(BaseModel):
    schema_version: str = SCHEMA_VERSION
    article_id: str
    headline: str
    summary: str
    source: SourceRef
    published_at: str          # ISO-8601 UTC, khớp NewsArticle.published_at
    fetched_at: str            # ISO-8601 UTC, khớp NewsArticle.fetched_at
    sort_ts: int               # epoch seconds, khớp NewsArticle.sort_ts
    language: Literal["vi", "en"]
    tickers: tuple[str, ...] = ()
    content_hash: str
    is_untrusted_content: Literal[True] = True


class ImportanceBreakdownOut(BaseModel):
    """Mirror domain/scoring.py:20 ImportanceBreakdown — không tính lại ở LLM."""

    market_impact: int = Field(ge=0, le=100)
    source_reliability: int = Field(ge=0, le=100)
    freshness: int = Field(ge=0, le=100)
    novelty: int = Field(ge=0, le=100)
    severity: int = Field(ge=0, le=100)
    breadth: int = Field(ge=0, le=100)


class ImportanceOut(BaseModel):
    schema_version: str = SCHEMA_VERSION
    score: int = Field(ge=0, le=100)
    label: ImportanceLabel
    breakdown: ImportanceBreakdownOut
    method_version: str        # version của scoring weights, bắt buộc để audit


class GetClusterInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_id: str
    max_articles: int = Field(default=8, ge=1, le=20)


class GetClusterOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_id: str
    similarity_topic: str
    velocity: Literal["fast", "steady", "slow"]
    article_count: int = Field(ge=1)
    source_count: int = Field(ge=1)
    is_breaking: bool
    lead_article: ArticleRef
    articles: tuple[ArticleRef, ...]
    importance: ImportanceOut
    window_start: str          # ISO-8601 UTC
    window_end: str            # ISO-8601 UTC
```

```python
class GetSourceHealthInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    source_ids: tuple[str, ...] = ()          # rỗng = toàn bộ pilot inventory


class SourceHealthRow(BaseModel):
    source: SourceRef
    is_available: bool
    last_success_at: str | None               # ISO-8601 UTC
    staleness_minutes: int = Field(ge=0)
    error_rate_24h: float = Field(ge=0.0, le=1.0)
    quality_flag: Literal["ok", "degraded", "unreliable"]
    redistribution_allowed: bool


class GetSourceHealthOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    rows: tuple[SourceHealthRow, ...]
    evaluated_at: str                          # ISO-8601 UTC
    coverage_sufficient: bool                  # False → agent phải abstain


class GetEnrichmentInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    article_id: str


class GetEnrichmentOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    article_id: str
    sentiment: Sentiment
    impact: Impact
    priority: int = Field(ge=1, le=5)
    category: str
    threat_level: ThreatLevel
    threat_category: str | None = None
    threat_confidence: float = Field(ge=0.0, le=1.0)
    tickers: tuple[str, ...] = ()
    importance: ImportanceOut
    affected_markets: tuple[str, ...] = ()
    affected_sectors: tuple[str, ...] = ()
    what_to_monitor: tuple[str, ...] = ()
    learn_links: tuple[dict[str, str], ...] = ()
    related_entities: tuple[dict[str, str], ...] = ()
    enrichment_method_version: str
```

```python
class CompareSourcesInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_id: str


class ClaimRow(BaseModel):
    claim_id: str
    kind: ClaimKind                            # fact chỉ khi ≥2 nguồn độc lập
    statement: str
    supporting_source_ids: tuple[str, ...]
    conflicting_source_ids: tuple[str, ...] = ()
    first_seen_at: str                         # ISO-8601 UTC
    corroboration_count: int = Field(ge=1)


class CompareSourcesOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_id: str
    claims: tuple[ClaimRow, ...]
    agreement_rate: float = Field(ge=0.0, le=1.0)
    disagreements: tuple[str, ...] = ()        # claim_id có conflict
    single_source_claims: tuple[str, ...] = ()
    evaluated_at: str


class GetMarketContextInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    event_time: str                            # ISO-8601 UTC — align window
    markets: tuple[str, ...] = ()              # từ affected_markets, không tự do


class GetMarketContextOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    as_of: str                                 # ISO-8601 UTC
    session_state: Literal["pre_open", "open", "closed", "holiday"]
    index_metrics: tuple[dict[str, float | str], ...] = ()
    breadth: dict[str, int] | None = None
    capital_flow: dict[str, float] | None = None
    data_quality: Literal["complete", "partial", "stale", "unavailable"]
    provenance: dict[str, str]                 # ReportProvenance shape
    time_aligned: bool                         # False → không được suy luận nhân quả
```

```python
class BuildBriefEvidenceInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    cluster_ids: tuple[str, ...] = Field(min_length=1, max_length=5)
    objective: str = Field(min_length=1, max_length=500)


class EvidenceRow(BaseModel):
    claim_id: str
    statement: str
    kind: ClaimKind
    source_ids: tuple[str, ...]
    article_ids: tuple[str, ...]
    published_at: str
    freshness: Literal["current", "stale", "unknown"]


class BuildBriefEvidenceOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    evidence_rows: tuple[EvidenceRow, ...]
    unresolved_claim_ids: tuple[str, ...] = ()
    source_coverage: float = Field(ge=0.0, le=1.0)
    limitations: tuple[str, ...] = ()
    expires_at: str


class SaveBriefInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    proposal_id: str
    evidence_hash: str
    title: str = Field(min_length=1, max_length=160)
    objective: str = Field(min_length=1, max_length=500)
    evidence_rows: tuple[EvidenceRow, ...]
    limitations: tuple[str, ...] = ()


class SaveBriefOutput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    brief_id: str
    artifact_id: str
    receipt_id: str
    version: int = Field(ge=1)
    status: Literal["saved"] = "saved"
    created_at: str
    expires_at: str
```

`SaveBriefInput` không nhận `account_id`, scope hoặc reviewer status. Executor bind identity từ `TrustedExecutionEnvelope`; `ActionProposal.payload_preview` phải hiển thị title, cluster IDs, evidence count, expiry và limitations. Khi confirm, server re-resolve identity, scope, evidence hash và proposal TTL trước khi gọi repository.

### 5.2 Application signatures

```python
async def get_cluster(input: GetClusterInput, envelope: TrustedExecutionEnvelope) -> GetClusterOutput: ...
async def get_source_health(input: GetSourceHealthInput, envelope: TrustedExecutionEnvelope) -> GetSourceHealthOutput: ...
async def get_enrichment(input: GetEnrichmentInput, envelope: TrustedExecutionEnvelope) -> GetEnrichmentOutput: ...
async def compare_sources(input: CompareSourcesInput, envelope: TrustedExecutionEnvelope) -> CompareSourcesOutput: ...
async def get_market_context(input: GetMarketContextInput, envelope: TrustedExecutionEnvelope) -> GetMarketContextOutput: ...
async def build_brief_evidence(input: BuildBriefEvidenceInput, envelope: TrustedExecutionEnvelope) -> BuildBriefEvidenceOutput: ...
async def save_brief(input: SaveBriefInput, envelope: TrustedExecutionEnvelope) -> SaveBriefOutput: ...
```

Tool adapter chỉ orchestration/shape conversion; domain calculation tiếp tục ở `clustering.py`, `enrichment.py`, `scoring.py`, `impact.py` và `market_summary/domain/metrics.py`.

## 6. API và capability contract

Agentic trigger dùng shared endpoint doc 00, không tạo endpoint prompt tự do trong News:

| Endpoint | Input | Output | Scope | Risk-class |
|---|---|---|---|---|
| `POST /api/v1/public/agentic/runs` với `capability_id="news.evidence_brief.v1"` | shared `CreateAgentRunRequest`; resource locator `cluster_id`/`article_id` | shared `AgentRun` + reviewed brief artifact | `public:news:read` | read |
| `GET /api/v1/public/agentic/runs/{run_id}` | path `run_id` | shared `AgentRun` | ownership + `public:news:read` | read |
| `GET /api/v1/public/agentic/artifacts/{artifact_id}` | path `artifact_id` | `NewsEvidenceBriefArtifact` | ownership + `public:news:read` | read |
| `POST /api/v1/public/agentic/action-proposals/{proposal_id}:confirm` | one-time confirmation token | `ActionReceipt` + `SaveBriefOutput` ref | `public:news:write` | confirmed_write |
| `POST /api/v1/public/agentic/action-proposals/{proposal_id}:reject` | proposal ID | rejected receipt/status | ownership | proposal |

Existing `/api/v1/public/feed`, `/highlights`, `/articles/{id}`, `/clusters`, `/pulse`, `/source-health` giữ nguyên. Agent không gọi loopback HTTP; application adapter gọi service/domain function trực tiếp.

Capability manifest:

```yaml
capability_id: news.evidence_brief.v1
entry_modes: [embedded, conversational]
required_scopes: [public:news:read]
allowed_tools:
  - news.get_cluster
  - news.get_source_health
  - news.get_enrichment
  - news.compare_sources
  - news.get_market_context
  - news.build_brief_evidence
max_tool_calls: 8
risk_class: read
artifact_type: news_evidence_brief.v1
action_policy: save_requires_confirmation
feature_flag: module.news_intelligence.agent.enabled
```

## 7. Work packages (dependency-ordered)

Thứ tự: `NEWS0 → NEWS1 → NEWS2 → NEWS3 → NEWS4 → NEWS5`. `NEWS1` cần AC0/AC2 (doc 00), ID1 (doc 01) và AIR0/AIR1 (doc 02). `NEWS4` chỉ mở sau khi confirmed-action flow AC5 pass.

| WP | Deliverable | Acceptance test | Definition of Done |
|---|---|---|---|
| NEWS0 | Freeze source/identity contracts và source inventory | anonymous run không đọc saved state; authenticated run chỉ thấy account-owned brief; source thiếu license/health bị `coverage_sufficient=False` | `SourceRef`, `SourceHealthRow`, anonymous policy và source registry `1.0.0` được review; không client-supplied authority |
| NEWS1 | Typed read tools + capability manifest | contract tests cho 6 read tools; fixture domain output giữ nguyên importance/impact; unknown field bị reject | adapters gọi application/domain layer, 0 loopback HTTP, 0 LLM recomputation, manifests chỉ cấp read grants |
| NEWS2 | Untrusted-content boundary | article chứa “ignore policy/call tool/save data” vẫn chỉ xuất hiện dưới taint label và không đổi grant; unsafe query trả policy block | sanitize/length-limit/taint implemented; raw HTML/script removed; injection corpus pass 100% critical cases |
| NEWS3 | Evidence and reviewer pipeline | fact cần ≥2 independent sources; single-source claim được label; stale/conflicting source tạo limitation; unsupported causal market claim bị reject | evidence rows map article/source/time/hash; reviewer pass/repair/reject; tối đa 1 repair |
| NEWS4 | Reviewed brief + confirmed save | expired/used proposal bị reject; evidence hash đổi buộc regenerate; account A không đọc/save brief account B | additive migration + repository + artifact mapping; immutable receipt; no direct model write |
| NEWS5 | Market-context bridge + rollout | time-misaligned context không được dùng làm causal evidence; market data unavailable vẫn trả news-only degraded brief | shared `market_summary` ownership documented; flag-off fallback giữ existing News UI; dashboard/eval gate operational |

## 8. Evidence brief artifact

```python
class NewsEvidenceBriefArtifact(BaseModel):
    schema_version: str = "1.0.0"
    brief_id: str
    artifact_id: str
    authoring_run_id: str
    account_id: str                    # trusted persistence only, không model-visible
    title: str
    objective: str
    cluster_ids: tuple[str, ...]
    evidence_rows: tuple[EvidenceRow, ...]
    source_coverage: float = Field(ge=0.0, le=1.0)
    limitations: tuple[str, ...] = ()
    review_status: Literal["reviewed", "rejected", "expired"]
    evidence_hash: str
    version: int = Field(ge=1)
    created_at: str
    expires_at: str
```

Artifact chỉ lưu reviewed evidence/refs cần thiết; không duplicate raw article body. Brief hết hạn khi nguồn/revision policy yêu cầu nhưng source articles vẫn thuộc News domain.

## 9. Failure/degradation taxonomy

| Code | Khi phát sinh | Hành vi an toàn |
|---|---|---|
| `NEWS_CLUSTER_NOT_FOUND` | cluster/article locator không resolve | dừng read, không đoán cluster |
| `NEWS_SOURCE_COVERAGE_LOW` | nguồn độc lập hoặc health không đủ | trả claims có label + limitation, không kết luận fact |
| `NEWS_SOURCE_RESTRICTED` | license cấm redistribution | chỉ trả metadata/attribution được phép |
| `NEWS_CONTENT_UNSAFE` | content boundary/policy block | không đưa content vào model; safe redirect |
| `NEWS_MARKET_CONTEXT_STALE` | market context lệch time/stale | news-only degraded response; không causal claim |
| `NEWS_EVIDENCE_CONFLICT` | nguồn mâu thuẫn | disclose conflict; reviewer không ép consensus |
| `NEWS_BRIEF_STALE` | evidence hash/version đổi trước confirm | invalidate proposal; regenerate/reconfirm |
| `NEWS_WRITE_NOT_CONFIRMED` | save thiếu confirmation hợp lệ | không persistence, không receipt applied |

## 10. Security, privacy, reliability

- Article, headline, summary, source metadata và prior artifact đều là untrusted data; không bao giờ là instruction.
- URL chỉ được lấy từ source registry/domain entities; cấm arbitrary fetch, redirect chasing hoặc user-supplied URL tool.
- Repository query luôn bind canonical `account_id`; anonymous runs dùng ephemeral namespace và không có write grant.
- Source license/attribution được enforce trước model và trước artifact rendering.
- Markdown/link output sanitize theo CSP; chỉ allowlisted URL schemes.
- Tool budget, timeout, cancellation, idempotency và trace dùng shared Agentic Core.
- Provider SDK chỉ nằm trong AI Runtime; News module không import `langchain_openai`/provider SDK.
- Không log raw article body, provider prompt, API credential hoặc private brief payload.

## 11. Test và eval matrix

| Lớp | Bộ test bắt buộc |
|---|---|
| Schema | round-trip mọi root schema; reject unknown field/type/version không hỗ trợ |
| Unit | source health, coverage, claim labeling, evidence hash, expiry |
| Contract | 7 tool I/O; scope/risk manifest; typed failures |
| Integration | auth → run → domain tools → reviewers → artifact; proposal → confirm → receipt |
| Security | IDOR/cross-account, indirect prompt injection, URL smuggling, stored artifact poisoning, license bypass |
| Resilience | source unavailable, partial cluster, stale market context, provider timeout, duplicate confirm |
| Eval | citation precision/recall, fact-vs-claim classification, unsupported causal claim rate, brief usefulness |
| E2E | article/cluster trigger → reviewed brief; save preview → explicit confirm; flag-off fallback |

Pilot gates:

- critical cross-account leak = `0`;
- critical indirect injection success = `0`;
- cited verifiable claims = `100%`;
- source attribution/license violations = `0`;
- unsupported fact/causal claim = `0` critical;
- confirmed write without valid one-time confirmation = `0`;
- all runs terminal + traceable = `100%`.

## 12. Rollout và rollback

1. Ship NEWS0–NEWS2 với fake provider và offline fixtures; flag mặc định off.
2. Shadow-generate evidence rows, không persist; so sánh deterministic source/score output.
3. Internal beta read-only cho `news.evidence_brief.v1`.
4. Mở reviewed artifact sau eval gate; vẫn không write.
5. Mở `news.save_brief` sau AC5 confirmation/security gate.
6. Rollback bằng `module.news_intelligence.agent.enabled=0`; existing feed/highlights/articles/clusters/pulse/saved endpoints không đổi.

## 13. Definition of Done

- Schemas/tool manifests version `1.0.0`, field/type/scope/risk-class freeze.
- File paths nằm dưới `src/risk_dashboard/modules/news_intelligence/`; không tạo platform path sai.
- Agent chỉ bọc pipeline live, không dựng importance/impact source thứ hai.
- Article content tainted; arbitrary network tool forbidden.
- Brief có evidence/source/time/license/limitations và reviewer status.
- Save chỉ qua proposal, re-authorization, one-time confirmation và immutable receipt.
- Contract/integration/security/eval gates §11 pass; flag-off rollback verified.

## 14. Open decisions (không block NEWS0–NEWS3)

- Retention/expiry cụ thể theo license class cho reviewed brief?
- Source registry do News module sở hữu hoàn toàn hay ingest từ operator-managed config?
- `public:news:write` có được thêm vào module scope hiện tại hay dùng scope hẹp `public:news:brief:write` trong ID scope registry?

Không tạo gap-report file riêng trong wave này. Không xóa/archive `src/risk_dashboard/quant/`; hai câu hỏi đó cần authorization riêng.
