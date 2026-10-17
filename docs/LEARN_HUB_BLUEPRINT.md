# ĐẶC TẢ KỸ THUẬT VÀ BẢN THIẾT KẾ TRIỂN KHAI PHÂN HỆ LEARN HUB v2.0
## (Technical Specification & Implementation Blueprint)

**Tài liệu**: `docs/LEARN_HUB_BLUEPRINT.md`  
**Phiên bản**: 2.0.0-PROD  
**Trạng thái**: Authoritative Technical Specification  
**Ngày ban hành**: 2026-10-10  
**Tác giả**: Teamwork Architecture & Engineering Guild (`worker_m3_blueprint`)  
**Đối tượng áp dụng**: Full-Stack AI Engineers, Frontend Engineers, Backend Engineers, QA/Auditors  

---

## MỤC LỤC CHI TIẾT

1. [Tổng Quan Dự Án & Mục Tiêu Kỹ Thuật (Executive Overview & Engineering Objectives)](#1-tổng-quan-dự-án--mục-tiêu-kỹ-thuật)
   - 1.1. Bối cảnh và Tầm nhìn Kiến trúc
   - 1.2. Các Nguyên Tắc Thiết Kế Bất Biến (System Invariants)
   - 1.3. Kiến trúc Tổng thể Hệ thống (End-to-End System Topology)
2. [Chi Tiết Bộ Hợp Đồng API REST & Streaming (Exhaustive API Contracts)](#2-chi-tiết-bộ-hợp-đồng-api-rest--streaming)
   - 2.1. Quy ước Kỹ thuật Chung (Conventions, Headers, Status Codes & Error Envelope)
   - 2.2. Nhóm API Danh mục Học liệu Đa định dạng (Multi-Format Catalog v2)
   - 2.3. Nhóm API Tiến độ Học tập & Xác thực Checkpoint (Progress & Cryptographic Receipts)
   - 2.4. Nhóm API Ghi chú & Đánh dấu Tài liệu (Annotations, Bookmarks & Video Notes)
   - 2.5. Đặc tả Giao thức Streaming AI Tutor qua Server-Sent Events (SSE)
3. [Cấu Trúc Thành Phần Giao Diện Frontend & Layout Chia Đôi (Frontend Component Architecture)](#3-cấu-trúc-thành-phần-giao-diện-frontend--layout-chia-đôi)
   - 3.1. Kiến trúc Master Layout: `<LearnHubDualPaneLayout />` & `<SocraticStreamProvider />`
   - 3.2. Cây Phân Cấp Thành Phần (Component Hierarchy Breakdown - Strict <200 Lines)
   - 3.3. State Machines & Custom Hooks Triệt tiêu Điểm nghẽn Hiệu năng
4. [Lộ Trình Triển Khai Phân Đoạn 5 Bước (5-Phase Tracer-Bullet Migration Roadmap)](#4-lộ-trình-triển-khai-phân-đoạn-5-bước)
   - 4.1. Phase 0: Quick Wins, Hardening & Bug Remediation (Remediate Audit Defects)
   - 4.2. Phase 1: Tracer Bullet #1 - Multi-Format DDL, Pydantic Schemas & Catalog v2
   - 4.3. Phase 2: Tracer Bullet #2 - Dual-Pane Layout, Ebook Reader & Video Player Workspaces
   - 4.4. Phase 3: Tracer Bullet #3 - BCTC Case-Study Sandbox & Stock Symbol Cross-Linking
   - 4.5. Phase 4: Tracer Bullet #4 - SSE Streaming AI Tutor with Multi-Modal Context Grounding
   - 4.6. Phase 5: Production Hardening, CFA Alignment & Legacy Deprecation
5. [Phụ Lục Kỹ Thuật (Technical Appendices)](#5-phụ-lục-kỹ-thuật)
   - Phụ lục A: Bảng Mã Lỗi Tiêu Chuẩn (Standardized Error Codes)
   - Phụ lục B: Bảng Ma Trận Ánh Xạ Độ Khó & Danh Mục Chủ Đề (Taxonomy & Difficulty Matrix)
   - Phụ lục C: Ma Trận Truy Xuất Mã Nguồn Đối Ứng (Traceability Matrix)

---

## 1. TỔNG QUAN DỰ ÁN & MỤC TIÊU KỸ THUẬT

### 1.1. Bối cảnh và Tầm nhìn Kiến trúc
Hệ thống **Agent Tài chính (Northstar Finance Lab)** định vị là nền tảng phân tích tài chính thông minh kết hợp môi trường đào tạo chuyên sâu chuẩn CFA và thực tế thị trường chứng khoán Việt Nam (HOSE/HNX). Phân hệ Tab Learn (Learn Hub) ban đầu được xây dựng dưới dạng các trang nội dung tĩnh và micro-lessons đơn lẻ, dẫn đến các điểm nghẽn nghiêm trọng:
1. **Thiếu tính đa định dạng có cấu trúc**: Các dạng tài nguyên (Ebook/PDF, Video bài giảng, Khóa học phân cấp, BCTC Case-study) bị phân tán, lưu trữ phẳng và không có sự liên kết hữu cơ.
2. **Giao diện người dùng bị chia cắt**: Người học không thể vừa xem tài liệu/video vừa tương tác cùng AI Tutor mà phải chuyển tab liên tục, làm gián đoạn dòng tư duy phân tích.
3. **Các lỗ hổng hiệu năng và tính toàn vẹn**: Trình phát video re-render 4–5 lần/giây, bộ nhớ đồ họa rò rỉ do vẽ canvas hàng loạt, dữ liệu đề thi CFA bị lộ 100% ở phía client, và các lệnh I/O đồng bộ gây block asyncio event loop ở backend.

**Learn Hub v2.0** tái thiết lập toàn bộ kiến trúc này thành một **Nền tảng Quản trị & Tương tác Học liệu Đa định dạng Đồng nhất**, vận hành trên nền kiến trúc giao diện **Dual-Pane Split Layout**, kết nối dữ liệu báo cáo tài chính thực tế của hơn 120 doanh nghiệp niêm yết, và trợ lý học tập Socratic hỗ trợ Server-Sent Events (SSE) streaming với khả năng neo ngữ cảnh đa chiều (Multi-Modal Context Grounding).

---

### 1.2. Các Nguyên Tắc Thiết Kế Bất Biến (System Invariants)
Mọi dòng code, cấu trúc dữ liệu và API trong Learn Hub v2.0 PHẢI tuân thủ 5 nguyên tắc bất biến:

1. **Nguyên tắc Bảo mật Checkpoint (Zero-Leakage Invariant)**:
   - Tuyệt đối không bao giờ trả về đáp án đúng (`correct_option`, `correct_answer`), lời giải thích hoàn chỉnh (`explanation`), hoặc trọng số chấm điểm trong payload API gửi xuống Client trước khi người học hoàn tất nộp bài.
   - Đáp án đề thi CFA Mock Exam và câu hỏi kiểm tra video phải được quản lý và chấm điểm 100% tại Backend. Client chỉ nhận ID câu hỏi và danh sách phương án lựa chọn.
2. **Nguyên tắc Cam kết Tiến độ Hai Pha (Deterministic 2-Phase Progress Receipts)**:
   - Mọi mốc hoàn thành bài học, chương video, hoặc checkpoint trắc nghiệm đều phải trải qua quy trình xác thực 2 pha: Phase 1 (Grade & Verify) sinh ra `verified_event_id` kèm chữ ký cryptographic hash, Phase 2 (Commit Progress) sinh ra `confirmation_id` với `idempotency_key` chống ghi đè hoặc tấn công lặp lại.
   - Tiến độ học tập phải được lưu trữ bền vững tại máy chủ SQLite/PostgreSQL, chấm dứt hoàn toàn việc phụ thuộc đơn lẻ vào `localStorage` của trình duyệt.
3. **Quy tắc Kiến trúc Mô-đun Hóa Frontend (Hard Limit <200 Lines/Module)**:
   - Mọi component, custom hook, hoặc service file tạo mới hoặc chỉnh sửa trong `frontend/src/features/learn-hub` PHẢI duy trì dưới 200 dòng code.
   - Các component vượt quá kích thước phải được phân rã thành các sub-components chuyên trách (Presentational Components, Container Hooks, Domain Views).
4. **Không Block Luồng Xử Lý (Non-Blocking Event Loop & Stream Isolation)**:
   - Tuyệt đối không gọi I/O đồng bộ (`urllib.request.urlopen`, SQLite blocking queries, file I/O thô) trực tiếp trong các hàm `async def` của FastAPI. Toàn bộ thao tác I/O đồng bộ phải bọc qua `asyncio.to_thread()` hoặc chuyển đổi sang thư viện bất đồng bộ (`httpx.AsyncClient`, `aiosqlite`).
   - Các endpoint stream (PDF proxy, SSE AI Tutor) phải sử dụng async generators để không chiếm giữ worker threads trong pool của server.
5. **Đồng Bộ Trạng Thái Hiệu Năng Cao (Throttled & Memoized Reactive State)**:
   - Các sự kiện thời gian thực từ video (`timeupdate`) hoặc cuộn trang PDF (`scroll`) phải được throttle tối thiểu 500ms – 1000ms trước khi cập nhật state hoặc gọi API lưu vị trí.
   - Sử dụng `useRef` và selective context subscriptions để cô lập việc re-render tại đúng widget hiển thị thời gian/số trang, không lan truyền re-render ra toàn bộ cây giao diện.

---

### 1.3. Kiến trúc Tổng thể Hệ thống (End-to-End System Topology)

```
+---------------------------------------------------------------------------------------------------+
|                                  CLIENT LAYER (React 18 + Vite)                                    |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  |                            <LearnHubDualPaneLayout /> (Split 60/40)                         |  |
|  |                                                                                             |  |
|  |  [LEFT PRIMARY PANE - WORKSPACES]                     [RIGHT COMPANION PANE - SOCRATIC]     |  |
|  |  +-------------------------------------------------+  +----------------------------------+  |  |
|  |  | - <EbookReaderWorkspace /> (PDF.js Vector)      |  | | - <SocraticAiCompanion />      |  |  |
|  |  | - <VideoPlayerWorkspace /> (YouTube API Bridge) |  | | - <AiTutorMessageList />       |  |  |
|  |  | - <CoursePlayerWorkspace /> (Hierarchical Tree) |  | | - <VideoTimestampNotes />      |  |  |
|  |  | - <BctcCaseStudyWorkspace /> (Financial Sandbox)|  | | - <SocraticContextBadge />     |  |  |
|  |  +-------------------------------------------------+  +----------------------------------+  |  |
|  +---------------------------------------------------------------------------------------------+  |
+--------------------------------------------------+------------------------------------------------+
                                                   | HTTP / REST (JSON) & SSE (text/event-stream)
                                                   v
+---------------------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION GATEWAY LAYER                                   |
|                                                                                                   |
|  [Router: /api/v1/public/learning/*]                 [Router: /api/v1/public/ai-tutor/*]          |
|  - Catalog & Asset Endpoints                         - Conversation Lifecycle Management          |
|  - Course Hierarchy & Lesson Delivery                - SSE Stream Endpoint (/messages/stream)    |
|  - Checkpoint Grade & 2-Phase Progress Receipts       - Multi-Modal Context Grounding Processor    |
|  - Annotation, Bookmark & Timestamped Notes CRUD     - Zero-Leakage Prompt Guardrails Engine      |
+--------------------------------------------------+------------------------------------------------+
                                                   |
         +-----------------------------------------+----------------------------------------+
         |                                                                                  |
         v                                                                                  v
+----------------------------------+                                      +---------------------------------+
|      DOMAIN & STORAGE LAYER      |                                      |      AI RUNTIME & SPECIALISTS   |
|                                  |                                      |                                 |
| - SQLite WAL Mode / PostgreSQL   |                                      | - TutorGraph State Machine      |
|   (courses_v2, modules, lessons, |                                      | - LearningSpecialist (Socratic) |
|    checkpoints, receipts, notes) |                                      | - Gemini 2.5 Flash / Pro Provider|
| - FTS5 Unified Multi-Format Index|                                      | - Evidence & Numeric Reviewers  |
| - BCTC Cache Engine (120+ VN30)  |                                      | - StreamEvent Serialization     |
+----------------------------------+                                      +---------------------------------+
```

---

## 2. CHI TIẾT BỘ HỢP ĐỒNG API REST & STREAMING

### 2.1. Quy ước Kỹ thuật Chung (Conventions, Headers, Status Codes & Error Envelope)

- **Base URL**: `/api/v1/public`
- **Content-Type**:
  - REST Endpoints: `application/json; charset=utf-8`
  - Streaming Endpoints: `text/event-stream; charset=utf-8`
- **Chuẩn hóa Header bắt buộc**:
  - `X-Session-ID`: Chuỗi định danh phiên làm việc của người dùng (UUID v4 hoặc định dạng `sess_anon_...`). Bắt buộc cho mọi request lưu tiến độ và gọi AI Tutor.
  - `X-Request-ID`: Chuỗi định danh phân tán cho mỗi request (UUID v4) để truy vết telemetry log.
  - `Idempotency-Key`: Khóa chống trùng lặp bắt buộc cho các thao tác ghi nhận tiến độ (`complete`, `commit`).
- **Cấu trúc Bao bọc Lỗi Chuẩn (Standard Error Envelope)**:
  Mọi lỗi từ hệ thống (HTTP 4xx, 5xx) đều tuân thủ schema Pydantic `ApiErrorResponse`:
  ```json
  {
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "Không tìm thấy khóa học với định danh được yêu cầu.",
      "details": {
        "resource_type": "course",
        "resource_id": "course_cfa_fsa_999"
      },
      "trace_id": "req_8f1a23c09b",
      "timestamp": "2026-10-10T11:20:00Z"
    }
  }
  ```
- **Quy tắc Kiểm soát Bộ nhớ Đệm HTTP (Standardized Cache-Control Specification Matrix)**:
  Để ngăn ngừa tuyệt đối lỗi hiển thị trạng thái học tập dở dang cũ (stale progress) sau khi người học đã hoàn thành bài học hoặc nộp bài checkpoint, toàn bộ các endpoint thuộc Learn Hub tuân thủ ma trận Cache-Control nghiêm ngặt:

  | Loại Endpoint | Phân Loại Tuyến API | Header Cache-Control Chuẩn | Rationale & Cơ Chế Hoạt Động |
  |---|---|---|---|
  | **Danh mục Chung (Public Catalog)** | `GET /learning/catalog`, `GET /learning/topics` | `public, max-age=300, stale-while-revalidate=60` | Dữ liệu danh mục chung, cho phép browser & CDN cache 5 phút, revalidate nền trong 60 giây tiếp theo. |
  | **Tiến độ Học tập & Chi tiết Khóa học** | `GET /learning/courses/{id}`, `GET /learning/lessons/{id}` | `private, no-cache, must-revalidate` *(khi có `X-Session-ID`)* | **BẮT BUỘC**: Chứa dữ liệu cá nhân hóa (`progress_summary`, `is_unlocked`, `status`). Trình duyệt PHẢI revalidate với server ở mọi lần truy cập; cấm dùng cache cũ để tránh báo sai bài học chưa xong. Khách vãng lai không session dùng `public, max-age=900`. |
  | **Tài nguyên Binary / PDF Stream** | `GET /learning/books/{id}/pdf-stream` | `public, max-age=86400, immutable` | File tĩnh không đổi theo người học, cache 24h trên client để tiết kiệm băng thông. |
  | **Đột biến Tiến độ & Chấm điểm (Mutations)** | `POST /learning/lessons/{id}/complete`, `POST /learning/checkpoints/{id}/submit` | `no-store, no-cache, must-revalidate` | Tuyệt đối không lưu cache cho các lệnh ghi nhận giao dịch tiến độ hoặc nộp bài thi. |
  | **Luồng SSE AI Tutor Stream** | `POST /ai-tutor/.../messages/stream` | `no-cache, no-transform` | Luồng sự kiện thời gian thực Server-Sent Events, cấm proxy nén hoặc hoãn buffer. |


---

### 2.2. Nhóm API Danh mục Học liệu Đa định dạng (Multi-Format Catalog v2)

#### 2.2.1. `GET /api/v1/public/learning/catalog`
Lấy danh mục học liệu đa định dạng với bộ lọc chuyên sâu, phân trang và chính sách cache tối ưu.

- **Query Parameters**:
  - `kind` (optional, string): Lọc theo loại học liệu: `course` | `book` | `video` | `bctc_case` | `paper`. Mặc định trả về tổng hợp.
  - `topic` (optional, string): Slug định danh chủ đề (ví dụ: `financial_statements`, `cashflow_quality`, `valuation_dcf`).
  - `tier` (optional, string): Phân cấp độ khó: `beginner` | `intermediate` | `advanced`.
  - `ticker` (optional, string): Lọc các học liệu có liên kết với mã cổ phiếu cụ thể (ví dụ: `HPG`, `VNM`, `FPT`).
  - `search` (optional, string): Từ khóa tìm kiếm toàn văn FTS5 trong tiêu đề, mô tả và nội dung tác giả.
  - `sort_by` (optional, string): Tiêu chí sắp xếp: `featured` | `latest` | `duration_asc` | `duration_desc`. Mặc định: `featured`.
  - `page` (optional, integer, default: 1): Trang hiện tại (1-indexed).
  - `page_size` (optional, integer, default: 20, max: 100): Số lượng mục trên mỗi trang.

- **Chính sách Cache (Caching Policy)**:
  - **HTTP Response Header**: `Cache-Control: public, max-age=300, stale-while-revalidate=60` (Client và Reverse Proxy cache 5 phút, cho phép phục vụ nội dung cũ trong 60 giây trong khi revalidate nền).
  - **Backend In-Memory/Redis Cache**: Khóa cache dạng `catalog:v2:{kind}:{topic}:{tier}:{ticker}:{sort}:{page}:{size}`. TTL: **600 giây (10 phút)**. Invalidate tự động khi có sự kiện xuất bản nội dung từ Admin CMS.

- **Response Body Schema (HTTP 200 OK)**:
  ```json
  {
    "meta": {
      "total_items": 142,
      "total_pages": 8,
      "current_page": 1,
      "page_size": 20,
      "applied_filters": {
        "kind": "all",
        "topic": "financial_statements",
        "tier": "intermediate",
        "ticker": null
      }
    },
    "topics": [
      {
        "topic_id": "financial_statements",
        "label_vi": "Phân Tích Báo Cáo Tài Chính",
        "label_en": "Financial Statement Analysis",
        "tier": "intermediate",
        "count": 45
      }
    ],
    "items": [
      {
        "resource_id": "course_cfa_fsa_101",
        "kind": "course",
        "title": "Phân Tích Báo Cáo Tài Chính Chuẩn CFA Level I",
        "slug": "phan-tich-bctc-cfa-level-1",
        "description": "Nắm vững bản chất liên kết giữa Bảng Cân Đối, P&L và Báo Cáo Lưu Chuyển Tiền Tệ.",
        "instructor": "Northstar Faculty",
        "tier": "intermediate",
        "duration_minutes": 180,
        "thumbnail_url": "/learning-assets/images/courses/cfa_fsa_thumb.webp",
        "topics": ["financial_statements", "cashflow_quality"],
        "linked_tickers": ["HPG", "VNM", "FPT"],
        "stats": {
          "total_modules": 4,
          "total_lessons": 16,
          "enrolled_count": 1250
        },
        "published_at": "2026-08-15T00:00:00Z"
      },
      {
        "resource_id": "book_benjamin_graham_intelligent_investor",
        "kind": "book",
        "title": "The Intelligent Investor - Nhà Đầu Tư Thông Minh",
        "slug": "the-intelligent-investor-benjamin-graham",
        "description": "Tác phẩm kinh điển về trường phái đầu tư giá trị và nguyên lý biên an toàn (Margin of Safety).",
        "instructor": "Benjamin Graham",
        "tier": "beginner",
        "duration_minutes": 420,
        "thumbnail_url": "/learning-assets/images/books/intelligent_investor.webp",
        "topics": ["valuation_dcf", "portfolio_theory"],
        "linked_tickers": [],
        "stats": {
          "total_pages": 640,
          "format": "pdf"
        },
        "published_at": "2026-01-10T00:00:00Z"
      },
      {
        "resource_id": "bctc_case_hpg_capex_2024",
        "kind": "bctc_case",
        "title": "HPG: Chu Kỳ Tồn Kho & Dòng Tiền Tự Do Giai Đoạn Mở Rộng Dung Quất 2",
        "slug": "hpg-chu-ky-ton-kho-fcf-dung-quat-2",
        "description": "Bóc tách BCTC thực tế của Hòa Phát, đánh giá áp lực FCF âm và cơ cấu nợ vay tài trợ tài sản dở dang.",
        "instructor": "Hội đồng Phân tích Northstar",
        "tier": "intermediate",
        "duration_minutes": 45,
        "thumbnail_url": "/learning-assets/images/bctc/hpg_case_thumb.webp",
        "topics": ["financial_statements", "cashflow_quality"],
        "linked_tickers": ["HPG"],
        "stats": {
          "ticker": "HPG",
          "period": "2024-Q3",
          "challenge_count": 3
        },
        "published_at": "2026-09-01T00:00:00Z"
      }
    ]
  }
  ```

---

#### 2.2.2. `GET /api/v1/public/learning/courses/{course_id}`
Lấy chi tiết toàn diện của khóa học phân cấp (Course -> Modules -> Lessons -> Checkpoints) kèm trạng thái mở khóa và tỷ lệ hoàn thành.

- **Path Parameters**: `course_id` (string): Mã định danh khóa học.
- **Headers**: `X-Session-ID` (optional): Định danh phiên để đối chiếu tiến độ cá nhân.
- **Cache**: `Cache-Control: private, no-cache, must-revalidate` khi có `X-Session-ID` (BẮT BUỘC: Ngăn ngừa hoàn toàn việc trình duyệt hoặc CDN lưu cache trạng thái học dở dang cũ, đảm bảo cập nhật tỷ lệ hoàn thành khóa học tức thì ngay khi hoàn thành bài học); `Cache-Control: public, max-age=900` khi không có session (khách vãng lai).

- **Response Body Schema (HTTP 200 OK)**:
  ```json
  {
    "course_id": "course_cfa_fsa_101",
    "title": "Phân Tích Báo Cáo Tài Chính Chuẩn CFA Level I",
    "slug": "phan-tich-bctc-cfa-level-1",
    "description": "Chương trình huấn luyện phân tích tài chính doanh nghiệp bài bản theo chuẩn viện CFA Hoa Kỳ.",
    "instructor": "Northstar Research Faculty",
    "tier": "intermediate",
    "total_duration_minutes": 180,
    "thumbnail_url": "/learning-assets/images/courses/cfa_fsa_thumb.webp",
    "topics": ["financial_statements", "cashflow_quality", "financial_ratios"],
    "linked_tickers": ["HPG", "VNM", "FPT"],
    "progress_summary": {
      "total_lessons": 4,
      "completed_lessons": 1,
      "completion_percentage": 25,
      "current_lesson_id": "les_fsa_01_02"
    },
    "modules": [
      {
        "module_id": "mod_fsa_01",
        "sequence_order": 1,
        "title": "Module 1: Bản Chất Liên Kết Giữa Ba Báo Cáo Cốt Lõi",
        "description": "Hiểu rõ cơ chế luân chuyển dòng vốn từ Bảng Cân Đối sang P&L và Báo Cáo Lưu Chuyển Tiền Tệ.",
        "is_unlocked": true,
        "prerequisites_met": true,
        "lessons": [
          {
            "lesson_id": "les_fsa_01_01",
            "sequence_order": 1,
            "title": "Bảng Cân Đối Kế Toán & Cơ Cấu Tài Sản - Nguồn Vốn",
            "lesson_type": "video",
            "content_ref_id": "vid_yt_balance_sheet_basics",
            "duration_minutes": 18,
            "is_free_preview": true,
            "status": "completed",
            "checkpoint": {
              "checkpoint_id": "chk_fsa_01_01",
              "has_completed": true,
              "score": 100
            }
          },
          {
            "lesson_id": "les_fsa_01_02",
            "sequence_order": 2,
            "title": "Case Study Thực Chiến HPG: Đánh Giá Tài Sản Dở Dang & Nợ Vay",
            "lesson_type": "bctc_case",
            "content_ref_id": "bctc_case_hpg_capex_2024",
            "duration_minutes": 35,
            "is_free_preview": false,
            "status": "in_progress",
            "checkpoint": {
              "checkpoint_id": "chk_fsa_01_02",
              "has_completed": false,
              "score": 0
            }
          }
        ]
      },
      {
        "module_id": "mod_fsa_02",
        "sequence_order": 2,
        "title": "Module 2: Đánh Giá Chất Lượng Doanh Thu & Lợi Nhuận",
        "description": "Phát hiện các thủ thuật kế toán bóp méo lợi nhuận và đánh giá chất lượng dòng tiền hoạt động kinh doanh (CFO).",
        "is_unlocked": false,
        "prerequisites_met": false,
        "lessons": [
          {
            "lesson_id": "les_fsa_02_01",
            "sequence_order": 1,
            "title": "Khoản Phải Thu & Tỷ Lệ DSO: Nhận Diện Doanh Thu Ảo",
            "lesson_type": "reading",
            "content_ref_id": "book_sec_financial_shenanigans_ch4",
            "duration_minutes": 25,
            "is_free_preview": false,
            "status": "locked",
            "checkpoint": null
          }
        ]
      }
    ]
  }
  ```

---

#### 2.2.3. `GET /api/v1/public/learning/lessons/{lesson_id}`
Lấy dữ liệu chi tiết bài học và trạng thái tiến độ cá nhân của người học.

- **Path Parameters**: `lesson_id` (string): Mã định danh bài học.
- **Headers**: `X-Session-ID` (optional): Định danh phiên để tra cứu tiến độ cá nhân hóa.
- **Cache**: `Cache-Control: private, no-cache, must-revalidate` khi có `X-Session-ID` (BẮT BUỘC: Ngăn chặn trình duyệt lưu cache trạng thái học dở dang cũ, bảo đảm khi học viên quay lại sau khi hoàn thành bài học thì trạng thái `completed` được phản ánh tức thì); `Cache-Control: public, max-age=600` khi không có session.

- **Response Body Schema (HTTP 200 OK)**:
  ```json
  {
    "lesson_id": "les_fsa_01_01",
    "course_id": "course_cfa_fsa_101",
    "module_id": "mod_fsa_01",
    "title": "Bảng Cân Đối Kế Toán & Cơ Cấu Tài Sản - Nguồn Vốn",
    "lesson_type": "video",
    "content_ref_id": "vid_yt_balance_sheet_basics",
    "duration_minutes": 18,
    "sequence_order": 1,
    "is_unlocked": true,
    "user_progress": {
      "status": "completed",
      "last_playback_position": 1080.0,
      "time_spent_seconds": 1240,
      "completed_at": "2026-10-10T11:22:00Z"
    },
    "checkpoint": {
      "checkpoint_id": "chk_fsa_01_01",
      "has_completed": true,
      "score": 100
    }
  }
  ```

---

#### 2.2.4. `GET /api/v1/public/learning/books/{book_id}`
Lấy thông tin siêu dữ liệu sách PDF, mục lục phân trang, tiến độ đọc của người dùng và URL stream tài liệu.

- **Response Body Schema (HTTP 200 OK)**:
  ```json
  {
    "book_id": "book_benjamin_graham_intelligent_investor",
    "title": "The Intelligent Investor",
    "author": "Benjamin Graham",
    "description": "Tác phẩm nền tảng của phân tích chứng khoán theo trường phái đầu tư giá trị.",
    "publication_year": 1949,
    "language": "en",
    "tier": "beginner",
    "total_pages": 640,
    "cover_url": "/learning-assets/images/books/intelligent_investor.webp",
    "stream_url": "/api/v1/public/learning/reader/stream?asset_id=book_benjamin_graham_intelligent_investor",
    "user_reading_state": {
      "current_page": 45,
      "read_percentage": 7,
      "total_annotations": 12,
      "total_bookmarks": 3,
      "last_read_at": "2026-10-09T16:30:00Z"
    },
    "table_of_contents": [
      {
        "title": "Chapter 1: Investment versus Speculation",
        "page_number": 18,
        "subsections": [
          { "title": "Results to Be Expected by the Lay Investor", "page_number": 24 }
        ]
      },
      {
        "title": "Chapter 2: The Investor and Inflation",
        "page_number": 47,
        "subsections": []
      }
    ]
  }
  ```

---

#### 2.2.5. `GET /api/v1/public/learning/videos/{video_id}`
Lấy dữ liệu chi tiết video bài giảng, danh sách phân đoạn chương mục (Chapters), tóm tắt AI Key Takeaways và mốc transcript song ngữ.

- **Response Body Schema (HTTP 200 OK)**:
  ```json
  {
    "video_id": "vid_yt_balance_sheet_basics",
    "title": "Bản Chất Bảng Cân Đối Kế Toán & Cách Đọc Chỉ Tiêu",
    "channel": "Northstar Academy",
    "duration_seconds": 1080.5,
    "video_source": "youtube",
    "external_id": "dQw4w9WgXcQ",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "embed_url": "https://www.youtube.com/embed/dQw4w9WgXcQ?enablejsapi=1&modestbranding=1",
    "thumbnail_url": "/learning-assets/images/videos/balance_sheet_thumb.webp",
    "topics": ["financial_statements"],
    "linked_tickers": ["HPG", "VNM"],
    "chapters": [
      {
        "chapter_id": "chap_01",
        "sequence_order": 1,
        "start_seconds": 0.0,
        "end_seconds": 245.0,
        "title": "Định Nghĩa Phương Trình Kế Toán Cơ Bản",
        "summary": "Tài sản = Nợ phải trả + Vốn chủ sở hữu. Nguyên lý cân bằng kép trong kế toán tài chính.",
        "key_takeaways": [
          "Tài sản đại diện cho nguồn lực do doanh nghiệp kiểm soát và kỳ vọng mang lại lợi ích kinh tế trong tương lai.",
          "Nguồn vốn phản ánh nghĩa vụ nợ và phần giá trị còn lại thuộc về các cổ đông sở hữu."
        ]
      },
      {
        "chapter_id": "chap_02",
        "sequence_order": 2,
        "start_seconds": 245.0,
        "end_seconds": 680.0,
        "title": "Phân Biệt Tài Sản Ngắn Hạn & Dài Hạn",
        "summary": "Quy ước chu kỳ kinh doanh 12 tháng và ý nghĩa thanh khoản của các khoản tiền gửi, tồn kho, phải thu.",
        "key_takeaways": [
          "Tài sản ngắn hạn có khả năng chuyển đổi thành tiền trong vòng 1 năm hoặc 1 chu kỳ kinh doanh thông thường.",
          "Cần thận trọng với các khoản phải thu tăng đột biến so với tốc độ tăng trưởng doanh thu."
        ]
      }
    ],
    "key_takeaways_summary": [
      "Phương trình kế toán là bất biến: Tổng Tài Sản luôn bằng Tổng Nguồn Vốn tại mọi thời điểm.",
      "Chất lượng tài sản quan trọng hơn quy mô tài sản: Cần trừ đi các khoản dự phòng giảm giá và tài sản ảo."
    ]
  }
  ```

---

#### 2.2.6. `GET /api/v1/public/learning/bctc-cases/{case_id}`
Lấy dữ liệu đầy đủ của một kịch bản tình huống thực hành BCTC, tích hợp ảnh chụp snapshot số liệu tài chính thực tế và các thử thách chỉ số.

- **Response Body Schema (HTTP 200 OK)**:
  ```json
  {
    "case_id": "bctc_case_hpg_capex_2024",
    "title": "HPG: Chu Kỳ Tồn Kho & Dòng Tiền Tự Do Giai Đoạn Mở Rộng Dung Quất 2",
    "ticker": "HPG",
    "period": "2024-Q3",
    "industry": "Thép & Vật Liệu Xây Dựng",
    "difficulty": "intermediate",
    "narrative_scenario": "Tập đoàn Hòa Phát đang tập trung nguồn lực khổng lồ để hoàn thành đại dự án Khu liên hợp Dung Quất 2. Người học đóng vai trò Chuyên viên Phân tích Rủi ro, cần kiểm tra bảng cân đối kế toán để xác định quy mô tài sản cố định dở dang, đánh giá chất lượng dòng tiền CFO và tính toán FCF để đưa ra kết luận về rủi ro thanh khoản ngắn hạn.",
    "financial_snapshot": {
      "currency": "VND",
      "scale": "tỷ",
      "balance_sheet": {
        "total_assets": 195200,
        "current_assets": 88400,
        "cash_and_equivalents": 31200,
        "inventories": 38500,
        "capex_wip": 45100,
        "total_liabilities": 89300,
        "short_term_debt": 52100,
        "long_term_debt": 18400,
        "owner_equity": 105900
      },
      "income_statement": {
        "revenue": 34100,
        "cogs": 29600,
        "gross_profit": 4500,
        "net_profit_after_tax": 3020
      },
      "cash_flow": {
        "operating_cash_flow": 12500,
        "investing_cash_flow": -18200,
        "financing_cash_flow": 4100,
        "capex_purchase_assets": -18000
      }
    },
    "challenges": [
      {
        "challenge_id": "ch_hpg_01",
        "title": "Tính Toán Dòng Tiền Tự Do (Free Cash Flow - FCF)",
        "prompt": "Sử dụng dòng tiền thuần từ hoạt động kinh doanh (CFO) và chi phí mua sắm tài sản cố định (Capex) trong kỳ Q3/2024 để tính toán FCF của Hòa Phát.",
        "target_metric": "fcf",
        "formula_hint": "FCF = CFO + Capex (Lưu ý dấu âm của dòng tiền đầu tư Capex)",
        "unit": "tỷ VND",
        "tolerance_percentage": 1.0
      },
      {
        "challenge_id": "ch_hpg_02",
        "title": "Đánh Giá Tỷ Số Nợ Vay / Vốn Chủ Sở Hữu (Debt-to-Equity)",
        "prompt": "Tính tổng nợ vay tài chính (Nợ vay ngắn hạn + Nợ vay dài hạn) chia cho Vốn chủ sở hữu để đánh giá đòn bẩy tài chính của tập đoàn.",
        "target_metric": "debt_to_equity",
        "formula_hint": "D/E = (Short-term Debt + Long-term Debt) / Owner Equity",
        "unit": "lần",
        "tolerance_percentage": 2.0
      }
    ]
  }
  ```

---

### 2.3. Nhóm API Tiến độ Học tập & Xác thực Checkpoint (Progress & Cryptographic Receipts)

#### 2.3.1. `POST /api/v1/public/learning/lessons/{lesson_id}/complete`
Ghi nhận hoàn thành bài học một cách tất định và bất biến trên máy chủ, cập nhật tiến độ module/khóa học và sinh chứng từ xác thực.

- **Path Parameters**: `lesson_id` (string): Mã định danh bài học.
- **Headers**:
  - `X-Session-ID` (required, string): Phiên định danh người học.
  - `Idempotency-Key` (required, string): Khóa chống trùng lặp từ client (UUID v4).
- **Request Body Schema**:
  ```json
  {
    "course_id": "course_cfa_fsa_101",
    "time_spent_seconds": 1240,
    "last_playback_position": 1080.0,
    "completed_at": "2026-10-10T11:22:00Z"
  }
  ```
- **Response Body Schema (HTTP 200 OK)**:
  ```json
  {
    "status": "success",
    "lesson_id": "les_fsa_01_01",
    "course_id": "course_cfa_fsa_101",
    "progress": {
      "lesson_status": "completed",
      "module_progress_pct": 50,
      "course_progress_pct": 25,
      "next_recommended_lesson_id": "les_fsa_01_02"
    },
    "receipt": {
      "receipt_id": "rec_prog_9a81f0b2",
      "idempotency_key": "idemp_client_34901",
      "checksum": "sha256:7c9e1...b84f",
      "recorded_at": "2026-10-10T11:22:01Z"
    }
  }
  ```

---

#### 2.3.2. `POST /api/v1/public/learning/checkpoints/{checkpoint_id}/submit`
Quy trình chấm điểm và xác thực câu hỏi kiểm tra tuân thủ **Zero-Leakage Invariant**. Hệ thống hỗ trợ bài đánh giá đa câu hỏi (**Multi-Question Assessment**) và thực thi theo cơ chế 2-Phase Verification.

- **Headers**:
  - `X-Session-ID` (required, string): Định danh phiên người học.
  - `Idempotency-Key` (required, string): Khóa chống nộp trùng lặp (UUID v4).
- **Cache**: `Cache-Control: no-store, no-cache, must-revalidate` (Bắt buộc không lưu cache cho giao dịch chấm điểm).
- **Quy trình Xác thực 2 Pha (2-Phase Verification)**:
  - **Phase 1: Grade & Sign Event**:
    - Client gửi danh sách lựa chọn của người học thông qua bảng ánh xạ đa câu hỏi `selected_options: dict[str, str]`.
    - Backend so khớp từng `question_id` với đáp án lưu trong CSDL máy chủ (tính `correct_count` / `total_questions`).
    - Nếu đạt điểm vượt qua (`score >= passing_threshold`, ví dụ >= 70%): Backend tạo bản ghi trong `learning_verified_events` và cấp `verified_event_id` kèm chữ ký số HMAC/SHA256 có thời hạn (TTL: 15 phút).
    - Phản hồi **KHÔNG BAO GIỜ** tiết lộ `correct_answer` hoặc đáp án đúng nếu câu hỏi làm sai (Zero-Leakage), chỉ cung cấp gợi ý tư duy Socratic (`socratic_hint`).
  - **Phase 2: Commit Progress Receipt**:
    - Client gửi `verified_event_id` lên endpoint xác nhận cam kết tiến độ (`POST /learning/progress/receipts/commit`).

- **Đặc tả Mô Hình Pydantic v2 (Strict Request & Response Schema)**:
  ```python
  class CheckpointSubmitRequest(BaseModel):
      """Payload nộp bài kiểm tra Checkpoint đồng bộ đa câu hỏi."""
      session_id: str = Field(..., description="Định danh session học viên (UUID v4 hoặc sess_...)")
      selected_options: dict[str, str] = Field(
          ...,
          description="Bảng ánh xạ {question_id: selected_option_id}. Hỗ trợ cả 1 câu lẫn bài tập đa câu hỏi trắc nghiệm."
      )
      time_spent_seconds: int = Field(default=0, ge=0, description="Thời gian làm bài tính bằng giây")
      idempotency_key: str = Field(..., min_length=16, max_length=128, description="Khóa chống nộp trùng lặp")

  class QuestionRubricFeedback(BaseModel):
      """Phản hồi sư phạm từng câu hỏi tuân thủ Zero-Leakage Invariant."""
      question_id: str
      is_correct: bool
      explanation: str | None = None  # Luôn hiển thị khi is_correct == True
      socratic_hint: str | None = None # Chỉ hiển thị khi is_correct == False để gợi ý tư duy

  class CheckpointSubmitResponse(BaseModel):
      """Kết quả chấm điểm và cấp chữ ký số xác thực bài học."""
      checkpoint_id: str
      passed: bool
      score: float = Field(..., ge=0.0, le=100.0, description="Điểm số phần trăm (0-100)")
      total_questions: int
      correct_count: int
      verified_event_id: str | None = None  # None nếu passed == False
      signature: str | None = None          # HMAC-SHA256 signature của verified_event_id
      expires_at: str | None = None         # Thời hạn 15 phút của verified event
      rubric_feedback: list[QuestionRubricFeedback]
  ```

- **Request Body JSON Example (Multi-Question Submission)**:
  ```json
  {
    "session_id": "sess_student_01",
    "selected_options": {
      "q1": "opt_b",
      "q2": "opt_c"
    },
    "time_spent_seconds": 180,
    "idempotency_key": "idemp_chk_sub_8921"
  }
  ```

- **Response Body Schema (Khi người học làm ĐẠT - HTTP 200 OK)**:
  ```json
  {
    "checkpoint_id": "chk_fsa_01_01",
    "passed": true,
    "score": 100,
    "total_questions": 2,
    "correct_count": 2,
    "verified_event_id": "vevent_89a01f_signed",
    "signature": "hmac_sha256:4d8a1f...90ef",
    "expires_at": "2026-10-10T11:37:00Z",
    "rubric_feedback": [
      {
        "question_id": "q1",
        "is_correct": true,
        "explanation": "Chính xác. Tài sản đại diện cho nguồn lực do doanh nghiệp kiểm soát và kỳ vọng mang lại lợi ích kinh tế trong tương lai."
      },
      {
        "question_id": "q2",
        "is_correct": true,
        "explanation": "Chính xác. Chi phí khấu hao là chi phí phi tiền mặt, cần được cộng ngược lại vào Lợi nhuận sau thuế khi lập Báo cáo lưu chuyển tiền tệ gián tiếp."
      }
    ]
  }
  ```

- **Response Body Schema (Khi người học làm CHƯA ĐẠT - Zero-Leakage Guaranteed)**:
  ```json
  {
    "checkpoint_id": "chk_fsa_01_01",
    "passed": false,
    "score": 50,
    "total_questions": 2,
    "correct_count": 1,
    "verified_event_id": null,
    "signature": null,
    "rubric_feedback": [
      {
        "question_id": "q1",
        "is_correct": true,
        "explanation": "Chính xác. Khái niệm cơ bản về tài sản đã được nắm vững."
      },
      {
        "question_id": "q2",
        "is_correct": false,
        "explanation": "Chưa chính xác. Hãy xem xét lại sự khác biệt giữa dòng tiền thực tế và chi phí tính dồn tích theo chuẩn mực kế toán.",
        "socratic_hint": "Khấu hao có thực sự làm phát sinh một dòng tiền chảy ra khỏi tài khoản ngân hàng của doanh nghiệp trong kỳ không?"
      }
    ]
  }
  ```

---

### 2.4. Nhóm API Ghi chú & Đánh dấu Tài liệu (Annotations, Bookmarks & Video Notes)

#### 2.4.1. Ebook Annotations & Bookmarks
- **`GET /api/v1/public/learning/books/{book_id}/annotations`**:
  - Trả về danh sách toàn bộ ghi chú và vùng bôi đen của người học trong cuốn sách:
  ```json
  {
    "book_id": "book_benjamin_graham_intelligent_investor",
    "annotations": [
      {
        "annotation_id": "anno_90123",
        "page_number": 45,
        "selected_text": "Biên an toàn là khoản chênh lệch giữa giá trị nội tại và thị giá.",
        "rects": [
          { "x": 120.5, "y": 340.2, "width": 450.0, "height": 18.5 }
        ],
        "color": "#FFE066",
        "comment": "Nguyên lý mấu chốt của Graham cần áp dụng cho định giá HPG",
        "created_at": "2026-10-09T14:20:00Z"
      }
    ]
  }
  ```

- **`POST /api/v1/public/learning/books/{book_id}/annotations`**:
  - Tạo mới highlight kèm tọa độ canvas vector.
  - Body: `{ page_number, selected_text, rects, color, comment }`.
  - Response: HTTP 201 Created với đối tượng annotation hoàn chỉnh.

- **`DELETE /api/v1/public/learning/books/{book_id}/annotations/{annotation_id}`**:
  - Xóa ghi chú highlight. Response: HTTP 204 No Content.

- **`GET / POST / DELETE /api/v1/public/learning/books/{book_id}/bookmarks`**:
  - Quản lý các trang đánh dấu của sách: `{ bookmark_id, page_number, title, created_at }`.

#### 2.4.2. Video Timestamped Notes
- **`GET /api/v1/public/learning/videos/{video_id}/notes`**:
  - Lấy danh sách ghi chú theo mốc thời gian của video cho session hiện tại.
- **`POST /api/v1/public/learning/videos/{video_id}/notes`**:
  - Body:
  ```json
  {
    "timestamp_seconds": 245.5,
    "content": "Thầy nhấn mạnh đoạn này: Tồn kho chỉ có giá trị khi chu kỳ luân chuyển ngắn và giá thép không sụt giảm bất ngờ."
  }
  ```
  - Response (HTTP 201 Created):
  ```json
  {
    "note_id": "vnote_4412",
    "video_id": "vid_yt_balance_sheet_basics",
    "timestamp_seconds": 245.5,
    "content": "Thầy nhấn mạnh đoạn này: Tồn kho chỉ có giá trị khi chu kỳ luân chuyển ngắn và giá thép không sụt giảm bất ngờ.",
    "created_at": "2026-10-10T11:25:00Z"
  }
  ```
- **`DELETE /api/v1/public/learning/videos/{video_id}/notes/{note_id}`**:
  - Xóa ghi chú video. Response: HTTP 204 No Content.

---

### 2.5. Đặc tả Giao thức Streaming AI Tutor qua Server-Sent Events (SSE)

#### 2.5.1. Endpoint Specification
- **URL**: `POST /api/v1/public/ai-tutor/conversations/{conversation_id}/messages/stream`
- **Headers**:
  - `Accept: text/event-stream`
  - `Content-Type: application/json`
  - `X-Session-ID: <session_id>`
- **Response Headers**:
  - `Content-Type: text/event-stream; charset=utf-8`
  - `Cache-Control: no-cache, no-transform`
  - `Connection: keep-alive`
  - `X-Accel-Buffering: no` (Vô hiệu hóa bộ đệm Nginx/Proxy để stream mượt mà)

#### 2.5.2. Request Payload Schema
```json
{
  "content": "Tại sao dòng tiền FCF của Hòa Phát lại âm dù lợi nhuận sau thuế đạt hơn 3.000 tỷ?",
  "surface": "learn",
  "mode": "socratic",
  "context_grounding": {
    "resource_id": "bctc_case_hpg_capex_2024",
    "resource_kind": "bctc_case",
    "document_context": null,
    "video_context": null,
    "bctc_context": {
      "ticker": "HPG",
      "period": "2024-Q3",
      "focused_line_item": "fcf",
      "focused_value": -5500,
      "reference_items": {
        "operating_cash_flow": 12500,
        "capex_purchase_assets": -18000,
        "net_profit_after_tax": 3020
      }
    },
    "checkpoint_context": null
  },
  "idempotency_key": "idemp_msg_stream_99182"
}
```

#### 2.5.3. Chi tiết Định dạng Dữ liệu SSE Events (Event Stream Spec)
Hệ thống phát ra 5 loại sự kiện có cấu trúc chuẩn hóa:

1. **`event: token`**  
   Phát từng mảnh văn bản (chunk) sinh ra từ LLM theo thời gian thực.
   ```text
   event: token
   id: 1
   data: {"chunk": "Chào anh, "}

   event: token
   id: 2
   data: {"chunk": "đây là một quan sát rất sắc bén. "}

   event: token
   id: 3
   data: {"chunk": "Lợi nhuận kế toán và Dòng tiền tự do (FCF) phản ánh hai góc nhìn hoàn toàn khác nhau về sức khỏe doanh nghiệp."}
   ```

2. **`event: citation`**  
   Phát các trích dẫn tài liệu được chứng thực nhằm neo nguồn tin cậy (Grounding Truth).
   ```text
   event: citation
   id: 4
   data: {"source_type": "bctc", "source_id": "HPG:2024-Q3", "label": "Báo cáo Lưu chuyển Tiền tệ HPG Q3/2024 - Dòng tiền Đầu tư Capex", "snippet": "Chi mua sắm, xây dựng TSCĐ: 18.000 tỷ VND"}
   ```

3. **`event: socratic_scaffold`**  
   Phát câu hỏi gợi mở tiếp theo của gia sư Socratic nhằm thúc đẩy người học tự suy luận.
   ```text
   event: socratic_scaffold
   id: 5
   data: {"scaffold_level": 2, "prompt": "Khi một doanh nghiệp chi ra 18.000 tỷ đồng tiền mặt để xây dựng nhà máy Dung Quất 2 trong kỳ, số tiền này được trừ ngay vào dòng tiền đầu tư nhưng chỉ được trích khấu hao dần vào chi phí P&L trong nhiều năm tới. Anh nghĩ điều này giải thích thế nào cho sự chênh lệch trên?"}
   ```

4. **`event: error`**  
   Phát khi có lỗi xảy ra trong quá trình inference hoặc rào chắn an toàn bị kích hoạt.
   ```text
   event: error
   id: 6
   data: {"code": "PROVIDER_TIMEOUT", "message": "Quá thời gian phản hồi từ mô hình. Đang chuyển sang dự phòng cục bộ."}
   ```

5. **`event: done`**  
   Phát khi chu kỳ stream kết thúc thành công, gửi metadata tổng kết.
   ```text
   event: done
   id: 7
   data: {"message_id": "msg_f901ab2", "finish_reason": "stop", "total_tokens": 284, "latency_ms": 1420}
   ```

#### 2.5.4. Vòng Đời Kết Nối, Heartbeat & Phục Hồi Lỗi (Connection Lifecycle & Resilience)
- **Heartbeat Keep-Alive**: Cứ mỗi **15 giây**, nếu không có token mới phát sinh, server chủ động gửi một comment SSE ping:
  ```text
  : ping - 1728559320
  ```
  giúp duy trì kết nối qua các proxy, Cloudflare và bộ cân bằng tải không bị timeout.
- **Client Disconnect Handling**: Server theo dõi tín hiệu hủy bỏ qua `request.is_disconnected()`. Khi người học đóng tab hoặc bấm Stop, coroutine streaming tại backend lập tức ngắt pipeline gọi LLM, giải phóng tài nguyên CPU/Memory.
- **Reconnection with Exponential Backoff**: Nếu mất kết nối mạng đột ngột:
  1. Client hook `useSocraticStream` tự động kích hoạt thử lại với backoff: Lần 1 (1000ms) -> Lần 2 (2000ms) -> Lần 3 (4000ms) -> Tối đa 10000ms.
  2. Gửi kèm header `Last-Event-ID: <id>` để server nhận diện trạng thái tiếp tục hoặc khôi phục stream.

---

## 3. CẤU TRÚC THÀNH PHẦN GIAO DIỆN FRONTEND & LAYOUT CHIA ĐÔI

### 3.1. Kiến trúc Master Layout: `<LearnHubDualPaneLayout />` & `<SocraticStreamProvider />`

Learn Hub v2.0 loại bỏ hoàn toàn các tab con phân mảnh để áp dụng **Dual-Pane Split Layout**:
- **Tỉ lệ phân chia mặc định**: Left Pane 60% (Nội dung học liệu chính) và Right Pane 40% (Trợ lý Socratic & Ghi chú đồng bộ).
- **Khả năng co giãn (Resizable Splitter)**: Cho phép kéo thanh chia giữa từ 40/60 đến 75/25, lưu cấu hình vào `localStorage` có debounce.
- **Tính đáp ứng di động (Responsive Mobile Fallback)**: Màn hình `< 1024px` tự động chuyển sang bố cục toàn màn hình Left Pane, Right Pane thu gọn thành Floating Action Button (FAB) kích hoạt Bottom Sheet / Drawer.
- **Lớp Bọc Ngữ Cảnh Dòng Chảy Socratic Cấp Cao (`<SocraticStreamProvider />`)**:
  - **Vấn đề trên thiết bị di động (< 1024px)**: Khi người học thu nhỏ màn hình hoặc truy cập bằng smartphone, Right Pane được hiển thị bên trong Drawer / BottomSheet có thể đóng mở. Nếu trạng thái streaming SSE (`ReadableStreamDefaultReader`, `AbortController`) nằm bên trong Drawer, việc đóng Drawer để xem tài liệu/video sẽ lập tức unmount component con, kích hoạt cleanup của React và gây **teardown / ngắt kết nối SSE stream dở dang**.
  - **Giải pháp Kiến trúc**: Toàn bộ `<LearnHubDualPaneLayout />` được bọc bởi `<SocraticStreamProvider />` tại cấp root của Learn Hub. Provider này duy trì persistent stream state, message accumulator buffer, và active abort signal xuyên suốt các thao tác đóng, mở, hoặc ẩn hiện Drawer. Khi người học mở lại Drawer trên mobile, giao diện tức thì hiển thị luồng token đang được nạp hoặc câu trả lời đã hoàn tất mà không bị đứt đoạn kết nối.

```
+---------------------------------------------------------------------------------------------------------+
| <SocraticStreamProvider sessionId={sessionId} activeContext={activeContext}>                           |
|   <LearnHubHeader />: [Trở về] [Tiêu đề Khóa học / Tài liệu] [Tiến độ: 25% ProgressBar] [Bookmarks Pill] |
|   +--------------------------------------------------------------------+---+----------------------------+
|   | LEFT PANE (60% Width, Min: 450px)                                  | S | RIGHT PANE (40% Width)     |
|   |                                                                    | P | (Desktop: Persistent Pane; |
|   | Phụ thuộc vào loại học liệu (Active Workspace):                    | L |  Mobile <1024px: Drawer)   |
|   | - Khi đọc Sách:   <EbookReaderWorkspace />                         | I | [Header: 🤖 Socratic]      |
|   | - Khi xem Video:  <VideoPlayerWorkspace />                         | T | [Tab: Chat | Notes]        |
|   | - Khi học Khóa:   <CoursePlayerWorkspace />                        | T | <AiTutorMessageList />     |
|   | - Khi làm BCTC:   <BctcCaseStudyWorkspace />                       | E | (Token streaming, Citations|
|   |                                                                    | R |  Persistent across Drawer) |
|   | [Thanh trạng thái Bottom Bar]:                                     |   | <AiTutorInputBox />        |
|   | - Điều hướng bài học trước/sau, phóng to, toàn màn hình            |   | [Stop Generation Button]   |
|   +--------------------------------------------------------------------+---+----------------------------+
| </SocraticStreamProvider>                                                                               |
+---------------------------------------------------------------------------------------------------------+
```

---

### 3.2. Cây Phân Cấp Thành Phần (Component Hierarchy Breakdown - Strict <200 Lines)

Mọi module thành phần đều tuân thủ nguyên tắc giới hạn dưới 200 dòng, phân chia rành mạch trách nhiệm:

#### 3.2.1. Phân hệ Khung Shell & Danh mục Catalog
1. **`LearnHubDualPaneLayout.jsx`** (~140 dòng): Khung chia đôi màn hình, điều khiển thanh splitter co giãn và layout responsive drawer cho mobile.
2. **`LearnHubHeader.jsx`** (~95 dòng): Thanh tiêu đề điều hướng, hiển thị tiến độ học tập toàn khóa và nút bookmark nhanh.
3. **`LearnCatalogGrid.jsx`** (~135 dòng): Grid lưới hiển thị danh mục học liệu đa định dạng, phân trang và trạng thái empty/loading.
4. **`LearnFilterBar.jsx`** (~120 dòng): Thanh lọc đa chiều: Loại học liệu (`kind`), chủ đề (`topic`), độ khó (`tier`) và ô tìm kiếm FTS.
5. **`LearnProgressSummaryCard.jsx`** (~85 dòng): Thẻ hiển thị tổng quan tiến độ học tập cá nhân, chuỗi ngày học và huy hiệu CFA đã đạt được.

#### 3.2.2. Phân hệ Ebook & PDF Reader Workspace
1. **`EbookReaderWorkspace.jsx`** (~160 dòng): Container chính điều phối trình đọc sách, kết nối state số trang hiện tại với context của AI Tutor.
2. **`PdfDocumentViewer.jsx`** (~185 dòng): Engine render PDF (PDF.js canvas), hỗ trợ cuộn mượt mà (smooth scrolling), phóng to thu nhỏ và tính năng ảo hóa trang (virtualizing pages).
3. **`PdfAnnotationLayer.jsx`** (~140 dòng): Lớp phủ SVG/Canvas trong suốt hiển thị các khối highlight màu sắc neo chính xác theo tọa độ bounding box của trang.
4. **`PdfBookmarkDrawer.jsx`** (~110 dòng): Thanh trượt bên hông liệt kê các mốc bookmark và mục lục sách (TOC), cho phép nhảy trang tức thì.
5. **`PdfTextSelectionMenu.jsx`** (~90 dòng): Menu ngữ cảnh nổi xuất hiện khi người học bôi đen văn bản: Nút **"Hỏi Socratic Tutor"**, **"Lưu Highlight"**, **"Tóm tắt"**.

#### 3.2.3. Phân hệ Video Bài Giảng & Đồng Bộ Ghi Chú
1. **`VideoPlayerWorkspace.jsx`** (~155 dòng): Container tích hợp trình phát video và danh sách bài học bên lề.
2. **`Html5VideoPlayer.jsx`** (~130 dòng): Trình phát video chuẩn HTML5 với custom controls và bộ lắng nghe `timeupdate` có throttling.
3. **`YouTubePlayerBridge.jsx`** (~170 dòng): Cầu nối tích hợp YouTube IFrame Player API (`enablejsapi=1`), đồng bộ thời gian phát thực tế hai chiều qua `postMessage`. Tích hợp cơ chế hàng đợi lệnh seek **`seekQueueRef`** giúp giải quyết dứt điểm lỗi tranh chấp thời gian (race condition) khi người dùng nhấp mốc thời gian trước khi player kích hoạt sự kiện `onReady`.
4. **`VideoTimestampNotes.jsx`** (~145 dòng): Danh sách ghi chú gắn mốc thời gian; click vào ghi chú tự động seek video đến đúng giây đó.
5. **`VideoChapterTimeline.jsx`** (~115 dòng): Thanh tiến độ phân đoạn trực quan các chương mục của video kèm tooltip tóm tắt khi rê chuột.
6. **`VideoTakeawaysList.jsx`** (~105 dòng): Danh sách các thẻ AI Key Takeaways rút ra từ phân đoạn video hiện tại.

#### 3.2.4. Phân hệ Khóa Học Phân Cấp & Checkpoint Quiz
1. **`CoursePlayerWorkspace.jsx`** (~165 dòng): Khung điều hướng khóa học đa bài học, tự động nạp loại workspace tương ứng theo từng bài học (video, reading, bctc).
2. **`CourseCurriculumSidebar.jsx`** (~175 dòng): Cây phân cấp Module -> Lesson có chỉ báo trạng thái hoàn thành, bài đang học và biểu tượng khóa.
3. **`LessonContentPane.jsx`** (~120 dòng): Khung render nội dung bài học lý thuyết dạng văn bản/công thức toán học có hỗ trợ MathJax/KaTeX.
4. **`CheckpointQuizModal.jsx`** (~180 dòng): Hộp thoại làm bài kiểm tra Checkpoint tuân thủ Zero-Leakage, kết nối với API chấm điểm 2-pha và hiển thị phản hồi Socratic.

#### 3.2.5. Phân hệ BCTC Case-Study Sandbox
1. **`BctcCaseStudyWorkspace.jsx`** (~170 dòng): Không gian làm việc tình huống BCTC, hiển thị kịch bản doanh nghiệp và các thử thách chỉ số.
2. **`BctcFinancialsViewer.jsx`** (~185 dòng): Bảng số liệu BCTC 3 báo cáo tương tác (Cân đối kế toán, P&L, Lưu chuyển tiền tệ), cho phép nhấp vào từng chỉ tiêu để neo ngữ cảnh sang AI Tutor.
3. **`BctcRatioChallenge.jsx`** (~150 dòng): Khung nhập công thức và tính toán chỉ số tài chính (FCF, ROE, D/E) từ dữ liệu gốc của doanh nghiệp.
4. **`BctcSubmissionFeedback.jsx`** (~110 dòng): Bảng phân tích kết quả thử thách BCTC, hiển thị tỷ lệ sai số và lời giải thích chuyên môn.

#### 3.2.6. Phân hệ Socratic AI Companion
1. **`SocraticAiCompanion.jsx`** (~165 dòng): Khung chính của trợ lý Socratic bên Right Pane, tích hợp quản lý luồng hội thoại và các gợi ý Quick Prompt.
2. **`AiTutorMessageList.jsx`** (~175 dòng): Danh sách tin nhắn hội thoại hỗ trợ render streaming markdown, trích dẫn tài liệu và tự động cuộn (auto-scroll).
3. **`AiTutorInputBox.jsx`** (~125 dòng): Ô nhập câu hỏi thông minh kèm nút gửi, nút dừng stream (Stop Generation) và chỉ báo trạng thái đang suy nghĩ.
4. **`SocraticContextBadge.jsx`** (~95 dòng): Huy hiệu ngữ cảnh trực quan ở đầu ô chat hiển thị vị trí người học đang neo (ví dụ: `📖 Trang 45: The Intelligent Investor` hoặc `📊 BCTC HPG Q3/2024: Capex`).
5. **`SocraticHintWidget.jsx`** (~115 dòng): Widget hiển thị các tầng gợi ý bậc thang (Hint Level 1 -> 2 -> 3) giúp người học tự khám phá đáp án mà không bị spoil.
6. **`SocraticStreamProvider.jsx`** (~145 dòng): Context Provider cấp cao nhất quản lý kết nối SSE streaming, bộ đệm tin nhắn và AbortController độc lập với vòng đời đóng/mở Drawer trên mobile.

---

### 3.3. State Machines & Custom Hooks Triệt tiêu Điểm nghẽn Hiệu năng

#### 3.3.1. `useMediaTimestampSync.js` & `YouTubePlayerBridge.jsx` (Khắc phục triệt để FE-PERF-01, FE-PERF-02 & Seek Race Condition)
- **Vấn đề cũ**: `CoursePlayerPage` lưu `currentTimeSeconds` trong root state và cập nhật 4–5 lần/giây qua `timeupdate`, làm giật lag toàn bộ cây component. YouTube embed không đồng bộ được thời gian (`currentTime = 0`). Đặc biệt, việc nhấp timestamp trước khi YouTube IFrame sẵn sàng gây race condition khiến lệnh seek bị mất.
- **Giải pháp thiết kế**:
  - Lưu thời gian chính xác trong `useRef` (`currentTimeRef.current`).
  - Sử dụng cơ chế **Throttled Subscription**: Chỉ bắn sự kiện cập nhật state tới các subscriber cần thiết sau mỗi **1000ms** (hoặc khi người dùng Pause / Seek).
  - Tích hợp YouTube Player Bridge lắng nghe sự kiện `YT.PlayerState.PLAYING` và chạy interval thăm dò `player.getCurrentTime()` đồng bộ mốc thời gian chuẩn xác.
  - **Cơ chế Hàng Đợi Lệnh Seek (`seekQueueRef`) trong `YouTubePlayerBridge.jsx`**:
    - **Nguyên nhân gốc rễ Race Condition**: Khi người học bấm mốc thời gian từ `VideoTimestampNotes` hoặc truyền `targetSeekSeconds` từ URL khi player IFrame đang nạp, lệnh `player.seekTo()` được gọi trước khi sự kiện `onReady` của YouTube Player API kích hoạt. Do đối tượng `player` chưa sẵn sàng, lệnh seek bị nuốt chửng (swallowed) hoặc văng lỗi, dẫn đến video phát lại từ mốc 0:00.
    - **Cơ chế Hàng Đợi An Toàn**: Sử dụng `const seekQueueRef = useRef(null)`. Nếu player đã sẵn sàng (`isPlayerReadyRef.current === true`), thực thi `player.seekTo(targetSeconds, true)`. Nếu player chưa sẵn sàng, đẩy mốc thời gian vào `seekQueueRef.current = targetSeconds`. Ngay khi sự kiện `onReady` kích hoạt, player kiểm tra `seekQueueRef.current` và tự động nhảy tới mốc thời gian đã xếp hàng, sau đó dọn sạch hàng đợi.

```javascript
// Minh họa cơ chế seekQueueRef trong YouTubePlayerBridge.jsx (<200 dòng)
export function YouTubePlayerBridge({ videoId, targetSeekSeconds, onTimeUpdate }) {
  const playerRef = useRef(null)
  const isReadyRef = useRef(false)
  const seekQueueRef = useRef(null)

  // 1. Lắng nghe yêu cầu seek từ bên ngoài
  useEffect(() => {
    if (targetSeekSeconds == null) return
    if (isReadyRef.current && playerRef.current) {
      playerRef.current.seekTo(targetSeekSeconds, true)
    } else {
      // Player chưa sẵn sàng: Đưa vào hàng đợi
      seekQueueRef.current = targetSeekSeconds
    }
  }, [targetSeekSeconds])

  // 2. Callback onReady từ YouTube IFrame API
  const handlePlayerReady = useCallback((event) => {
    isReadyRef.current = true
    playerRef.current = event.target
    // Xả hàng đợi seek ngay khi player sẵn sàng
    if (seekQueueRef.current !== null) {
      const queuedTarget = seekQueueRef.current
      seekQueueRef.current = null
      event.target.seekTo(queuedTarget, true)
    }
  }, [])

  // ... Throttled polling interval và player cleanup ...
}
```

```javascript
// Minh họa cấu trúc hook useMediaTimestampSync chuẩn <200 dòng
export function useMediaTimestampSync({ onTimeCommit, throttleMs = 1000 }) {
  const currentTimeRef = useRef(0)
  const [displaySeconds, setDisplaySeconds] = useState(0)
  const lastEmittedRef = useRef(0)

  const handleRawTimeUpdate = useCallback((seconds) => {
    currentTimeRef.current = seconds
    const now = Date.now()
    if (now - lastEmittedRef.current >= throttleMs) {
      lastEmittedRef.current = now
      setDisplaySeconds(Math.floor(seconds))
      onTimeCommit?.(seconds)
    }
  }, [throttleMs, onTimeCommit])

  return {
    getCurrentTime: () => currentTimeRef.current,
    displaySeconds,
    handleRawTimeUpdate,
  }
}
```

#### 3.3.2. `useBookReader.js` (Khắc phục triệt để FE-MEM-01 & FE-DATA-02)
- **Vấn đề cũ**: Tạo thẻ Canvas 960x1400 cho tất cả các trang ghi chú gây tốn 54MB GPU memory; gọi `localStorage.setItem` không bắt lỗi gây crash `QuotaExceededError`.
- **Giải pháp thiết kế**:
  - Chỉ mount canvas vẽ cho duy nhất **1 trang đang active**. Các trang còn lại được giải phóng bộ nhớ đồ họa bitmap.
  - Chuyển đổi dữ liệu vẽ từ bitmap PNG base64 sang **Vector SVG Strokes** (giảm 98% dung lượng dữ liệu lưu trữ).
  - Bọc toàn bộ các thao tác lưu trữ trong cơ chế an toàn: Thử lưu `IndexedDB` trước, nếu fallback về `localStorage` phải có khối `try ... catch (DOMException)` và cảnh báo giải phóng dung lượng khi đạt ngưỡng.

#### 3.3.3. `useSocraticStream.js` & `<SocraticStreamProvider />` (Triển khai Chuẩn Streaming SSE & Mobile Drawer Isolation)
- Quản lý vòng đời kết nối với endpoint `/api/v1/public/ai-tutor/.../messages/stream`.
- **Phối hợp Ngữ Cảnh Root Provider**: Hook `useSocraticStream` kết nối trực tiếp với `<SocraticStreamProvider />`. Việc quản lý `ReadableStreamDefaultReader` và giải mã UTF-8 SSE chunks diễn ra ở cấp Root Provider, cho phép:
  1. Giữ vững kết nối SSE ngầm khi AI Tutor Drawer bị đóng hoặc mở trên giao diện di động (`< 1024px`), không bị abort kết nối khi unmount drawer component.
  2. Quản lý tập trung đối tượng `AbortController` giúp nút **"Dừng phản hồi" (Stop Generation)** hoạt động tức thì từ bất kỳ vị trí giao diện nào.
  3. Cập nhật state tin nhắn dạng delta appending mượt mà 60fps qua `requestAnimationFrame`, loại bỏ 100% layout shift.

---

## 4. LỘ TRÌNH TRIỂN KHAI PHÂN ĐOẠN 5 BƯỚC (5-PHASE TRACER-BULLET ROADMAP)

Lộ trình áp dụng phương pháp luận **First Principles & Tracer Bullet**: Mỗi phase là một lát cắt hoàn chỉnh chạy được từ đầu đến cuối, đi kèm các cổng kiểm duyệt chất lượng (Quality Gates) và lệnh kiểm thử tự động xác minh trước khi bước sang giai đoạn tiếp theo. Tuyệt đối duy trì **100% tương thích ngược** với các API và dữ liệu hiện hữu.

```
+------------------------------------------------------------------------------------------------+
| Phase 0: Quick Wins, Hardening & Bug Remediation (Sửa triệt để các lỗi nghiêm trọng đã audit)  |
+------------------------------------------------------------------------------------------------+
                                                │
                                                ▼
+------------------------------------------------------------------------------------------------+
| Phase 1: Tracer Bullet #1 - Multi-Format DDL, Pydantic Schemas & Catalog v2 API                |
+------------------------------------------------------------------------------------------------+
                                                │
                                                ▼
+------------------------------------------------------------------------------------------------+
| Phase 2: Tracer Bullet #2 - Dual-Pane Master Layout, Ebook Reader & Video Player Workspaces   |
+------------------------------------------------------------------------------------------------+
                                                │
                                                ▼
+------------------------------------------------------------------------------------------------+
| Phase 3: Tracer Bullet #3 - BCTC Case-Study Sandbox & Stock Symbol Cross-Linking              |
+------------------------------------------------------------------------------------------------+
                                                │
                                                ▼
+------------------------------------------------------------------------------------------------+
| Phase 4: Tracer Bullet #4 - SSE Streaming AI Tutor with Multi-Modal Context Grounding         |
+------------------------------------------------------------------------------------------------+
                                                │
                                                ▼
+------------------------------------------------------------------------------------------------+
| Phase 5: Production Hardening, CFA Ecosystem Alignment & Legacy Deprecation                    |
+------------------------------------------------------------------------------------------------+
```

---

### 4.1. Phase 0: Quick Wins, Hardening & Bug Remediation
**Mục tiêu**: Khắc phục ngay lập tức các lỗ hổng nghiêm trọng đã được kiểm toán phát hiện trong M1 nhằm tạo nền tảng vững chắc trước khi mở rộng tính năng mới.

1. **Tự động hóa Phục hồi CSDL Bị Hỏng & Tái nạp Dữ liệu Sạch (Automated DB Recovery & Clean Re-seeding)**:
   - **Vấn đề phát hiện thực tế**: File CSDL SQLite dùng chung `data/db/northstar.db` bị lỗi hỏng phân vùng đĩa vật lý (`sqlite3.DatabaseError: database disk image is malformed (11)`) do các phiên chạy test/runtime trước bị ngắt đột ngột hoặc tranh chấp ghi khi nhiều luồng test truy cập đồng thời (hệ quả trực tiếp của các lỗi rò rỉ kết nối BE-04, bão query BE-06 và khóa ghi BE-09). Khi chạy trực tiếp các test suite như `tests/test_learning.py` trên file DB này, toàn bộ test đều crash.
   - **Quy trình phục hồi tự động 4 bước (Automated 4-Step Recovery Procedure)**:
     1. *Kiểm tra tính toàn vẹn vật lý (Integrity Check)*: Chạy `sqlite3 data/db/northstar.db "PRAGMA integrity_check;"`. Nếu kết quả trả về khác `ok` (hoặc ném lỗi `malformed`), tự động kích hoạt pipeline phục hồi.
     2. *Cách ly & Sao lưu an toàn (Safe Quarantine & Backup)*: Di chuyển file hỏng ra vùng cách ly để phục vụ forensics: `mv data/db/northstar.db data/db/northstar.db.corrupt.$(date +%Y%m%d%H%M%S)`.
     3. *Tái tạo CSDL sạch (Clean DDL Schema Re-generation)*: Kích hoạt pipeline migration tạo mới toàn bộ 19 schema bảng chuẩn: `python3 -m src.risk_dashboard.platform.database.migrate` (Đảm bảo cấu hình WAL mode: `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`).
     4. *Tái nạp hạt giống dữ liệu học liệu (Automated Re-seeding)*: Tái nạp danh mục khóa học, sách, video mặc định qua `SqliteLearningCatalog` và nạp snapshot 10 mã BCTC tiêu biểu:
        ```bash
        python3 -c "from src.risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog; SqliteLearningCatalog().list_courses()"
        python3 scripts/sync_bctc_to_db.py --limit 10
        ```
   - **Quy chuẩn Cách ly Cơ sở dữ liệu Kiểm thử (Test Database Isolation Hygiene)**:
     - Cập nhật fixture kiểm thử trong `conftest.py` và `tests/test_learning.py`: Tuyệt đối không trỏ mặc định vào `data/db/northstar.db` khi chạy automated tests. Luôn inject biến môi trường `RISK_DASHBOARD_DB_PATH` trỏ tới file DB tạm biệt lập trong thư mục `tmp_path`, triệt tiêu hoàn toàn rủi ro write lock contention giữa các test runners.
2. **Khắc phục Frontend Test Script (FE-TEST-01)**:
   - Thêm script chuẩn `"test": "node ./scripts/test-runner.mjs"` vào `frontend/package.json`.
3. **Khắc phục Blocking Network I/O trong Async Coroutine (BE-01)**:
   - Sửa `learning_specialist.py:146` và `video_agent_service.py:121`: Chuyển lời gọi blocking `urllib.request.urlopen` sang `asyncio.to_thread` hoặc sử dụng `httpx.AsyncClient`.
4. **Khắc phục Query Storm khi khởi tạo Catalog (BE-06)**:
   - Áp dụng Singleton Pattern và cờ `_is_seeded` mức process trong `SqliteLearningCatalog` (`catalog_reader.py`), loại bỏ 50+ câu lệnh SQL dư thừa trên mỗi request.
5. **Bổ sung Composite Indexes cho SQLite (BE-07 & BE-08)**:
   - Thêm index sắp xếp: `CREATE INDEX IF NOT EXISTS idx_learning_videos_fetched ON learning_videos(is_active, fetched_at DESC)`.
   - Thêm index tương tự cho `learning_books`, `learning_courses` và `learning_lesson_progress(user_id, path_id)`.
6. **Đóng kết nối SQLite rò rỉ (BE-04)**:
   - Chuẩn hóa các repository trong `financials_product` và `news_intelligence` luôn sử dụng context manager `with open_app_state_db()` để đảm bảo kết nối luôn được đóng trong `finally`.
7. **Bóc tách đáp án đề thi CFA khỏi Client Bundle (FE-DATA-01)**:
   - Loại bỏ thuộc tính `correctOptionId` và `explanation` khỏi file client `mockExamData.js`. Chuyển dữ liệu đáp án vào backend database và xây dựng endpoint chấm điểm server-side.

- **Files sửa đổi / tạo mới**:
  - `scripts/recover_database.sh` (Mới: Script tự động kiểm tra integrity, backup và tái nạp dữ liệu sạch)
  - `frontend/package.json`
  - `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py`
  - `src/risk_dashboard/modules/learning/application/video_agent_service.py`
  - `src/risk_dashboard/modules/learning/infrastructure/catalog_reader.py`
  - `src/risk_dashboard/platform/database/schema/baseline.sql`
  - `src/risk_dashboard/platform/database/migrate.py`
  - `src/risk_dashboard/modules/financials_product/infrastructure/sqlite_memo_repository.py`
  - `frontend/src/features/learn-hub/content/mockExamData.js`

- **Automated Verification Commands & Quality Gate**:
  ```bash
  # 0. Kiểm tra toàn vẹn vật lý của CSDL SQLite - Bắt buộc trả về "ok"
  sqlite3 data/db/northstar.db "PRAGMA integrity_check;"
  
  # 1. Chạy bộ kiểm thử backend đảm bảo không gãy regression (cách ly DB qua tmp_path)
  .venv/bin/pytest tests/test_learning.py tests/test_video_learning_agent.py tests/test_ai_tutor_learning.py

  # 2. Chạy bộ kiểm thử frontend sau khi fix script
  cd frontend && npm test
  ```
  *Tiêu chí PASS*: CSDL sạch hoàn toàn (`PRAGMA integrity_check` = `ok`). 100% tests backend (20/20) và frontend (20/20) pass. Không còn blocking I/O trong coroutine.

---

### 4.2. Phase 1: Tracer Bullet #1 - Multi-Format DDL, Pydantic Schemas & Catalog v2
**Mục tiêu**: Xây dựng mô hình dữ liệu đa định dạng hoàn chỉnh tại tầng lưu trữ và xuất bản API Catalog v2 có type contract chặt chẽ.

1. **Thiết lập DDL Relational**:
   - Viết migration tạo các bảng mới: `learning_courses_v2`, `learning_course_modules`, `learning_course_lessons`, `learning_user_course_progress`, `learning_book_annotations`, `learning_book_bookmarks`, `learning_video_chapters`, `learning_video_notes`, `learning_bctc_cases`.
2. **Pydantic v2 Schemas (`src/risk_dashboard/modules/learning/schemas/domain_v2.py`)**:
   - Định nghĩa đầy đủ các model: `LearningCatalogResponse`, `CourseHierarchyResponse`, `LessonDetailResponse`, `CheckpointSubmitRequest` (hỗ trợ `selected_options: dict[str, str]`), `CheckpointSubmitResponse`, `QuestionRubricFeedback`, `BctcCaseStudyDetail`, `BookAnnotationCreate`, `VideoNoteCreate`.
3. **Endpoint Catalog v2 & Caching**:
   - Nâng cấp `GET /api/v1/public/learning/catalog` trả về response model có type contract, kết nối in-memory caching 10 phút.
4. **Mở rộng FTS5 Indexing (BE-12)**:
   - Mở rộng `LearningRetrievalIndex.rebuild_index()` để lập chỉ mục tìm kiếm cho cả 4 định dạng (Sách, Video chapters, Khóa học và BCTC cases).

- **Files sửa đổi / tạo mới**:
  - `src/risk_dashboard/platform/database/migrate.py`
  - `src/risk_dashboard/modules/learning/schemas/domain_v2.py` (Mới)
  - `src/risk_dashboard/modules/learning/infrastructure/retrieval.py`
  - `src/risk_dashboard/modules/learning/api/public.py`
  - `tests/test_learning_v2_catalog.py` (Mới)

- **Automated Verification Commands & Quality Gate**:
  ```bash
  # Chạy kiểm thử migration DB và API Catalog v2
  .venv/bin/pytest tests/test_learning_v2_catalog.py tests/test_learning_agent_retrieval.py
  ```
  *Tiêu chí PASS*: Migration chạy thành công, FTS5 tìm kiếm được sách/video/BCTC, endpoint `/catalog` trả về đúng Pydantic schema v2 với HTTP Cache-Control header.

---

### 4.3. Phase 2: Tracer Bullet #2 - Dual-Pane Layout, Ebook Reader & Video Player Workspaces
**Mục tiêu**: Xây dựng kiến trúc giao diện Dual-Pane thống nhất và nâng cấp trải nghiệm người học cho Ebook/PDF và Video bài giảng.

1. **Triển khai Master Layout, Stream Provider & Hooks**:
   - Tạo `<SocraticStreamProvider />` context wrapper cấp cao duy trì persistent SSE connection trên mobile drawer.
   - Tạo `<LearnHubDualPaneLayout />` với thanh splitter co giãn 60/40.
   - Tạo custom hook `useMediaTimestampSync.js`, `useBookReader.js` và `useSocraticStream.js`.
2. **Nâng cấp Ebook/PDF Reader Workspace**:
   - Tích hợp `PdfDocumentViewer.jsx` render theo từng trang vector sắc nét.
   - Tích hợp `PdfAnnotationLayer.jsx` và `PdfBookmarkDrawer.jsx` kết nối với API lưu trữ server-side.
   - Thêm thanh menu nổi bôi đen chữ (`PdfTextSelectionMenu.jsx`) hỗ trợ đẩy văn bản sang AI Tutor.
3. **Nâng cấp Video Player Workspace**:
   - Hoàn thiện `YouTubePlayerBridge.jsx` hỗ trợ YouTube IFrame Player API hai chiều kèm hàng đợi `seekQueueRef`, giải quyết dứt điểm lỗi currentTime = 0 và seek race conditions trước `onReady`.
   - Triển khai `VideoTimestampNotes.jsx` cho phép tạo và nhảy mốc ghi chú trực tiếp trên video.

- **Files sửa đổi / tạo mới**:
  - `frontend/src/features/learn-hub/layouts/LearnHubDualPaneLayout.jsx` (Mới)
  - `frontend/src/features/learn-hub/context/SocraticStreamProvider.jsx` (Mới)
  - `frontend/src/features/learn-hub/hooks/useMediaTimestampSync.js` (Mới)
  - `frontend/src/features/learn-hub/hooks/useBookReader.js` (Mới)
  - `frontend/src/features/learn-hub/pages/BookReaderWorkspace.jsx`
  - `frontend/src/features/learn-hub/pages/PdfDocumentViewer.jsx` (Mới)
  - `frontend/src/features/learn-hub/pages/VideoPlayerWorkspace.jsx` (Mới)
  - `frontend/src/features/learn-hub/pages/YouTubePlayerBridge.jsx` (Mới)
  - `frontend/src/features/learn-hub/pages/VideoTimestampNotes.jsx` (Mới)
  - `frontend/src/__tests__/dualPaneWorkspaces.test.js` (Mới)

- **Automated Verification Commands & Quality Gate**:
  ```bash
  cd frontend && npm test
  ```
  *Tiêu chí PASS*: Các component workspace render chuẩn xác, không xảy ra re-render storm khi phát video (kiểm chứng qua hook test), dung lượng GPU được giải phóng khi chuyển trang sách.

---

### 4.4. Phase 3: Tracer Bullet #3 - BCTC Case-Study Sandbox & Stock Symbol Cross-Linking
**Mục tiêu**: Đóng gói các tình huống BCTC thực tế thành bài học trong Learn Hub, kết nối 120+ file cache tài chính và liên kết chéo mã cổ phiếu.

1. **Backend BCTC Case Engine**:
   - Triển khai endpoint `GET /api/v1/public/learning/bctc-cases/{id}` kết nối dữ liệu từ `data/financials/cache/` (FPT, VNM, HPG...).
   - Xây dựng service kiểm tra tính toán chỉ số tài chính (FCF, ROE, D/E) có sai số cho phép.
2. **Frontend BCTC Sandbox**:
   - Tạo `BctcCaseStudyWorkspace.jsx` tích hợp bảng cân đối kế toán, P&L, lưu chuyển tiền tệ thu nhỏ.
   - Tích hợp `BctcRatioChallenge.jsx` cho phép người học nhập kết quả tính toán và nhận phản hồi trực tiếp.
3. **Liên kết Chéo Mã Cổ Phiếu (Stock Cross-Linking)**:
   - Hiển thị pill badge mã cổ phiếu VN30 trên các thẻ bài học. Nhấp vào pill mở modal tra cứu nhanh số liệu BCTC mới nhất.

- **Files sửa đổi / tạo mới**:
  - `src/risk_dashboard/modules/learning/application/bctc_case_service.py` (Mới)
  - `src/risk_dashboard/modules/learning/api/public.py`
  - `frontend/src/features/learn-hub/pages/BctcCaseStudyWorkspace.jsx` (Mới)
  - `frontend/src/features/learn-hub/components/BctcFinancialsViewer.jsx` (Mới)
  - `frontend/src/features/learn-hub/components/BctcRatioChallenge.jsx` (Mới)
  - `tests/test_bctc_case_learning.py` (Mới)

- **Automated Verification Commands & Quality Gate**:
  ```bash
  .venv/bin/pytest tests/test_bctc_case_learning.py
  cd frontend && npm test
  ```
  *Tiêu chí PASS*: Dữ liệu tài chính của HPG/VNM/FPT nạp chính xác vào case study, thử thách tính FCF chấm điểm tự động thành công.

---

### 4.5. Phase 4: Tracer Bullet #4 - SSE Streaming AI Tutor with Multi-Modal Context Grounding
**Mục tiêu**: Hiện thực hóa trải nghiệm gia sư Socratic thời gian thực qua Server-Sent Events, hỗ trợ neo ngữ cảnh linh hoạt từ sách, video và BCTC.

1. **Backend SSE Streaming Engine**:
   - Xây dựng route `POST /api/v1/public/ai-tutor/conversations/{id}/messages/stream` trả về `StreamingResponse(iter_sse_events(), media_type="text/event-stream")`.
   - Kết nối `TutorGraph` với engine phát sự kiện tuần tự (`token`, `citation`, `socratic_scaffold`, `done`).
   - Xây dựng Heartbeat ping 15s và xử lý ngắt kết nối client an toàn.
2. **Cơ chế Neo Ngữ Cảnh Đa Chiều (Multi-Modal Context Grounding)**:
   - Xử lý payload `TutorContextPayload`: Trích xuất đoạn text bôi đen từ PDF, mốc giây từ video, hoặc ô chỉ tiêu từ BCTC.
   - Thiết lập System Prompt Socratic nghiêm ngặt: Nhắc nhở nguyên lý, không bao giờ lộ đáp án câu hỏi kiểm tra (Zero-Leakage Guardrail).
3. **Frontend Streaming Client**:
   - Triển khai hook `useSocraticStream.js` và component `AiTutorMessageList.jsx`.
   - Bổ sung nút **"Dừng phản hồi" (AbortController)** và huy hiệu `SocraticContextBadge.jsx`.

- **Files sửa đổi / tạo mới**:
  - `src/risk_dashboard/modules/ai_tutor/api/public.py`
  - `src/risk_dashboard/modules/ai_tutor/application/tutor_graph.py`
  - `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py`
  - `frontend/src/features/learn-hub/hooks/useSocraticStream.js` (Mới)
  - `frontend/src/features/learn-hub/components/SocraticAiCompanion.jsx` (Mới)
  - `frontend/src/features/learn-hub/components/AiTutorMessageList.jsx` (Mới)
  - `tests/test_ai_tutor_sse_streaming.py` (Mới)

- **Automated Verification Commands & Quality Gate**:
  ```bash
  .venv/bin/pytest tests/test_ai_tutor_sse_streaming.py tests/test_ai_tutor_teaching_policy.py
  cd frontend && npm test
  ```
  *Tiêu chí PASS*: Client nhận trọn vẹn chuỗi sự kiện SSE token theo thời gian thực; khi hỏi xin đáp án trắc nghiệm, AI Tutor kiên quyết áp dụng phương pháp Socratic 3 cấp độ mà không tiết lộ đáp án.

---

### 4.6. Phase 5: Production Hardening, CFA Alignment & Legacy Deprecation
**Mục tiêu**: Tinh chỉnh toàn diện, kiểm thử tích hợp đầu cuối (E2E) và hoàn tất kế hoạch chuyển dịch loại bỏ mã nguồn cũ an toàn.

1. **Chuẩn hóa Danh mục Chủ đề Chuẩn CFA Level I**:
   - Ánh xạ toàn bộ 19 topics hiện có vào 4 danh mục lớn của chương trình CFA (FSA, Equity, Portfolio & Risk, Macro/Quant).
2. **Kiểm thử Tích hợp Đầu Cuối (E2E Integration Testing)**:
   - Viết kịch bản kiểm thử toàn diện luồng: Khám phá danh mục -> Mở bài giảng Video -> Tạo ghi chú mốc thời gian -> Hỏi AI Tutor theo ngữ cảnh -> Hoàn thành Checkpoint -> Nhận chứng từ tiến độ.
3. **Kế hoạch Deprecation An Toàn**:
   - Đánh dấu `@deprecated` cho các endpoint và component cũ.
   - Duy trì backward-compatibility chuyển hướng dữ liệu trong tối thiểu 2 chu kỳ phát hành trước khi dọn dẹp triệt để.

- **Automated Verification Commands & Final Quality Gate**:
  ```bash
  # 1. Chạy toàn bộ regression test suite Backend
  .venv/bin/pytest tests/test_learning*.py tests/test_ai_tutor*.py tests/test_video_learning_agent.py

  # 2. Chạy toàn bộ test suite Frontend
  cd frontend && npm test

  # 3. Kiểm tra định dạng và linter
  ruff check src/risk_dashboard/modules/learning src/risk_dashboard/modules/ai_tutor
  ```
  *Tiêu chí Hoàn thành Toàn diện*: 100% test cases pass, 0 lỗi linting, thời gian phản hồi API p95 < 200ms (với cached catalog), Time-To-First-Token của AI Tutor SSE < 1.5s.

---

## 5. PHỤ LỤC KỸ THUẬT (TECHNICAL APPENDICES)

### Phụ lục A: Bảng Mã Lỗi Tiêu Chuẩn (Standardized Error Codes)

| Mã Lỗi (Error Code) | HTTP Status | Ý Nghĩa Chuyên Môn | Hướng Xử Lý Khuyến Nghị |
|---|---|---|---|
| `RESOURCE_NOT_FOUND` | 404 Not Found | Không tìm thấy Sách, Video, Khóa học hoặc BCTC case tương ứng. | Kiểm tra lại `resource_id` hoặc làm mới danh mục. |
| `CHECKPOINT_EXPIRED` | 410 Gone | Phiên câu hỏi trắc nghiệm đã quá hạn thời gian làm bài (TTL: 15 phút). | Yêu cầu người học khởi tạo lại câu hỏi mới. |
| `SIGNATURE_VERIFICATION_FAILED` | 403 Forbidden | Chữ ký số HMAC của `verified_event_id` không khớp hoặc đã bị chỉnh sửa. | Từ chối ghi nhận tiến độ, ghi log bảo mật. |
| `IDEMPOTENCY_KEY_DUPLICATED` | 409 Conflict | Khóa idempotency đã được xử lý thành công trước đó. | Trả về kết quả chứng từ đã lưu mà không ghi nhận lần hai. |
| `STREAM_GENERATION_FAILED` | 502 Bad Gateway | Nhà cung cấp AI (Gemini Provider) gặp sự cố kết nối trong khi stream. | Client tự động chuyển sang cơ chế fallback hoặc thử lại. |
| `STORAGE_QUOTA_EXCEEDED` | 413 Payload Too Large | Dung lượng dữ liệu vượt ngưỡng cho phép. | Giải phóng các bản ghi cũ hoặc lưu vào bộ nhớ bền vững. |

---

### Phụ lục B: Bảng Ma Trận Ánh Xạ Độ Khó & Danh Mục Chủ Đề (Taxonomy & Difficulty Matrix)

| Danh mục Cấp 1 | Mã Chủ Đề (Topic Slug) | Nhãn Tiếng Việt | Nhãn Tiếng Anh | Phân Cấp Mặc Định | Ánh Xạ Học Phần CFA |
|---|---|---|---|---|---|
| **FSA & Corporate Finance** | `financial_statements` | Đọc hiểu 3 Báo Cáo Tài Chính | Financial Statements Analysis | Intermediate | CFA L1 Reading 19, 20 |
| | `cashflow_quality` | Chất lượng Dòng tiền & Lợi nhuận | Cash Flow Quality & Forensic | Intermediate | CFA L1 Reading 21 |
| | `financial_ratios` | Hệ thống Chỉ số Tài chính & DuPont | Financial Ratios & DuPont | Beginner | CFA L1 Reading 24 |
| | `corporate_governance`| Quản trị Công ty & Đạo đức | Corporate Governance | Beginner | CFA L1 Corporate Issuers |
| **Equity & Valuation** | `stocks` | Thị trường Cổ phiếu Cơ bản | Equity Market Overview | Beginner | CFA L1 Equity Investments |
| | `valuation_dcf` | Định giá Chiết khấu Dòng tiền | DCF Valuation Models | Advanced | CFA L1 Reading 35 |
| | `valuation_multiples`| Định giá Tương đối P/E, P/B, EV/EBITDA | Relative Valuation Multiples | Intermediate | CFA L1 Reading 36 |
| | `vietnam_market` | Quy chế Giao dịch HOSE / HNX | Vietnam Equity Market Specifics| Beginner | Thị trường Chứng khoán VN |
| **Portfolio & Risk** | `portfolio_theory` | Lý thuyết Danh mục Hiện đại (MPT) | Modern Portfolio Theory | Intermediate | CFA L1 Portfolio Management |
| | `asset_allocation` | Phân bổ Lớp Tài sản Đầu tư | Strategic Asset Allocation | Intermediate | CFA L1 Asset Allocation |
| | `risk_management` | Quản trị Rủi ro VaR & Drawdown | Risk Management: VaR & Drawdown| Advanced | CFA L1 Risk Architecture |
| | `behavioral_finance` | Tài chính Hành vi & Tâm lý | Behavioral Finance Biases | Beginner | CFA L1 Behavioral Finance |
| **Macro & Quantitative** | `macroeconomics` | Kinh tế Vĩ mô & Chu kỳ Kinh tế | Macroeconomics & Business Cycles| Beginner | CFA L1 Economics |
| | `bonds_fixed_income` | Thị trường Trái phiếu & Lãi suất | Fixed Income & Yield Curve | Intermediate | CFA L1 Fixed Income |
| | `derivatives` | Phái sinh Hợp đồng Tương lai VN30| Derivatives & Futures Markets | Advanced | CFA L1 Derivatives |
| | `quantitative_finance`| Mô phỏng Monte Carlo & Định lượng | Quantitative Methods & Backtesting| Advanced | CFA L1 Quantitative Methods|

---

### Phụ lục C: Ma Trận Truy Xuất Mã Nguồn Đối Ứng (Traceability Matrix)

| Yêu Cầu / Vấn Đề Audit | Hạng Mục Thiết Kế Trong Blueprint | File Mã Nguồn Dự Kiến Tác Động |
|---|---|---|
| **DB-CORRUPT-01** (`northstar.db` malformed disk) | Section 4.1: Automated 4-Step DB Recovery & Re-seeding Pipeline | `scripts/recover_database.sh` & `src/risk_dashboard/platform/database/migrate.py` |
| **FE-STREAM-01** (Mobile Drawer stream teardown) | Section 3.1 & 3.2.6: Top-Level `<SocraticStreamProvider />` Context Wrapper | `frontend/src/features/learn-hub/context/SocraticStreamProvider.jsx` |
| **FE-SEEK-01** (Seek race condition trước onReady) | Section 3.2.3 & 3.3.1: Cơ chế hàng đợi `seekQueueRef` trong `YouTubePlayerBridge` | `frontend/src/features/learn-hub/pages/YouTubePlayerBridge.jsx` |
| **API-CHECKPOINT-01** (Schema đa câu hỏi Checkpoint) | Section 2.3.2 & 4.2: Payload `selected_options: dict[str, str]` Pydantic v2 | `src/risk_dashboard/modules/learning/schemas/domain_v2.py` |
| **API-CACHE-01** (Trình duyệt cache sai tiến độ dở dang) | Section 2.1 & 2.2.2: `Cache-Control: private, no-cache, must-revalidate` | `src/risk_dashboard/modules/learning/api/public.py` |
| **FE-PERF-01** (Re-render cascade 4-5 fps) | Section 3.3.1: Hook `useMediaTimestampSync` (Throttled subscription) | `frontend/src/features/learn-hub/hooks/useMediaTimestampSync.js` |
| **FE-PERF-02** (YouTube embed currentTime = 0)| Section 3.2.3: Component `YouTubePlayerBridge.jsx` | `frontend/src/features/learn-hub/pages/YouTubePlayerBridge.jsx` |
| **FE-MEM-01** (Rò rỉ Canvas 960x1400) | Section 3.3.2: Hook `useBookReader.js` & Active-only canvas | `frontend/src/features/learn-hub/hooks/useBookReader.js` |
| **FE-DATA-01** (Lộ đáp án CFA ở Client) | Section 2.3.2 & 4.1: Server-side grading & Zero-Leakage | `src/risk_dashboard/modules/learning/api/public.py` |
| **FE-STATE-01** (Tiến độ chỉ lưu LocalStorage) | Section 2.3.1: `POST /learning/lessons/{id}/complete` server commit | `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx` |
| **BE-01** (Blocking urllib trong coroutine) | Section 4.1: Chuyển sang `asyncio.to_thread` / `httpx.AsyncClient` | `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py` |
| **BE-06** (Query storm khởi tạo Catalog) | Section 4.1: Singleton & Process-level seeding flag | `src/risk_dashboard/modules/learning/infrastructure/catalog_reader.py` |
| **BE-07 / BE-08** (Thiếu index SQLite) | Section 4.1: Composite indexes cho `fetched_at` và `(user_id, path_id)` | `src/risk_dashboard/platform/database/schema/baseline.sql` |
| **BE-10** (AI Tutor thiếu SSE streaming) | Section 2.5: Endpoint `POST /ai-tutor/.../messages/stream` | `src/risk_dashboard/modules/ai_tutor/api/public.py` |
| **BE-11 / BE-12** (FTS5 thiếu sách/video/BCTC) | Section 4.2: Lập chỉ mục FTS5 cho cả 4 dạng học liệu | `src/risk_dashboard/modules/learning/infrastructure/retrieval.py` |
| **Dual-Pane Split Layout (R3)** | Section 3.1 & 3.2: `<LearnHubDualPaneLayout />` Split 60/40 | `frontend/src/features/learn-hub/layouts/LearnHubDualPaneLayout.jsx` |
| **BCTC Case-Study Sandbox (R2/R3)** | Section 2.2.5 & 3.2.5: `BctcCaseStudyWorkspace.jsx` | `frontend/src/features/learn-hub/pages/BctcCaseStudyWorkspace.jsx` |

---
*Tài liệu Đặc tả Kỹ thuật & Blueprint Thực thi hoàn tất biên soạn. Sẵn sàng cho các giai đoạn lập trình và kiểm định độc lập.*
