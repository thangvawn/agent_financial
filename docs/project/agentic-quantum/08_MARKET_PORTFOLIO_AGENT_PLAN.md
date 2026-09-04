# 08 — Market & Paper Portfolio Agent Plan

> Domain owner đích: `src/risk_dashboard/modules/market_portfolio/` (LIVE — extend)
> Read dependencies: `src/risk_dashboard/modules/data_hub/`, `src/risk_dashboard/modules/market_summary/`
> Foundation: doc 00 Agentic Core, doc 01 Identity/Trust, doc 02 Shared AI Runtime
> Roadmap: AT1, EA4 — gate VP-AT7
> Hard boundary: **agent read-only**. Place/cancel/reset/watchlist mutation và broker/live execution là `forbidden`.

## 0. Reality note

| Vùng | Live evidence | Implementation decision |
|---|---|---|
| Module | `market_portfolio` LIVE, mount `/api/v1`, dependency `data_hub`, scopes read/write (`src/risk_dashboard/modules/market_portfolio/module.py:4-16`) | Extend module; no duplicate domain |
| Market reads | Terminal/history/VN snapshot delegate to `DataHubService`/`get_vn_snapshot` (`modules/market_portfolio/api/public.py:159-161,254-281`); crypto preserves source/freshness (`:303-320`) | Agent calls application/provider layer, never self-calls REST |
| Portfolio read | `MarketPortfolioService.portfolio_summary()` computes cash, marks, PnL and positions (`application/services.py:120-161`) | Wrap as typed snapshot; do not recalculate in LLM |
| Mutations | Service exposes `place_order`, `cancel_order`, `reset_portfolio` (`application/services.py:68-118,163-165`); REST exposes POST `/orders`, `/orders/{id}/cancel`, `/portfolio/reset` (`api/public.py:358-393`) | Never import/register/grant these to agent |
| Identity debt | Endpoints accept client `session_id` (`api/public.py:335-347,353-355,386-393`); schemas contain it (`schemas.py:6-26`) | Agent accepts only server-resolved `AuthPrincipal` from doc 01 |
| Watchlist | Direct CRUD is in `market_portfolio` (`api/public.py:335-347`); `watchlist_product` only syncs/reads OHLCV (`modules/watchlist_product/api/public.py:14-46`) | Agent may read; add/remove/reorder/propose/confirm all forbidden |
| `portfolio_product` | Backtest endpoint is retired and returns 410 (`modules/portfolio_product/api/public.py:29-38`) | Do not depend on or reactivate it |
| `market_summary` | Shared library, no `module.py`; typed quality/provenance/report exist (`modules/market_summary/domain/models.py:10-17,67-91`) | Reuse deterministic outputs; do not register another module |
| Freshness | `TopicSnapshot` carries freshness, confidence, source, last success, TTL and stale reason (`modules/data_hub/domain/entities.py:21-42`) | Normalize without discarding provenance |
| Agent layer | No versioned agent schemas/tools/artifact currently exist | Greenfield thin adapter only; live repositories/feed stay source of truth |
| Provider | Doc 02 fixes `LLMProvider` abstraction and Gemini `gemini-3.5-flash` production model | Do not reopen decision; no direct `ChatOpenAI` import |

This plan is an explanation layer over live read models, not a trading rewrite. Existing legacy mutation APIs remain outside agent authority.

## 1. Capability and non-goals

Agent explains market context, paper-portfolio allocation/concentration/PnL, deterministic price-shock scenarios, and completed paper fills. Every output separates observed facts, deterministic calculations and model narrative; displays `paper`, currency, source, `as_of`, freshness and limitations.

Forbidden, with no `ActionProposal` path:

- place/submit/amend/replace/cancel orders;
- reset cash, positions or portfolio;
- add/remove/reorder watchlist;
- broker credentials, real holdings, live trading;
- allocation targets, ticker selection, buy/sell/short/all-in directives;
- arbitrary HTTP/browser/shell/MCP;
- restoring retired public backtest.

“Paper” does not reduce the mutation risk class.

## 2. Data/control flow and failures

```text
POST /api/v1/market-portfolio/agent/reviews
 → AuthPrincipal (doc 01; account/scopes server-resolved)
 → TrustedExecutionEnvelope 1.0.0 (doc 00)
 → exact five-tool read allowlist
 → DataHub/MarketSummary + MarketPortfolio read repositories
 → deterministic exposure/scenario calculation
 → LLMProvider.generate via GeminiAdapter using `gemini-3.5-flash` (doc 02 fixed)
 → numeric + evidence + safety reviewers
 → PortfolioReviewArtifactV1
 → typed response; zero portfolio/watchlist/order mutation
```

Input: principal, portfolio/review IDs, bounded scenario shocks, live repository rows/provider snapshots. Transform: ownership check, symbol/currency/time normalization, freshness classification, deterministic math, structured narrative/review. Output: typed artifact/read response only.

Failure policy:

- cross-account/unknown resource → non-disclosing `resource_not_found`;
- stale data → visibly `stale`; scenario blocked unless request explicitly sets `allow_stale=true`;
- missing mark → retain position, calculated fields `None`, list `missing_prices`; never estimate;
- closed/holiday → last valid close allowed, session visibly labeled;
- mixed currency → no aggregate without authorized FX snapshot; never assume 1:1;
- provider unavailable → deterministic response allowed with `narrative_status="unavailable"`;
- schema/reviewer failure → no `reviewed` artifact;
- no silent fallback or causal certainty.

## 3. Exact target paths and ownership

```text
src/risk_dashboard/modules/market_portfolio/
├── module.py                         # EXTEND: agent read flag/scope/router
├── api/public.py                     # LIVE legacy; agent never routes via mutations
├── api/agent.py                      # NEW: two agent endpoints
├── application/services.py           # LIVE read source; mutation symbols isolated
├── application/pricing.py            # LIVE quote reads
├── application/agent_tools.py        # NEW: exact five read adapters
├── application/exposure.py           # NEW deterministic weights/HHI
├── application/scenarios.py          # NEW deterministic price shocks
├── application/agent_service.py      # NEW orchestration boundary
├── domain/entities.py                # LIVE
├── domain/ports.py                   # NEW read-only ports
├── domain/agent_policy.py            # NEW freshness/advisory policy
├── infrastructure/repository.py      # LIVE source repository
├── infrastructure/artifact_repository.py # NEW account-scoped artifact store
└── schemas/
    ├── __init__.py                   # NEW; legacy re-exports
    ├── legacy_requests.py            # existing request models unchanged
    ├── agent_tools.py                # NEW tool contracts
    └── agent_api.py                  # NEW API/artifact contracts

tests/test_market_portfolio_agent_{contracts,tools,security,integration,e2e}.py
```

Compatibility: replace `schemas.py` with package only while `schemas/__init__.py` re-exports `WatchlistAddRequest`, `PlaceOrderRequest`, `CancelOrderRequest`, `ResetPortfolioRequest`, preserving import at `api/public.py:11-16`. Existing REST paths/responses and `mp_*` tables stay unchanged. Artifact migration is additive.

File ownership: MP0 owns `schemas/`; MP1 `domain/ports.py` + `domain/agent_policy.py`; MP2 `exposure.py` + `scenarios.py` + `agent_tools.py`; MP3 `agent_service.py`; MP4 artifact repository/migration; MP5 `api/agent.py` + `module.py`; MP6 tests only. No parallel WP edits same file.

## 4. Concrete versioned schemas

All root models: Pydantic v2, `extra="forbid"`, `schema_version: Literal["1.0.0"]`, UTC ISO-8601 timestamps. Monetary boundary values are canonical decimal strings; ratios/shocks are bounded floats.

```python
# schemas/agent_tools.py
SCHEMA_VERSION = "1.0.0"
RiskClass = Literal["read", "proposal", "confirmed_write", "forbidden"]
FreshnessState = Literal["fresh", "stale", "market_closed", "partial", "unavailable"]

class FreshnessStampV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    as_of: str
    source: str
    state: FreshnessState
    ttl_seconds: int = Field(ge=0)
    age_seconds: int = Field(ge=0)
    confidence_label: str
    stale_reason: str | None = None
    market_session: Literal["pre_open", "open", "closed", "holiday", "unknown"]

class MoneyV1(StrictModel):
    amount: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")

class PositionV1(StrictModel):
    symbol: str
    quantity: str
    avg_cost: MoneyV1
    mark_price: MoneyV1 | None
    market_value: MoneyV1 | None
    unrealized_pnl: MoneyV1 | None
    unrealized_pnl_pct: float | None
    weight_pct: float | None = Field(default=None, ge=0, le=100)
    freshness: FreshnessStampV1 | None

class GetMarketSnapshotInputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    market: Literal["VN"] = "VN"
    symbols: tuple[str, ...] = Field(default=(), max_length=100)

class GetMarketSnapshotOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    market: Literal["VN"]
    indices: tuple[dict[str, str | float | int], ...]
    breadth: dict[str, object] | None
    capital_flow: dict[str, object] | None
    quotes: tuple[dict[str, str | float | None], ...]
    freshness: FreshnessStampV1
    missing_symbols: tuple[str, ...] = ()

class GetPortfolioSnapshotInputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str  # no account_id/session_id

class GetPortfolioSnapshotOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    portfolio_kind: Literal["paper"] = "paper"
    snapshot_version: str
    cash: MoneyV1
    starting_cash: MoneyV1
    market_value: MoneyV1
    equity: MoneyV1
    total_pnl: MoneyV1
    total_pnl_pct: float
    positions: tuple[PositionV1, ...]
    missing_prices: tuple[str, ...] = ()
    freshness: FreshnessStampV1

class GetExposureInputV1(GetPortfolioSnapshotInputV1):
    benchmark: str | None = None

class GetExposureOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    snapshot_version: str
    invested_pct: float = Field(ge=0)
    cash_pct: float = Field(ge=0)
    largest_position_pct: float | None
    top3_concentration_pct: float | None
    hhi: float | None = Field(default=None, ge=0, le=1)
    weights_pct: dict[str, float]
    limitations: tuple[str, ...] = ()
    freshness: FreshnessStampV1

class PriceShockV1(StrictModel):
    symbol: str
    shock_pct: float = Field(ge=-50, le=50)

class RunScenarioInputV1(GetPortfolioSnapshotInputV1):
    shocks: tuple[PriceShockV1, ...] = Field(min_length=1, max_length=30)
    allow_stale: bool = False

class RunScenarioOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    base_snapshot_version: str
    assumptions: tuple[PriceShockV1, ...]
    base_equity: MoneyV1
    scenario_equity: MoneyV1
    pnl_delta: MoneyV1
    pnl_delta_pct: float
    position_deltas: dict[str, MoneyV1]
    deterministic_method: Literal["position_mark_price_shock_v1"]
    freshness: FreshnessStampV1
    limitations: tuple[str, ...]

class ExplainFillInputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    order_id: str

class ExplainFillOutputV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    status: str
    filled_quantity: str
    filled_price: MoneyV1 | None
    limit_price: MoneyV1 | None
    created_at: str
    filled_at: str | None
    explanation_facts: tuple[str, ...]
    freshness: FreshnessStampV1
```

```python
# schemas/agent_api.py
class StartPortfolioReviewRequestV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    portfolio_id: str
    review_type: Literal["market_context", "exposure", "scenario", "fill"]
    scenario: RunScenarioInputV1 | None = None
    order_id: str | None = None
    locale: Literal["vi-VN", "en-US"] = "vi-VN"
    idempotency_key: str = Field(min_length=16, max_length=128)

class EvidenceRefV1(StrictModel):
    tool_call_id: str
    tool_name: str
    output_schema_version: Literal["1.0.0"]
    resource_id: str
    as_of: str

class PortfolioReviewArtifactV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    artifact_id: str
    account_id: str  # server-generated, never request input
    portfolio_id: str
    portfolio_kind: Literal["paper"] = "paper"
    snapshot_version: str
    review_type: str
    observed_facts: tuple[str, ...]
    calculations: dict[str, str | float | None]
    scenario_assumptions: tuple[PriceShockV1, ...] = ()
    narrative: str | None
    narrative_status: Literal["generated", "unavailable", "blocked"]
    evidence: tuple[EvidenceRefV1, ...]
    limitations: tuple[str, ...]
    freshness: FreshnessStampV1
    review_status: Literal["reviewed", "rejected"]
    created_at: str
    expires_at: str

class StartPortfolioReviewResponseV1(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    run_id: str
    artifact: PortfolioReviewArtifactV1 | None
    error_code: str | None = None
```

Requests reject `account_id`, `session_id`, scopes, risk class, allowed tools, provider/model and currency override. Scenario symbols must be a unique subset of snapshot holdings.

## 5. Exact tools, scopes and risk classes

Manifest: `market_portfolio.tools@1.0.0`. Tool adapters are async for Agentic Core compatibility.

| Tool | Exact Python signature | Scope | Risk | Real import/call map |
|---|---|---|---|---|
| `market.get_snapshot.v1` | `async def get_market_snapshot(input: GetMarketSnapshotInputV1, ctx: ToolContext) -> GetMarketSnapshotOutputV1` | `public:market_portfolio:read` | read | `DataHubService` (`api/public.py:8,159-161`) + `market_summary` deterministic models (`domain/models.py:80-91`) |
| `portfolio.get_snapshot.v1` | `async def get_portfolio_snapshot(input: GetPortfolioSnapshotInputV1, ctx: ToolContext) -> GetPortfolioSnapshotOutputV1` | `account:market_portfolio:read` | read | `MarketPortfolioService.portfolio_summary` (`application/services.py:120-161`) after ownership resolution |
| `portfolio.get_exposure.v1` | `async def get_exposure(input: GetExposureInputV1, ctx: ToolContext) -> GetExposureOutputV1` | `account:market_portfolio:read` | read | snapshot adapter + `application/exposure.py` |
| `portfolio.run_scenario.v1` | `async def run_scenario(input: RunScenarioInputV1, ctx: ToolContext) -> RunScenarioOutputV1` | `account:market_portfolio:read` | read | snapshot adapter + `application/scenarios.py` |
| `portfolio.explain_fill.v1` | `async def explain_fill(input: ExplainFillInputV1, ctx: ToolContext) -> ExplainFillOutputV1` | `account:market_portfolio:read` | read | account-scoped `MarketPortfolioRepository.get_order` |

Forbidden catalog entries never resolve grants:

- `portfolio.place_order|submit_order|amend_order` — `forbidden`; live mutation at `application/services.py:68-107`;
- `portfolio.cancel_order` — `forbidden`; live mutation at `:109-118`;
- `portfolio.reset|reset_cash|reset_positions` — `forbidden`; live mutation at `:163-165`;
- `watchlist.add|remove|reorder|propose_change|confirm_change` — `forbidden`; live direct writes at `api/public.py:340-347`;
- `broker.*`, arbitrary HTTP/browser/shell/MCP — `forbidden`.

Grant uses exact name+version, never aliases/prefixes/model-supplied scopes. Static import test rejects agent references to `place_order`, `cancel_order`, `reset_portfolio`, `add_watchlist`, `remove_watchlist`, `apply_fill`, `apply_fill_atomic`.

## 6. Endpoints, skills and provider

| Endpoint | Contract | Scope | Effect |
|---|---|---|---|
| `POST /api/v1/market-portfolio/agent/reviews` | `StartPortfolioReviewRequestV1` → `StartPortfolioReviewResponseV1` | `account:market_portfolio:read` | read calculations + agent artifact metadata; no domain mutation |
| `GET /api/v1/market-portfolio/agent/reviews/{artifact_id}` | → `PortfolioReviewArtifactV1` | `account:market_portfolio:read` | own artifact read |

Both require `AuthPrincipal`; client `session_id` is rejected. Artifact persistence is agent metadata, not portfolio/watchlist mutation. No action proposal/confirmation endpoint.

Skills: `market.context_explainer.v1`, `portfolio.exposure_review.v1`, `portfolio.scenario_walkthrough.v1`, `portfolio.paper_fill_explainer.v1`, `market.research_checklist.v1`. Each pins manifest/prompt/schema versions. Model access is exclusively `LLMProvider`; production model is fixed to Gemini `gemini-3.5-flash` by doc 02. Numeric reviewer recomputes outputs, evidence reviewer maps every numeric claim to `EvidenceRefV1`, safety reviewer blocks recommendation/execution language.

## 7. Dependency-ordered work packages

```text
ID1+ID2 (doc 01)   AIR0+AIR1+AIR2 (doc 02)   AC0+AC2+AC3 (doc 00)
              \              |              /
MP0 schemas → MP1 authority/policy → MP2 tools/math
                                    ├→ MP3 skills/reviewers
                                    └→ MP4 artifact store
MP3 + MP4 → MP5 API/wiring → MP6 validation → MP7 rollout
```

| WP | Blockers | Owned files/deliverable | Acceptance test | DoD | Risk / mitigation | Rollback |
|---|---|---|---|---|---|---|
| MP0 | doc 00/01 contracts | `schemas/` | round-trip; extra/authority fields rejected; four old imports pass | `1.0.0` frozen, legacy API import-compatible | M×H package conversion; re-export + import suite | restore `schemas.py`; no data touched |
| MP1 | ID1, ID2, MP0 | `domain/ports.py`, `agent_policy.py` | two accounts with colliding IDs; stale/closed/FX matrix | every personal read principal-scoped; cross-account non-disclosing | H×H current client identity; ownership before adapter | disable agent flag |
| MP2 | MP0/1, AC2 | exposure/scenario/tools | golden HHI/weights/shocks; missing/stale; forbidden-import scan; exactly five tools | deterministic replay; zero write SQL/method calls | H×H accidental mutation import; exact allowlist + AST/import + mutation spies | unregister manifest |
| MP3 | MP2, AC3, AIR0/1/2 | `agent_service.py`, manifests | FakeProvider eval; unsupported claims/advisory verbs rejected; Gemini `gemini-3.5-flash` path | citations 100%; deterministic provider-outage fallback | M×H hallucination; structured output + three reviewers | skill flag off |
| MP4 | MP0/1, AC1/AC5 | artifact repository + additive migration | A cannot read B; idempotency=one artifact; snapshot staleness; TTL | minimal account-scoped store; no raw prompt/provider payload | M×H retention; minimize + TTL | stop writes; expire/purge additive table |
| MP5 | MP3/4, AC6 | `api/agent.py`, `module.py` | OpenAPI; principal-only; flag-off graceful; legacy regression | two endpoints mounted; no mutation route | M×M registry regression; isolated router/flag | unregister router/scope |
| MP6 | MP5 | five test files | matrix §8 green; kill-switch drill; DB before/after checksum | forbidden execution=0, cross-account leak=0, validation=100% | H×H false confidence; negative fuzz + audit | block rollout |
| MP7 | MP6 + license/SLA | flags/dashboard/runbook | 5%→25%→100%; §9 thresholds each stage | VN paper pilot, ops sign-off | M×H stale/license/cost; cohort gates + alerts | flag off ≤30s |

Estimate: MP0 2d, MP1 2d, MP2 4d, MP3 4d, MP4 3d, MP5 2d, MP6 4d, MP7 2d. Critical path 23 engineer-days after foundations; MP3/MP4 parallel.

## 8. Test matrix

| Layer | Required validation |
|---|---|
| Unit | normalization; Decimal serialization; weights/HHI; zero equity; phase-1 negative/short rejection; shock bounds/duplicates/subset; stale/closed/partial/missing price; currency mismatch |
| Contract | every root `1.0.0` + `extra="forbid"`; exact five read manifests; forbidden catalog; legacy imports stable |
| Integration | principal→ownership→repo→pricing→tool; DataHub freshness mapping; MarketSummary quality mapping; snapshot version; artifact idempotency/TTL |
| Security | A/B IDOR; spoofed identity/scope; alias/prefix escalation; prompt injection in label/metadata; forbidden imports; mutation spies + DB checksums |
| Resilience | provider timeout/429/malformed JSON; stale cache; missing quote; DB lock; disconnect/cancel; kill switch; fallback disclosure |
| Eval | numeric correctness 100%; numeric citations 100%; paper label 100%; recommendation/execution violations 0%; stale disclosure 100% |
| E2E | own exposure→scenario→artifact; second account non-disclosing 404; place/cancel/reset/watchlist requests refused with no proposal/tool/state change |

Keep existing `tests/test_market_portfolio_fills.py`, `tests/test_market_portfolio_facade.py` and market-summary/data suites green.

## 9. Success criteria and rollout gate

- forbidden grant/execution = 0;
- agent-attributable `mp_*` mutation = 0;
- cross-account leakage = 0;
- tool/model schema validation = 100%;
- market responses with `FreshnessStampV1` = 100%;
- unsupported numeric claims = 0; cited numeric claims = 100%;
- paper label/disclaimer = 100%;
- deterministic tools p50 <500 ms, p95 <2 s excluding refresh;
- reviewed response p50 <2 s, p95 <6 s when provider healthy;
- cost ≤USD 0.03/review; no LLM calculation;
- kill switch effective ≤30 s.

Rollout blocked until ID1/ID2, AIR0/AIR1/AIR2 and AC0/AC2/AC3/AC6 merge; VN license/cache and freshness SLA approved; security suite green. Any forbidden execution, cross-account access, missing freshness or advisory violation triggers rollback.

## 10. Compatibility and rollback

- Existing `/api/v1/market-portfolio/*` contracts remain unchanged.
- `schemas/__init__.py` preserves existing imports for one deprecation window.
- `mp_paper_accounts`, `mp_orders`, `mp_holdings`, `mp_watchlist_items` are read only and never migrated destructively.
- Artifact table is additive; old versions ignore it.
- `module.market_portfolio.agent.enabled` defaults off. Rollback unregisters router/tool manifest or flips flag; existing UI continues.
- Stored artifacts dispatch by `schema_version`; unsupported versions return `schema_unsupported`, never rewrite data.
- Provider rollback disables narrative or rolls back `GeminiAdapter`; never bypasses `LLMProvider`, silently changes provider or moves math into LLM.

## 11. Definition of Done

- Exactly five read tools registered; all execution/watchlist mutation aliases forbidden and ungrantable.
- Agent files have zero mutation/fill-apply imports or calls.
- Personal resources derive from `AuthPrincipal`; no agent request accepts client authority.
- Every applicable output includes version, freshness, provenance, currency, snapshot version and paper label.
- Exposure/scenario math is deterministic and reviewer-verified.
- Fixed provider abstraction/Gemini `gemini-3.5-flash` production policy and FakeProvider tests are honored.
- Test matrix and numeric gates pass; flag defaults off; rollback drill succeeds.
- Existing REST/UI and `mp_*` data remain compatible.

## 12. Resolved decisions and blockers

Resolved: VN market + paper portfolios only; strict read-only; no watchlist proposal/confirm; real holdings/broker forbidden; `market_portfolio` owns projection; `portfolio_product` stays retired; `market_summary` stays shared; stale is always labeled and scenarios block by default; provider abstraction/Gemini `gemini-3.5-flash` production policy is fixed.

Remaining blockers:

- Data owner approves exact VN TTL/SLA and redistribution/license policy before MP7.
- Foundation WPs above merge before integration.
- Product/compliance approves artifact TTL; until then rollout uses short-lived, non-durable artifacts.
