# Agentic Quantum — Bộ kế hoạch triển khai theo module

> Trạng thái: Planning package
> Cập nhật: 15/08/2026
> Phạm vi: tài liệu triển khai, chưa sửa source code
> Nguồn quyết định cao nhất: [`AGENTIC_QUANTUM_MASTER_PLAN.md`](../AGENTIC_QUANTUM_MASTER_PLAN.md)

## 1. Mục đích

Bộ tài liệu này phân rã master plan thành các capability có thể giao cho từng squad. Mỗi plan trả lời thống nhất bảy câu hỏi:

1. Module tạo ra outcome gì cho user hoặc operator?
2. Module nào sở hữu dữ liệu và quyết định nghiệp vụ?
3. Agent được đọc, đề xuất và thực thi đến đâu?
4. Contract nào nối module với Agentic Core, AI Runtime và domain khác?
5. Work package nào phải làm theo thứ tự nào?
6. Kiểm thử, eval, bảo mật và performance gate là gì?
7. Điều kiện nào cho phép release hoặc buộc rollback?

Nếu plan con mâu thuẫn với master plan thì master plan thắng, cho đến khi có ADR cập nhật cả hai.

## 2. Danh mục kế hoạch

| # | Tài liệu | Capability sở hữu | Ưu tiên |
|---|---|---|---|
| 00 | [`00_AGENTIC_CORE_PLAN.md`](00_AGENTIC_CORE_PLAN.md) | Graph orchestration, tools, artifacts, actions, memory policy | P0 |
| 01 | [`01_IDENTITY_TRUST_FOUNDATION_PLAN.md`](01_IDENTITY_TRUST_FOUNDATION_PLAN.md) | Canonical identity, authorization, consent, audit, safety boundary | P0 |
| 02 | [`02_AI_RUNTIME_PLAN.md`](02_AI_RUNTIME_PLAN.md) | Model provider, structured generation, redaction, telemetry, budgets | P0 |
| 03 | [`03_AI_TUTOR_PLAN.md`](03_AI_TUTOR_PLAN.md) | Conversation product, tutor persona, feedback, checkpoints | P0 |
| 04 | [`04_LEARN_AGENT_PLAN.md`](04_LEARN_AGENT_PLAN.md) | Lesson-grounded teaching, mastery checks, next learning step | P0 |
| 05 | [`05_BCTC_AGENT_PLAN.md`](05_BCTC_AGENT_PLAN.md) | Evidence-grounded financial-statement analysis | P1 |
| 06 | [`06_SIMULATION_AGENT_PLAN.md`](06_SIMULATION_AGENT_PLAN.md) | Strategy design and backtest critique, no live trading | P1 |
| 07 | [`07_NEWS_AGENT_PLAN.md`](07_NEWS_AGENT_PLAN.md) | Source-aware event briefs and impact hypotheses | P2 |
| 08 | [`08_MARKET_PORTFOLIO_AGENT_PLAN.md`](08_MARKET_PORTFOLIO_AGENT_PLAN.md) | Market context and paper-portfolio review | P2 |
| 09 | [`09_HOME_JOURNEY_AGENT_PLAN.md`](09_HOME_JOURNEY_AGENT_PLAN.md) | Cross-surface next-best learning/research action | P2 |
| 10 | [`10_INTERNAL_OPS_AGENT_PLAN.md`](10_INTERNAL_OPS_AGENT_PLAN.md) | Admin/analytics/trust triage with human approval | P2 |
| 11 | [`11_QUANTUM_RESEARCH_AGENT_PLAN.md`](11_QUANTUM_RESEARCH_AGENT_PLAN.md) | Quantitative-finance EOD, scenario and model research | P3/Research |
| 12 | [`12_LEGACY_REACTIVATION_GATES.md`](12_LEGACY_REACTIVATION_GATES.md) | Gates for Goals, Health, Community and Guided Investing | Hold |

## 3. Ánh xạ codebase hiện tại → plan sở hữu

| Module/package hiện tại | Vai trò trong kiến trúc đích | Plan chịu trách nhiệm |
|---|---|---|
| `modules/auth` | Identity/session source, không phải agent | 01 |
| `modules/trust_safety` | Disclosure, policy, trust events | 01, 10 |
| `modules/system_surface` | Public/admin system state and operational surface | 10 |
| `modules/quant_risk` | Deterministic risk metrics and model reports | 04, 06, 11 |
| `platform/ai_runtime` | Module mới: provider abstraction | 02 |
| `platform/model_runtime` | Existing local model-path health; keep distinct or consolidate by ADR | 02 |
| `modules/agentic_core` | Module mới: orchestration dùng chung | 00 |
| `modules/ai_tutor` | Module mới: conversational product | 03 |
| `modules/learning` | Content, quiz, progress source of truth | 04 |
| `modules/financials_product` | Company/report/revision/calculation source of truth | 05 |
| `modules/simulation_lab` | Registered Simulation product facade | 06 |
| `modules/pro_lab` | Current Simulation implementation; direct LLM cần migrate | 06 |
| `modules/news_intelligence` | News ingestion, clustering, enrichment and evidence | 07 |
| `modules/market_portfolio` | Market/pricing/paper trading domain | 08 |
| `modules/watchlist_product` | Watchlist facade and safe-action boundary | 08 |
| `modules/portfolio_product` | Portfolio product projection/read model | 08 |
| `modules/data_hub` | Data feed provider; chỉ cung cấp typed tools | 08 |
| `modules/market_summary` | Deterministic market summaries; tool/benchmark seed | 07, 08 |
| `modules/home_onboarding` | Live entry surface and target journey orchestration owner; không tạo `modules/home` mới | 09 |
| `modules/admin_cms` | Knowledge publishing and operator control | 10 |
| `modules/analytics_monitoring` | Telemetry/KPI/alert source of truth | 10 |
| `src/risk_dashboard/engines/agents/` | Demo deterministic/reference-only; không phải Agentic Core substrate | 00, 06 |
| `src/risk_dashboard/engines/quant/` | Canonical live quantitative engines; bọc thành typed read-only tools | 11 |
| `src/risk_dashboard/quant/` | Deprecated compatibility shim; không thêm importer mới hoặc xóa trong kế hoạch này | 11 |
| `modules/goals` | Archived/legacy, chưa đưa vào rollout | 12 |
| `modules/financial_health` | Archived/legacy, chưa đưa vào rollout | 12 |
| `modules/community` | Archived/legacy, chưa đưa vào rollout | 12 |
| `modules/guided_investing` | Retired/disabled, chưa đưa vào rollout | 12 |

## 4. Dependency map

```text
Identity & Trust ───────────────┐
                               ├──> Agentic Core ──> AI Tutor ──> Learn
AI Runtime ─────────────────────┘          │             │
                                          ├─────────────> BCTC
                                          ├─────────────> Simulation
                                          ├─────────────> News
                                          └─────────────> Market/Portfolio

Learn + reviewed artifacts + consented memory ──────────> Home Journey
All telemetry + policy events ──────────────────────────> Internal Ops
Canonical quant engines + Agentic Core + AI Runtime ───> Quant Research
```

Không domain plan nào được bypass Identity/Trust, tự gọi provider, hoặc tự tạo namespace memory.

## 5. Thứ tự triển khai tổng thể

| Wave | Module | Kết quả phải có trước khi chuyển wave |
|---|---|---|
| F0 | 01 Identity/Trust | canonical `account_id`, ownership tests, consent contract |
| F1 | 02 AI Runtime + 00 Agentic Core | fake provider, typed tool loop, budgets, trace, artifacts |
| V1 | 03 AI Tutor + 04 Learn | vertical slice có grounding, checkpoint và eval |
| V2 | 05 BCTC | mọi numeric claim có tool evidence và revision |
| V3 | 06 Simulation | critique có reproducibility, không order execution |
| V4 | 07 News + 08 Market/Portfolio | cited brief và paper-portfolio review |
| V5 | 09 Home | next-best-action dựa trên artifact đã duyệt |
| O1 | 10 Internal Ops | triage read-only, approval bắt buộc cho mutation |
| R&D | 11 Quantum | classical baseline trước quantum benchmark |
| Hold | 12 Legacy | chỉ mở khi qua reactivation gate |

## 6. Quy ước chung cho mọi module

### 6.1. Capability boundary

- Domain repository luôn là source of truth.
- Agentic Core sở hữu run, orchestration, grants, artifacts, memory policy và telemetry chung.
- AI Runtime chỉ sở hữu giao tiếp model; không chứa persona hay finance logic.
- Agent tạo `ActionProposal`; domain application service mới được validate và thực thi.
- LLM chỉ tạo `MemoryProposal`; policy service mới được ghi durable memory.
- Calculation, lookup, ownership và entitlement phải deterministic.

### 6.2. Mandatory contracts

Mọi tool phải có:

- schema input/output có version;
- owner module và operation name;
- required scopes và resource ownership;
- risk class: `read`, `proposal`, `confirmed_write`, `forbidden`;
- timeout, retry policy và cost budget;
- provenance, freshness và failure envelope;
- contract test và adversarial fixture.

Mọi agent run phải có:

- canonical `account_id` lấy từ server-side auth;
- `surface_context`, `correlation_id`, `idempotency_key`;
- execution mode, step/tool/token/time budgets;
- schema validation, account/IP rate limits và abuse controls;
- trace của tool call, reviewer decision và artifact;
- safe cancellation, retry và rollback bằng feature flag.

### 6.3. Release gate chung

- Cross-account leakage bằng 0 trong security suite.
- Không có unsupported numeric claim trên gold set đã duyệt.
- Citation/provenance coverage đạt ngưỡng của domain.
- p95 latency và cost/outcome nằm trong budget phase.
- Không action bị cấm nào đi qua tool grant.
- User có thể xem agent đang dùng context, nguồn và action gì.
- Unit, integration, contract, eval và E2E critical path đạt yêu cầu; code phase sau này phải duy trì coverage tối thiểu 80%.

## 7. Quy tắc quản trị tài liệu

- Master plan quyết định terminology, fixed policy, roadmap và commercial gates.
- Plan con quyết định module boundary, interface, work breakdown và Definition of Done.
- ADR quyết định thay đổi kiến trúc không thể đảo ngược.
- API/schema sau khi triển khai phải được liên kết ngược về plan tương ứng.
- Mỗi work package chỉ chuyển `Done` khi có evidence test/eval, không chỉ vì source code đã merge.

## 8. Definition of Ready cho implementation

Một module chỉ được bắt đầu code khi:

1. owner và reviewer đã được gán;
2. dependency upstream đã đạt exit gate;
3. input/output/error schemas đã khóa;
4. threat cases và gold-set slice đã có;
5. feature flag, rollout cohort và rollback condition đã có;
6. data retention/ownership và observability fields đã thống nhất;
7. non-goals và forbidden actions đã được review.
