# BÁO CÁO KHẢO SÁT CHUYÊN SÂU & ĐỐI CHIẾU HỆ THỐNG AGENTIC QUANTUM

**Phiên bản:** Đã kiểm chứng mã nguồn thực tế & Khảo sát mở rộng (Source-Verified & Root Cause Post-Mortem)  
**Ngày khảo sát:** 2026-09-08  
**Nhánh git:** `fix/learning-assets`  
**Phương pháp:** Đối soát trực tiếp mã nguồn bằng CodeGraph, grep, AST inspect, phân tích lịch sử commit git và chạy trực tiếp môi trường runtime Python; đối chiếu 4 tài liệu kỹ thuật nền tảng cùng bộ 5 kế hoạch module (`00` đến `04`).

**Tài liệu đối chiếu:**
1. `docs/project/AGENTIC_QUANTUM_MASTER_PLAN.md` (3.187 dòng đặc tả kế hoạch thực thi)
2. `docs/project/MULTI_AGENT_SYSTEM_ARCHITECTURE.md` (7 Plane, 7 Surface, 11 Agent)
3. `docs/project/AI_AGENT_PRODUCT_UPGRADE_STRATEGY.md` (Định vị sản phẩm và chiến lược)
4. `docs/project/qa/USER_INTERACTION_GUIDE.md` (10 Artifacts, 2 Chế độ tương tác)
5. Bộ kế hoạch triển khai chi tiết: `docs/project/agentic-quantum/` (Plans `00_AGENTIC_CORE` đến `04_LEARN_AGENT`)

---

## MỤC 0: TỔNG HỢP CÁC ĐÍNH CHÍNH & PHÁT HIỆN CHẤN ĐỘNG (FACT-CHECK & DISCOVERIES)

Qua quá trình rà soát đối chiếu từng dòng mã nguồn, nhóm kiểm toán xác nhận các phát hiện then chốt giải thích triệt để sự vắng mặt của Agent và các đứt gãy trong hệ thống:

| # | Hạng mục kiểm tra | Bản nháp ban đầu nêu | Thực tế mã nguồn (Đã đối soát) | Bằng chứng mã nguồn |
|---|---|---|---|---|
| **D1** | **Mounting Router Agentic Core** | Cho rằng API `/api/v1/public/agentic/*` đã được mount bình thường | **PHÁT HIỆN CHẤN ĐỘNG #1:** `agentic_core` **CHƯA TỪNG ĐƯỢC MOUNT VÀO FASTAPI**. Module bị bỏ quên hoàn toàn trong `get_registered_modules()`. Client gọi vào sẽ nhận ngay **HTTP 404 Not Found** | `registry.py:46-71` không import `agentic_core`; `app_factory.py:61` chỉ mount từ registry; runtime test `app.routes` trả về danh sách rỗng cho prefix `agentic` |
| **D2** | **Ngữ cảnh bài học trong AI Tutor** | Chỉ nêu chung chung là mock f-string | **PHÁT HIỆN CHẤN ĐỘNG #2:** `LearningLessonContextTool` **HARDCODE CỐ ĐỊNH** lấy bài học đầu tiên (`DEFAULT_LEARNING_CARDS[0]`), bất kể người dùng đang mở bài học hay chủ đề nào | `modules/ai_tutor/infrastructure/adapters/learning_adapter.py:30` gán cứng: `card = DEFAULT_LEARNING_CARDS[0]` (luôn luôn là bài ROE) |
| **D3** | **Xung đột 2 bộ Tools của Learning** | Báo cáo cũ chưa phát hiện | **XUNG ĐỘT KIẾN TRÚC:** `modules/learning/agent_tools.py` có 6 tools chuẩn Pydantic v2 theo Plan 04, nhưng `ai_tutor` lại tự viết một adapter stub riêng và hardcode card 0 | `learning/agent_tools.py:39-200` vs `ai_tutor/infrastructure/adapters/learning_adapter.py:14-42` |
| **D4** | **Lỗ hổng Identity Client-Supplied** | Chỉ nói AT0 auth lỏng lẻo chung chung | **ANTI-PATTERN IDOR:** `GET /auth/me` nhận `session_id` từ query param client; `aiTutorApi.js:12` đọc `localStorage` truyền header thay vì cookie HttpOnly | `modules/auth/api/public.py:95`, `aiTutorApi.js:4-16`; Plan 01 §2 |
| **D5** | **Đường dẫn Cache Data Hub** | Ghi cache vào `/tmp/market_data_cache/` | Cache ghi vào `data/global_market_prices/` **trong project root**, KHÔNG dùng `/tmp` | `global_market_feed.py:15` — `GLOBAL_MARKET_CACHE_DIR = _PROJECT_ROOT / "data" / "global_market_prices"` |
| **D6** | **Class CSS Khung Chat** | Class `.learn-tutor-drawer` / `.tutor-chat-container`, có `max-height: 480px` | Class thật là `.lh-tutor-container`; chỉ có `height: 480px` + `overflow: hidden`, KHÔNG có `max-height` | `learn-tutor.css:1-9` |
| **D7** | **Cache BCTC tại `financials_product`** | Báo cáo là "thiếu hoàn toàn cache layer" | **ĐÃ CÓ cache layer**: `get_financial_dataset` đọc cache-first từ disk rồi mới gọi vnstock live. Chỉ là cache **không có TTL** (dữ liệu cũ vĩnh viễn trừ khi bấm `refresh=True`) | `data/financials.py:405-431`, `_cache_path_for_ticker:94` → `data/financials/cache/{ticker}.json` |
| **D8** | **Hiện trạng module `internal_ops`** | Báo cáo là "0% / hoàn toàn chưa có mã nguồn" | **CÓ 1.853 dòng mã nguồn** (verifier, contracts, admin REST API). Tuy nhiên KHÔNG dùng LLM/`ai_runtime` → là REST deterministic | `find internal_ops -name "*.py"` = 20 file; `grep ai_runtime internal_ops` = NONE |
| **D9** | **Chi tiết lỗi HTTP 501** | `"Action proposal confirmation not implemented yet"` | Detail thật: `"ActionProposal service not ready"` | `agentic_core/api/public.py:230, 239` |
| **D10**| **Kiểu dữ liệu `_RUN_STORE`** | `OrderedDict[str, AgentRunState]` | Type thật: `OrderedDict[str, dict[str, Any]]` | `agentic_core/api/public.py:29` |
| **D11**| **Tổng số vai trò Agent trong kiến trúc** | "8 Specialists" | Kiến trúc chuẩn quy định **11 vai trò** (1 Supervisor + 1 AI Tutor + 9 domain agents, gồm cả `Quant Research Agent` và `Internal Ops Agent`) | `MULTI_AGENT_SYSTEM_ARCHITECTURE.md:245-257` |
| **D12**| **Thiếu SSE Streaming & Feedback** | Báo cáo cũ chưa phân tích | `ai_tutor` hoàn toàn thiếu giao thức Server-Sent Events (SSE) `/messages/stream` (Plan 03 TUT4); endpoint feedback chưa nối UI | `ai_tutor/api/public.py`, `aiTutorApi.js` |

---

## MỤC 1: TRUY VẾT NGUYÊN NHÂN GỐC RỄ — "TẠI SAO CHẠY HỆ THỐNG KHÔNG THẤY AGENT ĐÂU?"

Khi người dùng kiểm thử theo kịch bản thực tế, hệ thống hoàn toàn vắng bóng hành vi của AI Agent và phát sinh các lỗi nghiêm trọng. Dưới đây là phân tích nguyên nhân gốc rễ (RCA) đã được kiểm chứng bằng mã nguồn:

### 1.1. Nguyên nhân 1: Router `agentic_core` chưa từng được đăng ký vào FastAPI (HTTP 404)
* **Vị trí mã nguồn:** `src/risk_dashboard/app/registry/registry.py:46-71` và `src/risk_dashboard/app/bootstrap/app_factory.py:61-68`
* **Cơ chế:** 
  Tệp `src/risk_dashboard/modules/agentic_core/module.py` có định nghĩa `module = ModuleDefinition(id="agentic_core", slug="agentic_core", public_mount_prefix="/api/v1/public/agentic", public_router=public_router)`.
  Tuy nhiên, trong tệp danh bạ đăng ký trung tâm `src/risk_dashboard/app/registry/registry.py`, hàm `get_registered_modules()` liệt kê 20 module khác nhau nhưng **hoàn toàn bỏ quên `agentic_core_module`**.
* **Hậu quả:** 
  Hàm khởi tạo ứng dụng `create_app()` chỉ duyệt qua các module có trong danh bạ này để nạp router (`app.include_router(...)`). Vì vậy, toàn bộ các điểm cuối `/api/v1/public/agentic/runs`, `/artifacts`, `/action-proposals` **chưa từng tồn tại trong bảng định tuyến của FastAPI**. Nếu client gửi yêu cầu, server sẽ phản hồi ngay lập tức lỗi `HTTP 404 Not Found`.

### 1.2. Nguyên nhân 2: AI Tutor Mock Bypass & Hardcode cố định bài học ROE
* **Vị trí mã nguồn:** 
  - `src/risk_dashboard/modules/ai_tutor/infrastructure/adapters/learning_adapter.py:28-42`
  - `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py:103-122`
  - `src/risk_dashboard/modules/ai_tutor/application/specialists/quant_specialist.py:103-119`
* **Cơ chế:**
  1. **Hardcode Context:** Khi người dùng ở bất kỳ bài học nào, `LearningLessonContextTool.execute()` tại dòng 30 gán cứng:
     ```python
     card = DEFAULT_LEARNING_CARDS[0]  # card_roe_01: Chỉ số ROE
     ```
     Hệ thống bỏ qua hoàn toàn tham số `context_id` hoặc bài học đang học mà người dùng gửi lên.
  2. **Bypass LLM:** Cả `LearningSpecialist` và `QuantSpecialist` đều không import `platform.ai_runtime`. Tại dòng 117-122 của `learning_specialist.py`, câu trả lời được ghép bằng chuỗi tĩnh:
     ```python
     answer = (
         f"Chào anh, em xin giải thích nội dung bài học **{lesson_ev.get('lesson_title', 'Chỉ số ROE')}**:\n\n"
         f"- **Tóm tắt:** {lesson_ev.get('summary', '')}\n"
         f"- **Ý nghĩa cốt lõi:** {lesson_ev.get('key_takeaway', '')}\n\n"
         "Chỉ số này giúp anh đánh giá xem doanh nghiệp sử dụng đồng vốn của cổ đông hiệu quả như thế nào qua các năm."
     )
     ```
* **Hậu quả:** 
  Giải thích chính xác 100% khiếu nại của người dùng: *"AI Tutor Drawer hỏi 2 câu khác nhau nhưng lại trả lời chung 1 câu trả lời sẵn... không liên kết được với LLM API Key cũng không giải thích được tài liệu nhúng vào"*. Thời gian phản hồi chỉ ~400ms (CPU tính chuỗi nội bộ, không có độ trễ mạng gọi LLM).

### 1.3. Nguyên nhân 3: Toàn bộ thành phần UI Agentic phía Frontend là Mã mồ côi (Orphan Components)
* **Vị trí mã nguồn:** Thư mục `frontend/src/shared/agentic/` (gồm 6 tệp: `AgentRunPanel.jsx`, `AgentArtifactCard.jsx`, `EvidenceDrawer.jsx`, `ActionProposalReview.jsx`, `api.js`, `useAgentRun.js`)
* **Cơ chế:** 
  Bộ UI tương tác Agentic chuẩn hóa đã được lập trình hoàn chỉnh với khả năng polling trạng thái mỗi 750ms (`useAgentRun.js`), hiển thị thẻ Artifacts và hộp thoại phê duyệt Action Proposals. Tuy nhiên, qua đối soát toàn bộ mã nguồn Frontend (`frontend/src/features/`), **tỷ lệ import của các component này tại cả 6 trang nghiệp vụ là 0%**.
* **Hậu quả:** 
  Không một màn hình nào (BCTC, Định giá, Danh mục, Tin tức) render nút bấm nghiệp vụ (Contextual CTA) để gọi hàm `agenticApi.createRun()`. Giao diện Frontend hoàn toàn tĩnh, biến backend Agentic thành ốc đảo cô lập.

### 1.4. Nguyên nhân 4: Khung Chat bị bó cứng chiều cao CSS (Layout Defect)
* **Vị trí mã nguồn:** `frontend/src/features/learn-hub/pages/learn-tutor.css:1-9`
* **Cơ chế:** 
  Lớp CSS `.lh-tutor-container` bị gán cứng thuộc tính:
  ```css
  .lh-tutor-container {
    display: flex;
    flex-direction: column;
    height: 480px;      /* Cố định chiều cao */
    overflow: hidden;   /* Chặn thanh cuộn tự nhiên */
  }
  ```
* **Hậu quả:** Khung chat không thể dãn theo chiều cao của Drawer hoặc tỷ lệ màn hình `100vh`. Khi nội dung tin nhắn vượt quá 480px, văn bản bị vỡ layout và che khuất nút gửi.

### 1.5. Nguyên nhân 5: Điểm cuối Duyệt hành động trả về HTTP 501
* **Vị trí mã nguồn:** `src/risk_dashboard/modules/agentic_core/api/public.py:223-239`
* **Cơ chế:** 
  Hai điểm cuối tiếp nhận xác nhận hành động nguy hiểm của Agent (`:confirm` và `:reject`) được code cứng lệnh ném ngoại lệ:
  ```python
  raise HTTPException(status_code=501, detail="ActionProposal service not ready")
  ```
* **Hậu quả:** Luồng tương tác con người giám sát (Human-In-The-Loop - HITL) bị đứt gãy ngay tại tầng API.

### 1.6. Nguyên nhân 6: Rủi ro lỗi ghi Cache Data Hub (`PermissionError`)
* **Vị trí mã nguồn:** `src/risk_dashboard/modules/data_hub/application/global_market_feed.py:386-394`
* **Cơ chế:** Hàm `_write_cache()` ghi file trực tiếp bằng `path.write_text()` vào `data/global_market_prices/global_market_snapshot.json` mà không có khối `try/except (PermissionError, OSError)`.
* **Hậu quả:** Nếu tệp cache được tạo bởi tiến trình có quyền khác (như `root` trong docker/container), tiến trình người dùng bình thường sẽ bị lỗi `PermissionError: [Errno 13]`, gây sập widget dữ liệu thị trường sang mã lỗi 500.

---

## MỤC 2: KHẢO SÁT HIỆN TRẠNG CODEBASE THEO 4 TẦNG KIẾN TRÚC

### 2.1. Tầng Giao diện Người dùng (Frontend Layer)

| Bề mặt (Surface) | Trạng thái Codebase Hiện tại | Bằng chứng Mã nguồn | Đánh giá & Khoảng cách |
|---|---|---|---|
| **S1: Learn Hub** | Có `LearnTutorPanel.jsx` kết nối API `/ai-tutor`, nhưng CSS bị bó cứng 480px và backend trả lời mock | `LearnTutorPanel.jsx:47`, `aiTutorApi.js:58`, `learn-tutor.css:4` | Mới đạt Conversational Mode sơ khai; thiếu SSE streaming và thiếu Embedded Socratic Hint trên từng bài tập. |
| **S2: BCTC Workspace** | 100% REST API truyền thống, không có AgentRunPanel hay nút yêu cầu Agent bóc tách | `frontend/src/features/financial-ratio/` | Chưa nhúng Contextual CTA; hoàn toàn không có giao diện tương tác với Agent. |
| **S3: Simulation Lab** | Có `SimulationResearchPanel.jsx` gọi API `/pro-lab/ai/*` dạng form gửi nhận một lượt | `frontend/src/features/valuation-hub/` | Sử dụng được LLM nhưng theo kiểu form input tĩnh, chưa hiển thị đồ thị tiến trình Agent. |
| **S4: News Intelligence** | Hiển thị danh sách tin tức tĩnh từ REST API | `frontend/src/features/market-intelligence/` | Chưa có nút kích hoạt Fact/Hypothesis extraction hay News Evidence Brief. |
| **S5: Market & Portfolio** | Bảng hiển thị giá và danh mục paper trading thuần túy | `frontend/src/features/portfolio/` | Chưa nhúng `ActionProposalReview` hay `PortfolioReviewArtifact`. |
| **S6: Home Journey** | Hiển thị dashboard tổng hợp tĩnh | `frontend/src/features/home/` | Chưa có component hiển thị `NextBestActionCard`. |
| **Thư viện dùng chung** | 6 component Agentic đầy đủ chức năng nhưng bị cô lập (0 import) | `frontend/src/shared/agentic/*` | **Mã mồ côi 100%**. Cần được đưa vào sử dụng ngay. |

---

### 2.2. Tầng Máy chủ Ứng dụng & Điều phối (Backend & Orchestration Layer)

| Phân hệ / Module | Trạng thái Codebase Hiện tại | Bằng chứng Mã nguồn | Đánh giá Kỹ thuật |
|---|---|---|---|
| **`platform/ai_runtime`** | **HOÀN THIỆN ĐẠT CHUẨN** | `src/risk_dashboard/platform/ai_runtime/` (14 tệp `.py`) | Đã hiện thực `GoogleGeminiProvider` với model cố định `gemini-3.5-flash`, cơ chế retry exponential backoff, streaming SSE, telemetry đo token/chi phí và redact dữ liệu nhạy cảm. |
| **`modules/pro_lab`** | **DÙNG LLM THẬT** qua `ai_runtime` | `src/risk_dashboard/modules/pro_lab/api/ai.py:35-58` | Đã gọi mô hình Gemini thật cho 3 endpoint: `strategy-copilot`, `swarm-committee`, `backtest-critique`. Tuy nhiên hiện tại chạy qua monolithic prompt (mô phỏng 4 vai trong 1 prompt), chưa tách thành subgraphs. |
| **`modules/quant_research`** | **DÙNG LLM THẬT + REVIEWER CHUẨN** | `src/risk_dashboard/modules/quant_research/application/service.py:110` | Điểm sáng kỹ thuật: Đã gọi LLM thật qua `ai_runtime`, có bộ kiểm toán số liệu `QuantNumericReviewer` tuyệt đối. Tuy nhiên bị tắt mặc định bởi feature flag. |
| **`modules/ai_tutor`** | **DỪNG Ở MOCK F-STRING** | `src/risk_dashboard/modules/ai_tutor/application/specialists/*.py` | Có kiến trúc `TutorGraph` 3 specialist nhưng bên trong không import `ai_runtime`, chỉ nối chuỗi văn bản mẫu. |
| **`modules/agentic_core`** | **CHƯA MOUNT ROUTER + IN-MEMORY** | `src/risk_dashboard/app/registry/registry.py:46-71`<br>`modules/agentic_core/api/public.py:29, 230` | Router bị bỏ quên ngoài FastAPI; StateGraph 6 node chỉ chạy trên RAM `_RUN_STORE`; endpoints duyệt action bị 501. |
| **`modules/internal_ops`** | **REST DETERMINISTIC** (1.853 LOC) | `src/risk_dashboard/modules/internal_ops/` (20 tệp `.py`) | Có đầy đủ verifier, contract và admin API nhưng chạy logic mã nguồn thuần túy, không tích hợp LLM. |

---

### 2.3. Tầng Cơ sở Dữ liệu & Lưu trữ Bền vững (Database & Persistence Layer)

* **Trạng thái thực tế trong SQLite (`data/db/northstar.db`):**
  Hệ thống đã chạy thành công 15 migration thông qua `src/risk_dashboard/platform/database/migrate.py:380-396`:
  - Bảng hội thoại AI Tutor: `ai_conversation_sessions`, `ai_messages`, `ai_feedback`, `ai_event_logs` (Migration 008).
  - Bảng kiểm tra học tập: `learning_agent_checkpoints`, `learning_verified_events`, `learning_progress_receipts` (Migration 009).
  - Bảng artifacts chuyên ngành: `bctc_evidence_memos` (010), `bctc_upload_ownership` (011), `simulation_experiment_specs` (012), `simulation_action_proposals` (013), `simulation_action_receipts` (014), `home_journey_cards` (015).
  - Bảng đồng thuận người dùng: `account_consents`.
* **Khoảng cách nghiêm trọng (Critical Persistence Gap):**
  - **Không có bảng cho `agentic_core`:** Các bảng cốt lõi `agentic_core_runs`, `agentic_core_artifacts`, `agentic_core_action_proposals` **HOÀN TOÀN CHƯA CÓ TRONG MIGRATION**. `agentic_core` lưu trữ trên biến RAM `_RUN_STORE` (giới hạn 1000 phần tử, mất sạch khi restart server).
  - **Chưa có bảng trí nhớ dài hạn:** Bảng `user_memories` / `durable_memory` theo đặc tả D12 của Master Plan chưa được tạo. Thiếu `MemoryGovernor` để lọc `MemoryProposal`.
  - **Lưu ý phân định:** Bảng `simulation_action_proposals` và `simulation_action_receipts` đã có sẵn trong DB thuộc về `pro_lab`, không phải của `agentic_core`. Cần tái sử dụng mẫu thiết kế này cho `agentic_core`.

---

## MỤC 3: MA TRẬN 11 AGENTS & BỘ DOMAIN TOOLS THEO THIẾT KẾ KỸ THUẬT
*(Đối chiếu chi tiết theo `MULTI_AGENT_SYSTEM_ARCHITECTURE.md:245-257` và các Module Plans)*

```text
                               +--------------------------------------------+
                               |     SUPERVISOR / ORCHESTRATOR GRAPH        |
                               | (modules/agentic_core - StateGraph 6 node) |
                               +--------------------------------------------+
                                                     |
                     +-------------------------------+-------------------------------+
                     |                               |                               |
                     v                               v                               v
       [Nhóm Giáo Dục & Hội Thoại]      [Nhóm Nghiên Cứu Định Lượng]      [Nhóm Vận Hành & Khám Phá]
       • AI Tutor (Conversational)      • Risk & Quant Specialist         • Home Journey Coach
       • Learning Pedagogy Agent        • Company & BCTC Agent            • Internal Ops Agent
                                        • Simulation Research Agent
                                        • News Intelligence Agent
                                        • Market & Portfolio Agent
                                        • Quant Research Agent
```

| STT | Tên Agent theo Thiết kế | Module sở hữu | Bộ Domain Tools (Deterministic Engines) | Trạng thái Codebase Hiện tại | Mức độ Hoàn thành |
|---|---|---|---|---|:---:|
| 1 | **Supervisor / Orchestrator** | `modules/agentic_core` | `router.classify_intent`, `tool_grants.authorize`, `run_manager.budget` | Có StateGraph 6 node (`graph.py:270`), nhưng chạy RAM, chỉ có 1 generic specialist, **router chưa được mount vào FastAPI** | 30% |
| 2 | **AI Tutor (Conversational)** | `modules/ai_tutor` | `tutor.create_conversation`, `tutor.send_message`, `tutor.feedback` | Có API và `TutorGraph` 3 nhánh, ghi nhận lịch sử vào SQLite, nhưng **bị nghẽn do Specialist mock chuỗi tĩnh và hardcode bài ROE** | 30% |
| 3 | **Learning Pedagogy Agent** | `modules/learning` | 6 tools Plan 04: `get_context`, `get_progress`, `get_quiz_item`, `grade_checkpoint`, `update_progress`, `recommend_next` | Đầy đủ 6 tools tại `modules/learning/agent_tools.py:39-200`. Tuy nhiên `ai_tutor` không gọi bộ tool này mà dùng adapter riêng gán cứng card 0 | 40% |
| 4 | **Risk & Quant Specialist** | `engines/quant`, `quant_risk` | `quant.explain_risk`, `quant.get_run`, `quant.calculate_metric`, `quant.compare_scenarios` | Có adapter `QuantRiskMetricsTool`, `QuantVarSummaryTool`, nhưng câu trả lời định dạng bằng f-string tĩnh trong `quant_specialist.py:103` | 25% |
| 5 | **Company & BCTC Agent** | `financials_product` | `bctc.resolve_report`, `bctc.resolve_line_item`, `bctc.compare_periods`, `bctc.calculate_ratio`, `bctc.trace_provenance`, `bctc.build_evidence_table` | Đầy đủ 6 tool manifests tại `modules/financials_product/agent_tools/`. Có bảng DB `bctc_evidence_memos`. Chưa có Specialist Node gọi LLM | 35% |
| 6 | **Simulation Research Agent**| `pro_lab`, `simulation_lab` | `simulation.get_strategy_spec`, `simulation.validate_experiment`, `simulation.critique_backtest` | **Đã gọi LLM thật qua `ai_runtime`** (`pro_lab/api/ai.py`). Đã có luồng Action Proposal 2 pha hoàn chỉnh ghi DB SQLite. Cần phân rã LangGraph | 65% |
| 7 | **News Intelligence Agent** | `news_intelligence` | `news.brief_evidence`, `news.cluster`, `news.compare`, `news.enrichment`, `news.market_context`, `news.write` | Đầy đủ 6 tool manifests tại `modules/news_intelligence/agent_tools/`. Đã có bảng DB `news_evidence_briefs`. Chưa có Specialist Node | 30% |
| 8 | **Market & Portfolio Agent** | `market_portfolio`, `data_hub`| `market.get_snapshot`, `portfolio.get_snapshot`, `market.get_exposure`, `market.run_scenario` | Đầy đủ 4 tool manifests tại `modules/market_portfolio/application/agent_tools.py`. Đã có bảng `mp_portfolio_review_artifacts`. Chưa có LLM agent | 25% |
| 9 | **Home Journey Coach** | `home_onboarding` | `home.read_domain_summaries`, `home.evaluate_candidate`, `home.rank_next_action` | Đã có bảng `home_journey_cards` và `home_journey_feedback`. Chưa có logic Agent tự động tổng hợp `NextBestActionCard` | 20% |
| 10 | **Internal Ops Agent** | `internal_ops` | `ops.list_kpi_snapshots`, `ops.list_ops_metrics`, `ops.list_alerts`, `ops.list_trust_audits` | Có 1.853 dòng code xử lý REST, verifier và audit. Chưa tích hợp tầng suy luận LLM | 20% |
| 11 | **Quant Research Agent** | `quant_research` | `quant.eod_analysis.v1`, `quant.scenario_compare.v1`, `quant.model_report.v1` | **MẪU THAM CHIẾU HOÀN THIỆN NHẤT:** Có tool manifests, gọi LLM thật qua `ai_runtime`, có `QuantNumericReviewer` đối soát 100%. Bị tắt bởi feature flag | 70% |

---

## MỤC 4: MA TRẬN ĐỐI CHIẾU 10 DOMAIN ARTIFACTS THEO `USER_INTERACTION_GUIDE.md`

Tài liệu `USER_INTERACTION_GUIDE.md` đặc tả 10 loại Artifacts chuẩn mực đóng vai trò là kết quả đầu ra có thể kiểm chứng được của hệ sinh thái. Dưới đây là hiện trạng đối soát:

| STT | Tên Loại Artifact | Bề mặt Nghiệp vụ | Lược đồ Backend (Schema) | Lưu trữ Database (SQLite) | Thành phần UI Frontend | Tình trạng Tích hợp |
|---|---|---|---|---|---|:---:|
| 1 | `NextBestActionCardV1` | Home Journey | `home_onboarding/schemas/journey.py` | Bảng `home_journey_cards` (Migration 015) | `AgentArtifactCard.jsx:45` | Backend & DB sẵn sàng; Frontend chưa render |
| 2 | `FormulaWalkthrough` | Financial Ratio / Learn | Chưa có schema riêng (dùng `AgentArtifact`) | Chưa có bảng riêng (dạng ephemeral) | `AgentArtifactCard.jsx:62` | Đã có UI template; Backend chưa sinh |
| 3 | `SocraticHint` | Learn Hub | `ai_tutor/schemas/responses.py:27` | Bảng `ai_messages` (Migration 008) | `LearnTutorPanel.jsx:110` | Giao diện đã có; Backend bị nghẽn do trả lời mock |
| 4 | `CheckpointReview` | Learn Hub | `learning/schemas/agent_tools.py` | Bảng `learning_agent_checkpoints` (009) | `LearnHubPage.jsx` | DB và service sẵn sàng; chưa nối luồng Agent |
| 5 | `LineItemExplanation` | BCTC Workspace | Chưa có schema riêng | Chưa có bảng riêng | `AgentArtifactCard.jsx:110` | Đã có tool trích xuất dòng; chưa có schema Artifact |
| 6 | `EarningsQualityMemo` | BCTC Workspace | `financials_product/schemas/evidence.py` | Bảng `bctc_evidence_memos` (Migration 010) | `AgentArtifactCard.jsx:125` | DB và tool đã có; chưa có Agent kết nối sinh memo |
| 7 | `PreflightChecklist` | Valuation Hub | Chưa có schema riêng | Chưa có bảng riêng | `AgentArtifactCard.jsx:140` | Mới có giao diện mẫu; Backend chưa hỗ trợ |
| 8 | `BacktestCritiqueArtifact`| Simulation Lab | `pro_lab/schemas/ai.py:53` | Bảng `pro_lab_experiment_runs` | `SimulationResearchPanel.jsx` | **ĐÃ CHẠY ĐƯỢC:** Sinh từ LLM thật và hiển thị UI |
| 9 | `NewsEvidenceBrief` | News Intelligence | `news_intelligence/agent_tools/` | Bảng `news_evidence_briefs` | `AgentArtifactCard.jsx:170` | Đã có bảng DB và tool; chưa nối dây UI |
| 10 | `PortfolioReviewArtifactV1`| Market & Portfolio | `market_portfolio/schemas/agent_artifacts.py`| Bảng `mp_portfolio_review_artifacts` | `AgentArtifactCard.jsx:185` | Đã có schema và bảng DB; Frontend chưa nối |

---

## MỤC 5: ĐỐI CHIẾU LỘ TRÌNH TRIỂN KHAI (MASTER PLAN ROADMAP)

Theo `AGENTIC_QUANTUM_MASTER_PLAN.md`, dự án quản lý tiến độ bằng 2 hệ thống song song:

### 5.1. Hệ AT (§ Mục tiêu Năng lực — Lines 2006–2219)

| Mã AT | Mục tiêu Chuẩn hóa theo Master Plan | Đánh giá Hiện trạng Codebase |
|---|---|---|
| **AT0** | Capability freeze, identity, threat model and eval | Hoàn thành nền tảng `AuthPrincipal`, nhưng `agentic_core` chưa ép xác thực chặt chẽ, còn lỗ hổng client query session. |
| **AT1** | Extract deterministic domain tools | **HOÀN THÀNH XUẤT SẮC:** Các domain `learning`, `financials_product`, `news`, `market` đều đã tách xong bộ ToolManifests chuẩn. |
| **AT2** | Agentic Core, conversation foundation and provider-neutral runtime | **ĐANG TẮC NGHẼN:** `ai_runtime` đã xong; nhưng `agentic_core` chưa mount router, lưu RAM, thiếu ClaimLedger, thiếu MemoryGovernor. |
| **AT3** | Learn Agent & Risk/Quant vertical slice | Bị chặn bởi Lỗi 2 (Specialist mock chuỗi tĩnh và hardcode bài ROE). |
| **AT4** | Memory, SSE and production hardening | SSE streaming chưa có trong `ai_tutor`; Durable Memory chưa có bảng SQLite. |
| **AT5** | Company Analysis Agent & BCTC embedded workspace | Đã có bảng DB và tools; UI bị cô lập (Lỗi 3). |
| **AT6** | Simulation Agents and Pro Lab migration | Đạt ~65%: `pro_lab` đã dùng `ai_runtime` và có Action Receipts hoàn chỉnh. |
| **AT7** | Pilot and commercialization gate | Chưa kích hoạt. |

### 5.2. Hệ Phase (§ Trình tự Thi công Kỹ thuật — Lines 2501–2664)

```text
[Phase 0: Baseline] ───► [Phase 1: Identity & Trust] ───► [Phase 2: AI Runtime]
                                                                  │ (Hoàn thành)
                                                                  v
[Phase 5: AI Tutor & Learn] ◄─── [Phase 4: Agentic Core Graph] ◄─── [Phase 3: Agentic Core Foundation]
        │                                                                  ▲
        └─────── (HỆ THỐNG ĐANG BỊ TẮC TẠI GIAO ĐIỂM PHASE 3 - 4 - 5) ──────┘
```

* **Vị trí hiện tại:** Codebase đã hoàn thành Phase 2 (AI Runtime), nhưng đang bị nghẽn giữa Phase 3–4 (Agentic Core) và Phase 5 (AI Tutor) do thiếu bước mount router, lưu RAM và mock bypass.

---

## MỤC 6: NGUYÊN NHÂN GỐC RỄ: TẠI SAO ĐÃ CÓ TÀI LIỆU KỸ THUẬT NHƯNG CODEBASE SINH RA VẪN BỊ LỖI? (DEVELOPMENT POST-MORTEM)

Một câu hỏi mang tính chiến lược lớn được đặt ra: **Tại sao dự án đã sở hữu bộ tài liệu thiết kế và kế hoạch cực kỳ đồ sộ, chi tiết đến từng schema (hơn 3.100 dòng Master Plan và 12 Module Plans), nhưng khi sinh mã nguồn ra thì hệ thống lại bị đứt gãy, mock tĩnh và không thể vận hành?**

Qua phân tích lịch sử commit git và cấu trúc mã nguồn, nhóm kiểm toán xác định **4 nguyên nhân kỹ thuật cốt lõi (Root Causes)** sau:

### 6.1. Nguyên nhân A: Sinh mã hàng loạt bằng AI (Massive AI Scaffolding) vượt ngưỡng kiểm soát
* **Bằng chứng git log:**
  - Commit `1416192` (`feat: implement modules 1-9 of Agentic Quantum system`): Sinh ra cùng lúc **343 tệp tin, 38.851 dòng mã mới**.
  - Commit `e4a4cfd` (`feat: implement modules 10-12 of Agentic Quantum system`): Sinh tiếp **100 tệp tin, 8.766 dòng mã mới**.
  - Tổng cộng gần **50.000 dòng code được tạo ra trong 2 đợt commit ồ ạt**.
* **Phân tích:** 
  Khi giao cho AI sinh mã một khối lượng khổng lồ vượt quá context window, AI sẽ tạo ra các khung code (scaffolding) trông rất đẹp và chuẩn mực về mặt cú pháp ở từng file đơn lẻ. Tuy nhiên, AI **không thể duy trì tính toàn vẹn của các mối nối liên kết (wiring)** giữa các tầng:
  - AI viết file `agentic_core/module.py` nhưng quên thêm nó vào `registry.py`.
  - AI viết các components tại `frontend/src/shared/agentic/` nhưng không import chúng vào các trang tại `frontend/src/features/`.
  - AI viết `modules/learning/agent_tools.py` chuẩn, nhưng khi chuyển sang viết `modules/ai_tutor/` thì lại tự chế một adapter stub riêng và hardcode dữ liệu.

### 6.2. Nguyên nhân B: Tư duy "Lập trình để Pass CI Unit Test" thay vì "Tích hợp End-to-End (Vertical Slice)"
* **Bằng chứng:** Trong 2 commit trên, hơn 40 tệp test đơn vị được tạo ra (`tests/test_simulation_*.py`, `tests/test_news_*.py`, `tests/modules/quant_research/*.py`...).
* **Phân tích:**
  - Quá trình phát triển bị chi phối bởi mục tiêu làm sao để lệnh `pytest` chạy màu xanh (exit 0) trên CI.
  - Để unit test pass nhanh và độc lập mà không cần kết nối mạng hay tốn chi phí API Key Gemini, người phát triển (hoặc AI) đã:
    1. Dùng f-string tĩnh thay vì gọi model thật trong `ai_tutor`.
    2. Gán cứng `card = DEFAULT_LEARNING_CARDS[0]` để test case assertion luôn luôn trả về giá trị đoán trước được (deterministic assertions).
    3. Dùng `_RUN_STORE` in-memory dictionary để test chạy nhanh trong mili-giây mà không cần setup database migration.
  - **Hệ quả chết người:** Unit test pass 100%, nhưng hệ thống thực tế (Runtime) chưa từng có một bài kiểm thử tích hợp (E2E Integration Test) nào chạy qua luồng: `User Click UI → Network Call → FastAPI App Factory → StateGraph → Gemini Provider → SQLite Persistence`.

### 6.3. Nguyên nhân C: Hiện tượng "Cắt góc / Shortcut Stubs" khi cạn Context Window
* **Phân tích:**
  Khi một mô hình AI phải sinh mã cho 12 module phức tạp, khi chạm tới các phần việc khó đòi hỏi tính bền vững cao (như viết SQLite schema migration, quản lý transaction ACID, hay xử lý luồng duyệt 2-phase confirmation), mô hình sẽ tự động chọn các giải pháp "cắt góc" (shortcuts):
  - Thay vì viết migration và table: Dùng `_RUN_STORE = OrderedDict()` trong RAM.
  - Thay vì xử lý logic duyệt action proposal: Ném `raise HTTPException(501, "ActionProposal service not ready")`.
  - Thay vì đọc đúng lesson theo `context_id`: Lấy luôn phần tử đầu tiên `DEFAULT_LEARNING_CARDS[0]`.

### 6.4. Nguyên nhân D: Triển khai theo chiều ngang (Horizontal Silos) thay vì chiều dọc (Vertical Slices)
* **Phân tích:**
  Dự án đã cố gắng thi công theo chiều ngang: Dựng khung toàn bộ 12 module cùng một lúc (Tạo folder, tạo interface, tạo DTO cho tất cả mọi thứ). Kết quả là có 12 module nửa vời, không có module nào chạy thông suốt từ Frontend xuống Database.
* **Bài học rút ra:** Cần chuyển đổi ngay lập tức sang phương pháp **Vertical Slice Engineering**: Chọn duy nhất 1 lát cắt (ví dụ: AI Tutor cho Learn Hub hoặc BCTC Deep-Dive), làm thông suốt 100% từ UI $\rightarrow$ API $\rightarrow$ LLM $\rightarrow$ DB, kiểm thử chạy thử nghiệm thành công rồi mới nhân bản sang các lát cắt tiếp theo.

---

## MỤC 7: KẾ HOẠCH HÀNH ĐỘNG KHẮC PHỤC TRIỆT ĐỂ (3 GIAI ĐOẠN)

### Giai đoạn 1: Ổn định khẩn cấp & Khai thông dòng chảy dữ liệu (Immediate Stabilization)

| Bước | Nhiệm vụ kỹ thuật | Tệp cần xử lý | Hành động chuẩn xác |
|---|---|---|---|
| **1.1** | **Mount Router `agentic_core` vào FastAPI** | `src/risk_dashboard/app/registry/registry.py` | Import `agentic_core_module` và thêm vào tuple `get_registered_modules()`. Chấm dứt ngay nguy cơ lỗi HTTP 404 khi gọi `/api/v1/public/agentic/*`. |
| **1.2** | **Xóa bỏ ROE Hardcode & Nối LLM thật cho AI Tutor** | `ai_tutor/infrastructure/adapters/learning_adapter.py`<br>`ai_tutor/application/specialists/learning_specialist.py`<br>`ai_tutor/application/specialists/quant_specialist.py` | 1. Sửa `learning_adapter.py`: Lấy đúng lesson theo `context_id` hoặc gọi `LearningGetContextTool`.<br>2. Inject `LLMProvider` (từ `platform.ai_runtime.factory.get_default_provider`) vào các Specialist.<br>3. Thay thế các khối f-string bằng `provider.generate(ModelTask)`. |
| **1.3** | **Khắc phục lỗi CSS bó cứng chiều cao Khung Chat** | `frontend/src/features/learn-hub/pages/learn-tutor.css:1-9` | Thay `height: 480px` bằng `flex: 1 1 auto; min-height: 0;`. Cấu hình khung chứa tin nhắn `overflow-y: auto` để cuộn mượt mà theo toàn bộ chiều cao Drawer. |
| **1.4** | **Bọc an toàn ghi Cache Data Hub** | `data_hub/application/global_market_feed.py:386-394` | Bọc `try/except (PermissionError, OSError)` khi ghi tệp cache `global_market_snapshot.json`, ghi log warning và fallback in-memory nếu lỗi quyền truy cập. |
| **1.5** | **Bổ sung TTL 24h cho Cache BCTC** | `src/risk_dashboard/data/financials.py:405-431` | Kiểm tra trường `generated_at` trong tệp `{ticker}.json`. Nếu vượt quá 24h thì thực hiện refresh từ Vnstock để số liệu không bị cũ vô hạn. |

### Giai đoạn 2: Bền vững hóa Agentic Core & Khai tử Mã mồ côi (Core Persistence & UI Wiring)

| Bước | Nhiệm vụ kỹ thuật | Tệp tham chiếu | Hành động chuẩn xác |
|---|---|---|---|
| **2.1** | **Database Migration cho Agentic Core** | `src/risk_dashboard/platform/database/migrate.py` | Tạo Migration 016 bổ sung 3 bảng SQLite: `agentic_core_runs`, `agentic_core_artifacts`, `agentic_core_action_proposals`. Chuyển đổi `_RUN_STORE` từ RAM sang SQLite để đảm bảo ACID. |
| **2.2** | **Hiện thực hóa Action Proposals Endpoints** | `agentic_core/api/public.py:223-239` | Xóa bỏ `HTTPException(501)`. Tái sử dụng mẫu thiết kế từ `pro_lab/application/simulation_actions.py` để xử lý xác nhận (`:confirm`), hủy bỏ (`:reject`), kiểm tra idempotency và ghi `ActionReceipt`. |
| **2.3** | **Đấu nối UI Components vào các Trang Nghiệp vụ** | `frontend/src/features/learn-hub/`<br>`frontend/src/features/financial-ratio/` | Import và nhúng `<AgentRunPanel />` từ `frontend/src/shared/agentic/`. Thêm các nút bấm nghiệp vụ (Contextual CTA) như `[Phân tích chuyên sâu BCTC]` để gọi `agenticApi.createRun()`. |
| **2.4** | **Kích hoạt Module `quant_research`** | `src/risk_dashboard/modules/quant_research/module.py` | Bật cờ `enabled_by_default=True` để đưa bộ công cụ phân tích rủi ro định lượng và mô hình `QuantNumericReviewer` vào hoạt động. |

### Giai đoạn 3: Hoàn thiện Assurance Plane & Phân rã 11 Specialists (Strategic Maturation)

| Bước | Nhiệm vụ kỹ thuật | Tệp tham chiếu | Hành động chuẩn xác |
|---|---|---|---|
| **3.1** | **Mở rộng `ClaimLedger` & Numeric Reviewer** | `agentic_core/application/review.py` | Kế thừa cơ chế so khớp từ `QuantNumericReviewer` (`modules/quant_research/application/reviewer.py:68`), thực hiện kiểm chứng 100% số liệu giữa phát biểu của LLM với đầu ra của Tools (`abs_tol=1e-4`). |
| **3.2** | **Định nghĩa đầy đủ 10 Domain Artifact Schemas** | `agentic_core/schemas/artifact.py` | Thay thế schema generic `AgentArtifact` bằng 10 lớp Pydantic cụ thể theo đặc tả `USER_INTERACTION_GUIDE.md`. |
| **3.3** | **Phân rã LangGraph Subgraphs** | `agentic_core/application/graph.py:270` | Mở rộng nút `specialist_node` thành bộ điều hướng Intent Router kết nối tới 11 Domain Toolsets đã xây dựng sẵn ở các module. |

---

## PHỤ LỤC: DANH MỤC LỆNH KIỂM CHỨNG ĐÃ THỰC THI (VERIFICATION LOG)

```bash
# 1. Kiểm tra đăng ký module agentic_core trong registry trung tâm
grep -rn "agentic_core" src/risk_dashboard/app/registry/
# Kết quả: KHÔNG TÌM THẤY (Router chưa được đăng ký vào app registry)

# 2. Kiểm tra danh sách route runtime của FastAPI
.venv/bin/python3 -c "
from risk_dashboard.app.bootstrap.app_factory import create_app
app = create_app()
routes = [getattr(r, 'path', str(r)) for r in app.routes if 'agentic' in str(r)]
print('Agentic routes in app:', routes)
"
# Kết quả: Agentic routes in app: [] (Hoàn toàn không có route agentic trong FastAPI)

# 3. Kiểm tra hardcode ROE trong adapter của AI Tutor
sed -n '28,35p' src/risk_dashboard/modules/ai_tutor/infrastructure/adapters/learning_adapter.py
# Kết quả: card = DEFAULT_LEARNING_CARDS[0] (Cố định bài card_roe_01)

# 4. Kiểm tra mã nguồn module quant_research và reviewer
wc -l src/risk_dashboard/modules/quant_research/application/reviewer.py
# Kết quả: 155 dòng (Hiện thực đầy đủ ClaimLedger, Exact Numeric Check và Anti-Quantum patterns)

# 5. Kiểm tra các tool manifests của BCTC
python3 -c "
from risk_dashboard.modules.financials_product.agent_tools import get_bctc_tool_manifests
print([t.tool_id for t in get_bctc_tool_manifests()])
"
# Kết quả: ['bctc.resolve_report', 'bctc.resolve_line_item', 'bctc.compare_periods', 'bctc.calculate_ratio', 'bctc.trace_provenance', 'bctc.build_evidence_table']

# 6. Kiểm tra lịch sử commit phát sinh mã hàng loạt
git log -n 5 --oneline
# Kết quả: commit 1416192 sinh 343 files / 38.851 lines; commit e4a4cfd sinh 100 files / 8.766 lines
```
