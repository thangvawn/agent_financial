# Agentic Quantum — Kế hoạch tổng thể hệ sinh thái Multi-Agent và Embedded Agents

> Trạng thái: Master architecture and implementation plan
> Cập nhật: 15/08/2026
> Next executable phase: AT0
> Phạm vi thay đổi hiện tại: tài liệu kế hoạch, chưa triển khai source code
> Tài liệu nền: [`AI_AGENT_PRODUCT_UPGRADE_STRATEGY.md`](AI_AGENT_PRODUCT_UPGRADE_STRATEGY.md)
> Bộ kế hoạch triển khai theo module: [`agentic-quantum/README.md`](agentic-quantum/README.md)
> Implementation authority: tài liệu này là nguồn kế hoạch thực thi duy nhất; tài liệu nền chỉ giữ vai trò khảo sát và định hướng sản phẩm

## 1. Capability

### 1.1. Capability statement

Northstar cung cấp một **agentic assistance layer** xuyên suốt sản phẩm, hoạt động theo hai interaction mode:

1. **Conversational mode:** AI Tutor/Chatbot giúp user hỏi, học, giải thích và khám phá.
2. **Embedded workflow mode:** agent xuất hiện ngay trong Home, Learn, BCTC, News, Market/Portfolio và Simulation để đọc đúng surface state, gọi domain tools, tạo artifact hoặc đề xuất bước tiếp theo trong workflow.

Hệ thống giúp người dùng:

- hỏi về lesson, quantitative finance, econometrics, BCTC và simulation;
- nhận câu trả lời có nguồn, freshness, công thức, số liệu và giới hạn;
- gọi đúng deterministic domain tool thay vì để LLM tự tạo dữ liệu;
- được hỏi lại để kiểm tra mức độ hiểu;
- lưu tiến độ và nhận bước học tiếp theo;
- tiếp cận Quantum Finance theo lộ trình education → experiment → benchmark.
- biến kết quả phân tích thành artifact có thể kiểm tra: lesson plan, evidence memo, research checklist, scenario review hoặc next-best-action card;
- tiếp tục một workflow qua nhiều phiên mà không giao quyền hành động tự trị cho model.

Kết quả cần tối ưu là **verified learning outcome + reviewed decision artifact + time-to-insight**, không phải số lượng message, số agent hoặc độ dài response.

“Agent trong từng chức năng” không có nghĩa biến mọi endpoint/CTA thành agent. Mỗi product domain phải có ít nhất một **agentic decision workflow** tại điểm người dùng cần hiểu, so sánh, kiểm chứng hoặc lập kế hoạch; CRUD, calculation và retrieval xác định vẫn là service/tool thông thường.

### 1.2. Định nghĩa “Agentic Quantum”

Trong kế hoạch này:

| Trục | Ý nghĩa sản phẩm | Trạng thái mục tiêu |
|---|---|---|
| Agentic | Orchestration có state, routing, tool use, artifact/action proposal, reviewer, checkpoint và recovery | Capability xuyên product |
| Quant/Quantum | Quantitative finance, econometrics, risk, BCTC và simulation tools | Nền tảng chuyên môn |

Trong toàn bộ kế hoạch này, “Quantum” có nghĩa là quantitative finance (“quant”), không phải quantum computing. Qubits, circuits, QAOA/VQE, quantum simulators, quantum hardware và claims về quantum advantage đều ngoài phạm vi.

### 1.3. Product name và first release

```text
Program: Agentic Quantum
Internal ecosystem name: Northstar Agentic Finance Workspace
Conversational product: Northstar Agentic Quantum Finance Tutor
External MVP positioning: Northstar AI Quant Finance Tutor
First surface: Learn Hub
First specialist: Learning & Risk/Quant Tutor
First embedded workflows: Learn checkpoint coach + BCTC evidence review
First transport: Structured JSON
First model deployment: Gemini `gemini-3.5-flash` qua provider-neutral runtime
```

Tên “Agentic Quantum” được dùng cho program và product vision. Thông điệp ra thị trường phải dùng “AI Quant Finance Tutor”; không được mô tả sản phẩm như quantum-computing capability.

## 2. Fixed decisions

Các quyết định dưới đây được coi là fixed policy cho MVP.

### Normative implementation-ready bar

| ID | Requirement | Acceptance evidence |
|---|---|---|
| BAR-1 | AI Runtime provider-neutral; production model cố định là Gemini `gemini-3.5-flash`. | GeminiAdapter + FakeProvider contract tests pass; zero domain import provider SDK hoặc model override từ client. |
| BAR-2 | “Quantum” nghĩa là quantitative finance, không phải quantum computing. | Zero QC dependency, credential, hardware claim hoặc QC roadmap item. |
| BAR-3 | `src/risk_dashboard/engines/quant/` là canonical live quantitative implementation. | New imports dùng `risk_dashboard.engines.quant`; zero new `risk_dashboard.quant` import. |
| BAR-4 | `src/risk_dashboard/engines/agents/` là demo/reference-only, không phải substrate. | Agentic Core và domain agents có zero import từ `risk_dashboard.engines.agents`. |
| BAR-5 | Plans/WPs dùng exact paths rooted tại `src/risk_dashboard/`. | Mọi path tồn tại hoặc được đánh dấu greenfield rõ ràng. |
| BAR-6 | Live feature flag chỉ có `FeatureFlagService.is_enabled()`; decorator/cache/admin refresh là AC7 proposed. | Existing parsing behavior được bảo toàn; docs không claim AC7 capability là live. |

### D1 — Product ownership

`modules/agentic_core` sở hữu capability dùng chung ở product layer:

- agent run/handoff lifecycle;
- capability/skill registry;
- context snapshot và Tool Grant orchestration;
- action proposal/artifact lifecycle;
- user memory policy và repositories;
- cross-surface telemetry, budget và operator controls.

`modules/ai_tutor` chỉ sở hữu conversational product:

- conversation lifecycle;
- Tutor-specific orchestration/persona;
- feedback;
- learning checkpoint;
- conversation API contract.

Mỗi domain module sở hữu embedded workflow và business boundary của mình:

- trigger/entry point;
- authoritative resource context;
- deterministic tools và calculations;
- artifact nghiệp vụ;
- validation và explicit-confirmation write path;
- domain-specific eval.

Không đặt product chatbot hoặc embedded workflow mới trong `engines/agents`. Package này chỉ là legacy deterministic seed cho đến khi được tách thành domain tools.

### D2 — Shared AI runtime

`platform/ai_runtime` chỉ sở hữu:

- provider-neutral `LLMProvider` protocol;
- `GeminiAdapter` dùng model cố định `gemini-3.5-flash` cho mọi production capability;
- `FakeProvider` chỉ cho deterministic contract/integration tests;
- `OpenAIAdapter` chỉ là compatibility boundary tạm thời cho migration live `ChatOpenAI` call sites, không phải production model policy;
- structured generation và function calling;
- model health;
- timeout, retry và cancellation;
- token, cost và latency telemetry;
- prompt/context redaction.

Platform runtime không sở hữu persona, learning logic hoặc công thức tài chính.

### D3 — Model policy

Policy áp dụng cho **AI Tutor và embedded agents** được migrate sang runtime mới. Pro Lab hiện tại là legacy AI surface ngoài runtime này cho đến AT6.

```env
AI_PROVIDER=google
AI_MODEL=gemini-3.5-flash
AI_FALLBACK_ENABLED=0
GEMINI_API_KEY=
```

Khi bất kỳ production agent capability nào được bật, startup phải fail nếu:

- provider/model không nằm trong server-side policy;
- fallback được bật khi chưa có approved fallback policy;
- thiếu credential của provider đã chọn.

Provider protocol bắt buộc cho test, isolation và model lifecycle. User, frontend và endpoint không được chọn provider/model. Domain module không được import provider SDK.

Gemini `gemini-3.5-flash` là model production cố định. AIR6 di dời direct OpenAI call sites sang shared runtime và chuyển behavior sang Gemini sau khi golden behavior/eval parity đạt; không duy trì OpenAI như production fallback.

### D4 — LangGraph orchestration

- AI Tutor và embedded workflow phức tạp dùng bounded LangGraph `StateGraph`.
- Shared graph primitives nằm trong `modules/agentic_core`; Tutor graph nằm trong `modules/ai_tutor/application/graph.py`; domain playbook nằm trong module sở hữu capability.
- Node chỉ phụ thuộc domain ports và AI runtime protocol.
- Conditional edge xử lý routing, failure và reviewer retry.
- Graph bị giới hạn bởi max steps, max tool calls, timeout và cost budget.
- LangGraph checkpoint chỉ phục vụ resume/retry.
- Product conversation state vẫn nằm trong repositories.
- Embedded artifact/action state nằm trong agentic-core repository và domain repository tương ứng.
- Không lưu hoặc expose internal chain-of-thought.

### D5 — Persistence ownership

```text
Conversation repository = product history
Graph checkpoint         = orchestration recovery
Agent run repository      = execution/audit lifecycle
Agent artifact repository = reviewed derived output/reference
Action proposal/receipt   = confirmation and mutation audit
Learning repository      = learning progress
Domain module            = business data/source of truth
```

### D6 — Domain-owned calculations

Công thức và calculation service tiếp tục thuộc module chuyên môn:

- `financials_product`: ratio và BCTC calculations;
- `quant_risk`: risk metrics và model explanations;
- `simulation_lab`: backtest/scenario results;
- `learning`: formula catalog và teaching metadata.

Agent layer chỉ gọi typed domain ports. Không tạo nguồn công thức thứ hai trong `agentic_core` hoặc `ai_tutor`.

### D7 — Transport sequence

```text
Structured JSON contract
→ persistence/idempotency
→ eval và safety gate
→ SSE streaming

Embedded contract
→ reviewed AgentArtifact
→ ActionProposal preview/confirmation when needed
→ domain action receipt
```

### D8 — API namespace

Giữ convention hiện có:

```text
/api/v1/public/ai-tutor/...
/api/v1/public/agentic/...
```

Trong codebase này, `public` có nghĩa **customer-facing**, không có nghĩa unauthenticated. Tất cả conversation/run/artifact/action endpoint đều bắt buộc authentication, ownership và rate limit.

### D9 — Freshness resolution

Client không được gửi `data_version`, `freshness`, `source` hoặc `allowed_tools` như dữ kiện đáng tin cậy.

Backend/domain tools phải tự resolve:

- source;
- data version;
- published/fetched time;
- report revision;
- freshness state;
- entitlement;
- allowed tools.

### D10 — Multi-Agent operating model

Northstar dùng mô hình **supervisor + bounded specialist subgraphs**, không dùng autonomous swarm tự do.

- Một Supervisor/Orchestrator nhận request và lập execution plan giới hạn.
- Mỗi specialist chỉ thấy context và toolset tối thiểu cần cho nhiệm vụ.
- Agent không gửi free-form prompt trực tiếp cho agent khác; mọi handoff đi qua schema.
- Một request thông thường chỉ kích hoạt một primary specialist.
- Chỉ dùng sequential hoặc parallel collaboration khi eval chứng minh một specialist không đủ.
- Reviewer không được tự thay đổi dữ liệu nghiệp vụ; reviewer chỉ pass, reject hoặc yêu cầu một lần repair.
- Mọi agent run có deadline, step budget, tool budget, token budget và correlation ID.

### D11 — Tiêu chuẩn để một component được gọi là agent

Một component chỉ là agent khi có đầy đủ:

1. Goal riêng có thể đánh giá.
2. Input/output contract riêng.
3. Tool allowlist riêng.
4. Policy và trust boundary riêng.
5. Failure taxonomy riêng.
6. Eval set và quality gate riêng.

Các bước auth, schema validation, context loading, deterministic numeric matching, persistence và event emission là **nodes/services**, không phải agent.

### D12 — Memory operating model

- Working memory thuộc conversation/graph và có TTL ngắn.
- Durable user memory luôn scope theo canonical `account_id`.
- Learning mastery vẫn thuộc Learning domain repository.
- Knowledge thuộc domain modules; retrieval index chỉ là derived cache.
- LLM chỉ tạo `MemoryCandidate`; Deterministic Memory Governor mới bind identity và tạo/decide `MemoryProposal`.
- Memory write phải qua policy, sensitivity, provenance, dedupe và conflict check.
- User có quyền xem, sửa, quên, tắt và export memory.
- Không dùng một filesystem workspace dùng chung cho nhiều user như mô hình personal desktop agent.

### D13 — Skills khác tools

- Skill là procedure/versioned instruction giúp agent quyết định cách xử lý.
- Tool là capability server-side có schema và authorization thực thi.
- Skill không cấp quyền tool.
- Model không được tự tạo, tự sửa hoặc tự publish production skill.
- Agent có thể đề xuất skill draft; human review và version control quyết định activation.

### D14 — Chatbot không phải product boundary của Agent

- Chatbot là một presentation surface, không phải nơi duy nhất được gọi agent.
- Embedded agent nhận trigger từ current screen/resource và trả artifact/action proposal thay vì buộc user mở chat.
- Conversational và embedded mode dùng chung identity, runtime, tool contracts, reviewers, memory policy và telemetry.
- Domain module không được tự tạo một provider client hoặc memory silo riêng.

### D15 — Human-confirmed action policy

- Read-only analysis có thể chạy ngay sau explicit user trigger.
- Mọi write tạo note, save item, blueprint, journal hoặc progress phải đi qua typed `ActionProposal` và domain application service.
- Chỉ verified Learning checkpoint được phép auto-apply theo policy đã duyệt.
- Agent không được đặt/hủy paper order, reset portfolio, publish CMS content, đóng incident hoặc thực thi external action trong MVP.
- “User asked in natural language” không tự động đồng nghĩa với authorization cho write có tác động.

### D16 — Embedded agent activation policy

Một feature chỉ được gắn nhãn Agent khi có state, goal, tool, artifact/action contract, failure recovery và eval riêng. Nếu chỉ summarize một payload hoặc generate copy không có state/tool/recovery, feature phải được gọi là **AI Assist**, không phải Agent.

## 3. Current starting point

| Thành phần | Hiện trạng codebase | Hành động |
|---|---|---|
| Product chatbot | Module cũ đã bị gỡ khỏi registry | Tạo `modules/ai_tutor` |
| Learn Tutor | Có deterministic service nhưng chưa có public tutor flow | Dùng làm seed cho AT3 |
| Agent graph | Router/tool deterministic, chưa dùng `StateGraph` | Xây bounded LangGraph |
| Pro Lab AI | Gọi `ChatOpenAI` trực tiếp theo endpoint | Giữ legacy đến AT6 |
| AI storage | Đã có bốn bảng AI nhưng chưa có repository | Migrate và tái sử dụng |
| Authentication | Learning, Home, Market/Portfolio và Pro Lab còn truyền session/user ID ở request; News còn default `anonymous` | Sửa boundary toàn product trong AT0 |
| Streaming | Chưa có chatbot SSE | Xây ở AT4B |
| Trust/safety | Có disclaimer, freshness, audit và surface state | Mở rộng cho agent threat model |
| Quant/BCTC | Có nhiều deterministic assets | Extract thành typed services |
| Quant research | Canonical engines live tại `src/risk_dashboard/engines/quant/`; REST wrapper live tại `modules/quant_risk` | Bọc read-only qua plan 11; không viết lại engine |

### 3.1. Codebase anchors

- [`src/risk_dashboard/app/registry/registry.py`](../../src/risk_dashboard/app/registry/registry.py)
- [`src/risk_dashboard/engines/agents/graph.py`](../../src/risk_dashboard/engines/agents/graph.py)
- [`src/risk_dashboard/engines/README.md`](../../src/risk_dashboard/engines/README.md)
- [`src/risk_dashboard/modules/learning/api/public.py`](../../src/risk_dashboard/modules/learning/api/public.py)
- [`src/risk_dashboard/modules/learning/application/services.py`](../../src/risk_dashboard/modules/learning/application/services.py)
- [`src/risk_dashboard/modules/pro_lab/api/ai.py`](../../src/risk_dashboard/modules/pro_lab/api/ai.py)
- [`src/risk_dashboard/modules/pro_lab/application/services.py`](../../src/risk_dashboard/modules/pro_lab/application/services.py)
- [`src/risk_dashboard/modules/financials_product/api/public.py`](../../src/risk_dashboard/modules/financials_product/api/public.py)
- [`src/risk_dashboard/modules/news_intelligence/api/public.py`](../../src/risk_dashboard/modules/news_intelligence/api/public.py)
- [`src/risk_dashboard/modules/market_portfolio/api/public.py`](../../src/risk_dashboard/modules/market_portfolio/api/public.py)
- [`src/risk_dashboard/modules/watchlist_product/api/public.py`](../../src/risk_dashboard/modules/watchlist_product/api/public.py)
- [`src/risk_dashboard/modules/portfolio_product/api/public.py`](../../src/risk_dashboard/modules/portfolio_product/api/public.py)
- [`src/risk_dashboard/modules/quant_risk/api/public.py`](../../src/risk_dashboard/modules/quant_risk/api/public.py)
- [`src/risk_dashboard/modules/home_onboarding/application/services.py`](../../src/risk_dashboard/modules/home_onboarding/application/services.py)
- [`src/risk_dashboard/app/registry/product_domains.py`](../../src/risk_dashboard/app/registry/product_domains.py)
- [`frontend/src/app/productRegistry.js`](../../frontend/src/app/productRegistry.js)
- [`src/risk_dashboard/platform/database/schema/baseline.sql`](../../src/risk_dashboard/platform/database/schema/baseline.sql)
- [`src/risk_dashboard/modules/auth/application/services.py`](../../src/risk_dashboard/modules/auth/application/services.py)
- [`frontend/src/features/auth/services/useAuth.js`](../../frontend/src/features/auth/services/useAuth.js)
- [`docs/submissions/ai-quantum-challenge-2026.md`](../submissions/ai-quantum-challenge-2026.md)

### 3.2. Khảo sát capability ngoài chatbot

Registry hiện công bố sáu product domain active: Home, Market & Portfolio, Learn Hub, BCTC, News và Simulation Lab. Quant Risk, Trust Safety, Analytics và Admin CMS là platform/operations capabilities. Community, Goals, Financial Health và Guided Investing còn package/table nhưng đã unmount hoặc retire; không đưa agent mới vào các module này trước quyết định reactivation.

| Surface/domain | Capability codebase hiện có | Agentic workflow phù hợp | Write/risk boundary | Ưu tiên |
|---|---|---|---|---:|
| Learn Hub | catalog, lesson, quiz, completion; deterministic `ExplainLessonWithTutor`, `GetLearningCoach` | Learning Coach, lesson explainer, misconception detector, checkpoint/next lesson | progress chỉ qua verified checkpoint/Learning service | P0 |
| BCTC | company workspace, statements, ratio/formula, trends, peers, upload analysis, student notes, instructor review | Company Evidence Agent, ratio walkthrough, period comparison, evidence memo | note chỉ draft→confirm; không đưa raw upload vào agent memory | P0/P1 |
| Simulation Lab | blueprint, scenario, backtest, review, report, audit; ba endpoint AI gọi `ChatOpenAI` trực tiếp | Research Workflow Agent, Validation Planner, Backtest Critic, Strategy Committee thật | run tốn chi phí và artifact write cần explicit confirm; không live execution | P1 |
| News | feed, source health, clusters, pulse, article detail, save/note | News Sensemaking Agent, event cluster brief, “why it matters”, watchlist impact hypothesis | citation/freshness bắt buộc; save/note confirm; article là untrusted input | P2 |
| Market & Portfolio | terminal, leaders, instrument history/profile, watchlist, paper orders, holdings/P&L | Market Context Agent, Watchlist Research Agent, Paper Portfolio Review Agent | read-only trong MVP; tuyệt đối không place/cancel order hoặc reset portfolio | P2 |
| Home | onboarding profile, personalized home state, learning state | Journey/Next-Best-Action Agent tổng hợp bước nên học hoặc review tiếp | không suy diễn tình trạng tài chính; không background action | P2 sau memory |
| Quant Risk | EOD run, scenario rerun, model report; deterministic narrative/reviewer seed | Shared Quant/Risk Specialist và typed tools | source of truth vẫn là quant run/model report | Foundation |
| Trust/Analytics/Admin | moderation, incident/audit, event metrics, CMS workflows | Trust Ops Triage, Eval Analyst, Content QA Agent | internal only; draft/recommend, không auto-publish/close incident | P3 |
| Legacy modules | goals, financial health, community, guided investing unmounted/retired | Chưa xây agent | cần product reactivation ADR + identity migration trước | Hold |

### 3.3. Kết luận khảo sát

1. **Learn và BCTC có readiness cao nhất** vì đã có deterministic explanations, formulas, progress/note workflow và UI context rõ.
2. **Simulation có giá trị agentic cao nhưng technical debt lớn nhất:** `strategy-copilot`, `swarm-committee` và `backtest-critique` hiện là direct OpenAI calls. Đặc biệt “Swarm Committee” là một model prompt mô phỏng bốn vai trò, chưa phải multi-agent có task/handoff/tool/reviewer riêng.
3. **News và Market có dữ liệu/freshness tốt cho read-only agents**, nhưng nguồn tin, market feed và article content phải được coi là untrusted/tainted.
4. **Market/Portfolio đang có paper-order write endpoints.** Đây là hard boundary: agent chỉ được giải thích/rà soát, không được thực thi order dù là paper trading trong MVP.
5. **Identity là P0 trên toàn hệ sinh thái**, không chỉ Learning: nhiều route còn tin `session_id`, `user_id` hoặc `anonymous` từ client.
6. **Home chỉ nên trở thành cross-surface coordinator sau khi account identity và memory consent hoàn tất**, nếu không sẽ tạo personalization sai hoặc rò dữ liệu.

## 4. Target ecosystem architecture

### 4.1. System-wide topology

```text
PRODUCT SURFACES
Home | Learn | BCTC | News | Market/Portfolio | Simulation | Internal Ops
   |         | Conversational trigger | Embedded action trigger |
   v
Domain API: auth → ownership → entitlement → input schema → rate/cost gate
   |
   v
modules/agentic_core
  Run Manager → Context Snapshot → Capability Router → Budget/Grant Controller
   |                                      |
   |                                      +→ modules/ai_tutor conversational graph
   |                                      +→ domain-owned embedded playbook
   v
Bounded specialist agents
Learning | Company | News | Market | Portfolio Review | Simulation | Quant/Risk
   |
   v
Server-side typed domain tools
   |
   v
Claim Ledger → Evidence/Numeric/Safety Review
   |
   +→ Final Composer → answer/card/memo/checklist
   |
   +→ ActionProposal → preview → user confirmation → domain application service
   |
   +→ AgentArtifact → versioned domain reference/audit
   v
Telemetry | memory candidate | feedback | rollback/degrade

platform/ai_runtime
  LLMProvider | GeminiAdapter | FakeProvider | structured generation | telemetry/redaction
```

Ba ownership rule:

- `agentic_core` điều phối run, grants, artifacts, action proposals, memory policy và audit nhưng không sở hữu business formula/data.
- `ai_tutor` sở hữu conversation/Tutor behavior nhưng không trở thành gateway bắt buộc cho embedded workflows.
- Domain module sở hữu trigger, tool adapter, artifact và mọi mutation cuối cùng.

`agentic_core` không phải “god agent”. Capability Router chỉ chọn một registered playbook; cross-domain fan-out vẫn bị giới hạn và domain không được truy cập database của nhau qua core.

### 4.2. Conversational Tutor slice

```text
Learn Hub / BCTC / Simulation / Quantum Education
                         |
                         v
modules/ai_tutor/api
  auth → validation → ownership → entitlement → rate limit
                         |
                         v
Context Builder
  policy + surface + profile + mastery + recalled memory + knowledge refs
                         |
                         v
Supervisor / Orchestrator StateGraph
  classify → choose execution mode → dispatch → adjudicate → candidate claims
        |              |                 |                  |
        v              v                 v                  v
  Learning Agent  Quant/Risk Agent  Company Agent   Simulation Agent
        |              |                 |                  |
        +--------------+--------+--------+------------------+
                               |
                               v
                    typed domain tools/evidence
                               |
                +--------------+--------------+
                |                             |
                v                             v
      Evidence/Numeric Reviewer       Safety/Policy Reviewer
                |                             |
                +--------------+--------------+
                               |
                               v
              Final Composer (no new claims)
                               |
                               v
                 response/checkpoint/persistence
                               |
                               v
                 async bounded Memory Curator

Shared infrastructure:
  agentic_core repositories | knowledge index | skill registry
  platform/ai_runtime    | GeminiAdapter/FakeProvider | telemetry/redaction

Quantitative Finance Research Agent chỉ được nối sau QF contract/grant gates.
```

### 4.3. Target file structure

```text
src/risk_dashboard/
├── modules/agentic_core/
│   ├── module.py
│   ├── api/public.py
│   ├── schemas/
│   │   ├── runs.py
│   │   ├── tasks.py
│   │   ├── claims.py
│   │   ├── actions.py
│   │   ├── artifacts.py
│   │   └── memory.py
│   ├── domain/
│   │   ├── entities.py
│   │   ├── policies.py
│   │   ├── ports.py
│   │   ├── memory.py
│   │   ├── skills.py
│   │   └── failures.py
│   ├── application/
│   │   ├── run_manager.py
│   │   ├── context_builder.py
│   │   ├── capability_router.py
│   │   ├── tool_grants.py
│   │   ├── action_service.py
│   │   ├── artifact_service.py
│   │   ├── memory_service.py
│   │   └── review_nodes.py
│   └── infrastructure/
│       ├── sqlite.py
│       ├── checkpoints.py
│       ├── knowledge_index.py
│       └── skill_registry.py
├── modules/ai_tutor/
│   ├── module.py
│   ├── api/
│   │   └── public.py
│   ├── schemas/
│   │   ├── conversations.py
│   │   ├── messages.py
│   │   ├── feedback.py
│   │   └── events.py
│   ├── application/
│   │   ├── services.py
│   │   ├── graph.py
│   │   ├── tutor_router.py
│   │   └── tutor_nodes.py
│   └── infrastructure/sqlite_conversations.py
├── modules/<domain>/application/agentic/
│   ├── capabilities.py
│   ├── playbooks.py
│   ├── tool_adapters.py
│   ├── action_handlers.py
│   └── evals/
└── platform/ai_runtime/
    ├── config.py
    ├── provider.py
    ├── gemini_adapter.py
    ├── fake_provider.py
    ├── telemetry.py
    └── redaction.py

frontend/src/features/ai-tutor/
├── api/
├── components/
├── hooks/
├── state/
└── surfaces/
    ├── LearnTutorPanel.jsx
    ├── BctcTutorPanel.jsx
    └── SimulationCoachPanel.jsx

frontend/src/shared/agentic/
├── AgentRunPanel.jsx
├── AgentArtifactCard.jsx
├── ActionProposalReview.jsx
├── EvidenceDrawer.jsx
└── useAgentRun.js
```

Không bắt buộc tạo đủ năm file `application/agentic/*` cho domain nhỏ; đây là logical boundary. Có thể gộp khi file vẫn focused, nhưng domain tool/action handler không được chuyển vào model/runtime package.

### 4.4. Three-plane architecture

```text
CONTROL PLANE
Auth/Ownership
→ Context Snapshot Builder
→ Policy Guard
→ Supervisor/Execution Planner
→ Budget and Deadline Controller

EXECUTION PLANE
Learning | Quant/Risk | Company | News | Market | Portfolio Review | Simulation | Quant Research
→ Server-side Typed Tool Executor

ASSURANCE PLANE
Claim Ledger
→ Evidence/Numeric Reviewer
→ Safety/Policy Reviewer
→ Final Composer
→ Artifact/Action Proposal
→ Confirmation Gate when write is requested
→ Persistence/Delivery
→ Async Memory Extractor + Deterministic Memory Governor
```

Các agent/subgraph cùng chạy trong modular monolith ở giai đoạn đầu. `agentic_core`, `ai_tutor` và domain modules là logical boundaries, không phải microservices. Không tách deployment trước khi load, ownership hoặc operational evidence yêu cầu.

Mỗi run dùng immutable context/memory snapshot. Memory mới được chấp nhận chỉ có hiệu lực từ run kế tiếp, tránh thay đổi prompt state giữa một workflow.

## 5. Multi-Agent Brain and orchestration contract

### 5.1. Graph state

Graph state tối thiểu:

```text
request_id
conversation_id
account_id
entry_mode
capability_id
surface
trigger
resource_context
knowledge_level
question
classified_intent
risk_labels
resolved_sources
context_snapshot_ref
memory_snapshot_ref
skill_versions
tool_grant_refs
execution_mode
selected_agents
agent_tasks
agent_results
handoff_count
claim_ledger
review_decisions
budget_remaining
deadline_at
tool_calls
numeric_claims
draft
review_result
check_question
next_action
artifacts
action_proposals
confirmation_state
failure
step_count
```

Không đưa secret, raw session token hoặc chain-of-thought vào graph state/checkpoint.

`account_id` chỉ tồn tại ở trusted runtime state để scope repository/tool grant; không đưa vào model-visible prompt nếu agent không cần biết giá trị định danh đó.

`conversation_id` bắt buộc cho conversational mode và có thể `null` cho embedded/internal run. `entry_mode + capability_id + surface + resource_ref` mới là routing identity của mọi agent run.

### 5.2. Node sequence

```text
chat message or embedded action accepted
    ↓
auth / input / policy guard
    ↓
surface + memory + knowledge context builder
    ↓
Capability Router/Supervisor selects playbook, execution mode and specialist(s)
    ├─ direct deterministic
    ├─ single specialist
    ├─ sequential handoff
    └─ bounded parallel fan-out
    ↓
specialist calls typed domain tools
    ↓
Supervisor merges structured AgentResult objects
    ↓
evidence/numeric review + safety/policy review
    ├─ pass → Final Composer / Artifact Builder
    ├─ repair → one bounded specialist repair
    └─ reject → typed failure/degraded response
    ↓
optional checkpoint or ActionProposal
    ├─ read-only artifact → persist/deliver
    └─ write proposal → preview → explicit confirmation → domain service
    ↓
persist → deliver → telemetry
    ↓
post-turn MemoryCandidate → governed MemoryProposal and bounded consolidation
```

### 5.3. Bounded execution rules

- Max graph steps: cấu hình server-side, đề xuất ban đầu `8`.
- Max domain tool calls/request: đề xuất ban đầu `3`.
- Max reviewer correction loop: `1`.
- Tool mặc định read-only.
- Không có autonomous swarm trong MVP.
- Không cho model tự mở rộng tool permission.
- Timeout và cost budget phải tạo typed failure, không silent retry vô hạn.

### 5.4. Brain không phải một model hoặc một prompt

“Brain” của Northstar gồm năm lớp:

1. **Policy brain:** invariant, role, advisory boundary, permission và versioned prompts.
2. **Context brain:** chọn surface state, user memory, mastery và knowledge phù hợp.
3. **Planning brain:** Supervisor chọn execution mode, specialist và budget.
4. **Domain brain:** specialist skills + deterministic tools theo module sở hữu dữ liệu.
5. **Review brain:** evidence, numeric, freshness, safety và teaching-quality gates.

Model là reasoning engine nằm sau protocol; model không phải source of truth và không tự sở hữu memory/tool permission.

### 5.5. Execution modes

| Mode | Khi dùng | Ví dụ | Giới hạn ban đầu |
|---|---|---|---|
| Direct deterministic | FAQ, glossary, progress lookup | “Bài tiếp theo là gì?” | Không gọi specialist nếu service đủ trả lời |
| Single specialist | Một domain rõ | “Giải thích VaR 95%” | Một specialist, tối đa ba tool calls |
| Sequential handoff | Kết quả domain A là input cho domain B | Quant giải thích số liệu → Learning chuyển thành bài giảng | Tối đa hai specialists |
| Parallel fan-out | Cần hai góc nhìn độc lập | Company + Quant đánh giá chất lượng lợi nhuận | Controlled eval sau AT4B; production gate ở AT6; tối đa hai nhánh MVP |
| Reviewer repair | Claim thiếu nguồn nhưng có thể sửa | Specialist bổ sung citation | Tối đa một vòng |
| Confirmed action | Agent đã tạo typed proposal cho domain write được phép | Lưu BCTC note hoặc strategy blueprint draft | Pause trước write; confirm token một lần; re-authorize khi apply |

Không dùng parallel fan-out mặc định. Supervisor phải chứng minh lợi ích dự kiến lớn hơn latency/cost tăng thêm.

### 5.6. TrustedExecutionEnvelope và ModelTask contracts

Authorization context và model task là hai object khác nhau. Executor giữ envelope dưới đây ở trusted runtime; object này không được serialize vào prompt:

```json
{
  "schema_version": "trusted_execution_envelope.v1",
  "run_id": "run_...",
  "request_id": "req_...",
  "conversation_id": null,
  "account_id": "acct_...",
  "entry_mode": "embedded",
  "capability_id": "bctc.evidence_memo.v1",
  "resource_ref": "financial_report:FPT:2025Q4",
  "task_id": "task_...",
  "parent_task_id": null,
  "idempotency_key": "idem_...",
  "agent_id": "quant_risk",
  "tool_grant_refs": ["grant:learn-context", "grant:quant-risk"],
  "deadline_at": "2026-08-15T10:00:06Z",
  "max_tool_calls": 3,
  "max_output_tokens": 1200,
  "policy_version": "finance-education.v1"
}
```

Model chỉ nhận task tối thiểu, không có tenant identity hoặc grant token:

```json
{
  "schema_version": "model_task.v1",
  "task_id": "task_...",
  "agent_role": "quant_risk",
  "objective": "Giải thích ý nghĩa và giới hạn của VaR hiện tại",
  "surface": "learn",
  "capability_id": "learn.explain_risk.v1",
  "context_refs": ["lesson:risk-101", "quant_run:run_..."],
  "available_tool_names": ["get_quant_run", "calculate_risk_metric"],
  "required_output_schema": "agent_result.v1",
  "response_constraints": ["education_only", "cite_numeric_claims"]
}
```

`account_id`, scopes và `tool_grant_refs` do server bind tại executor, không lấy từ client, prompt hoặc output của agent khác. Model có thể chọn tên tool được công bố trong task, nhưng executor chỉ thực thi nếu grant tương ứng hợp lệ theo `run_id`, operation, resource, expiry và call budget.

### 5.7. AgentResult contract

```json
{
  "schema_version": "agent_result.v1",
  "run_id": "run_...",
  "task_id": "task_...",
  "agent_id": "quant_risk",
  "status": "completed",
  "answer_fragment": "...",
  "claims": [],
  "evidence_refs": [],
  "numeric_claims": [],
  "assumptions": [],
  "limitations": [],
  "suggested_next_tasks": [],
  "memory_signals": [],
  "failure": null,
  "usage": {
    "tool_calls": 1,
    "latency_ms": 820,
    "input_tokens": 900,
    "output_tokens": 420
  }
}
```

`answer_fragment` không được xem là response cuối. `memory_signals` chỉ là tín hiệu post-turn, không có quyền ghi. Supervisor tập hợp candidate claims; reviewers mới tạo accepted/rejected claim ledger trước khi Final Composer deliver.

#### Claim contract

Mỗi assertion có thể kiểm chứng phải trở thành một claim độc lập thay vì chỉ nằm trong prose:

```json
{
  "claim_id": "claim_...",
  "type": "numeric",
  "statement": "Biên lợi nhuận gộp tăng 2,1 điểm phần trăm",
  "value": 2.1,
  "unit": "percentage_point",
  "evidence_refs": ["tool_result:..."],
  "calculation_ref": "calculation:...",
  "source_version": "report-revision:...",
  "freshness": "current",
  "confidence": 0.98
}
```

Numeric claim bắt buộc có `value`, `unit`, `evidence_refs`, calculation hoặc deterministic tool result, source version và freshness. Narrative claim vẫn phải có evidence hoặc được gắn nhãn rõ là interpretation/limitation.

#### ReviewDecision contract

```json
{
  "review_id": "review_...",
  "verdict": "repair",
  "accepted_claim_ids": ["claim_1"],
  "rejected_claim_ids": ["claim_2"],
  "violations": ["missing_source_version"],
  "repair_instructions": ["Re-run ratio tool against the active report revision"],
  "terminal_failure": null
}
```

Reviewer chỉ trả `pass`, `repair` hoặc `reject`. Repair instruction là dữ liệu có cấu trúc, không chứa chain-of-thought; toàn workflow chỉ có tối đa một repair loop.

#### FailureEnvelope contract

```json
{
  "code": "TOOL_SOURCE_UNAVAILABLE",
  "stage": "quant_risk",
  "retryable": false,
  "safe_message": "Nguồn số liệu hiện không khả dụng.",
  "degraded_mode": "education_only",
  "correlation_id": "corr_..."
}
```

Mọi agent, tool và reviewer failure phải map về taxonomy chung để Supervisor có thể degrade/cancel nhất quán mà không lộ nội dung nội bộ.

### 5.8. Handoff rules

- Handoff chỉ truyền IDs, structured facts, evidence refs và explicit objective.
- Không chuyển toàn bộ transcript khi không cần.
- Không truyền hidden reasoning/chain-of-thought.
- Receiving agent không được kế thừa tool permissions của sender.
- Receiving agent chỉ nhận `ModelTask`; executor bind `TrustedExecutionEnvelope` và grants ở server-side. Authorization policy không được đưa vào model-visible context.
- Mỗi handoff increment `handoff_count`; vượt budget phải degrade hoặc dừng.
- Handoff cycle bị cấm; execution plan là DAG trong một request.
- Artifact lớn được persist và tham chiếu bằng ID, không nhúng toàn bộ vào prompt.

### 5.9. Supervisor adjudication

Khi specialist mâu thuẫn:

1. Ưu tiên live domain data và report revision mới nhất.
2. Ưu tiên deterministic calculation hơn narrative inference.
3. Yêu cầu Evidence Reviewer đánh dấu conflict.
4. Không ép tạo consensus nếu evidence chưa đủ.
5. Response cuối phải trình bày uncertainty và nguồn xung đột.

Supervisor không được “bỏ phiếu đa số” cho numeric claim.

### 5.10. Failure and degradation matrix

| Failure | Hành vi |
|---|---|
| Specialist timeout | Hủy nhánh, dùng kết quả đã review hoặc trả degraded response |
| Tool unavailable | Không cho specialist tự thay nguồn; báo source unavailable |
| AgentResult sai schema | Reject; tối đa một structured repair |
| Numeric mismatch | Block claim và yêu cầu một repair |
| Source stale/conflict | Hiển thị freshness/conflict; không kết luận chắc chắn |
| Safety rejection | Dừng graph và trả education-safe response |
| Memory retrieval failure | Tiếp tục không personalization; không fail toàn request |
| Parallel branch partial failure | Chỉ dùng nhánh pass review và disclose missing perspective |
| Budget exceeded | Cancel downstream work và emit typed budget failure |
| State/checkpoint version không tương thích | Không resume mù; migrate có kiểm soát hoặc tạo typed restart-required failure |
| Memory delete xảy ra khi run đang hoạt động | Tombstone + invalidate snapshot; cancel/rebuild personalization branch và không deliver nội dung còn phụ thuộc memory đã xóa |

Final Composer là deterministic/application node, không phải specialist tự do: chỉ được sắp xếp các claim đã pass review, thêm citation/limitation/checkpoint và không được sinh claim mới. Specialist không stream trực tiếp nội dung chưa review tới người dùng.

### 5.11. AgentArtifact contract

Embedded agent phải tạo artifact có lifecycle thay vì chỉ trả chat text:

```json
{
  "schema_version": "agent_artifact.v1",
  "artifact_id": "artifact_...",
  "run_id": "run_...",
  "capability_id": "bctc.evidence_memo.v1",
  "surface": "bctc",
  "resource_refs": ["financial_report:FPT:2025Q4"],
  "artifact_type": "evidence_memo",
  "status": "reviewed",
  "title": "Chất lượng lợi nhuận FPT 2025Q4",
  "claim_refs": ["claim_1", "claim_2"],
  "evidence_refs": ["tool_result:..."],
  "limitations": [],
  "version": 1,
  "expires_at": null
}
```

Lifecycle:

```text
draft → under_review → reviewed → delivered → archived
                     └→ rejected
```

Artifact là output của agent run nhưng domain data vẫn là source of truth. BCTC memo không thay report; portfolio review không thay holdings; simulation critique không thay experiment result.

### 5.12. ActionProposal contract và confirmation gate

```json
{
  "schema_version": "action_proposal.v1",
  "proposal_id": "action_...",
  "run_id": "run_...",
  "capability_id": "bctc.save_student_note.v1",
  "action_type": "save_note",
  "target_ref": "financial_report:FPT:2025Q4:income_statement",
  "payload_preview": {"title": "CFO và lợi nhuận", "body": "..."},
  "risk_class": "user_content_write",
  "required_scope": "public:financials:write",
  "requires_confirmation": true,
  "expires_at": "2026-08-15T10:05:00Z",
  "status": "awaiting_confirmation"
}
```

Lifecycle:

```text
proposed → awaiting_confirmation → confirmed → executing → applied
                                ├→ rejected
                                ├→ expired
                                └→ failed
```

Rules:

- Model chỉ đề xuất intent/payload; server bind account, target, scope, expiry và idempotency key.
- Confirmation phải hiển thị target, thay đổi dự kiến, source/evidence và khả năng hoàn tác.
- Apply phải re-resolve identity, ownership, resource version và permission; confirm token dùng một lần.
- Proposal hết hạn hoặc target version thay đổi phải regenerate/reconfirm.
- Domain application service thực thi write và audit; agent/tool executor không ghi database trực tiếp.
- Auto-apply chỉ dành cho verified Learning checkpoint đã được policy phê duyệt; mọi loại khác mặc định confirm.

## 6. Specialist rollout

Đây là target topology dùng chung cho conversational và embedded mode. First MVP chỉ bật Agentic Orchestrator, Learning Agent, Quant/Risk Agent và reviewers cần thiết; các specialist khác mở theo EA/AT gate.

### 6.1. Agentic Orchestrator / Tutor Supervisor

Release: graph shell ở AT2; first production Tutor plan ở AT3.

Sở hữu:

- intent và risk classification;
- execution-mode selection;
- task decomposition;
- agent/tool budgets;
- structured handoff;
- result aggregation;
- tập hợp candidate claim package cho reviewers;
- terminal/failure state.

Không sở hữu business formulas, user mastery hoặc knowledge content.

### 6.2. Learning Pedagogy Agent

Release: AT3.

Năng lực:

- lesson-grounded explanation;
- Socratic hint;
- explanation-depth adaptation;
- misconception check;
- checkpoint question;
- next-lesson recommendation.

Toolset:

```text
get_lesson_context
get_learning_progress
get_learning_path
submit_verified_checkpoint
```

Write boundary: chỉ gọi learning application service khi user action hoặc deterministic checkpoint đáp ứng policy.

### 6.3. Quant & Risk Specialist Agent

Release: AT3.

Năng lực:

- probability/risk;
- SHAP và model limitations;
- VaR/CVaR;
- econometrics;
- scenario và model provenance;
- formula/result interpretation.

Toolset read-only:

```text
explain_quant_risk
get_quant_run
calculate_risk_metric
compare_scenarios
```

### 6.4. Company Analysis Agent

Release: AT5.

Năng lực:

- line-item explanation;
- ratio và substitution steps;
- cash-flow/earnings quality;
- leverage/liquidity;
- source, period, unit và freshness.

Toolset read-only:

```text
resolve_financial_line_item
explain_financial_calculation
compare_financial_periods
get_report_provenance
```

### 6.5. Simulation Research Agent

Release: AT6.

Năng lực:

- strategy assumption extraction;
- backtest critique;
- overfit, p-hacking và look-ahead review;
- validation queue;
- run ID và scenario provenance.

Toolset read-only:

```text
get_simulation_run
extract_strategy_assumptions
critique_backtest
compare_validation_runs
```

### 6.6. Quantitative Finance Research Agent

Agent này bọc read-only canonical live assets tại `src/risk_dashboard/engines/quant/`; không dùng `src/risk_dashboard/quant/` làm importer mới và không viết lại calculation engine.

Capability phase đầu:

- EOD market-risk analysis có provenance;
- macro scenario comparison trên cùng baseline/date;
- model/backtest research report;
- giải thích typed engine output mà không thay đổi số.

Không arbitrary Python/shell/notebook, model training, trading/portfolio mutation hoặc financial recommendation. Quantum-computing dependencies, experiments, hardware và roadmap đều ngoài phạm vi.

### 6.7. Evidence & Numeric Reviewer

Đây là hybrid reviewer: deterministic checks trước, semantic review sau khi thật sự cần.

- map numeric claim về tool output;
- kiểm tra unit, period, revision, source và freshness;
- phát hiện unsupported/conflicting claim;
- không viết lại số liệu;
- trả `pass`, `repair` hoặc `reject`.

Reviewer bắt buộc cho BCTC, Quant, Simulation và Quantum paths.

### 6.8. Safety & Policy Reviewer

- education/advisory boundary;
- prompt/indirect/tool-output injection;
- PII và sensitive inference;
- unauthorized tool escalation;
- disclaimer và safe completion;
- policy-version compliance.

Critical safety rejection là terminal, không được specialist override.

### 6.9. Memory Curator

Memory Curator là workflow hai phần và chạy sau response/conversation, không nằm trên critical response path trong MVP:

```text
LLM Memory Extractor → chỉ tạo MemoryCandidate
Deterministic Memory Governor → bind identity, create proposal, validate/accept/reject/persist
```

- tạo structured summary;
- đề xuất memory candidates;
- phân loại explicit/observed/derived;
- phát hiện duplicate/conflict;
- đề xuất supersede/expire;
- không tăng mastery score;
- không ghi durable memory nếu policy chưa pass.

Governor phải idempotent theo `proposal_id + source_ref`, có audit event, và fail-closed: curator lỗi không được làm fail response chính hoặc tạo partial durable write.

### 6.10. Agent capability matrix

| Agent | Primary goal | Tool scope | Write scope | Eval chính |
|---|---|---|---|---|
| Supervisor | Lập plan và tổng hợp | Dispatch only | Run/handoff state | routing, budget, completion |
| Learning | Tạo learning outcome | Learning tools | Verified checkpoint qua service | pedagogy, checkpoint quality |
| Quant/Risk | Giải thích định lượng | Quant tools | Không | numeric/provenance accuracy |
| Company | Giải thích BCTC | Financial tools | Không | period/unit/formula accuracy |
| News | Tổng hợp sự kiện có nguồn | News/source-health tools | Save/note proposal | citation/coverage/novelty |
| Market Context | Giải thích market state | Market/DataHub tools | Không | freshness/regime accuracy |
| Portfolio Review | Rà soát paper portfolio | Holdings/risk read tools | Không; không order | concentration/risk detection |
| Simulation | Phản biện nghiên cứu | Simulation tools | Không | overfit/assumption detection |
| Journey Coach | Chọn next-best workflow | Cross-surface summary reads | Preference proposal only | relevance/action completion |
| Quantum | Giải thích benchmark R&D | QR artifacts | Không | limitation/benchmark accuracy |
| Evidence Reviewer | Kiểm chứng claim | Evidence lookup | Không | false-pass/false-reject |
| Safety Reviewer | Enforce policy | Policy lookup | Audit event | safety leakage/refusal quality |
| Memory Curator | Đề xuất durable context | Memory read/propose | Proposal/event only | memory precision/conflict rate |

### 6.11. Routing playbook theo surface

| User task | Default plan | Khi nâng lên Multi-Agent | Output bắt buộc |
|---|---|---|---|
| Learn: giải thích một khái niệm | Learning single | Learning → Quant nếu cần công thức/kết quả định lượng | lesson citation + checkpoint |
| Learn: đọc kết quả risk hiện tại | Quant → Learning | Không parallel ở AT3 | run/version + formula/limitations + explanation theo level |
| BCTC: giải thích một chỉ tiêu | Company single | Company → Learning nếu user đang học lesson liên quan | report/period/unit + calculation steps |
| BCTC: đánh giá chất lượng lợi nhuận | Company → Quant | Company ∥ Quant chỉ sau added-value gate | accepted/rejected claim ledger + conflict disclosure |
| News: hiểu một sự kiện/cluster | News single | News → Company/Market nếu cần impact hypothesis | multi-source citations + freshness + uncertainty |
| Market: giải thích biến động | Market → News | Quant chỉ khi cần scenario/risk metric | market snapshot + source time + event hypothesis |
| Watchlist: review các mã đang theo dõi | Market → Company/News theo mã | Tối đa hai nhánh read-only | comparison artifact; không buy/sell ranking |
| Paper portfolio: rà soát rủi ro | Portfolio Review → Quant | News/Company chỉ cho evidence drill-down | concentration/scenario memo; không order/rebalance action |
| Simulation: phản biện backtest | Simulation → Quant | Parallel read-only chỉ khi cần independent risk review | run ID + assumptions + bias warnings |
| Home: chọn bước tiếp theo | Journey Coach single | Không fan-out trực tiếp; dùng reviewed summaries từ domain | một next-best action + lý do + destination |
| Quant research: EOD/scenario/model report | Quant Research single | Learning chỉ khi cần giải thích theo knowledge level | versioned artifact + exact metrics + provenance + limitations |

Router luôn chọn plan đơn giản nhất đáp ứng quality gate. User không thấy “cuộc hội thoại nội bộ” giữa agent; họ nhận một response thống nhất, có nguồn và cho biết limitation/degraded mode khi cần.

### 6.12. Embedded specialist extensions

#### News Intelligence Agent

- Trigger: article, cluster, today brief hoặc saved-news workspace.
- Đọc article metadata, source tier/health, cluster, affected markets và related entities.
- Tạo event brief, source-divergence note, “what to monitor” checklist và learning links.
- Không tóm tắt như sự thật nếu chỉ có một nguồn; không suy diễn market impact thành recommendation.

#### Market Context Agent

- Trigger: selected symbol/index, movers table, derivatives/crypto/commodity panel hoặc selected time range.
- Đọc snapshot/history/profile/freshness và có thể yêu cầu News Agent cung cấp event context.
- Tạo market-state card, anomaly explanation hypothesis và data-quality warning.
- Không forecast giá, không tạo signal/order và không thay thế unavailable data.

#### Paper Portfolio Review Agent

- Trigger: explicit “Review risk” trên paper portfolio/watchlist.
- Đọc holdings, cash, P&L, concentration và Quant scenario tools.
- Tạo risk review, concentration checklist và learning exercise.
- Không sinh personalized buy/sell list, target allocation hoặc `place_order`/`cancel_order`/`reset_portfolio` proposal trong MVP.

#### Home Journey Coach

- Trigger: signed-in Home load hoặc explicit refresh; không background daemon.
- Đọc compact, reviewed summaries từ Learn/BCTC/News/Simulation, không kéo raw transcript/report.
- Chọn duy nhất một next-best learning/research action và giải thích vì sao.
- Không tổng hợp sensitive financial inference; user có thể dismiss và correction phải đi qua memory policy.

#### Internal Trust/Content/Eval Agents

- Trust Ops Triage: cluster incident/audit evidence và draft response playbook; human quyết định action.
- Content QA: kiểm tra citation, terminology, prerequisite và quiz quality; chỉ tạo CMS draft/review comment.
- Eval Analyst: phân tích regression, failure cluster, latency/cost; không tự thay prompt/model/feature flag.
- Các agent này dùng internal scopes, tách memory namespace và không được truy cập personal memory mặc định.

### 6.13. Feature-by-feature realization backlog

#### Home

| Chức năng hiện có | Hiện thực hóa agent | Output/Action | Classification | Phase |
|---|---|---|---|---|
| Onboarding questions | Giải thích câu hỏi khi user yêu cầu; không tự trả lời thay | explanation card | AI Assist | EA5 |
| Personalized Home | Journey Coach chọn một next-best action từ reviewed summaries | navigation card + rationale | Agent | EA5 |
| Product discovery | Giải thích Learn/BCTC/News/Simulation phù hợp với mục tiêu đã xác nhận | deep-link artifact | Agent | EA5 |
| Marketing/guest Home | Không personalization hoặc agent run | static content | No Agent | — |

#### Learn Hub

| Chức năng hiện có | Hiện thực hóa agent | Output/Action | Classification | Phase |
|---|---|---|---|---|
| Catalog/course discovery | Lập learning path từ goal/prerequisite đã xác nhận | learning-plan artifact | Agent | EA1 |
| Lesson player | Explain selected section, Socratic hint, formula walkthrough | cited explanation card | Agent | EA1 |
| Quiz | Diagnose misconception từ deterministic answer result | misconception + remediation card | Agent | EA1 |
| Lesson completion | Đề xuất checkpoint/next lesson | verified progress action | Agent | EA1 |
| Book/reader notes | Draft summary/flashcard từ curated passage được chọn | study-note draft | AI Assist trước; Agent khi có retrieval/eval | Post-EA1 |
| Media/library filter | Giữ deterministic search/filter | normal UI | No Agent | — |

#### BCTC

| Chức năng hiện có | Hiện thực hóa agent | Output/Action | Classification | Phase |
|---|---|---|---|---|
| Company workspace | Tổng hợp reviewed company evidence theo active period | company evidence memo | Agent | EA2 |
| Statement line item | Giải thích definition, period change và source | calculation walkthrough | Agent | EA2 |
| Trends/margins | Company + Quant kiểm tra trend/denominator/base effect | trend-review artifact | Agent | EA2 |
| Ratio Practice Lab | Hướng dẫn substitution, kiểm tra cách tính của learner | worked-example/checkpoint | Agent | EA2 |
| Peer comparison | So sánh cùng unit/period/methodology và nêu limitation | comparison memo | Agent | EA2 |
| Risk alerts | Giải thích evidence và câu hỏi cần kiểm tra tiếp | risk-question checklist | Agent | EA2 |
| Student notes | Draft note từ accepted claims | ActionProposal `save_note` | Agent + confirm | EA2 |
| Upload/analyze | Deterministic parser/analyzer giữ nguyên; agent chỉ đọc analyzed revision | evidence memo | Service + Agent | EA2 |
| Instructor review | Summarize common misconception/coverage nếu privacy policy cho phép | cohort review draft | Internal Agent | EA6 |

#### News

| Chức năng hiện có | Hiện thực hóa agent | Output/Action | Classification | Phase |
|---|---|---|---|---|
| Today Brief | Chọn/nhóm story từ deterministic snapshot và giải thích coverage | cited daily brief | Agent | EA4 |
| Article reader | Why-it-matters, entities, counterpoints, monitor checklist | article evidence card | Agent | EA4 |
| Clusters/Pulse | So sánh nguồn và phát hiện narrative divergence | cluster memo | Agent | EA4 |
| Saved news | Draft research note/tag | save/note ActionProposal | Agent + confirm | EA4 |
| Feed filter/search | Giữ deterministic query/filter | normal UI | No Agent | — |
| Source health | Triage failed/stale sources cho operator | diagnostic artifact | Internal Agent | EA6 |

#### Market & Portfolio

| Chức năng hiện có | Hiện thực hóa agent | Output/Action | Classification | Phase |
|---|---|---|---|---|
| Global terminal/selected symbol | Giải thích current state với data timestamp và News context | market context card | Agent | EA4 |
| Movers/leaders | Nêu drivers giả thuyết có evidence, không forecast | movers brief | Agent | EA4 |
| Derivatives/Crypto/Commodities | Giải thích contract/market mechanics, volatility và data quality | education/risk card | Agent | EA4 |
| Watchlist | Compare tracked symbols theo explicit criteria | watchlist research memo | Agent | EA4 |
| Watchlist add/remove | Optional typed proposal | ActionProposal + confirm | Deferred decision | EA4 beta |
| Paper portfolio | Rà soát concentration, P&L attribution và scenarios | portfolio risk memo | Agent | EA4 |
| Trade panel/order form | Giải thích order type/risk; không điền hoặc gửi order | education card | AI Assist only | — |
| Place/cancel order/reset | Không expose cho Tool Registry | none | Forbidden | — |

#### Simulation Lab

| Chức năng hiện có | Hiện thực hóa agent | Output/Action | Classification | Phase |
|---|---|---|---|---|
| Strategy Copilot | Idea → hypothesis/universe/signals/risk/validation schema | blueprint draft | Agent | EA3 |
| Validation Lab | Lập walk-forward/Monte Carlo/cost/fail-condition plan | validation artifact | Agent | EA3 |
| Scenario Lab | Chuẩn bị assumptions và compare scenario result | scenario memo | Agent | EA3 |
| Backtest Lab | Kiểm tra data, benchmark, costs, leakage và robustness | critique artifact | Agent | EA3 |
| “Swarm Committee” | Bounded Simulation + Quant + Reviewer, không role-play trong một prompt | reviewed committee memo | Multi-Agent | EA3 |
| Blueprint/journal | Draft structured content | ActionProposal + confirm | Agent + confirm | EA3 |
| Run experiment | Preview data/version/cost/config rồi confirm | run ActionProposal + receipt | Agent + confirm | EA3 |
| Export report | Deterministic export từ reviewed artifact | file/export service | No Agent | EA3 |

#### Platform/Internal

| Chức năng hiện có | Hiện thực hóa agent | Output/Action | Classification | Phase |
|---|---|---|---|---|
| Quant EOD/scenario/model report | Giữ deterministic engine; expose typed read tools | evidence/tool result | Tool, not Agent | Foundation |
| Trust incident/audit | Cluster evidence, draft severity/runbook | triage artifact | Internal Agent | EA6 |
| Analytics/eval | Diagnose regression/cost/latency cohorts | eval memo | Internal Agent | EA6 |
| Admin CMS | Check source/prerequisite/quiz/terminology | QA review draft | Internal Agent | EA6 |
| Feature flags/prompt/model config | Human/operator control only | audited admin action | Forbidden to Agent | — |

Backlog này là capability map, không phải cam kết triển khai tất cả cùng lúc. P0/P1 chỉ gồm EA0–EA3; EA4–EA6 cần product evidence và capacity review riêng.

## 7. Memory, knowledge, skills and domain tools

### 7.1. Memory layers

| Layer | Nội dung | Source of truth | Retrieval/write policy |
|---|---|---|---|
| Working memory | current turn, recent messages, active task | conversation + graph state | TTL ngắn, không auto-promote |
| User profile | locale, goal, knowledge level, teaching style | account/onboarding + user confirmation | compact, versioned, user editable |
| Learning mastery | lesson/quiz/checkpoint state | Learning repository | chỉ Learning service cập nhật |
| Episodic memory | verified misconception, accepted learning plan, prior research summary | memory event store | proposal → policy → durable write |
| Active intent | current course/research question/next action | explicit user goal | có expiry và cancel |
| Shared knowledge | CMS, formulas, BCTC schemas, Quant research references | domain modules | indexed derived copy, version/freshness |

Memory không phải toàn bộ conversation history. Conversation là evidence source; durable memory chỉ là thông tin đã tuyển chọn.

Memory item mặc định có `scope = surface|capability`; chỉ profile preference đã xác nhận mới có thể dùng cross-surface. Home Journey Coach đọc reviewed summary refs theo consent, không tự nâng mọi memory thành global context. User phải có quyền tắt personalization theo từng surface ngoài global switch.

User-uploaded/private knowledge ingestion chưa nằm trong roadmap MVP vì cần malware scanning, file-type isolation, ACL, licensing, retention và retrieval eval riêng. Chỉ bổ sung bằng ADR + phase độc lập sau AT7.

### 7.2. MemoryCandidate và MemoryProposal contracts

Canonical path duy nhất:

```text
specialist memory_signals
→ post-turn Memory Curator tạo MemoryCandidate
→ Deterministic Memory Governor bind trusted identity và tạo MemoryProposal
→ policy decision
→ append event/materialize hoặc reject
```

Specialist không tạo `MemoryProposal`. Với thao tác user chủ động qua memory API, application service tạo `MemoryCandidate` deterministic mà không cần LLM.

Model-visible `MemoryCandidate` không chứa tenant identity:

```json
{
  "schema_version": "memory_candidate.v1",
  "candidate_id": "memcand_...",
  "kind": "learning_preference",
  "key": "explanation_depth",
  "value": {"level": "detailed"},
  "source_type": "explicit_user_statement",
  "source_ref": "message:msg_...",
  "confidence": 1.0,
  "sensitivity": "low",
  "valid_from": "2026-08-15T00:00:00Z",
  "expires_at": null,
  "user_visible": true,
  "reason": "User explicitly requested detailed formula walkthroughs"
}
```

Sau khi schema, provenance và sensitivity pass, Governor mới bind server-side identity vào trusted proposal:

```json
{
  "schema_version": "memory_proposal.v1",
  "proposal_id": "memprop_...",
  "candidate_id": "memcand_...",
  "account_id": "acct_...",
  "conversation_id": "conv_...",
  "source_ref": "message:msg_...",
  "policy_version": "memory-policy.v1",
  "decision": "pending"
}
```

Pipeline:

```text
candidate extraction
→ schema validation
→ provenance check
→ sensitivity/PII classification
→ dedupe and contradiction check
→ bind canonical account/conversation server-side
→ append memory event
→ update materialized current view
```

Durable write chỉ cho:

- explicit preference/goal;
- learning plan user đã chấp thuận;
- misconception được checkpoint xác nhận;
- reference tới mastery/progress do Learning service xác nhận; không sao chép score/state vào agent memory.

Cấm lưu:

- chain-of-thought;
- credential/session token;
- raw private report/tool payload;
- inferred sensitive financial condition;
- buy/sell intent;
- stale market/BCTC values;
- một suy đoán từ một chat turn.

### 7.3. Retrieval and context budget

Context Builder lấy dữ liệu theo thứ tự:

1. Auth, policy và current surface/resource.
2. Recent conversation window.
3. Authoritative domain state: learning progress/report revision/run state.
4. Compact user profile và active intent.
5. Top-k account-scoped episodic memories.
6. Curated knowledge chunks có version/freshness/ACL.
7. Live tool results.

Budget pilot đề xuất:

| Context block | Budget |
|---|---:|
| User profile | 400–600 tokens |
| Active mastery/goals | 400–800 tokens |
| Episodic recall | top 3–5, tối đa 1.000 tokens |
| Knowledge snippets | 2.000–3.000 tokens |
| Tool evidence | structured fields cần thiết, tối đa 2.000 tokens |

Bắt đầu bằng SQLite metadata + FTS5 + structured filters. Chỉ thêm embeddings/vector store khi eval chứng minh semantic recall tạo uplift đủ lớn. Shared knowledge cache được; personal context và personalized answer không cache chéo account.

### 7.4. Skill manifest

```yaml
name: explain_financial_calculation
version: 1.0.0
capability_id: bctc.explain_calculation.v1
entry_modes:
  - conversational
  - embedded
when_to_use:
  - surface == bctc
  - intent == explain_ratio
allowed_agents:
  - company_analysis
required_scopes:
  - public:financials:read
allowed_tools:
  - explain_financial_calculation
risk_class: numeric_high
timeout_ms: 5000
max_tool_calls: 2
output_schema: agent_result.v1
artifact_type: calculation_walkthrough
action_policy: read_only
eval_suite: bctc_formula_explanation.v1
```

Skill manifests nằm trong code/config version-controlled ở MVP. Progressive disclosure chỉ load skill cần cho task, không nhúng toàn bộ skill catalog vào mọi prompt.

### 7.5. Common tool result

Mọi tool phải trả:

```text
tool_call_id
tool_name
status
value/result
unit
inputs
source
data_version
published_at/fetched_at
freshness
provenance/run_id
warnings
typed_failure
```

### 7.6. Initial ports

```python
class LearningContextPort(Protocol):
    def get_lesson_context(...) -> LessonContext: ...

class FinancialCalculationPort(Protocol):
    def explain_calculation(...) -> CalculationExplanation: ...

class QuantRiskPort(Protocol):
    def explain_risk(...) -> QuantRiskExplanation: ...

class NewsEvidencePort(Protocol):
    def get_event_cluster(...) -> NewsEvidenceBundle: ...

class MarketContextPort(Protocol):
    def get_market_context(...) -> MarketContextSnapshot: ...

class PaperPortfolioReadPort(Protocol):
    def get_risk_snapshot(...) -> PortfolioRiskSnapshot: ...

class SimulationCritiquePort(Protocol):
    def critique_run(...) -> SimulationCritique: ...

class DomainActionPort(Protocol):
    def apply_confirmed_action(...) -> ActionReceipt: ...
```

`CalculationExplanation` cần:

```text
formula_id
display_formula
input_values
substitution_steps
result
unit
interpretation
source
freshness
warnings
```

### 7.7. Numeric invariant

LLM không được tự tạo hoặc tự tính lại con số tài chính trong response cuối.

Mọi numeric claim phải map được về:

- deterministic tool result;
- source field;
- data version;
- calculation ID hoặc run ID.

### 7.8. Write-boundary matrix

| Surface | Agent có thể đề xuất | Ai thực thi | Confirmation | Cấm trong MVP |
|---|---|---|---|---|
| Learn | checkpoint answer, lesson completion | Learning application service | auto-apply chỉ khi deterministic verified policy pass | LLM tự tăng mastery/progress |
| BCTC | student note draft | Financials application service | luôn confirm | sửa report, import/upload thay user, investment recommendation |
| News | save article/note draft | News application service | luôn confirm | tự follow source, publish brief hoặc external share |
| Watchlist | add/remove candidate | Market application service | luôn confirm; có thể giữ read-only ở first release | order/rebalance |
| Paper portfolio | không có write proposal | Không | Không áp dụng | place/cancel order, reset portfolio |
| Simulation | blueprint/journal draft, run configuration | Simulation application service/job | confirm; hiển thị cost/data/version | live execution, hidden parameter change |
| Home | dismiss/nudge preference | Agentic memory/application service | explicit user action | tự đổi goal/profile hoặc mở workflow nền |
| Admin/Ops | CMS/incident/policy draft | Admin/Trust service | privileged human approval | auto-publish, auto-close incident, auto-change prompt/flag |

Domain-owned state không được duplicate thành memory. Memory có thể lưu `resource_ref`, user preference hoặc accepted intent; artifact và action receipt lưu ở run/domain repository.

## 8. API contract

### 8.1. Endpoints

```text
POST /api/v1/public/ai-tutor/conversations
GET  /api/v1/public/ai-tutor/conversations/{conversation_id}
POST /api/v1/public/ai-tutor/conversations/{conversation_id}/messages
POST /api/v1/public/ai-tutor/conversations/{conversation_id}/messages:stream
POST /api/v1/public/ai-tutor/messages/{message_id}/feedback
POST /api/v1/public/agentic/runs
GET  /api/v1/public/agentic/runs/{run_id}
POST /api/v1/public/agentic/runs/{run_id}:cancel
GET  /api/v1/public/agentic/artifacts/{artifact_id}
POST /api/v1/public/agentic/action-proposals/{proposal_id}:confirm
POST /api/v1/public/agentic/action-proposals/{proposal_id}:reject
GET  /api/v1/public/agentic/memory/preferences
PATCH /api/v1/public/agentic/memory/preferences
GET  /api/v1/public/agentic/memory/items
DELETE /api/v1/public/agentic/memory/items/{memory_id}
DELETE /api/v1/public/agentic/memory
POST /api/v1/public/agentic/memory:export
```

Agent routing là internal contract. Không cung cấp public endpoint cho user chọn specialist, tool hoặc execution mode. Generic `agentic` endpoint chỉ nhận capability đã đăng ký; nó không phải endpoint cho client gửi prompt/agent/tool tùy ý.

### 8.2. Identity

- Không nhận `user_id` từ client.
- Giai đoạn chuyển tiếp: opaque token qua `X-Session-Id`.
- Backend gọi `ResolveSession` và dùng `account_id` làm canonical identity.
- Không đưa session token vào URL hoặc request body.
- Mọi conversation/message/feedback/checkpoint/run/artifact/action proposal đều kiểm tra ownership.
- Production gate: secure `HttpOnly`, `Secure`, `SameSite` session cookie hoặc bearer-session design tương đương.
- Nếu cookie được dùng cho mutation, phải có CSRF protection.
- `memory_enabled=false` chỉ tắt durable personalization/memory write. Conversation/message vẫn theo consent và retention policy riêng; chỉ được gọi là ephemeral khi product có explicit no-history mode và storage contract tương ứng.

### 8.3. Message request

```json
{
  "question": "Vì sao current ratio tăng nhưng dòng tiền yếu?",
  "surface": "bctc",
  "resource": {
    "ticker": "FPT",
    "period": "2025Q4",
    "active_view": "cash_flow"
  },
  "knowledge_level": "intermediate",
  "locale": "vi"
}
```

Backend tự resolve source, freshness, tool permission và entitlement.

`agent_id`, `execution_mode`, `allowed_tools`, `memory_namespace` và `account_id` không nằm trong public request schema.

### 8.4. Message response

```json
{
  "message_id": "msg_...",
  "answer": "...",
  "citations": [],
  "numeric_claims": [],
  "freshness": {},
  "assumptions": [],
  "limitations": [],
  "check_question": "...",
  "next_action": {},
  "trace_id": "trace_..."
}
```

### 8.5. SSE events

Chỉ triển khai trong AT4B:

```text
message.accepted
route.selected
tool.started
tool.completed
answer.delta
answer.completed
checkpoint.ready
error
```

Mỗi event có:

- request ID;
- monotonically increasing sequence;
- timestamp;
- terminal status khi kết thúc.

Không stream raw prompt, chain-of-thought hoặc raw sensitive tool output.

Embedded run có thêm event:

```text
run.accepted
run.planned
artifact.draft
artifact.reviewed
action.proposed
action.awaiting_confirmation
action.applied
run.completed
run.degraded
run.failed
```

### 8.6. Embedded run request

```json
{
  "capability_id": "bctc.evidence_memo.v1",
  "surface": "bctc",
  "resource": {
    "ticker": "FPT",
    "period": "2025Q4",
    "active_view": "income_statement"
  },
  "objective": "Kiểm tra chất lượng lợi nhuận và tạo evidence memo",
  "locale": "vi",
  "idempotency_key": "client-generated-opaque-key"
}
```

Backend phải map `capability_id + surface` vào allowlist, resolve canonical resource/version và từ chối field lạ. `resource` là locator để server resolve, không phải trusted business payload.

### 8.7. Embedded run response

```json
{
  "run_id": "run_...",
  "status": "awaiting_confirmation",
  "capability_id": "bctc.evidence_memo.v1",
  "artifact_refs": ["artifact_..."],
  "action_proposal_refs": ["action_..."],
  "limitations": [],
  "next_poll_after_ms": 750,
  "trace_id": "trace_..."
}
```

Frontend render bằng shared Agent Run UI nhưng artifact-specific view thuộc feature/domain. Chat response không được dùng thay ActionProposal confirmation UI.

## 9. Data and lifecycle

### 9.1. Reuse existing tables

Tái dùng:

- `ai_conversation_sessions`;
- `ai_messages`;
- `ai_feedback`;
- `ai_event_logs`.

Tạo migration mới; không chỉ sửa baseline vì database hiện hữu đã được stamp migration.

### 9.2. Schema additions

- canonical `account_id`;
- request/idempotency/correlation ID;
- message sequence;
- provider/model/model revision;
- input/output token và estimated cost;
- latency breakdown;
- source/freshness/citation metadata;
- failure code và terminal state;
- prompt/policy/tool schema version;
- retention/redaction/deletion state;
- tool-call records;
- graph checkpoint/state version.

Master plan cần các logical stores sau; tên bảng cuối cùng được khóa trong migration ADR:

```text
agent_user_profiles
  account_id, locale, teaching_style, memory_enabled,
  policy_version, created_at, updated_at

agent_memory_items
  memory_id, account_id, scope, kind, key, value_json,
  source_type, source_ref, confidence, sensitivity,
  valid_from, expires_at, status, version, supersedes_id,
  user_visible, last_recalled_at, created_at, updated_at

agent_memory_events
  event_id, memory_id, account_id, action, actor_type,
  actor_id, reason, before_json, after_json, redaction_state,
  created_at

agent_conversation_summaries
  conversation_id, account_id, source_sequence,
  summary_json, summary_version, created_at

agent_runs
  agent_run_id, request_id, conversation_id, account_id,
  entry_mode, capability_id, surface, resource_ref,
  agent_id, schema_version, idempotency_key, status,
  task_json, result_json, usage_json,
  started_at, completed_at

agent_handoffs
  handoff_id, request_id, conversation_id, account_id,
  source_agent_run_id, source_task_id, target_agent_run_id,
  target_task_id, source_agent, target_agent, schema_version,
  idempotency_key, envelope_json, status, created_at

agent_tool_calls
  tool_call_id, agent_run_id, account_id, tool_name,
  input_hash, output_ref, evidence_json, status,
  latency_ms, created_at

agent_artifacts
  artifact_id, agent_run_id, account_id, capability_id,
  surface, resource_ref, artifact_type, status,
  content_ref, claim_refs_json, evidence_refs_json,
  limitations_json, version, expires_at, created_at, updated_at

agent_action_proposals
  proposal_id, agent_run_id, account_id, capability_id,
  action_type, target_ref, target_version, payload_json,
  risk_class, required_scope, confirmation_required,
  status, expires_at, idempotency_key, created_at, updated_at

agent_action_receipts
  receipt_id, proposal_id, agent_run_id, account_id,
  domain_module, action_type, target_ref, result_ref,
  reversible, undo_ref, status, applied_at
```

Không duplicate `learning_lesson_progress`, saved news, watchlist/holdings/orders, BCTC reports/notes, quant runs, simulation blueprints hoặc experiment results vào agent/memory tables. Agent stores chỉ lưu lifecycle, evidence/action references và user-specific interpretation đã qua policy.

### 9.2.1. Tenant isolation invariant

- Mọi repository method nhận canonical `account_id` từ auth context.
- Client không được truyền memory namespace hoặc ownership field.
- FTS/vector index phải filter account/ACL trước ranking, không filter sau retrieval.
- Nếu private knowledge được phê duyệt sau AT7, shared/private index bắt buộc dùng namespace, ACL và retention pipeline khác nhau.
- Admin không đọc personal memory mặc định; chỉ xem aggregate operational metrics.
- Memory consent và conversation retention là hai policy độc lập; tắt memory không tự động xóa conversation.
- Delete/export map phải bao phủ item, event projection, summary, index, cache, agent run/handoff/tool-call payload, artifact/action payload, checkpoint và log có dữ liệu memory.
- Audit event chỉ giữ metadata tối thiểu đã redact; `before_json`/`after_json` không được trở thành bản sao vĩnh viễn của dữ liệu đã xóa.
- Data at rest và backup phải được mã hóa; deletion ADR phải khóa tombstone/redaction, cache invalidation, backup expiry và SLA có thể công bố cho user.
- Nếu user xóa memory trong lúc run đang dùng snapshot đó, hệ thống invalidates snapshot, cancel/rebuild nhánh personalization và suppress delivery cho đến khi response không còn phụ thuộc dữ liệu đã xóa.

### 9.3. Product lifecycles

Agent run lifecycle:

```text
accepted
→ context_resolved
→ planned
→ running
→ reviewing
→ awaiting_confirmation (optional)
→ completed
```

Terminal alternatives:

```text
degraded | rejected | canceled | expired | failed
```

Conversation lifecycle:

```text
created
→ active
→ waiting_for_user
→ completed
→ archived
→ deletion_requested
→ deleted/redacted
```

Message lifecycle:

```text
accepted
→ persisted
→ processing
→ reviewed
→ completed
```

Failure terminals:

```text
rejected_by_policy
insufficient_context
source_unavailable
stale_data
tool_failure
unsupported_numeric_claim
model_timeout
reviewer_rejected
canceled
```

### 9.4. Data not stored

- API keys và credentials;
- raw session token;
- chain-of-thought;
- PII không cần cho sản phẩm;
- toàn bộ tài liệu nhạy cảm chỉ để làm memory;
- raw tool payload không cần cho audit.

## 10. Security and trust constraints

### 10.1. Required controls

- schema validation ở mọi boundary;
- whitelist schema cho capability/resource/action payload; reject unknown fields;
- parameterized SQL;
- secrets chỉ từ environment/secret manager và validate khi startup; không ghi prompt/log/checkpoint;
- server-side identity resolution;
- ownership test cho mọi resource;
- account/IP rate limit;
- stricter account/capability/concurrent-run limit cho simulation, multi-agent và action-confirm endpoints;
- token/tool/time/cost budgets;
- PII and secret redaction;
- generic client error, detailed server trace;
- prompt injection/jailbreak detection;
- indirect injection từ lesson/report/tool output;
- indirect injection từ news article, market metadata, uploaded-report analysis và simulation note;
- stored prompt injection và memory poisoning detection;
- taint label cho untrusted memory/knowledge candidate;
- per-agent least-privilege tool allowlist;
- handoff schema validation và cycle prevention;
- capability allowlist theo surface và domain ownership;
- ActionProposal preview, one-time confirmation, expiry, target-version recheck và idempotency;
- denylist tuyệt đối cho order/cancel/reset, CMS publish, incident close và external dispatch từ agent runtime;
- account-scoped retrieval trước ranking;
- output schema validation;
- numeric/evidence reviewer;
- CSP/XSS-safe rendering cho AI content;
- restrictive CORS allowlist, HTTPS và security headers ở production;
- CSRF protection nếu dùng cookie;
- file upload phải kiểm tra size, extension, MIME, magic bytes, archive depth, malware/quarantine trước parser; agent chỉ đọc sanitized analyzed revision;
- dependency security review trước deploy.

### 10.1.1. Trust priority

Khi context mâu thuẫn, thứ tự authority là:

```text
immutable policy
→ authenticated live domain state
→ reviewed/versioned knowledge
→ explicit current user correction
→ verified mastery/progress
→ curated durable memory
→ conversation summary
→ inferred/tainted candidate
```

Memory và retrieved content luôn được coi là data, không phải instruction. Chỉ policy và reviewed skill manifests được phép điều khiển hành vi/tool selection.

### 10.2. Financial policy

- Education/research only.
- Không personalized buy/sell recommendation.
- Không cam kết lợi nhuận.
- Không gửi lệnh giao dịch.
- Không gọi `place_order`, `cancel_order` hoặc `reset_portfolio`, kể cả paper portfolio.
- Không có trading/order/portfolio-mutation/external-execution write tool trong MVP. User-content writes như note, saved item, blueprint/journal draft chỉ được phép theo matrix 7.8 qua confirmed ActionProposal; Learning progress chỉ qua explicit action hoặc verified checkpoint policy.
- Mọi dữ liệu stale/conflicting phải hiển thị cảnh báo hoặc từ chối.
- Disclaimer không thay thế numeric validation và provenance.

### 10.3. Embedded-agent threat additions

- **Confused deputy:** capability ở News không được dùng grant của Market hoặc Admin.
- **Cross-surface context leak:** Home chỉ đọc compact reviewed summary, không raw private artifact từ surface khác.
- **Confirmation spoofing:** chat text “đã xác nhận” không thay one-time server confirmation token.
- **Stale action:** target/resource version đổi giữa proposal và confirm phải invalidate proposal.
- **Artifact poisoning:** artifact do agent tạo là untrusted input khi được agent khác đọc; luôn giữ provenance/taint.
- **Background overreach:** không schedule, push, save, publish hoặc run simulation ngoài explicit product event và entitlement đã duyệt.
- **Legacy AI bypass:** Pro Lab direct OpenAI endpoint không được giữ song song sau migration để né reviewer, budget hoặc audit.
- **Payload smuggling/mass assignment:** ActionProposal apply chỉ map field allowlist vào explicit domain command; không truyền `payload_json` trực tiếp cho repository/ORM.
- **Upload-to-prompt attack:** raw filename, metadata, formula/macro/script hoặc extracted instruction đều mang taint; không được nâng thành system/skill instruction.
- **Client rendering:** artifact Markdown/HTML phải sanitize và chịu CSP; citation URL chỉ cho scheme/domain được policy chấp thuận.

## 11. Observability, performance and cost

### 11.1. Required events

```text
ai_tutor_conversation_created
ai_tutor_message_accepted
ai_tutor_routed
ai_tutor_execution_plan_created
ai_tutor_agent_started
ai_tutor_agent_completed
ai_tutor_handoff_created
ai_tutor_parallel_fanout_started
ai_tutor_agent_result_rejected
ai_tutor_tool_started
ai_tutor_tool_completed
ai_tutor_review_passed
ai_tutor_review_rejected
ai_tutor_response_completed
ai_tutor_checkpoint_answered
ai_tutor_feedback_submitted
ai_tutor_memory_proposed
ai_tutor_memory_accepted
ai_tutor_memory_rejected
ai_tutor_memory_superseded
ai_tutor_memory_deleted
agentic_run_accepted
agentic_capability_routed
agentic_artifact_created
agentic_artifact_reviewed
agentic_action_proposed
agentic_action_confirmed
agentic_action_rejected
agentic_action_expired
agentic_action_applied
agentic_run_degraded
agentic_run_completed
ops_model_call_logged
```

### 11.2. Required metrics

| Nhóm | Metric |
|---|---|
| Quality | grounded answer rate, numeric accuracy, task success |
| Safety | advice violation, unsupported claim, injection success |
| Performance | p50/p95 TTFT, full response latency, tool latency |
| Reliability | provider/tool failure, retry, canceled, duplicate rate |
| Orchestration | routing accuracy, agents/request, handoffs/request, fan-out uplift |
| Embedded workflow | artifact completion, proposal acceptance, confirmed-action success, time-to-insight, resume rate |
| Cost | input/output tokens, cost/successful session |
| Learning | check-question success, completion uplift, helpfulness |
| Memory | recall precision, accepted-memory precision, conflict/stale rate, deletion SLA |
| Commercial | activation, D7/D30 retention, paid conversion, gross margin |

### 11.3. Initial pilot gates

Các giá trị là target cần kiểm chứng, không phải benchmark hiện tại:

| Gate | Target |
|---|---:|
| Grounded/cited answer | ≥95% |
| Numeric claim-evidence coverage | 100% |
| Numeric accuracy | ≥99% |
| Tutor task success | ≥80% |
| Critical cross-user access | 0 |
| Critical advisory violation | 0 |
| Unauthorized/forbidden agent action | 0 |
| Confirm-required write without valid confirmation | 0 |
| Cross-user memory/retrieval leakage | 0 |
| Cross-surface unauthorized context leakage | 0 |
| Unsupported durable memory write | 0 critical; <1% non-critical candidate false accept |
| Durable memory có provenance hợp lệ | 100% |
| Critical indirect/stored prompt injection success | 0 |
| Unsupported Quantum advantage claim | 0 |
| Multi-agent conflict kết thúc đúng policy | 100% trên conflict eval set |
| Delivered artifact có provenance/owner/resource version | 100% |
| Model/tool failure | <2% |
| p95 TTFT sau AT4B | <2 giây |
| p95 single-specialist full response | <6 giây |
| Tutor helpfulness | ≥75% |

### 11.4. Multi-Agent added-value gate

Một sequential/parallel plan chỉ được bật cho production use case nếu so với single-specialist baseline:

- task success tăng tối thiểu 5 điểm phần trăm hoặc đạt uplift được AT0 phê duyệt;
- grounded/numeric quality không giảm;
- learner helpfulness hoặc surface workflow outcome tăng;
- reviewer rejection không tăng bất thường;
- cost và latency nằm trong budget;
- 100% handoff schema-valid;
- không execution nào vượt step/tool/handoff budget;
- mọi run có terminal state.

Nếu không vượt gate, route phải giữ single specialist. Multi-Agent là optimization theo evidence, không phải default marketing feature.

### 11.5. Mode-specific performance targets

Không dùng một SLO cho mọi execution mode:

| Mode | Initial target |
|---|---:|
| Direct deterministic | p95 <1 giây |
| Single specialist | p95 full response <6 giây |
| Sequential/parallel | AT0 khóa budget riêng; initial ceiling <10 giây |
| Embedded artifact | p95 reviewed artifact <8 giây cho synchronous capability; job dài trả run handle <1 giây |
| Confirmed action | confirmation receipt <1 giây, không tính domain job async |
| SSE TTFT | p95 <2 giây |

Theo dõi latency/cost theo mode, agent count, handoff count và fan-out. Không lấy average toàn chatbot để che tail latency của multi-agent path.

### 11.6. Surface outcome metrics

| Surface | Primary outcome | Guardrail |
|---|---|---|
| Learn | checkpoint pass/completion uplift, concept correction | không inflate mastery |
| BCTC | evidence-memo completion, formula comprehension, time-to-insight | unsupported numeric claim = 0 critical |
| News | source coverage, useful brief/save rate | single-source certainty và stale claim |
| Market | explanation usefulness, drill-down completion | forecast/advice violation |
| Paper portfolio | risk issue detection, learning action completion | order/rebalance action = 0 |
| Simulation | validation tasks completed, bias detection, artifact reuse | overfit false reassurance |
| Home | next-best-action acceptance/completion | irrelevant/sensitive nudge |
| Internal Ops | triage time reduction, accepted QA finding | unauthorized publish/policy change = 0 |

Mỗi embedded capability cần baseline không-agent hoặc deterministic-only. Không rollout chỉ vì artifact acceptance cao; phải chứng minh user hoàn thành workflow tốt hơn hoặc nhanh hơn mà trust gate không giảm.

## 12. Master workstreams and dependency-ordered implementation plan

### 12.1. Workstreams

| Workstream | Ownership | Deliverable xuyên suốt |
|---|---|---|
| WS-A Identity & Trust | Auth/Security | canonical account, ownership, policy, retention, audit |
| WS-B Agent Brain | Agentic Core + AI Tutor | run manager, Supervisor, specialist subgraphs, handoff/adjudication |
| WS-C Memory | Agentic Core | profile, episodic memory, proposal/consolidation, user controls |
| WS-D Knowledge & Skills | Domain owners + Agentic Core adapters | reviewed sources, index, skill manifests, typed tools |
| WS-E Product Surfaces | Product frontend teams | chat panel, embedded run/artifact/action UI |
| WS-F Eval & Operations | Analytics/Trust/Product | eval harness, tracing, cost, freeze/degrade/rollback |
| WS-G Embedded Experiences | Domain owners | capability manifests, triggers, artifacts, action handlers, surface eval |
| WS-QF Quant Research | Quant/Research | engine adapters, provenance, numeric review, compatibility rollout |

Một phase chỉ exit khi tất cả workstream deliverables bắt buộc của phase cùng đạt gate.

Không bắt đầu bằng chatbot UI hoặc LangGraph graph trước khi hoàn thành AT0 và phần tool contract cần thiết của AT1.

### AT0 — Capability freeze, identity, threat model and eval

Ước lượng: 1–2 tuần.

Work packages:

- `AT0.1` đóng băng capability/non-goals và terminology;
- `AT0.2` ADR cho module ownership, LangGraph, model và persistence;
- `AT0.3` session → account identity dependency;
- `AT0.4` API/tool/error contracts;
- `AT0.5` threat model và abuse cases;
- `AT0.6` gold-set 100–200 câu;
- `AT0.7` baseline deterministic tool quality/latency;
- `AT0.8` feature flag và rollout contract;
- `AT0.9` TrustedExecutionEnvelope/ModelTask/AgentResult/handoff contracts;
- `AT0.10` memory consent, retention, export/delete và write policy;
- `AT0.11` specialist capability matrix, budgets và eval ownership;
- `AT0.12` embedded capability catalog và Agent-vs-AI-Assist classification;
- `AT0.13` AgentArtifact/ActionProposal/confirmation contracts;
- `AT0.14` paper-order/Admin/external-action denylist;
- `AT0.15` identity migration inventory cho Home/Learn/News/Market/Simulation.

Exit gate:

- không endpoint AI tin `user_id` do client gửi;
- mọi use case có expected tool/evidence/refusal;
- mọi embedded capability có trigger, artifact/action, owner, permission, failure và eval contract;
- advisory boundary và Agentic Quantum definition được duyệt;
- memory/knowledge/skill/tool boundaries được duyệt;
- cross-agent permission inheritance bị cấm trong contract;
- AT1/AT2 interface không còn blocker.

### AT1 — Extract deterministic domain tools

Ước lượng: 1–2 tuần.

Work packages:

- `AT1.1` learning context service;
- `AT1.2` financial calculation/explanation service;
- `AT1.3` quant risk explanation service;
- `AT1.4` simulation critique service contract;
- `AT1.5` common provenance/freshness/failure schema;
- `AT1.6` versioned skill manifests cho Learn/Quant;
- `AT1.7` server-side typed Tool Registry;
- `AT1.8` scoped Tool Grant service theo run/resource/operation/expiry/budget;
- `AT1.9` Claim/ReviewDecision/FailureEnvelope schemas;
- `AT1.10` adversarial tool-output fixtures;
- `AT1.11` unit và contract tests;
- `AT1.12` news evidence/source-health service contract;
- `AT1.13` market context và paper-portfolio read service contracts;
- `AT1.14` domain action-handler protocol và forbidden-action tests.

Exit gate:

- tool chạy không cần LLM;
- mọi output có unit/source/freshness/version;
- agent chỉ gọi tool qua grant hợp lệ và không thể mở rộng grant;
- claim/review/failure schemas pass compatibility tests;
- không sao chép công thức vào `agentic_core` hoặc `ai_tutor`.

### AT2 — Agentic Core, conversation foundation and provider-neutral runtime

Ước lượng: 2 tuần.

Work packages:

- `AT2.1` database migration;
- `AT2.2` repositories và ownership;
- `AT2.3` idempotency/correlation;
- `AT2.4` provider protocol và fake provider;
- `AT2.5` Gemini adapter dùng cố định `gemini-3.5-flash`;
- `AT2.6` startup validation/health;
- `AT2.7` structured output/function-call matching;
- `AT2.8` redaction và model telemetry;
- `AT2.9` agent run/handoff/tool-call repositories;
- `AT2.10` user profile, memory item/event và summary repositories;
- `AT2.11` Context Builder và Supervisor graph shell;
- `AT2.12` fake specialists/reviewers cho orchestration tests;
- `AT2.13` `agentic_core` run/artifact/action repositories;
- `AT2.14` generic embedded-run API và shared frontend run panel;
- `AT2.15` confirmation token, expiry, re-authorization và action receipt flow;
- `AT2.16` register `agentic_core` và `ai_tutor` module definitions/dependencies/flags.

Exit gate:

- invalid model configuration fail fast;
- retry không tạo duplicate message/tool call;
- function call ID/name/count được kiểm tra;
- retry/resume không chạy trùng specialist hoặc tool side effect;
- every agent/tool query được account-scope;
- không log secret/PII/chain-of-thought;
- provider failure có typed terminal state.

### AT3 — Learn Agent & Risk/Quant vertical slice

Ước lượng: 2–3 tuần.

Work packages:

- `AT3.1` LangGraph state và nodes;
- `AT3.2` Supervisor single-mode + Learning Agent; Quant/Risk Agent chỉ được dispatch cho quant-specific intents;
- `AT3.3` structured Learning ↔ Quant sequential handoff và reviewer loop;
- `AT3.4` Evidence/Numeric + Safety reviewers;
- `AT3.5` conversation/message JSON endpoints;
- `AT3.6` Learn Hub contextual panel;
- `AT3.7` citations/numeric claims/limitations;
- `AT3.8` checkpoint question;
- `AT3.9` progress update qua learning service;
- `AT3.10` working memory + compact profile read;
- `AT3.11` feedback, tracing và eval regression;
- `AT3.12` embedded Learn actions: Explain this, Check my understanding, Build next-step card;
- `AT3.13` shared AgentArtifact/Evidence UI trong Learn Hub.

Exit gate:

- vượt quality/safety gate của first specialist;
- zero cross-user access;
- frontend có loading/cancel/retry/error state;
- one complete verified learning session hoạt động end-to-end;
- routing và handoff accuracy đạt gate trên Learn/Quant eval set;
- chưa có durable inferred memory write;
- parallel fan-out vẫn tắt; majority request chỉ chạy một specialist.

### AT4 — Memory, SSE and production hardening

Ước lượng: 3–4 tuần, chia thành hai package có exit gate riêng.

#### AT4A — Durable memory hardening

- `AT4A.1` durable memory proposal + deterministic governor;
- `AT4A.2` explicit confirmation và write policy;
- `AT4A.3` supersede/conflict/expiry/idempotency;
- `AT4A.4` user APIs/UI xem, sửa, quên, disable và export;
- `AT4A.5` post-turn Memory Curator và bounded consolidation;
- `AT4A.6` retention worker và cache/index invalidation;
- `AT4A.7` memory poisoning/cross-account/deletion-race tests.

AT4A gate:

- user có thể xem/sửa/quên/export/disable memory;
- rejected/sensitive proposal không được persist;
- memory event idempotent và có provenance;
- mastery vẫn chỉ thay đổi qua Learning service;
- curator failure không làm fail response đã deliver.

#### AT4B — SSE and runtime hardening

- `AT4B.1` POST SSE endpoint;
- `AT4B.2` event sequence và terminal state;
- `AT4B.3` reconnect/idempotency;
- `AT4B.4` cancellation propagation;
- `AT4B.5` account/IP rate limit;
- `AT4B.6` cache isolation và version key;
- `AT4B.7` parallel fan-out feature flag cho controlled eval;
- `AT4B.8` load/disconnect/timeout/partial-branch tests.

AT4B gate:

- reconnect không nhân đôi response;
- mọi stream có terminal event;
- cancellation dừng downstream work;
- cache không rò dữ liệu giữa account;
- parallel mode chỉ bật nếu quality uplift vượt cost/latency budget.

### AT5 — Company Analysis Agent & BCTC embedded workspace

Ước lượng: 2 tuần.

Work packages:

- `AT5.1` BCTC surface context;
- `AT5.2` ratio/line-item/cash-flow adapters;
- `AT5.3` calculation-step UI;
- `AT5.4` company-analysis gold-set;
- `AT5.5` period/unit/freshness presentation;
- `AT5.6` Company ↔ Quant parallel/sequential patterns;
- `AT5.7` Company evidence → Learning explanation sequential pattern;
- `AT5.8` conflict adjudication tests;
- `AT5.9` embedded BCTC evidence memo/ratio walkthrough actions;
- `AT5.10` student-note ActionProposal preview/confirm;
- `AT5.11` uploaded report chỉ được tham chiếu qua analyzed result/revision, không đưa raw file vào memory.

Exit gate:

- mọi con số map về calculation/tool result;
- ticker, period, unit và freshness luôn hiển thị;
- không tạo personalized recommendation.

### AT6 — Simulation Agents and Pro Lab migration

Ước lượng: 2–3 tuần.

Work packages:

- `AT6.1` simulation context adapter;
- `AT6.2` strategy assumption tool;
- `AT6.3` backtest critique tool;
- `AT6.4` overfit/look-ahead/p-hacking reviewer;
- `AT6.5` migrate direct Pro Lab AI calls qua shared runtime;
- `AT6.6` Simulation ↔ Quant handoff pattern;
- `AT6.7` production gate cho parallel read-only plan và partial-branch recovery;
- `AT6.8` compatibility/deprecation plan cho OpenAI endpoints;
- `AT6.9` thay single-prompt “Swarm Committee” bằng bounded Simulation + Quant + Reviewer plan;
- `AT6.10` embedded validation-plan/backtest-critique artifacts;
- `AT6.11` blueprint/journal/run-config ActionProposal với explicit confirmation.

Exit gate:

- production AI endpoint không tự khởi tạo provider client ngoài shared runtime;
- simulation claim có run ID và assumptions;
- không có trading/order/portfolio-mutation/external-execution write tool; blueprint/journal/run-config chỉ qua confirmed ActionProposal.

### AT7 — Pilot and commercialization gate

Ước lượng: 4–6 tuần pilot.

Work packages:

- `AT7.1` entitlement/quota;
- `AT7.2` cost dashboard;
- `AT7.3` cohort/instructor reporting tối thiểu;
- `AT7.4` privacy/retention review;
- `AT7.5` data-license review;
- `AT7.6` agent/memory operations dashboard;
- `AT7.7` freeze/degrade/rollback runbooks;
- `AT7.8` paid pilot measurement;
- `AT7.9` per-surface entitlement/cost budget cho embedded capabilities;
- `AT7.10` chọn tối đa ba embedded workflows cho paid pilot, không rollout đồng loạt.

Exit gate:

- quality, safety, performance và margin gate đạt;
- có learning-outcome và selected embedded-workflow outcome evidence;
- có quyết định go/no-go cho scale và QR execution lane.

### 12.2. Embedded Agent delivery track

Track này không thay AT0–AT7; nó xác định capability nào được hiện thực hóa trong từng product domain và phụ thuộc vào foundation phase nào.

#### EA0 — Embedded foundation

Mapping: AT0–AT2.

- `EA0.1` capability manifest và Agent-vs-AI-Assist rubric;
- `EA0.2` generic run/artifact/action contracts;
- `EA0.3` shared Agent Run/Evidence/Confirmation UI;
- `EA0.4` domain trigger/ownership convention;
- `EA0.5` action denylist và confirmation policy;
- `EA0.6` cross-surface context summary contract.

Gate: fake-provider flow chạy được từ embedded CTA → reviewed artifact → optional confirmed action receipt, không cần chat conversation.

#### EA1 — Learn embedded coach

Mapping: AT3.

- “Explain this section”, “Check my understanding”, “Show formula steps” và “What next?”;
- artifact: explanation card, misconception card, checkpoint card;
- write: verified checkpoint/progress qua Learning service;
- baseline: current deterministic Tutor/Coach services.

Gate: completion/checkpoint uplift; mastery không bị LLM tự ghi.

#### EA2 — BCTC evidence workspace

Mapping: AT5.

- “Explain this line item”, “Compare periods”, “Trace this ratio”, “Review earnings quality”;
- artifact: calculation walkthrough, evidence memo, risk-question checklist;
- write: student note draft → explicit confirm;
- uploaded file: chỉ đọc analyzed dataset/revision, không gửi raw file vào memory.

Gate: 100% numeric claim-evidence mapping; period/unit/freshness visible.

#### EA3 — Simulation research workflow

Mapping: AT6.

- idea → structured hypothesis → validation queue → run configuration → critique → research memo;
- migrate Strategy Copilot và Backtest Critic vào shared runtime;
- thay “Swarm Committee” một-prompt bằng bounded Simulation/Quant/Reviewer execution khi eval chứng minh lợi ích;
- artifact: blueprint draft, validation plan, critique, report;
- write/run: explicit confirmation + cost/data preview.

Gate: no direct provider bypass; artifact/run reproducible; bias/overfit detection đạt eval.

#### EA4 — News and Market intelligence

Mapping: bắt đầu sau AT4B; production sau source/freshness eval riêng.

- News: event brief, source comparison, watchlist-impact hypothesis;
- Market: selected-symbol/index context, movers explanation, market/news drill-down;
- artifact: cited brief, monitored-variable checklist, market context card;
- write: optional save/note/watchlist proposal, explicit confirm;
- paper order/reset endpoints nằm ngoài Tool Registry.

Gate: source coverage/freshness đạt; advice/forecast/order violations bằng 0 critical.

#### EA5 — Home Journey Coach

Mapping: sau AT4A và ít nhất EA1 + một domain artifact workflow đạt production gate.

- tổng hợp compact reviewed summaries;
- chọn một next-best learning/research action;
- deep-link đến đúng lesson/report/article/run;
- không fan-out toàn hệ thống khi Home load;
- cache theo account/context version với budget thấp.

Gate: next-action relevance/completion uplift, cross-surface leakage bằng 0.

#### EA6 — Internal Operations Agents

Mapping: sau AT7 khi trace/eval volume đủ lớn.

- Trust Ops Triage;
- Content QA;
- Eval/Cost Analyst;
- Data Quality diagnostic assistant.

Gate: human acceptance và triage-time improvement; auto-publish/auto-close/auto-change configuration bằng 0.

#### Embedded priority order

```text
EA0 foundation
→ EA1 Learn
→ EA2 BCTC
→ EA3 Simulation
→ EA4 News/Market
→ EA5 Home
→ EA6 Internal Ops
```

EA4 có thể chạy song song với EA2/EA3 nếu identity, source contract và team capacity cho phép, nhưng không được làm chậm Core Tutor MVP. Mỗi release chỉ nên đưa 1–2 capability mới vào controlled cohort để đo uplift độc lập.

## 13. Quantitative Finance Research roadmap

“Quantum” trong tên program chỉ quantitative finance. Lane này bọc canonical live implementation tại `src/risk_dashboard/engines/quant/`; quantum computing không phải một phase hiện tại hoặc future product expectation.

### QF0 — Contracts and grants

Bắt đầu sau AC0/AC2, ID1 và AIR0/AIR1.

- khóa request/tool/artifact schema `1.0.0`;
- server-resolved principal và read-only grants;
- client không gửi scope, tool name, model path hoặc authority fields.

Exit gate: invalid combinations/path injection bị reject; contract tests green.

### QF1 — Canonical engine adapters

Bắt đầu sau QF0.

- wrap `run_quant_eod`, `rerun_with_macro_override`, `build_model_research_report`;
- output có source refs, freshness và typed failure;
- zero new import từ deprecated `risk_dashboard.quant`;
- parity fixture so sánh adapter với canonical engine và live compatibility wrapper.

Exit gate: exact core output parity; không training/model write/trading side effect.

### QF2 — Service and numeric reviewer

Bắt đầu sau QF1 và FakeProvider.

- model chỉ giải thích typed payload;
- deterministic reviewer exact-compare mọi metric;
- NaN/Inf, thiếu provenance hoặc mismatch tạo blocked artifact.

Exit gate: injected numeric mismatch block rate 100%; mọi artifact có limitations.

### QF3 — API and module

Bắt đầu sau QF2 và Agentic Core run/artifact API.

- hai read-only endpoints với ownership/scope checks;
- module flag disabled mặc định;
- existing `quant_risk` routes giữ nguyên trong compatibility window.

Exit gate: unauthorized/cross-account success = 0; OpenAPI snapshots pass.

### QF4 — Compatibility rollout

Bắt đầu sau QF3.

- offline golden parity;
- internal rồi canary cohort;
- reversible feature flag;
- không redirect/remove old routes hoặc xóa deprecated shim.

Exit gate: numeric/error behavior parity và release thresholds được product owner khóa trước canary.

## 14. Dependency map

```text
AT0 → AT1 → AT2 → AT3 ─┬→ AT4A ─┐
                        └→ AT4B ─┴→ AT5 → AT6 → AT7

AC0/AC2 + ID1 + AIR0/AIR1 → QF0 → QF1 → QF2 → QF3 → QF4

AT0 + AT1 + AT2 → EA0
AT3             → EA1
AT5             → EA2
AT6             → EA3
AT4B + source eval → EA4
AT4A + EA1 + one production domain artifact → EA5
AT7 + operational evidence → EA6
```

Core Tutor MVP:

```text
AT0 + AT1 + AT2 + AT3
```

Tutor production beta:

```text
Core MVP + AT4A + AT4B
```

Expanded commercial product:

```text
AT5 + AT6 + AT7
```

Agentic ecosystem beta:

```text
EA0 + EA1 + EA2 + one of EA3/EA4 + AT4A + AT4B
```

## 14A. Build order, phase entry criteria and validation checkpoints

> Section này tổng hợp gap findings từ brainstorm session 24/08/2026.
> Bổ sung cho §12 (roadmap) và §17 (DoD) bằng entry/exit criteria cụ thể.

### 14A.1. Phase priority tiers

| Priority | Phases | Lý do |
|---|---|---|
| **P0 — Blocker** | AT0, AT1, AT2 | Foundation: identity, runtime, tools, graph. Mọi module khác phụ thuộc. |
| **P0 — Core MVP** | AT3 | Vertical slice: proves agentic learning works end-to-end. |
| **P1 — Production** | AT4A, AT4B | Memory hardening + SSE. Cần cho paid pilot. |
| **P1 — Expanded** | AT5, AT6 | BCTC + Simulation. Product differentiation. |
| **P2 — Scale** | AT7, EA0–EA6 | Pilot, embedded experiences, ops. |
| **P3 — Quant Research** | QF0–QF4 | Read-only quantitative engine integration. Không block core product. |
| **Hold** | 12 Legacy | Chỉ mở qua reactivation gate. |

### 14A.2. Phase entry criteria

Mỗi phase CHỈ bắt đầu khi tất cả entry criteria đạt.

| Phase | Entry criteria bắt buộc |
|---|---|
| **AT0** | 1. Architecture review hoàn tất và ADR cho model, persistence, streaming đã lock. |
| | 2. `modules/auth` có ResolveSession contract hoặc ADR cho canonical identity dependency. |
| | 3. Threat model document exist và reviewed bởi security owner. |
| | 4. Eval harness infra baseline (gold-set storage, runner, regression detection) đã design. |
| **AT1** | 1. AT0 exit gate đạt hoàn toàn. |
| | 2. Domain module API surface inventory đã complete (learning, financials_product, quant_risk, simulation_lab/pro_lab, news_intelligence, market_summary). |
| | 3. Mỗi domain tool contract có typed input/output/provenance/freshness schema. |
| **AT2** | 1. AT1 exit gate đạt. |
| | 2. `platform/ai_runtime` ADR đã decide: mở rộng model_runtime hay tạo mới. |
| | 3. Fake provider và fake domain tools sẵn sàng cho orchestration tests. |
| | 4. Sub-feature flag enforcement mechanism đã decide (registry-level vs middleware vs decorator). |
| **AT3** | 1. AT2 exit gate đạt. |
| | 2. Gold-set ≥100 câu bao phủ: factual, numeric, reasoning, unsafe, tool failure, injection. |
| | 3. Persona definition đã review và approve (tutor tone, Vietnamese register, teaching style). |
| | 4. Learn Hub contextual panel UI skeleton sẵn sàng. |
| **AT4A** | 1. AT3 exit gate đạt. |
| | 2. Memory retention TTLs đã approve: preference, misconception, summary, audit event. |
| | 3. User memory controls API (view/edit/forget/export) đã implement. |
| **AT4B** | 1. AT3 exit gate đạt. |
| | 2. SSE endpoint design reviewed và contract-locked. |
| | 3. Cache isolation strategy đã decide (account-scoped keys, TTL, invalidation). |
| **AT5** | 1. AT4A + AT4B exit gate đạt. |
| | 2. BCTC formula registry có ≥5 ratios được domain expert approve. |
| | 3. Numeric reviewer threshold đã set (grounded rate, unsupported claim threshold). |
| **AT6** | 1. AT5 exit gate đạt. |
| | 2. Pro Lab → shared runtime migration checklist đã review. |
| | 3. Behavior parity tests đã write (existing Pro Lab behavior vs new runtime). |
| | 4. Reproducibility contract template đã approve. |
| **AT7** | 1. AT6 exit gate đạt. |
| | 2. ≥2 embedded capabilities (EA1, EA2) đã production-ready. |
| | 3. Cost dashboard có per-surface, per-mode breakdown. |
| | 4. Data source licensing review hoàn tất cho pilot cohort. |
| **EA0–EA6** | Mỗi EA chỉ start khi AT dependency tương ứng đã exit. Xem §14 dependency map. |
| **QF0–QF4** | Mỗi QF phase start khi dependency tương ứng đã exit; Quant product/domain owner đã assign. |

### 14A.3. Execution order for implementation

Nguyên tắc: foundation trước, vertical slice sau, domain expansion cuối. Không triển khai `00–11` đồng thời.

#### Phase 0 — Chuẩn bị baseline

1. Dọn trạng thái Git:
   - resolve conflict `data/global_market_prices/global_market_snapshot.json` trước implementation commit;
   - không stage `.claude/settings.json` hoặc credential-bearing files;
   - review và đưa bộ Agentic Quantum docs vào baseline;
   - chạy test suite hiện tại để ghi nhận baseline.
2. Khóa AI Runtime boundary:
   - `src/risk_dashboard/platform/ai_runtime/` là LLM provider runtime mới;
   - `src/risk_dashboard/platform/model_runtime/` giữ local model-path health hiện tại;
   - không hợp nhất hai responsibility trong MVP.
3. Khóa Gemini integration:
   - thêm official `google-genai` dependency;
   - production model cố định `gemini-3.5-flash`;
   - server config chuẩn: `AI_PROVIDER=google`, `AI_MODEL=gemini-3.5-flash`, `AI_FALLBACK_ENABLED=0`, `GEMINI_API_KEY`;
   - request/client không được override model/provider.

Exit gate: working tree không còn unmerged file; `git diff --check` pass; baseline tests đã ghi nhận; Gemini dependency và model-policy assertion sẵn sàng.

#### Phase 1 — Identity & Trust Foundation

1. `ID0` identity inventory:
   - liệt kê endpoint nhận `session_id`, `user_id`, `account_id`;
   - phân loại server-resolved vs client-supplied;
   - lập migration list, chưa sửa toàn bộ endpoint trong WP này.
2. `ID1` canonical principal:
   - tạo `src/risk_dashboard/modules/auth/schemas/principal.py`;
   - implement `ConsentSnapshot`, `AuthPrincipal` và FastAPI dependency bọc `ResolveSession`;
   - scopes/assurance/consent resolve server-side.
3. `ID2` ownership và entitlement:
   - deny-by-default policy;
   - scope/resource/operation checks;
   - recheck tại tool execution và action confirmation;
   - two-account IDOR matrix.

Exit gate: một shared dependency duy nhất phát `AuthPrincipal`; cross-account successful access bằng 0; endpoint agentic mới không nhận authority fields từ client.

#### Phase 2 — AI Runtime

1. `AIR0` provider-neutral contracts:
   - tạo `contracts.py`, `provider.py`;
   - implement `ModelMessage`, `ModelSettings`, `ModelTask`, `TokenUsage`, `ModelResult`, `ModelError`, `LLMProvider`.
2. `AIR1` `FakeProvider`:
   - deterministic scripted output;
   - inject delay/timeout/error/malformed JSON;
   - orchestration tests không cần network.
3. `AIR2` `GeminiAdapter`:
   - official `google-genai` SDK;
   - model fixed `gemini-3.5-flash`;
   - message mapping, structured output, function calls, usage, finish reason, health;
   - provider error sanitization.
4. `AIR3` guardrails:
   - deadline, bounded retry, cancellation, size limits, redaction, budget checks.
5. `AIR4` telemetry:
   - token/cost/latency/finish_reason/model_policy_version/correlation_id;
   - no raw credential/prompt/private context in traces.

Exit gate: `GeminiAdapter` + `FakeProvider` pass contract suite; no domain module imports `google.genai`; no production fallback.

#### Phase 3 — Agentic Core foundation

1. `AC0` schema freeze:
   - `TrustedExecutionEnvelope`, `ExecutionBudget`, `ResourceRef`, `AgentRun`, `AgentStep`, `ToolCall`, `AgentArtifact`, `ActionProposal`, `ActionReceipt`, `MemoryProposal`, failure envelope;
   - all root contracts `schema_version="1.0.0"`.
2. `AC1` persistence:
   - additive migrations và repositories cho runs, steps, tool calls, artifacts, proposals, receipts, audit events, idempotency.
3. `AC2` tool registry và grants:
   - versioned manifests;
   - one-run grants;
   - scope/resource/operation/expiry/budget checks;
   - forbidden tool denial.
4. Foundation integration checkpoint:

```text
AuthPrincipal
→ TrustedExecutionEnvelope
→ ToolGrant
→ FakeProvider
→ reviewed AgentArtifact
→ terminal AgentRun
→ audit/telemetry
```

Exit gate: offline E2E không cần network; timeout/cancel/budget/schema failure đều có terminal state; không domain mutation.

#### Phase 4 — Agentic Core orchestration

Chỉ bắt đầu sau Foundation F1.

1. `AC3` bounded run service:
   - run creation, context snapshot, direct/single-specialist mode;
   - max steps/tool calls/wall time/cost;
   - cancellation, resume/retry, terminal state.
2. `AC4` review pipeline:
   - Claim Ledger;
   - Evidence Reviewer;
   - Numeric Reviewer;
   - Safety/Policy Reviewer;
   - Final Composer không thêm claim mới.
3. `AC5` artifact/action lifecycle:
   - `ActionProposal` → preview → explicit confirmation → re-auth/re-authorization → domain application service → immutable `ActionReceipt`;
   - mutation path có thể hoãn nếu vertical slice đầu chỉ read-only.

Exit gate: mọi run có terminal state; unsupported claim bị block; numeric claim evidence coverage 100%; forbidden action không tạo proposal.

#### Phase 5 — AI Tutor + Learn vertical slice

1. `TUT0` module/API skeleton:
   - tạo `modules/ai_tutor`;
   - registry wiring;
   - disabled-by-default feature flag;
   - request không nhận identity authority.
2. `TUT1` conversation persistence:
   - conversations, messages, feedback, idempotency, ownership, retention metadata.
3. `LEARN0/LEARN1` typed learning tools:
   - lesson context, quiz/checkpoint, progress, next lesson/recommendation, reviewed citations.
4. `TUT2` single-specialist flow:

```text
Question
→ Learning context tool
→ GeminiAdapter
→ evidence review
→ Tutor response
→ optional checkpoint
```

5. Vertical-slice E2E:

```text
Login
→ open lesson
→ ask grounded question
→ receive cited explanation
→ complete checkpoint
→ verified progress update
```

Exit gate: grounded response đạt target; cross-account leakage = 0; prompt-injection fixtures bị chặn; feature flag rollback về deterministic Learn flow; cost/latency đo được.

#### Phase 6 — Production hardening

1. `ID3–ID7`: consent lifecycle, session hardening, retention, export/delete, operational access, break-glass.
2. `AIR5`: SSE streaming, ordered events, disconnect cancellation, reconnect without duplicate.
3. `AC6–AC8`: memory governor, user memory controls, feature-flag extensions, kill switch, degradation, retention enforcement.
4. `AIR6`: migrate Pro Lab direct `ChatOpenAI` calls sang `LLMProvider → GeminiAdapter → gemini-3.5-flash` sau behavior/eval parity.

Exit gate: memory/privacy/security tests pass; streaming có terminal events; Pro Lab migration không có OpenAI production fallback.

#### Phase 7 — Domain agents

Triển khai tuần tự, mỗi release chỉ 1–2 capability:

1. BCTC Agent — numeric claim map 100% về report/revision/formula evidence.
2. Simulation Agent — reproducibility, no live trading, run/artifact writes qua confirmation.
3. News Agent — untrusted article handling, citations/freshness, save brief qua confirmed write.
4. Market/Portfolio Agent — strict read-only; không order/reset/rebalance/watchlist mutation.
5. Home Journey Agent — sau consented memory và ≥1 reviewed domain artifact; trả `0..1` next-best action.
6. Internal Ops Agent — read/draft/recommend only; không publish/incident mutation/config change/shell/SQL/log search.
7. Quant Research Agent — EOD, scenario, model report; exact numeric reviewer; compatibility parity với existing Quant Risk routes.

Exit gate: mỗi capability có feature flag riêng, kill switch, ownership/security tests, deterministic fallback, latency/cost dashboard, eval regression và rollback.

#### Phase 8 — Controlled rollout

```text
offline fixtures
→ local integration
→ internal accounts
→ canary cohort
→ limited beta
→ production
```

Mỗi rollout gate phải có outcome, trust, economics và rollback evidence.

#### Critical path rút gọn

```text
Clean Git baseline
→ Lock AI Runtime path
→ Add google-genai
→ ID0 → ID1 → ID2
                 ┐
→ AIR0 → AIR1 → AIR2 → AIR3 → AIR4
                 ├→ AC3 → AC4
→ AC0 → AC1 → AC2
                 ┘
→ AI Tutor + Learn vertical slice
→ Production hardening
→ BCTC
→ Simulation
→ News + Market/Portfolio
→ Home
→ Internal Ops
→ Quant Research
→ Controlled rollout
```

#### Parallel lanes cho sprint đầu

| Lane | Thứ tự | File ownership |
|---|---|---|
| Identity | `ID0 → ID1 → ID2` | `modules/auth`, shared policy tests |
| AI Runtime | `AIR0 → AIR1 → AIR2 → AIR3 → AIR4` | `platform/ai_runtime`, dependency config |
| Agentic Core foundation | `AC0 → AC1 → AC2` | `modules/agentic_core`, migrations |

Điểm hội tụ: `ID1 + AIR0 + AIR1 + AC0–AC2 → foundation integration → AC3 orchestration`.

#### Sprint đầu tiên nên làm

1. Dọn Git baseline.
2. Khóa `platform/ai_runtime`.
3. Thêm `google-genai`.
4. Implement `AuthPrincipal`.
5. Implement AI Runtime contracts.
6. Implement `FakeProvider`.
7. Implement `GeminiAdapter`.
8. Freeze Agentic Core schemas.
9. Implement Tool Registry/Grant foundation.
10. Chạy offline foundation integration test.

Không bắt đầu frontend hoặc domain agents trong sprint đầu.

### 14A.4. Validation checkpoints giữa các phase

Sau mỗi phase, chạy validation checkpoint trước khi chuyển phase tiếp:

| Checkpoint | Sau phase | Kiểm tra | Pass condition |
|---|---|---|---|
| **VP-AT0** | AT0 | Identity inventory completeness | 100% endpoints mapped; zero client-trusted `user_id` |
| | | Threat model coverage | ≥15 attack vectors documented với controls |
| | | Eval harness baseline | ≥100 gold-set questions, runner chạy được, regression detectable |
| **VP-AT1** | AT1 | Tool contract completeness | ≥6 domain tools có typed schema, provenance, freshness |
| | | Deterministic baseline | Mỗi tool chạy offline, trả correct output cho golden inputs |
| | | Domain API surface readiness | Không domain API thiếu required fields cho tool contract |
| **VP-AT2** | AT2 | Runtime isolation | Agentic Core và AI Tutor KHÔNG import provider SDK trực tiếp |
| | | Fake provider coverage | Graph, retry, cancellation, streaming tests chạy với fake |
| | | Feature flag infra | Sub-feature flags enforce được (not just module-level) |
| | | Embedded skeleton | Fake-provider flow: CTA → artifact → action receipt hoạt động |
| **VP-AT3** | AT3 | Core MVP quality | Grounded ≥95%, numeric coverage 100%, zero cross-user access |
| | | Learning session E2E | ≥1 complete verified learning session từ lesson → checkpoint → progress |
| | | Multi-agent baseline | Single-specialist là default; sequential chỉ bật khi eval chứng minh uplift |
| | | Coverage | Unit + integration + E2E ≥80% cho AT0–AT3 scope |
| **VP-AT4** | AT4A+AT4B | Memory safety | Cross-user memory leakage = 0 |
| | | User memory controls | View/edit/forget/export/disable hoạt động end-to-end |
| | | SSE reliability | Reconnect không duplicate; mọi stream có terminal event |
| | | Cache isolation | Cross-account cache leakage = 0 |
| **VP-AT5** | AT5 | BCTC numeric integrity | 100% numeric claims map về tool evidence |
| | | Formula registry | ≥5 approved formulas với units, applicability, limitations |
| **VP-AT6** | AT6 | Pro Lab migration | Zero direct provider calls ngoài shared runtime |
| | | Reproducibility | Every critique pins run/data/engine versions |
| | | Trading boundary | order/broker/execution tools fail closed |
| **VP-AT7** | AT7 | Pilot readiness | ≥3 embedded capabilities production-ready |
| | | Economics | p95 latency và contribution margin trong budget |
| | | Go/no-go decision | Outcome + Trust + Economics gates đồng thời pass |

### 14A.4. Tutor persona definition

> Gap finding: không module plan nào define tutor persona.

Persona cho MVP:

| Attribute | Value |
|---|---|
| Name | Northstar Tutor |
| Language | Vietnamese (default), English khi user chuyển |
| Tone | Professional-educational, không casual, không robot |
| Teaching style | Socratic khi context đủ; explanatory khi context mới |
| Formula presentation | Variable definitions → substitution → units → result → limitations |
| Error handling | "Hiện tại em chưa có đủ dữ liệu để trả lời chính xác. Câu hỏi này cần kiểm tra thêm..." |
| Disclaimer prefix | Khi đề cập investment: "Đây là giáo dục, không phải khuyến nghị đầu tư." |
| Memory voice | Không tự xưng "em" trong durable memory; third-person cho audit logs |

Persona review gate: approve trước AT3 start. Persona refinement sau pilot data.

### 14A.5. Sub-feature flag enforcement

> Gap finding: master plan §16 list 25+ flags nhưng không decide enforcement mechanism.

Decision:

```text
Registry-level module flags  → module ON/OFF (hiện có)
Middleware/decorator flags   → sub-feature ON/OFF (cần thêm)
```

Live reality: runtime hiện chỉ có `FeatureFlagService.is_enabled(flag_name, default=False)`. Chưa có decorator, middleware enforcement, cache/polling, admin refresh/mutation audit hoặc graceful drain.

AC7 proposed implementation:

- `@feature_flag("module.ai_tutor.multi_agent")` hoặc middleware tương đương sau khi contract được khóa;
- luôn chạy auth/ownership trước khi trả resource-sensitive response; flag không được bypass security dependency;
- cache/refresh/admin mutation/audit/drain là deliverables riêng, có contract và tests;
- rollback: toggle flag → stop new runs → deterministic fallback; in-flight drain chỉ bật sau khi AC7 chứng minh semantics.

Không plan nào được claim các capability AC7 trên là live trước acceptance tests của AC7.

### 14A.6. Memory retention TTLs

> Gap finding: memory TTLs unspecified across all modules.

| Memory type | TTL | Renewal | Deletion |
|---|---|---|---|
| Conversation message | 90 days (configurable) | Extend on new message in same conversation | soft delete → hard delete sau 30 days |
| Conversation summary | Same as raw conversation | Auto-generate từ messages | Delete cùng raw |
| Preference (explicit) | Until user delete hoặc override | Supersede on new preference | User-initiated delete |
| Goal (explicit) | Until achieved hoặc user delete | Update on progress | User-initiated delete |
| Verified mastery | 12 months, renewable | Extend on verified checkpoint | Decay → "needs review" |
| Misconception | Until verified correction | Supersede on correction | Auto-delete sau 2 corrections |
| Summary (agent-generated) | 30 days | Recompute | Auto-delete, rebuild on next run |
| Audit event | 12 months | Append-only | Archive → hard delete theo policy |
| Artifact (reviewed) | 90 days hoặc until source stale | Recompute khi source thay đổi | Auto-expire hoặc user delete |
| Action receipt | 12 months | Append-only | Archive |
| Knowledge cache (shared) | Version-pinned | Refresh khi content version thay đổi | Bump version |

Work package: `AC8` trong Module 00. TTL values cần approval từ product + compliance trước AT4A.

### 14A.7. Performance targets per module

> Gap finding: master §11.3 có targets nhưng module plans không reference.

| Module | Endpoint type | p50 target | p95 target | Cost ceiling |
|---|---|---|---|---|
| 00 Agentic Core | Run creation | <200ms | <500ms | — |
| 00 Agentic Core | Tool execution | <300ms | <800ms | — |
| 01 Identity | Session resolve | <50ms | <150ms | — |
| 02 AI Runtime | Model call (excl. network) | <100ms | <300ms | — |
| 03 AI Tutor | Conversation create | <200ms | <500ms | — |
| 03 AI Tutor | Single-specialist response | <3s | <6s | $0.02/session |
| 03 AI Tutor | Sequential/parallel | <6s | <10s | $0.05/session |
| 04 Learn | Checkpoint grade | <500ms | <1s | — |
| 05 BCTC | Ratio calculation | <200ms | <500ms | — |
| 05 BCTC | Evidence memo | <3s | <8s | $0.03/memo |
| 06 Simulation | Run critique | <3s | <8s | $0.04/critique |
| 07 News | Brief generation | <3s | <8s | $0.02/brief |
| 08 Market | Portfolio review | <2s | <6s | $0.03/review |
| 09 Home | Next-best-action | <1s | <2s | $0.005/request |
| 10 Ops | Investigation report | <5s | <15s | $0.05/report |

Targets là aspirational cần validate qua pilot. Dashboard AT7 phải track actual vs target.

## 15. Test and evaluation plan

### 15.1. Unit tests

- domain policies;
- state transition;
- artifact/action proposal lifecycle;
- confirmation expiry, target-version mismatch và idempotency;
- router và execution-mode selection;
- handoff budget/cycle prevention;
- Tool Grant validation;
- numeric claim matcher;
- Claim Ledger merge và conflict rule;
- MemoryProposal governor, dedupe, supersede và expiry;
- redaction;
- freshness;
- calculation formatting;
- error mapping.

### 15.2. Contract tests

- provider protocol;
- GeminiAdapter và FakeProvider structured output;
- migration parity suite cho các legacy OpenAI call sites;
- function call ID/name/count;
- every domain tool;
- TrustedExecutionEnvelope/ModelTask/AgentResult;
- Claim/ReviewDecision/FailureEnvelope;
- AgentArtifact/ActionProposal/ActionReceipt;
- capability manifest và surface allowlist;
- skill manifest và Tool Grant;
- graph state/checkpoint version compatibility;
- repository ports;
- memory preference/item/export/delete APIs;
- SSE event schema.

### 15.3. Integration tests

- session resolve → account ID;
- conversation ownership;
- unauthorized/expired/revoked session;
- persistence/idempotency;
- graph resume/retry;
- provider timeout;
- tool failure;
- reviewer rejection;
- single → sequential handoff;
- bounded parallel fan-out và partial-branch failure;
- Final Composer không thêm claim ngoài accepted ledger;
- memory proposal → governor → event → current view;
- memory disable/delete → cache/index invalidation;
- feedback ownership.
- embedded CTA → run → artifact → review → delivery;
- proposal confirm → domain service → action receipt;
- proposal reject/expire/version-change không tạo domain write;
- Home chỉ đọc reviewed cross-surface summaries.

### 15.4. Security tests

- cross-user conversation access;
- cross-user memory/summary/index/cache retrieval;
- prompt and indirect injection;
- stored injection qua memory, lesson, report và tool result;
- memory poisoning và unauthorized auto-capture;
- tool permission escalation;
- forged `agent_id`, `execution_mode`, `tool_grant_refs`, `account_id` và namespace;
- forged capability/surface/resource/action target/confirmation token;
- direct invocation của paper-order/reset/Admin publish tools từ mọi agent;
- confused-deputy giữa News, Market, BCTC và Admin scopes;
- PII/log redaction;
- rate limit;
- capability/concurrent-run/cost rate limits;
- replay/duplicate request;
- ActionProposal unknown-field/mass-assignment và target-version race;
- malicious upload: MIME/extension/magic mismatch, archive bomb, embedded instruction/script;
- XSS-safe AI rendering;
- citation URL scheme/domain validation, CORS và security headers;
- generic client error không lộ stack/prompt/tool payload;
- CSRF nếu dùng cookie.

### 15.5. E2E tests

- Learn lesson → ask Tutor → answer → checkpoint → progress;
- Learn multi-agent route → reviewed answer → MemoryProposal confirmation;
- user xem, sửa, quên, export và disable memory;
- cancel and retry;
- stale source warning;
- BCTC Company → Quant → Learning explanation có calculation và citations;
- BCTC evidence memo → note proposal → preview → confirm → receipt;
- News cluster → cited brief → optional save proposal;
- Market/portfolio review → risk artifact và không có order CTA;
- Simulation → Quant critique có run ID và limitations;
- Simulation hypothesis → validation plan → confirmed run config → critique artifact;
- Home next-best action → deep-link đúng resource;
- partial specialist failure → safe degraded response;
- stream disconnect/reconnect.

### 15.6. Eval regression

Gold-set phải bao phủ:

- factual grounding;
- numeric correctness;
- multi-tool reasoning;
- routing accuracy theo execution mode;
- single-specialist baseline so với sequential/parallel plan;
- handoff quality và branch-conflict adjudication;
- insufficient context;
- stale/conflicting data;
- unsafe advice;
- prompt injection;
- memory precision, poisoning và stale/conflict handling;
- unsupported Quantum advantage claim;
- model/tool failure;
- Vietnamese explanation quality;
- learning checkpoint quality.
- embedded artifact usefulness/completion;
- action proposal precision và confirmation comprehension;
- per-surface non-agent/deterministic baseline;
- forbidden-action compliance;
- cross-surface routing/context minimization.

## 16. Rollout

### Feature flags

```text
module.agentic_core.enabled
module.agentic_core.embedded.enabled
module.agentic_core.actions.enabled
module.ai_tutor.enabled
module.ai_tutor.multi_agent.enabled
module.ai_tutor.streaming.enabled
module.ai_tutor.bctc.enabled
module.ai_tutor.simulation.enabled
module.ai_tutor.quantum_content.enabled
module.ai_tutor.quantum_tools.enabled
module.ai_tutor.agent.learning.enabled
module.ai_tutor.agent.quant_risk.enabled
module.ai_tutor.agent.company.enabled
module.ai_tutor.agent.simulation.enabled
module.ai_tutor.agent.quantum.enabled
module.agentic_core.memory.enabled
module.agentic_core.memory.auto_capture.enabled
module.agentic_core.embedded.learn.enabled
module.agentic_core.embedded.bctc.enabled
module.agentic_core.embedded.simulation.enabled
module.agentic_core.embedded.news.enabled
module.agentic_core.embedded.market.enabled
module.agentic_core.embedded.portfolio_review.enabled
module.agentic_core.embedded.home.enabled
module.agentic_core.embedded.internal_ops.enabled
```

Registry hiện chỉ enforce module-level flag. AT0 phải quyết định cách enforce sub-feature flags trước khi dùng các flag trên.

### Rollout order

```text
local fake provider
→ internal staff
→ one embedded capability/internal surface
→ controlled learner/domain cohort
→ paid pilot
→ broader beta
```

Rollback:

- tắt specialist/surface bằng feature flag;
- tắt riêng embedded capability hoặc toàn bộ ActionProposal apply, giữ deterministic domain UI hoạt động;
- hạ multi-agent về single-specialist hoặc direct deterministic mode;
- tắt auto-capture mà không làm mất quyền xem/sửa/xóa memory hiện có;
- giữ conversation history theo retention policy;
- deterministic fallback phải ghi rõ model/tool unavailable;
- không fallback sang model khác.

## 17. Definition of done

### 17.1. Core Tutor MVP DoD — kết thúc AT3

Core MVP được coi là hoàn tất khi:

1. `modules/agentic_core` và `modules/ai_tutor` được mount đúng dependency; module/specialist feature flags được enforce.
2. LangGraph bounded workflow chạy end-to-end ở direct và single-specialist mode.
3. Learning → Quant sequential handoff chỉ chạy internal/eval flag; production route vẫn fallback single nếu chưa vượt added-value gate.
4. Identity được resolve server-side và ownership có integration test.
5. Conversation/message/feedback có persistence, idempotency và retention.
6. Domain tools có typed provenance/freshness/failure contract và scoped Tool Grant.
7. Evidence/Numeric và Safety reviewers chạy trước response delivery.
8. Final Composer chỉ dùng claim đã pass review; numeric claim-evidence coverage đạt 100%.
9. Provider/model policy fail fast; production dùng cố định Gemini `gemini-3.5-flash` và không có model fallback.
10. Trust/safety bao phủ injection, advice boundary, PII và step/tool/time/token/cost budgets.
11. TrustedExecutionEnvelope/ModelTask/AgentResult/Claim/ReviewDecision/FailureEnvelope và handoff versioning được enforce.
12. Mọi run có terminal state; latency, failure, token/cost và learning events được đo.
13. Learn Hub hoàn thành ask → answer → checkpoint → progress loop.
14. “Quantum” được dùng nhất quán với nghĩa quantitative finance; QC claims/dependencies bằng 0.
15. Eval regression đạt pilot gate liên quan và unit/integration/E2E coverage tổng đạt tối thiểu 80% cho phạm vi Core MVP.

### 17.2. Production Beta DoD — kết thúc AT4A và AT4B

Production Beta chỉ được coi là hoàn tất khi thỏa Core MVP và:

1. Durable memory chỉ đi qua `MemoryCandidate` → Deterministic Memory Governor → `MemoryProposal`, có provenance và audit.
2. User có quyền xem, sửa, quên, export và disable memory; conversation retention được quản lý riêng.
3. Cross-user conversation/memory/index/cache leakage bằng 0 trên security test suite.
4. Deletion đang diễn ra có snapshot invalidation, delivery suppression/rebuild và SLA cho cache/backup.
5. SSE reconnect/cancel/idempotency và terminal event đạt AT4B gate.
6. Mọi sequential/parallel route được bật cho production đều vượt added-value gate so với single-specialist baseline.
7. Coverage tối thiểu 80% được duy trì cho toàn phạm vi AT0–AT4B.

### 17.3. Embedded Agent capability DoD

Mỗi capability EA chỉ được gọi là production-ready khi:

1. Có capability manifest gồm trigger, owner, allowed surfaces, ModelTask, tools, risk class, artifact/action schemas, budgets, failure map và eval suite.
2. Chạy được từ embedded CTA mà không cần tạo chat conversation giả.
3. Resource context được server resolve theo canonical account/ownership/version.
4. Output là reviewed `AgentArtifact` hoặc typed failure; không chỉ là prose không kiểm chứng.
5. Mọi write đi qua `ActionProposal` preview, confirmation/re-authorization và domain application service; ngoại lệ verified Learning checkpoint được ghi rõ.
6. Forbidden action test chứng minh agent không thể order/reset, publish, close incident hoặc dùng tool ngoài capability grant.
7. Artifact/action/run có audit, idempotency, cancel/retry và terminal state.
8. Surface-specific quality, safety, performance, cost và outcome gate vượt deterministic/non-agent baseline.
9. Feature flag có thể tắt riêng capability, agent và action write mà không làm hỏng deterministic product flow.
10. User-facing UI cho biết agent đang làm gì, nguồn nào được dùng, bước nào cần confirm và limitation nào còn tồn tại.

## 18. Non-goals

- Generic financial chatbot.
- Autonomous trading hoặc order execution.
- Personalized buy/sell recommendation.
- Autonomous swarm.
- Free-form agent-to-agent chat hoặc specialist tự stream câu trả lời.
- Chạy Multi-Agent cho mọi request chỉ để tăng cảm giác “agentic”.
- Biến mọi CRUD endpoint, filter, chart hoặc CTA thành Agent.
- Invisible background agent tự chạy xuyên surface mà user không biết.
- Dùng Home như global autonomous supervisor quét toàn bộ dữ liệu user mỗi lần tải trang.
- General shell/browser/MCP access cho model trong MVP.
- Agentic RAG/memory ingestion cho user-uploaded/private knowledge trong AT0–AT7; existing BCTC upload chỉ được dùng qua sanitized analyzed revision.
- Agent tự cấp quyền tool hoặc tự sửa/publish production skill.
- User-selectable model/provider.
- Model fallback trong MVP.
- Global long-term memory không có retention boundary.
- LLM tự tính số liệu tài chính.
- Quantum-computing dependencies, credentials, circuits, simulators, hardware, experiments hoặc product claims.
- Thay toàn bộ deterministic workflow bằng LLM.

## 19. Open questions

Các câu hỏi không chặn AT0 nhưng phải được khóa trước phase liên quan:

1. Pilot syllabus đầu tiên là Quant Foundation hay Risk Foundation?
2. Session hardening dùng secure cookie hay bearer opaque token?
3. Retention mặc định cho conversation và feedback là bao lâu?
4. Ai duyệt financial correctness và Quant Research artifacts?
5. Cost budget mỗi verified learning session là bao nhiêu?
6. Data source nào có quyền thương mại cho paid pilot?
7. Instructor có được xem raw conversation hay chỉ aggregated progress?
8. QF canary p95/error thresholds và product owner cuối cùng là gì?
9. Quant Research explanation mặc định chỉ tiếng Việt hay song ngữ?
10. Durable memory là opt-in hay opt-out cho pilot, và consent được version hóa thế nào?
11. Retention/TTL riêng cho preference, misconception, summary và audit event là bao lâu?
12. Ngưỡng confidence nào cho routing single/sequential và khi nào phải hỏi lại user?
13. Cost/latency budget tối đa cho parallel plan theo từng paid tier là bao nhiêu?
14. Instructor được xem memory nào, hay chỉ xem mastery/progress đã aggregate?
15. Deletion SLA và quy trình xóa khỏi FTS/vector/cache/backup là bao lâu?
16. Ba embedded capability nào được chọn cho paid pilot: Learn+BCTC+Simulation hay Learn+BCTC+News?
17. Watchlist add/remove có được phép thành confirmed action ở beta đầu hay giữ hoàn toàn read-only?
18. Simulation run budget/entitlement nào yêu cầu confirm lần hai vì chi phí cao?
19. Cross-surface summary nào Home được đọc, TTL bao lâu và user có quyền tắt từng surface không?
20. Internal Ops agent dùng shared model deployment hay deployment/retention policy tách biệt?
21. Artifact nào user có thể export/share và license/citation contract đi kèm là gì?

## 20. Commercialization hypothesis and performance economics

Không bán “số lượng agent”. Giá trị thương mại phải gắn với learning outcome, thời gian phân tích tiết kiệm và mức độ tin cậy của evidence.

| Stage | Offer giả thuyết | Primary user/buyer | Value unit | Điều kiện mở bán |
|---|---|---|---|---|
| Core MVP | Learn Tutor cho Quant/Risk foundation | Learner | verified learning session | AT3 quality/safety gate |
| Production beta | Personalized Tutor có memory và streaming | Learner/subscriber | retained learner + checkpoint uplift | AT4A/AT4B privacy/performance gate |
| Expanded Pro | BCTC + Simulation Research Coach | Analyst/advanced learner | reviewed analysis session | AT5/AT6 numeric and research gate |
| Research Intelligence | News + Market context artifacts | Advanced learner/research user | cited brief/review completed | EA4 source/advice gate |
| Personal Journey | Home next-best-action across reviewed artifacts | Retained subscriber | accepted/completed next action | EA5 privacy/relevance gate |
| Institutional pilot | Cohort Tutor + aggregated learning insights | Training provider/university/team | active seat + completion uplift | AT7 entitlement/privacy/license gate |
| Quant Research | EOD/scenario/model-report explanation | Advanced learner/research partner | reviewed quantitative research artifact | QF4 parity, ownership và latency gates |

Pricing cụ thể là open decision của AT7. Trước đó cần đo unit economics theo công thức:

```text
AI variable cost / successful agentic outcome
= model input/output cost
+ tool/data-source cost
+ retrieval/artifact/storage cost
+ retry/repair/fan-out overhead

Contribution margin / paid session
= allocated revenue
- AI variable cost
- licensed data cost
- support/operations allowance
```

Quy tắc performance-to-margin:

- direct deterministic và single specialist là default để giữ latency/cost;
- multi-agent chỉ được bật khi uplift vượt added-value gate ở mục 11.4;
- cache chỉ dùng cho shared, versioned knowledge; không cache chéo personalized response;
- token, tool, repair và fan-out budget được đặt theo entitlement/tier nhưng không làm giảm safety gate;
- khi hết budget, hệ thống degrade minh bạch về single-specialist/education-only, không âm thầm bỏ citation/reviewer;
- dashboard AT7 phải phân rã cost theo surface, execution mode, agent, successful session và cohort.

Quyết định go-to-market dùng ba gate đồng thời:

1. **Outcome:** learning completion, artifact completion hoặc time-to-insight tăng so với deterministic/non-agent experience.
2. **Trust:** grounding, numeric, privacy và advisory gates đạt.
3. **Economics:** p95 và contribution margin đạt budget pilot.

Không đạt một trong ba gate thì giữ ở research/internal beta hoặc thu hẹp route, không dùng số lượng agent/Quantum branding để bù cho product value chưa chứng minh.

## 21. Handoff

Trạng thái:

```text
Product direction: Ready
Architecture direction: Ready
Direct AT3 implementation: Not ready
Next phase: AT0
Master plan: Ready for ADR and work-package decomposition
Embedded capability map: Ready
```

Handoff đề xuất:

1. Architecture review và đóng băng ADR cho `agentic_core` vs `ai_tutor` vs domain ownership.
2. Dùng [`agentic-quantum/README.md`](agentic-quantum/README.md) để giao owner và dependency cho từng module plan.
3. Product/compliance review advisory boundary.
4. Chuyển AT0 và EA0 thành issues có owner.
5. Chọn ba embedded capability pilot và khóa baseline/KPI riêng.
6. Sau AT0, dùng TDD workflow cho AT1/AT2.
7. Review security trước khi mount endpoint hoặc bật ActionProposal write.
8. Chạy verification loop ở mỗi exit gate.
9. Không bắt đầu QR execution trước classical baseline.
