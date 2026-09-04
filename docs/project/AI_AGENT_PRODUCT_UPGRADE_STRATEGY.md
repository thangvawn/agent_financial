# Northstar Finance Lab — Chiến lược nâng cấp AI Agent và thương mại hóa

> Trạng thái: Khảo sát và định hướng sản phẩm  
> Ngày tổng hợp: 29/07/2026  
> Phạm vi: Product, Finance, Agentic AI, Quant, Quantum, Performance và Commercialization  
> Lưu ý: Tài liệu này không xác nhận việc đã triển khai các capability được đề xuất.

## 1. Executive summary

Northstar Finance Lab nên được định vị là:

> **AI Quant Finance Learning Lab cho thị trường Việt Nam — nơi AI Agent trợ giảng giúp người dùng học, giải thích và kiểm chứng kiến thức tài chính bằng dữ liệu, mô hình định lượng và simulation.**

Vai trò của từng trục:

- **AI/Agentic AI:** động cơ sản phẩm và doanh thu ngắn hạn.
- **AI trong tài chính:** use case thương mại chính.
- **Quantitative Finance và Econometrics:** nền tảng chuyên môn tạo khác biệt.
- **Quantum Computing for Finance:** nhánh nghiên cứu dài hạn, chưa phải sản phẩm thương mại.

Không nên dùng “kinh tế lượng tử” làm headline. Thuật ngữ này dễ bị nhầm với:

- **Kinh tế lượng — Econometrics:** VAR, regression, time series, GARCH và các phương pháp định lượng đang có trong dự án.
- **Tài chính định lượng — Quantitative Finance:** risk model, portfolio risk, SHAP, backtest và scenario.
- **Điện toán lượng tử trong tài chính — Quantum Computing for Finance:** QAOA, quantum optimization hoặc quantum-inspired methods, hiện mới là hướng R&D.

Lợi thế thật hiện tại của dự án là **explainable quant + financial learning surfaces**, chưa phải một chatbot Agentic AI hoàn chỉnh. Vì vậy, hướng nâng cấp hiệu quả nhất là xây một AI Tutor có giới hạn, gắn chặt với Learn Hub, BCTC và Simulation Lab, thay vì mở một chatbot tài chính tổng quát.

## 2. Đánh giá hiện trạng

### 2.1. Scorecard

| Năng lực | Đánh giá khảo sát | Nhận xét |
|---|---:|---|
| Quantitative finance | 4/5 | Tài sản kỹ thuật mạnh nhất của dự án |
| Learning product | 3/5 | Đã có nội dung, quiz, progress, books và media |
| AI workflows | 2.5/5 | Pro Lab có LLM thật nhưng chủ yếu là one-shot workflow |
| AI Tutor/Agent | 1.5/5 | Có thiết kế nội bộ nhưng chưa có flow end-to-end |
| Trust và observability | 3.5/5 | Có nền disclaimer, audit, freshness và latency monitoring |
| Commercial readiness | 2/5 | Chưa có billing, entitlement, pricing và paid funnel hoàn chỉnh |

Các điểm số trên là đánh giá định tính phục vụ ra quyết định sản phẩm, không phải benchmark kỹ thuật chính thức.

### 2.2. Bằng chứng từ runtime

- Product chatbot và multi-agent chat trước đây đã bị gỡ khỏi runtime:
  - [`src/risk_dashboard/engines/README.md`](../../src/risk_dashboard/engines/README.md)
  - [`src/risk_dashboard/app/registry/registry.py`](../../src/risk_dashboard/app/registry/registry.py)
- Learn Hub có tab “Hỏi AI Tutor”, nhưng chưa mở một trải nghiệm tutor riêng:
  - [`frontend/src/features/learn-hub/pages/LearningHomePage.jsx`](../../frontend/src/features/learn-hub/pages/LearningHomePage.jsx)
- Test hiện chủ động kỳ vọng endpoint tutor trả về `404`:
  - [`tests/test_learning.py`](../../tests/test_learning.py)
- Logic tutor nội bộ hiện tạo phản hồi theo template từ lesson, question và knowledge level:
  - [`src/risk_dashboard/modules/learning/domain/policies.py`](../../src/risk_dashboard/modules/learning/domain/policies.py)
  - [`src/risk_dashboard/modules/learning/application/services.py`](../../src/risk_dashboard/modules/learning/application/services.py)
- Quant-agent hiện là luồng router → tool → câu trả lời có provenance, không phải reasoning loop tự chủ:
  - [`src/risk_dashboard/engines/agents/graph.py`](../../src/risk_dashboard/engines/agents/graph.py)
- Các AI workflow gần với sản phẩm thật nhất hiện nằm trong Pro Lab:
  - Strategy Copilot
  - Swarm Committee
  - Backtest Critique
  - [`src/risk_dashboard/modules/pro_lab/api/ai.py`](../../src/risk_dashboard/modules/pro_lab/api/ai.py)

### 2.3. Khoảng cách giữa tài liệu và runtime

Một số tài liệu hiện vẫn mô tả `ai_assistant`, LangGraph hoặc multi-agent surfaces rộng hơn những gì runtime đang cung cấp:

- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)
- [`docs/project/WORK.md`](WORK.md)

Đây là rủi ro PM quan trọng vì proposal, demo hoặc marketing có thể overclaim. Trước khi truyền thông hoặc pilot, cần đồng bộ:

1. Capability đang chạy thật.
2. Capability đang phát triển.
3. Capability chỉ là R&D.
4. Capability đã bị retire.

## 3. Đánh giá nền tảng tài chính định lượng

Benchmark hiện lưu trong repo cho thấy AUC xấp xỉ:

| Horizon | AUC |
|---|---:|
| 1 tuần | 0,654 |
| 2 tuần | 0,696 |
| 1 tháng | 0,722 |

Nguồn:

- [`data/models/risk_model_vnindex_hgb_breadth_20260330T053022Z.json`](../../data/models/risk_model_vnindex_hgb_breadth_20260330T053022Z.json)
- [`data/models/model_benchmark_20260330T034245Z.json`](../../data/models/model_benchmark_20260330T034245Z.json)
- [`data/models/feature_benchmark_20260330T040521Z.json`](../../data/models/feature_benchmark_20260330T040521Z.json)

Đây là kết quả nghiên cứu đáng khích lệ, nhưng chưa đủ để biến sản phẩm thành advisory hoặc risk signal thương mại. Trước khi dùng làm claim sản phẩm, cần xác nhận:

- walk-forward và out-of-time validation;
- số lượng cảnh báo đứng sau precision;
- calibration theo market regime;
- transaction cost, slippage và survivorship bias;
- khả năng tránh look-ahead leakage;
- hiệu năng trên dữ liệu chưa được dùng để lựa chọn feature hoặc tuning;
- data licensing, freshness và SLA.

Trong giai đoạn đầu, quant engine nên được đóng gói như **công cụ học, giải thích và kiểm chứng giả thuyết**, không phải “máy dự báo thị trường”.

## 4. Định vị AI, Quant và Quantum

### 4.1. Cấu trúc nội dung đề xuất

#### Track A — AI Foundations

- Machine learning và deep learning căn bản.
- LLM, prompting, RAG và hallucination.
- Evaluation, monitoring và model limitations.
- Chatbot, workflow và AI Agent khác nhau ở đâu.

#### Track B — Agentic AI for Finance

- Tool use, retrieval, planning, memory và guardrails.
- Agent đọc báo cáo tài chính.
- Agent giải thích risk model.
- Agent phản biện scenario và backtest.
- Kiểm tra số liệu, provenance và compliance.

#### Track C — Quantitative Finance & Econometrics

- Xác suất, thống kê và time series.
- Regression, VAR, GARCH và HMM.
- Portfolio risk, VaR/CVaR và drawdown.
- SHAP, calibration và model evaluation.
- Backtesting, scenario analysis và robustness.

#### Track D — Quantum Finance Lab

- Quantum computing fundamentals.
- QAOA và portfolio optimization.
- Quantum-inspired optimization.
- So sánh với mean–variance hoặc classical optimization.
- Benchmark chất lượng nghiệm, thời gian tính và khả năng mở rộng.

Track D chỉ được đưa thành capability sản phẩm khi có:

1. Code chạy được.
2. Dataset và benchmark tái lập được.
3. So sánh công bằng với classical baseline.
4. Giới hạn phần cứng và phương pháp được công bố rõ.

Tài liệu submission hiện cũng đã xác định Quantum là hướng nghiên cứu, chưa phải chức năng hiện tại:

- [`docs/submissions/ai-quantum-challenge-2026.md`](../submissions/ai-quantum-challenge-2026.md)

## 5. Capability mục tiêu

### 5.1. Capability statement

Người học tài chính và người vận hành lớp học có thể sử dụng một AI Tutor gắn với syllabus, dữ liệu tài chính Việt Nam và các công cụ phân tích của Northstar để:

- đặt câu hỏi theo ngữ cảnh;
- nhận lời giải thích có nguồn và giới hạn;
- gọi đúng công cụ quant/BCTC/simulation khi cần;
- được kiểm tra lại mức độ hiểu;
- lưu tiến độ;
- nhận bước học tiếp theo.

Kết quả cần thay đổi không phải là “người dùng hỏi chatbot nhiều hơn”, mà là:

- hiểu đúng khái niệm hơn;
- hoàn thành learning loop;
- biết kiểm chứng mô hình và giả thuyết;
- giảm hành vi tin vào tín hiệu thiếu bằng chứng;
- chuyển đổi thành người học trả phí hoặc cohort trả phí.

### 5.2. Learning loop

```text
Câu hỏi
   ↓
Xác định lesson, ngữ cảnh và trình độ người học
   ↓
Chọn tool chuyên môn
   ├─ Lesson retrieval
   ├─ BCTC explainer
   ├─ Quant/risk explainer
   └─ Simulation/backtest critic
   ↓
Trả lời có nguồn, số liệu và giới hạn
   ↓
Reviewer kiểm tra số liệu, provenance và safety
   ↓
Câu hỏi kiểm tra hiểu bài
   ↓
Cập nhật tiến độ và đề xuất bài tiếp theo
```

### 5.3. Persona trong MVP

Chỉ nên triển khai ba persona:

1. **Risk & Quant Tutor**
   - Xác suất rủi ro.
   - SHAP và model driver.
   - VaR/CVaR.
   - Macro scenario.

2. **Company Analysis Tutor**
   - BCTC.
   - Dòng tiền và earnings quality.
   - Margin, leverage và liquidity.
   - Red flags và peer comparison.

3. **Simulation Coach**
   - Chuyển giả thuyết thành strategy draft.
   - Kiểm tra assumptions.
   - Phản biện overfit, p-hacking và look-ahead.
   - Đề xuất bước validation tiếp theo.

Không cần tạo nhiều agent “đóng vai” nếu chúng không có tool, data boundary hoặc evaluation criteria khác nhau.

## 6. Implementation contract cấp sản phẩm

### 6.1. Actors

- Người học cá nhân.
- Sinh viên trong cohort.
- Giảng viên/instructor.
- Content operator.
- Risk/compliance operator.
- System administrator.

### 6.2. Product surfaces

- Learn Hub.
- BCTC workspace.
- Simulation Lab/Pro Lab.
- Instructor/cohort view tối thiểu.
- Admin analytics và trust/safety view.

### 6.3. Input contract

Mỗi tutor request tối thiểu cần:

- opaque authentication credential để backend resolve thành `account_id`;
- lesson/surface context;
- user question;
- knowledge level;
- data version/freshness;
- advisory boundary;
- locale/language.

Danh sách allowed tools và entitlement phải được backend suy ra từ identity, surface và policy; client không được tự khai báo quyền.

### 6.4. Output contract

Mỗi tutor response cần có:

- câu trả lời trực tiếp;
- phần giải thích;
- nguồn hoặc provenance;
- các số liệu được dùng;
- data freshness;
- assumptions và limitations;
- disclaimer phù hợp;
- câu hỏi kiểm tra hiểu;
- bước học hoặc hành động tiếp theo.

### 6.5. Required states

```text
received
  → classified
  → grounded
  → tool_executed
  → drafted
  → reviewed
  → delivered
  → feedback_received
  → progress_updated
```

Failure states:

- insufficient_context;
- source_unavailable;
- stale_data;
- tool_failure;
- unsupported_numeric_claim;
- unsafe_advice_request;
- model_timeout;
- reviewer_rejected.

Mỗi failure state cần có fallback rõ ràng và không được âm thầm trả lời như thể dữ liệu đầy đủ.

### 6.6. Khảo sát codebase cho module Agentic Chatbot

Kết luận kỹ thuật quan trọng nhất:

> Codebase có đủ tài sản chuyên môn để xây Agentic Tutor, nhưng chưa có một product module, runtime LLM, authentication boundary và conversation lifecycle thống nhất. Nếu triển khai chatbot trực tiếp lên các endpoint hiện có, hệ thống sẽ tạo thêm một luồng AI thứ ba khó kiểm soát.

| Hạng mục | Trạng thái đã xác minh | Hệ quả đối với kế hoạch |
|---|---|---|
| Product module | `ai_assistant` và `agent_orchestration` đã bị gỡ khỏi registry | Cần một vertical slice mới có owner rõ ràng |
| Learn Tutor | Có service deterministic nội bộ; UI có tab nhưng chưa có tutor body/API | Learn Hub là nơi phù hợp nhất để làm MVP end-to-end |
| Agent graph | `engines/agents/graph.py` là router → tool deterministic; không có `StateGraph` runtime | Không được coi graph hiện tại là LangGraph chatbot đã sẵn sàng |
| LLM runtime | Pro Lab gọi `ChatOpenAI` trực tiếp theo từng endpoint | Cần provider/runtime dùng chung trước khi mở rộng agent |
| Gemini | Chưa có Google GenAI SDK, key hoặc provider/model settings | Cần adapter và startup health check nếu khóa Gemini |
| Conversation data | Baseline đã có `ai_conversation_sessions`, `ai_messages`, `ai_feedback`, `ai_event_logs` nhưng chưa có repository sử dụng | Nên migrate và tái dùng, không tạo storage song song |
| Checkpoint/memory | Không có LangGraph checkpointer, Redis session hoặc conversation repository | Phải tách product history khỏi graph checkpoint |
| Streaming | Chưa có SSE/chat streaming ở backend hoặc frontend | Streaming là phase sau khi JSON contract ổn định |
| Identity | Learning API dùng `session_id` trực tiếp như `user_id` | Đây là blocker bảo mật; phải resolve session thành `account_id` |
| Session frontend | Session token đang lưu trong `localStorage` | Production gate cần harden token transport/storage |
| Trust/safety | Có disclaimer, risk label, freshness, audit và degrade/freeze | Tái dùng được nhưng phải thêm prompt/tool injection và numeric claim policy |
| Financial tools | Công thức nằm rải ở financials API và quant engines | Extract service theo domain; không tạo “formula engine” mới trong AI platform |
| Telemetry | Có `emit_product_event` và ops snapshots | Có nền đo lường, nhưng agent/model/tool event chưa được phát đầy đủ |
| Test coverage | Không tìm thấy test cho ba live AI endpoint của Pro Lab | Shared runtime chỉ được dùng sau contract, safety và failure tests |

Bằng chứng chính:

- [`src/risk_dashboard/app/registry/registry.py`](../../src/risk_dashboard/app/registry/registry.py)
- [`src/risk_dashboard/engines/agents/graph.py`](../../src/risk_dashboard/engines/agents/graph.py)
- [`src/risk_dashboard/engines/README.md`](../../src/risk_dashboard/engines/README.md)
- [`src/risk_dashboard/modules/learning/api/public.py`](../../src/risk_dashboard/modules/learning/api/public.py)
- [`src/risk_dashboard/modules/learning/application/services.py`](../../src/risk_dashboard/modules/learning/application/services.py)
- [`frontend/src/features/learn-hub/pages/LearningHomePage.jsx`](../../frontend/src/features/learn-hub/pages/LearningHomePage.jsx)
- [`src/risk_dashboard/modules/pro_lab/api/ai.py`](../../src/risk_dashboard/modules/pro_lab/api/ai.py)
- [`src/risk_dashboard/platform/database/schema/baseline.sql`](../../src/risk_dashboard/platform/database/schema/baseline.sql)
- [`src/risk_dashboard/modules/auth/application/services.py`](../../src/risk_dashboard/modules/auth/application/services.py)
- [`frontend/src/features/auth/services/useAuth.js`](../../frontend/src/features/auth/services/useAuth.js)

### 6.7. Quyết định kiến trúc đề xuất

#### D1 — Tạo `modules/ai_tutor` làm product owner

Module mới sở hữu:

- conversation lifecycle;
- request/response contract;
- orchestration và policy;
- feedback;
- learning checkpoint;
- surface context;
- authorization;
- product telemetry.

Không đặt product chatbot trong `engines/agents`, vì engine contract hiện cấm phụ thuộc vào `modules/*` và không sở hữu user-facing routes hoặc session state.

#### D2 — Tách `platform/ai_runtime` khỏi product module

Lớp platform chỉ sở hữu:

- provider protocol;
- Gemini adapter;
- model settings và health;
- structured generation/function calling;
- timeout, retry và cancellation;
- token/cost/latency telemetry;
- prompt redaction.

Lớp này không sở hữu persona, learning flow, công thức tài chính hoặc prompt nghiệp vụ.

#### D3 — Một deployment được bật, không đồng nghĩa hard-code provider

Nếu chọn Gemini, production chỉ bật một model được kiểm soát bằng settings và fail fast khi cấu hình sai. Application vẫn phụ thuộc vào provider protocol để:

- test không cần gọi mạng;
- thay model khi model lifecycle thay đổi;
- không lan truyền constant provider/model qua toàn codebase.

`gemini-3.5-flash` hiện là model stable theo tài liệu chính thức của Google. Codebase chưa hỗ trợ model này; cần thêm Google GenAI SDK v2+, `GEMINI_API_KEY`, settings và health check. Không lưu hoặc hiển thị chain-of-thought; chỉ lưu structured state, tool calls, citations và checkpoint.

Nguồn: <https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.5>

#### D4 — Product storage là source of truth

- Conversation và message repository là nguồn sự thật sản phẩm.
- Graph checkpoint chỉ phục vụ resume/retry orchestration.
- Learning progress chỉ được cập nhật qua learning application service.
- Không dùng LangGraph memory như database nghiệp vụ duy nhất.

#### D5 — Tool theo domain, không sao chép business logic

AI Tutor chỉ gọi typed ports. Adapter cụ thể gọi application service của module sở hữu dữ liệu:

| Tool port | Owner | Output bắt buộc |
|---|---|---|
| `get_lesson_context` | learning | lesson version, excerpt, learning level |
| `explain_financial_item` | financials_product | formula/input/result/unit/source/freshness |
| `explain_quant_risk` | quant_risk | run ID, model version, metrics, provenance |
| `critique_simulation` | simulation_lab/Pro Lab | assumptions, red flags, validation queue |

Không gọi HTTP nội bộ giữa các module và không import private helper từ API layer.

#### D6 — Structured JSON trước, streaming sau

Đầu tiên cần chứng minh một request end-to-end có:

- identity đúng;
- persistence đúng;
- tool call đúng;
- numeric review đúng;
- output schema đúng;
- audit đúng.

Sau đó mới thêm SSE. Cách này giảm đáng kể độ khó khi debug retry, partial response và duplicate message.

### 6.8. Target architecture

```text
Learn / BCTC / Simulation UI
            |
            v
modules/ai_tutor/api
  - auth dependency
  - request validation
  - JSON/SSE transport
            |
            v
modules/ai_tutor/application
  guard -> context -> router -> tool -> numeric/evidence review
                                      -> composer -> checkpoint
            |
            +-------------------------------+
            |                               |
            v                               v
modules/ai_tutor/infrastructure       platform/ai_runtime
conversation/message/checkpoint      Gemini + telemetry + redaction
repositories
            |
            v
Typed adapters to learning / financials / quant_risk / simulation_lab
```

Cấu trúc file mục tiêu:

```text
src/risk_dashboard/
├── modules/ai_tutor/
│   ├── module.py
│   ├── api/public.py
│   ├── schemas/
│   ├── domain/
│   │   ├── entities.py
│   │   ├── policies.py
│   │   └── ports.py
│   ├── application/
│   │   ├── services.py
│   │   ├── graph.py
│   │   └── nodes/
│   └── infrastructure/
│       ├── sqlite.py
│       ├── checkpoints.py
│       └── tool_adapters.py
└── platform/ai_runtime/
    ├── config.py
    ├── provider.py
    ├── gemini.py
    ├── telemetry.py
    └── redaction.py
```

### 6.9. API, identity và event contract

API tối thiểu:

```text
POST /api/v1/public/ai-tutor/conversations
GET  /api/v1/public/ai-tutor/conversations/{conversation_id}
POST /api/v1/public/ai-tutor/conversations/{conversation_id}/messages
POST /api/v1/public/ai-tutor/conversations/{conversation_id}/messages:stream
POST /api/v1/public/ai-tutor/messages/{message_id}/feedback
```

Identity contract:

- Không nhận `user_id` từ client.
- Giai đoạn chuyển tiếp có thể nhận opaque session qua `X-Session-Id`, nhưng backend phải gọi `ResolveSession` và dùng `account_id` làm canonical identity.
- Không đưa session token vào query string hoặc request body.
- Production gate: chuyển sang secure, `HttpOnly`, `SameSite` cookie hoặc bearer session phù hợp; nếu dùng cookie cho mutation phải có CSRF protection.
- Mỗi conversation, message, feedback và checkpoint đều phải kiểm tra ownership.

Request contract:

```json
{
  "question": "Vì sao current ratio tăng nhưng dòng tiền yếu?",
  "surface": "bctc",
  "resource": {
    "ticker": "FPT",
    "period": "2025Q4",
    "active_view": "cash_flow"
  },
  "locale": "vi"
}
```

`allowed_tools`, role, entitlement và data access phải do server tính; client không được tự cấp quyền.

Response contract:

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

SSE event contract sau khi JSON flow ổn định:

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

Mỗi event cần `request_id`, `sequence`, timestamp và terminal status. Không stream chain-of-thought, raw prompt hoặc raw tool output chứa dữ liệu nhạy cảm.

### 6.10. Data migration cần thiết

Tái dùng bốn bảng AI hiện có và bổ sung migration mới thay vì sửa trực tiếp baseline cho database đã chạy:

- thêm `request_id`, `idempotency_key`, `sequence_no`;
- thêm provider/model/model revision;
- thêm input/output token, estimated cost và latency breakdown;
- thêm source/freshness/citation metadata;
- thêm error code và failure state;
- thêm retention/redaction state;
- tạo tool-call table hoặc structured event schema có correlation ID;
- tạo graph checkpoint/state-version table nếu checkpointer không dùng bảng riêng;
- thêm foreign key/ownership index phù hợp với `account_id`.

Không lưu:

- API key;
- raw credential;
- chain-of-thought;
- toàn bộ tài liệu nhạy cảm chỉ để “làm memory”;
- tool payload không cần cho audit.

### 6.11. Guardrail và threat model bổ sung

Trust/safety hiện tại cần mở rộng cho:

- prompt injection và jailbreak;
- indirect injection từ lesson, report hoặc web content;
- tool output injection;
- yêu cầu personalized buy/sell advice;
- yêu cầu gửi lệnh hoặc thay đổi tài sản;
- hallucinated/unsupported numeric claim;
- stale hoặc conflicting source;
- vượt tool-call/token/time budget;
- PII trong prompt, log, feedback và trace;
- horizontal access vào conversation của user khác;
- replay/duplicate message khi reconnect.

Policy quan trọng:

1. Mọi số liệu tài chính phải xuất phát từ deterministic tool output.
2. Reviewer phải so sánh từng numeric claim với tool result trước khi deliver.
3. Tool mặc định read-only; write tool không nằm trong MVP.
4. Mỗi request có max steps, max tool calls, timeout và cost budget.
5. Fallback deterministic phải nói rõ thiếu dữ liệu hoặc model unavailable, không giả lập câu trả lời AI.

## 7. Constraints và invariants

### 7.1. Fixed product policy

- Education-first và research-first.
- Không gửi lệnh giao dịch thật.
- Không cam kết lợi nhuận.
- Không đưa personalized buy/sell recommendation trong public product.
- Mọi claim định lượng phải truy được về input hoặc tool output.
- Mọi dữ liệu cần có freshness và source state.
- Người dùng phải nhìn thấy assumptions và limitations.
- Quantum không được quảng bá là capability production khi chưa có benchmark.

### 7.2. Trust boundary

- LLM không được tự tạo số liệu tài chính.
- LLM không được tự quyết định tool có quyền ghi hoặc giao dịch.
- Các tool tài chính chỉ trả dữ liệu trong phạm vi đã được cấp phép.
- Sensitive user data không được đưa vào prompt nếu không cần thiết.
- Raw OTP, số tài khoản, CCCD, mật khẩu và dữ liệu định danh không được log.

Nền trust/safety hiện có:

- [`src/risk_dashboard/modules/trust_safety/domain/policies.py`](../../src/risk_dashboard/modules/trust_safety/domain/policies.py)
- [`src/risk_dashboard/modules/trust_safety/application/services.py`](../../src/risk_dashboard/modules/trust_safety/application/services.py)

### 7.3. Data boundary

- Dữ liệu miễn phí phù hợp cho prototype và pilot có kiểm soát.
- Thương mại hóa cần quyền sử dụng dữ liệu rõ ràng.
- Dữ liệu market/BCTC/news cần source version và freshness.
- Không dùng cache cũ như dữ liệu live.
- Không dùng dữ liệu người học cho training nếu chưa có consent và policy.

## 8. Performance strategy

### 8.1. Hai đường xử lý

#### Fast path

Dùng deterministic logic, retrieval trực tiếp hoặc cache cho:

- định nghĩa;
- recap bài học;
- quiz feedback;
- glossary;
- câu hỏi lặp lại;
- câu trả lời có cấu trúc cố định.

#### Agent path

Chỉ gọi LLM/agent khi cần:

- tổng hợp nhiều nguồn;
- gọi quant/BCTC/simulation tool;
- phân tích giả thuyết;
- phản biện kết quả;
- tạo explanation theo trình độ người học.

### 8.2. Cache key đề xuất

```text
lesson_id
+ question_intent
+ knowledge_level
+ data_version
+ policy_version
```

Không cache câu trả lời chứa dữ liệu cá nhân hoặc trạng thái tài chính riêng nếu chưa có cơ chế isolation phù hợp.

### 8.3. KPI gate đề xuất

Các giá trị dưới đây là target cho MVP, chưa phải số liệu hiện tại:

| Nhóm | Chỉ số | Gate đề xuất |
|---|---|---:|
| Quality | Grounded/cited answers | ≥95% |
| Quality | Độ chính xác số liệu | ≥99% |
| Quality | Tutor task success | ≥80% |
| Safety | Unsafe advice lọt qua | <1% |
| Performance | p95 time-to-first-token | <2 giây |
| Performance | p95 full response | <6 giây |
| Reliability | Model/tool failure rate | <2% |
| Cost | Chi phí mỗi lượt thành công | ≤0,03–0,05 USD |
| Learning | Quiz improvement | +15 điểm phần trăm |
| Learning | Tutor helpfulness | ≥75% |
| Retention | D7 learner retention | ≥30% |

Nền analytics hiện có:

- [`src/risk_dashboard/modules/analytics_monitoring/application/services.py`](../../src/risk_dashboard/modules/analytics_monitoring/application/services.py)

## 9. Commercialization strategy

### 9.1. Wedge ưu tiên: B2B2Edu

Khách hàng đầu tiên nên là:

- trường đại học;
- câu lạc bộ tài chính/đầu tư;
- trung tâm đào tạo;
- lớp corporate finance/data/quant;
- nhóm nghiên cứu nhỏ.

Lý do:

- Phù hợp với learning, quiz, progress, BCTC và Simulation Lab hiện có.
- Learning outcome đo được rõ hơn.
- Có thể bán theo cohort hoặc semester.
- Chi phí phân phối có khả năng thấp hơn B2C đại trà.
- Giữ sản phẩm gần phạm vi giáo dục, giảm rủi ro bị hiểu là advisory.

### 9.2. Packaging sáu tháng đầu

Chỉ nên có hai gói chính:

#### Campus Pilot

- Syllabus và course content.
- AI Tutor.
- BCTC Lab.
- Simulation Lab.
- Cohort progress.
- Instructor view.
- Báo cáo learning outcome.

#### Pro Individual Beta

- Tutor nâng cao.
- Quant/risk explanation.
- Simulation.
- Backtest critique.
- Research report export.

Free content có thể dùng cho acquisition, nhưng không nên tiếp tục mở rộng thêm nhiều community/news/module trước khi hai gói trên chứng minh được nhu cầu.

### 9.3. North-star metric

> **Weekly Verified Learning Sessions:** số learning session mỗi tuần hoàn thành đủ vòng hỏi → grounded answer → check question → progress update.

Metric này tốt hơn số lượng message vì nó gắn:

- engagement;
- learning outcome;
- agent quality;
- product retention.

### 9.4. Commercial KPIs

- Cohort activation rate.
- First tutor question rate.
- Verified learning session rate.
- Lesson completion uplift.
- Tutor helpfulness.
- D7/D30 retained learners.
- Cost per successful learning session.
- Paid pilot count.
- Paid seats.
- Pilot-to-renewal rate.
- Gross margin sau model và data cost.

### 9.5. Market và pháp lý

Nguồn tham khảo:

- VSDC công bố hơn 13,35 triệu tài khoản nhà đầu tư cá nhân trong nước tại tháng 6/2026:  
  <https://web.vsd.vn/vi/ad/197778>
- UBCKNN nhấn mạnh hợp tác với trường đại học, đào tạo và phổ biến kiến thức chứng khoán:  
  <https://ssc.gov.vn/webcenter/portal/ubck/pages_r/l/chitit?dDocName=APPSSCGOVVN1620168858>
- CFA Institute về Agentic AI workflows trong tài chính:  
  <https://rpc.cfainstitute.org/research/the-automation-ahead-content-series/agentic-ai-for-finance>
- ESMA về Quantum Computing trong thị trường tài chính:  
  <https://www.esma.europa.eu/sites/default/files/2026-05/ESMA50-481369926-33801_TRV_Risk_Analysis_Quantum_Computing_in_Financial_Markets.pdf>
- Luật Chứng khoán Việt Nam 2019:  
  <https://vanban.chinhphu.vn/default.aspx?docid=198541&lang=vi&pageid=27160>

Số tài khoản đầu tư không đồng nghĩa với số người sẵn sàng trả tiền. Mức sẵn sàng chi trả, distribution cost và learning need cần được kiểm chứng bằng pilot.

Tư vấn đầu tư chứng khoán là hoạt động kinh doanh có điều kiện. Trước khi mở rộng từ education/research sang personalized advice, dự án cần legal review riêng.

## 10. Roadmap 30–60–90 ngày

### 10.1. Kế hoạch xây dựng theo dependency

Thứ tự dưới đây là implementation plan đề xuất. Không chạy song song các phase có quan hệ phụ thuộc chỉ để rút ngắn lịch.

#### Phase AT0 — Product truth, security boundary và eval

Deliverables:

- capability/API/tool contract;
- advisory boundary;
- threat model;
- 100–200 câu hỏi gold-set, chia theo factual, numeric, reasoning, unsafe và tool failure;
- canonical identity dependency `session → account_id`;
- ADR cho model, persistence, streaming và retention;
- baseline latency/cost/quality của deterministic tools hiện có.

Exit gate:

- không endpoint AI nào tin `user_id` do client gửi;
- mỗi use case có expected tool, expected evidence và refusal behavior;
- owner phê duyệt scope “education/research only”.

#### Phase AT1 — Extract deterministic tools

Deliverables:

- learning context service;
- BCTC formula/explainer service được tách khỏi API helper;
- quant risk explainer service giữ nguyên provenance;
- simulation critique service;
- typed tool schemas, validation, timeout và error taxonomy;
- unit/contract tests cho từng tool.

Exit gate:

- tool chạy độc lập không cần LLM;
- số liệu, unit, source, freshness và version có trong output;
- không sao chép công thức sang AI module.

#### Phase AT2 — Conversation foundation và AI runtime

Deliverables:

- migration cho conversation/message/feedback/event/checkpoint;
- repositories có ownership và idempotency;
- `platform/ai_runtime` provider protocol;
- Gemini adapter, config, health, timeout/retry/cancellation;
- structured output validation;
- model-call telemetry và redaction;
- fake provider cho test.

Exit gate:

- model misconfiguration fail fast;
- retry không tạo duplicate message/tool call;
- không log secret, chain-of-thought hoặc raw sensitive context;
- model call failure có typed fallback state.

#### Phase AT3 — Learn/Quant Tutor vertical slice

Chỉ triển khai một tutor đầu tiên: **Learning & Quant Tutor**. Router vẫn có interface mở rộng, nhưng BCTC và Simulation specialist chưa được bật.

Deliverables:

- graph `guard → context → route → tool → numeric/evidence reviewer → composer → checkpoint`;
- create/resume conversation;
- JSON message endpoint;
- Learn Hub tutor panel bám `lesson_id`, course và knowledge level;
- citations, assumptions, limitations và check question;
- feedback và progress update qua learning service;
- agent/product/ops events.

Exit gate:

- grounded answer ≥95% trên gold-set;
- numeric accuracy ≥99%;
- zero critical cross-user access và advisory violation;
- p95 full response và cost/session đạt budget pilot;
- frontend có loading, cancel, retry và deterministic error state.

#### Phase AT4 — Streaming và hardening

Deliverables:

- POST streaming endpoint và SSE state machine;
- sequence/reconnect/idempotency;
- cancellation propagation;
- rate limit theo account/IP;
- tool/token/time/cost budgets;
- safe cache theo content/data/policy version;
- load, disconnect, timeout và partial-stream tests.

Exit gate:

- reconnect không nhân đôi response;
- stream luôn kết thúc bằng terminal event;
- cache không rò dữ liệu giữa user;
- p95 time-to-first-token <2 giây trong môi trường pilot.

#### Phase AT5 — BCTC Tutor

Deliverables:

- BCTC surface context adapter;
- line-item/ratio/cash-flow tools;
- numeric claim map và citation UI;
- company-analysis eval set;
- contextual tutor panel trong BCTC workspace.

Exit gate:

- mọi con số map được về tool output;
- period, ticker, unit và data freshness luôn hiển thị;
- không tạo recommendation mua/bán cá nhân hóa.

#### Phase AT6 — Simulation Coach và hợp nhất Pro Lab AI

Deliverables:

- strategy assumption và backtest critique tools;
- simulation context adapter;
- overfit/look-ahead/p-hacking reviewer;
- di chuyển dần ba direct OpenAI endpoints của Pro Lab ra sau shared runtime;
- loại bỏ provider invocation phân tán sau thời gian compatibility.

Exit gate:

- không còn endpoint production tự khởi tạo LLM client ngoài shared runtime;
- mọi simulation claim có run ID và assumptions;
- tool vẫn read-only, không gửi lệnh giao dịch.

#### Phase AT7 — Pilot và commercialization gate

Deliverables:

- entitlement, quota và cost dashboard;
- instructor/cohort reporting tối thiểu;
- weekly verified learning sessions;
- paid pilot analytics;
- retention, privacy và data-license review.

Exit gate:

- quality, safety, performance và gross-margin gate đều đạt;
- có bằng chứng learning uplift;
- chỉ sau gate này mới mở rộng persona hoặc Quantum research surface.

### 10.2. Ưu tiên backlog

| Priority | Xây ngay | Chưa xây |
|---|---|---|
| P0 | Auth boundary, eval, deterministic tools, storage, runtime, Learn/Quant slice | Global chatbot, agent tự trị |
| P1 | SSE, BCTC Tutor, feedback, cost/rate controls | Nhiều model fallback, long-term memory rộng |
| P2 | Simulation Coach, Pro Lab runtime migration, cohort dashboard | Billing phức tạp, write tools |
| R&D | Quantum course và benchmark classical vs quantum-inspired | Claim Quantum production |

### 10.3. Definition of done cấp module

Module chỉ được coi là “Agentic Tutor MVP hoàn thành” khi:

1. Được mount qua registry và feature flag thực sự được enforce.
2. Identity luôn được resolve server-side và ownership có integration test.
3. Conversation/message/feedback có persistence và retention policy.
4. Tool contract có provenance, freshness, typed failure và contract test.
5. Structured output qua schema validation; numeric reviewer chạy trước deliver.
6. Trust/safety bao phủ prompt injection, advice boundary và PII.
7. Có eval regression trong CI, không chỉ unit test.
8. Có latency, failure, token/cost và quality telemetry.
9. Frontend có contextual state, cancel/retry/error và accessibility cơ bản.
10. Documentation phân biệt capability live, beta và R&D.

### 0–30 ngày — Khóa product truth

Mục tiêu:

- Chốt định vị “AI Quant Finance Learning Lab”.
- Chọn ICP đầu tiên: đề xuất lớp đại học hoặc CLB tài chính.
- Chốt target ba persona và bốn tool, nhưng chỉ bật Learning & Quant Tutor trong vertical slice đầu.
- Xây bộ 100–200 câu hỏi đánh giá tutor.
- Đo baseline correctness, safety, latency và cost.
- Đồng bộ tài liệu với runtime.
- Tìm một design partner.

Gate:

- Eval set hoàn chỉnh.
- Advisory boundary được duyệt.
- Có ít nhất một đối tác đồng ý thử nghiệm.

### 31–60 ngày — Bounded Agentic Tutor

Mục tiêu:

- Một learning loop duy nhất.
- Retrieval bám lesson/BCTC/quant output.
- Tool routing.
- Provenance và source visibility.
- Numeric reviewer.
- Trust/safety policy.
- Progress memory.
- JSON flow hoàn chỉnh; chỉ thêm streaming/cache sau khi vượt contract gate.
- Một model deployment được kiểm soát; không bật model fallback trong MVP.

Gate:

- Grounded answer ≥95%.
- Numeric accuracy ≥99%.
- Task success ≥80%.
- p95 full response <6 giây.
- Không có critical safety failure trong eval.

### 61–90 ngày — Paid pilot

Mục tiêu:

- Pilot hai cohort hoặc một tổ chức có LOI.
- So sánh nhóm dùng/không dùng tutor nếu khả thi.
- Đo quiz uplift, completion, D7 retention và cost/learner.
- Instructor dashboard tối thiểu.
- Thu tiền theo cohort/semester, không bán token AI.

Gate:

- Hai pilot trả phí hoặc một hợp đồng/LOI tổ chức.
- Lesson completion tăng ít nhất 15–20%.
- Tutor helpfulness ≥75%.
- D7 learner retention ≥30%.

### 90–180 ngày — Scale có kiểm soát

- Chuẩn hóa entitlement và billing.
- Tối ưu cache, routing và gross margin.
- Mở Pro Individual beta.
- Chuyển dần sang nguồn dữ liệu có SLA/quyền thương mại.
- Chỉ bắt đầu Quantum experiment sau khi core tutor có retention và doanh thu.

## 11. Non-goals trong 90 ngày

- Chatbot tài chính tổng quát.
- Personalized buy/sell recommendation.
- Autonomous trading hoặc gửi lệnh thật.
- Full LMS.
- Community platform mở rộng.
- Quantum production.
- Multi-agent chỉ để tạo hiệu ứng marketing.
- Mở rộng thêm module trước khi chứng minh learning outcome.
- Thay toàn bộ deterministic workflow bằng LLM.

## 12. Risks và mitigation

| Risk | Ảnh hưởng | Mitigation |
|---|---|---|
| Overclaim AI Agent | Mất trust | Phân biệt workflow, agent và R&D trong tài liệu |
| Nhầm Quant với Quantum | Sai định vị | Dùng taxonomy bốn track |
| Hallucinated financial numbers | Rủi ro tài chính/pháp lý | Tool-only numbers + numeric reviewer |
| Dữ liệu stale hoặc không có license | Không thể thương mại hóa | Freshness, source state, commercial data plan |
| Scope quá rộng | Chậm ra thị trường | Một learning loop, ba persona, bốn tool |
| Model cost cao | Gross margin thấp | Fast path, cache và model routing |
| Tutor hay nhưng không tạo learning outcome | Retention thấp | Check question, progress và controlled pilot |
| Đi vào personalized advice | Rủi ro pháp lý | Education boundary và legal review |
| Benchmark quant chưa đủ mạnh | Claim sai | External validation và công bố giới hạn |

## 13. Open questions cần khóa

1. ICP đầu tiên có phải trường/CLB tài chính không?
2. Learning outcome chính cần cải thiện là gì?
3. Course hoặc syllabus đầu tiên sẽ là Risk, BCTC hay Quant Foundation?
4. Ngân sách và quyền thương mại của dữ liệu market/BCTC là bao nhiêu?
5. Phạm vi education/research dừng ở đâu trước vùng advisory?
6. Quantum phục vụ nghiên cứu, cuộc thi hay sản phẩm trả phí dài hạn?
7. Ai là owner của content quality và ai duyệt financial correctness?
8. Pilot cần tiếng Việt hoàn toàn hay song ngữ?
9. Mức giá cohort và renewal model nào cần được test?
10. Dữ liệu người học nào được phép dùng cho personalization?

## 14. Handoff

Trạng thái hiện tại:

> **Chưa nên triển khai diện rộng. Cần product clarification và architecture review trước, sau đó mới chuyển sang TDD implementation.**

Thứ tự handoff đề xuất:

1. Chốt năm quyết định cốt lõi: ICP, learning outcome, syllabus, data budget và advisory boundary.
2. Viết PRD cho bounded AI Tutor.
3. Viết eval specification trước implementation.
4. Review target architecture và trust boundary.
5. Triển khai theo TDD.
6. Chạy verification loop.
7. Pilot có đo lường.
8. Chỉ scale sau khi vượt quality, performance và commercial gates.

## 15. Kết luận

Northstar không nên cạnh tranh bằng một chatbot tổng quát hoặc câu chuyện Quantum chưa có bằng chứng. Cơ hội tốt nhất là nối những tài sản đã có — Learn Hub, BCTC, quant engine, Simulation Lab, trust/safety và analytics — thành một learning loop Agentic AI có thể đo được.

Chiến lược cô đọng:

> **AI là động cơ doanh thu; Quant là nền tảng tạo trust; Quantum là nhánh R&D; learning outcome là thước đo sản phẩm.**
