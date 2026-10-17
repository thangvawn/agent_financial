# Báo Cáo Khảo Sát Kiến Trúc Domain & Đặc Tả Nâng Cấp Tab Learn Hub

**Người thực hiện**: `explorer_survey_domain` (Teamwork Explorer)  
**Ngày thực hiện**: 2026-10-10  
**Phạm vi**: Kiến trúc Domain, Khảo sát mã nguồn hiện hữu, Thiết kế lại phân hệ Learn Hub đa định dạng (Ebook/PDF, Video, Khóa học phân cấp, BCTC Case-study), Tích hợp AI Tutor Socratic, và Đặc tả Blueprint thực thi (R2 & R3).

---

## 1. Tóm Tắt Điều Hành (Executive Summary)

Tab Learn Hub hiện tại của Northstar Finance Lab sở hữu nền tảng sơ khởi bao gồm:
1. Thư viện học liệu cục bộ (`data/learning_assets/`), bảng catalog tài nguyên trong SQLite (`learning_courses`, `learning_videos`, `learning_books`, `learning_papers`).
2. Trợ lý AI phân tích phụ đề video (`VideoLearningAgentService`) có khả năng đối soát transcript theo mốc thời gian và chấm câu hỏi kiểm tra video.
3. Hệ thống Checkpoint Socratic 2 pha có cam kết tiến độ (`learning_checkpoints`, `learning_verified_events`, `learning_progress_receipts`) đã được kiểm thử chặt chẽ với nguyên tắc Zero-Leakage.
4. Cơ sở dữ liệu và công cụ BCTC phong phú (`financials_product`, `data/financials/cache/` với hơn 120 mã cổ phiếu như FPT, VNM, HPG), cùng các màn hình thực hành chỉ số (`RatioPracticeLab`, `RawDataChallenge`).

Tuy nhiên, hệ thống hiện tồn tại **4 khoảng cách kiến trúc nghiêm trọng (Architectural Gaps)**:
- **Giao diện rời rạc, thiếu trải nghiệm Dual-Pane thống nhất**: Trình đọc sách (`BookReaderWorkspace`) dùng `iframe` thô sơ không có theo dõi trang/ghi chú neo tọa độ; Trình xem video (`CoursePlayerPage`) và AI Tutor bị chia cắt thành các tab con (`overview`, `video-agent`, `checkpoint`, `tutor`, `notes`) thay vì giao diện chia đôi (Split-view/Dual-pane) cho phép học và tương tác cùng lúc.
- **Dữ liệu khóa học bị phẳng hóa (Flat Schema)**: Bảng `learning_courses` trong database chỉ lưu 1 bản ghi phẳng, không có cấu trúc phân cấp Module -> Lesson -> Checkpoint. Frontend phải tự tạo cấu trúc giả lập (`normalizeDbCourse`) hoặc dựa vào file tĩnh `demoCourses.js`, đồng thời tiến độ học khóa học bị lưu cục bộ trong `localStorage` thay vì đồng bộ lên máy chủ.
- **Phân hệ BCTC bị cô lập khỏi Learn Hub**: Công cụ phân tích và thực hành BCTC (`frontend/src/features/bctc`) hoạt động riêng rẽ, chưa được đóng gói thành các **BCTC Case-studies** có kịch bản học tập, liên kết chéo với giáo trình và mã cổ phiếu thực tế.
- **AI Tutor chưa hỗ trợ phản hồi Streaming và thiếu Neo ngữ cảnh linh hoạt (Context Grounding)**: Endpoint hội thoại hiện tại là HTTP POST đồng bộ, chưa có Server-Sent Events (SSE) để stream câu trả lời; AI Tutor mới chỉ nhận `videoTimeSeconds`, hoàn toàn thiếu cơ chế neo ngữ cảnh từ đoạn văn bản được bôi đen (text highlight/selection) trong PDF hoặc chỉ tiêu/ô số liệu được chọn trong BCTC.

Bản khảo sát này cung cấp thiết kế toàn diện để giải quyết triệt để các khoảng cách trên, nâng cấp Learn Hub thành nền tảng quản trị học liệu tài chính chuyên sâu chuẩn CFA & thị trường Việt Nam.

---

## 2. Khảo Sát Hiện Trạng Codebase (Codebase Archaeology & Findings)

### 2.1. Cấu trúc lưu trữ dữ liệu & DB Models hiện hữu

1. **Thư mục tài nguyên cục bộ**:
   - Đường dẫn: `/Users/mac/Documents/Dự án Agent Tài chính/data/learning_assets/`
   - Cấu trúc: `videos/`, `audios/`, `books/`, `images/`.
   - Cơ chế phục vụ: Được backend ánh xạ qua endpoint static `/learning-assets/{kind}/{filename}` (`src/risk_dashboard/modules/learning/api/public.py:96-144`).
   - Định hướng tương lai: Sẵn sàng chuyển dịch sang Cloud Object Storage (S3 / Cloudflare R2 / GCS) thông qua việc thay đổi URL prefix sang CDN URL (`data/learning_assets/README.md:26-29`).

2. **Dữ liệu tài chính thực tế (BCTC & vnstock cache)**:
   - Đường dẫn: `/Users/mac/Documents/Dự án Agent Tài chính/data/financials/cache/`
   - Chứa 120+ file JSON chuẩn hóa báo cáo tài chính của các doanh nghiệp niêm yết (ví dụ: `FPT.json`, `VNM.json`, `HPG.json`, `VCB.json`, `MWG.json`...).
   - Mỗi file chứa đầy đủ 3 báo cáo cốt lõi: Cân đối kế toán (Balance Sheet), Báo cáo kết quả kinh doanh (Income Statement), Báo cáo lưu chuyển tiền tệ (Cash Flow) qua nhiều quý/năm, được trích xuất và chuẩn hóa theo bộ chỉ tiêu chuẩn tại `src/risk_dashboard/data/financials.py:38-68`.
   - Ngoài ra có `data/financial_uploads/` lưu trữ các bản BCTC tự tải lên của người dùng.

3. **Mô hình Catalog SQLite hiện tại** (`src/risk_dashboard/modules/learning/crawlers/common.py:23-143`):
   - `learning_topics`: `topic_id`, `label_vi`, `label_en`, `tier`, `description`, `sort_order`.
   - `learning_courses`: `course_id`, `source`, `external_id`, `title`, `provider`, `instructor`, `description`, `url`, `thumbnail_url`, `language`, `level`, `duration_minutes`, `topics_json`, `tier`, `published_at`, `fetched_at`, `is_active`.
   - `learning_videos`: `video_id`, `source`, `external_id`, `title`, `channel`, `description`, `url`, `thumbnail_url`, `duration_seconds`, `topics_json`, `tier`, `published_at`, `fetched_at`.
   - `learning_books`: `book_id`, `source`, `external_id`, `title`, `author`, `description`, `url`, `download_url`, `cover_url`, `language`, `publication_year`, `topics_json`, `tier`, `fetched_at`.
   - `learning_papers`: `paper_id`, `source`, `external_id`, `title`, `authors_json`, `abstract`, `url`, `pdf_url`, `category`, `topics_json`, `tier`.
   - `learning_resource_topics`: Bảng liên kết M:N giữa `(resource_kind, resource_id)` và `topic_id`.

4. **Bảng trạng thái học tập & Đánh giá Socratic** (`src/risk_dashboard/platform/database/migrate.py`):
   - `learning_checkpoints`: Lưu câu hỏi kiểm tra kèm `correct_answer`, `explanation`, `expires_at`.
   - `learning_verified_events`: Lưu sự kiện chấm điểm thành công (`score`, `passed`, `rubric_evidence`).
   - `learning_progress_receipts`: Lưu chứng từ tiến độ 2 pha chống ghi đè/tấn công lặp lại (`idempotency_key`, `confirmation_id`).
   - `learning_video_transcripts` & `learning_video_quizzes`: Lưu phân đoạn phụ đề theo mốc giây và ngân hàng câu hỏi video.
   - `learning_home_state` & `learning_progress`: Quản lý tiến độ lộ trình học tập cá nhân.

### 2.2. Các API Endpoints hiện hữu

| Endpoint | Method | Trách nhiệm | Đánh giá hiện trạng |
| :--- | :--- | :--- | :--- |
| `/api/v1/public/learning/catalog` | GET | Lấy danh sách video, sách, paper, khóa học theo topic, tier | Hoạt động tốt, trả về danh sách phân trang |
| `/api/v1/public/learning/catalog/topics` | GET | Lấy taxonomy chủ đề và số lượng tài nguyên | Hoạt động tốt, phân chia 19 topic theo 3 tier |
| `/api/v1/public/learning/assets` | GET | Quét file đa phương tiện từ thư mục local test | Chỉ đọc file local, chưa hỗ trợ metadata phong phú |
| `/api/v1/public/learning/reader/stream` | GET | Proxy stream file PDF/sách tránh CORS, kiểm soát SSRF | Giới hạn 40MB, bảo vệ domain, nhưng chỉ là HTTP proxy |
| `/api/v1/public/learning/lessons/{id}` | GET | Lấy chi tiết bài học và câu hỏi trắc nghiệm | Thiết kế cho micro-lessons đơn lẻ, chưa có hierarchy |
| `/api/v1/public/learning/lessons/{id}/video-agent/prepare` | POST | Chuẩn bị phụ đề video và sinh câu hỏi trắc nghiệm | Hoạt động tốt với YouTube captions hoặc transcript cung cấp |
| `/api/v1/public/learning/lessons/{id}/video-agent/ask` | POST | Hỏi đáp nội dung video dựa trên mốc playback | Trả lời trích dẫn theo mốc giây, từ chối khi ngoài transcript |
| `/api/v1/public/learning/checkpoint` | GET | Lấy checkpoint kiểm tra không để lộ đáp án | Tuân thủ Zero-Leakage nghiêm ngặt |
| `/api/v1/public/learning/checkpoint/grade` | POST | Chấm câu hỏi và cấp `verified_event_id` | Ràng buộc tài khoản, kiểm tra hạn chót (TTL) |
| `/api/v1/public/learning/checkpoint/complete` | POST | Cam kết hoàn thành tiến độ qua 2-phase commit | Đảm bảo tính nhất quán và bất biến (Idempotent) |
| `/api/v1/public/ai-tutor/conversations` | POST | Khởi tạo phiên hội thoại với AI Tutor | Hỗ trợ context `learn`, `quant`, `general` |
| `/api/v1/public/ai-tutor/conversations/{id}/messages` | POST | Gửi câu hỏi tới AI Tutor qua `TutorGraph` | **Chưa có SSE streaming**, chỉ nhận `videoTimeSeconds` |

### 2.3. Frontend Components & Luồng giao diện

1. **Điểm nhập chính**: `frontend/src/features/learn-hub/pages/LearningHomePage.jsx`
   - Điều hướng tab con qua `LearningTopControls`: `courses` (Khóa học), `docs` (Sách & Tài liệu), `ai_tutor` (Hỏi AI Tutor), `mock_exam` (CFA Mock).
   - Bộ lọc: Tìm kiếm theo từ khóa, lọc theo độ khó (`Cơ bản`, `Trung bình`, `Nâng cao`), sắp xếp theo thời lượng/số bài/bookmark.
2. **Trình đọc sách (`BookReaderWorkspace.jsx` & `BookDocumentPane.jsx`)**:
   - Dùng `<iframe>` nhúng URL qua `/learning/reader/stream` hoặc Google Docs Viewer.
   - Bên phải là `NotePaper` gồm canvas vẽ tay và khung upload ảnh độc lập, **hoàn toàn không có liên kết với trang PDF hiện tại**.
   - Không có bộ đếm trang, không có thanh mục lục (TOC), không lưu lại trang đang đọc dở.
3. **Trình phát khóa học (`CoursePlayerPage.jsx`)**:
   - Sử dụng layout đơn: Video player ở trên, danh sách bài học ở sidebar bên trái/phải, phía dưới là một khung tab (`PLAYER_TABS`: `overview`, `video-agent`, `checkpoint`, `tutor`, `notes`, `resources`).
   - Người học khi muốn ghi chú hoặc hỏi AI Tutor phải chuyển tab làm che mất nội dung video hoặc thông tin đang xem.
   - Tab `notes` chỉ là dòng chữ placeholder: `"Ghi chú bài học đang phát triển"`.
   - Tiến độ khóa học lưu trong `localStorage` với key `northstar.learn-hub.progress:${sessionId}`, khi đổi trình duyệt hoặc thiết bị sẽ mất toàn bộ tiến độ.
4. **Phân hệ BCTC (`frontend/src/features/bctc/pages/`)**:
   - Đã phát triển rất mạnh mẽ: `BctcAnalysisWorkspace` (bảng BCTC 3 báo cáo đầy đủ, tỷ số tài chính, so sánh ngành), `RatioPracticeLab` (workflow 4 bước: Đặt câu hỏi -> Khám phá -> So sánh -> Giải thích), `RawDataChallenge` (thử thách tính toán chỉ số từ khoản mục gốc).
   - Tuy nhiên nằm tách biệt tại `/bctc`, người học trong Learn Hub không thể truy cập như một bài học case-study có tính điểm và lộ trình.

### 2.4. Tình trạng chạy thực tế của Test Suite hiện hữu

Đã tiến hành chạy độc lập cả hai bộ kiểm thử tự động của hệ thống:

1. **Backend Python Test Suite** (thực hiện qua `.venv/bin/pytest`):
   ```bash
   .venv/bin/pytest tests/test_learning.py tests/test_video_learning_agent.py tests/test_learning_agent_checkpoint.py tests/test_ai_tutor_learning.py
   ```
   **Kết quả**: `20 passed in 22.41s` (100% PASS).
   - `test_learning.py`: Kiểm tra luồng onboarding -> home state -> lesson -> quiz -> progress commit.
   - `test_video_learning_agent.py`: Kiểm tra chuẩn bị transcript, chống injection, tạo checkpoint video, ràng buộc tài khoản, kiểm tra hạn chót.
   - `test_learning_agent_checkpoint.py`: Kiểm tra Zero-Leakage (không lộ `correct_answer`), cơ chế từ chối khi hết hạn, xác thực tài khoản 2 pha.
   - `test_ai_tutor_learning.py`: Kiểm tra AI Tutor Socratic hướng dẫn học không làm lộ đáp án, giải thích đúng ngữ cảnh bài học.

2. **Frontend Node Test Suite** (thực hiện qua `npm run test:unit` trong `frontend/`):
   ```bash
   node ./scripts/test-runner.mjs
   ```
   **Kết quả**: `20 passed, 0 failed, 6 suites in 2.10s` (100% PASS).
   - `CheckpointCard Component Contract & Zero-Leakage`: Đảm bảo không render đáp án đúng vào thuộc tính DOM hoặc thẻ ẩn.
   - `SocraticHintWidget Component Contract`: Kiểm tra kỹ thuật Progressive Disclosure (gợi ý bậc 1 -> bậc 2) và thiết kế chuẩn token fintech.
   - `Learn Hub fallback catalog`: Kiểm tra số lượng bài học hiển thị đồng bộ với fallback data và BCTC course tồn tại.
   - `Mock exam room contract` & `BCTC raw data challenge`: Hoạt động đúng đặc tả.

---

## 3. Phân Tích Yêu Cầu 4 Dạng Nội Dung Đa Định Dạng Cốt Lõi

Để Learn Hub trở thành nền tảng học tập tài chính hoàn chỉnh, kiến trúc mới cần hỗ trợ đồng thời 4 định dạng với các hành vi đặc tả như sau:

### 3.1. Ebook / PDF Reader Chuyên Nghiệp

| Tiêu chí | Trạng thái hiện tại | Yêu cầu thiết kế mới (R2/R3 Spec) |
| :--- | :--- | :--- |
| **Engine hiển thị** | `iframe` tải URL proxy hoặc Google Docs Viewer | Tích hợp thư viện hiển thị PDF chuyên dụng (PDF.js / WebViewer canvas) với khả năng render từng trang vector sắc nét. |
| **Theo dõi trang & Tiến độ** | Không có | Thuộc tính `current_page`, `total_pages`, `read_percentage`, `last_read_at`. Tự động lưu vị trí trang khi cuộn (scroll debounce 500ms) và đồng bộ lên server. |
| **Đánh dấu (Bookmarks)** | Không có | Cho phép tạo Bookmark tại trang bất kỳ kèm tiêu đề ghi nhớ: `{ bookmark_id, page_number, title, created_at }`. Danh sách bookmark hiển thị ở thanh bên để nhảy trang tức thì. |
| **Highlight & Chú thích (Annotations)** | Canvas vẽ tự do riêng biệt, không neo vào văn bản | Neo trực tiếp tọa độ vùng chọn (`rects: [{ x, y, width, height }]`) hoặc phạm vi văn bản (`text_range: { start_offset, end_offset }`). Cho phép chọn màu highlight (Vàng, Xanh lá, Xanh dương, Tím) và gán ghi chú/comment. |
| **Tương tác AI Tutor** | Phải gõ lại câu hỏi thủ công | Nút ngữ cảnh tức thì: Khi bôi đen đoạn văn bản trong sách, xuất hiện menu nổi: **"Hỏi AI Tutor"**, **"Tóm tắt đoạn này"**, **"Phân tích công thức"**. Tự động đẩy đoạn trích dẫn và số trang vào AI Companion. |

### 3.2. Video Bài Giảng Kèm AI Timestamps & Đồng Bộ Ghi Chú

| Tiêu chí | Trạng thái hiện tại | Yêu cầu thiết kế mới (R2/R3 Spec) |
| :--- | :--- | :--- |
| **Phân đoạn chương (Chapters)** | Không có cấu trúc chương mục, video chạy từ đầu đến cuối | Cấu trúc dữ liệu chương mục: `chapters: [{ chapter_id, start_seconds, end_seconds, title, summary, key_concepts }]`. Thanh tiến độ video hiển thị các vạch chia chương (chapter markers) có thể click để nhảy playback. |
| **AI Key Takeaways** | Modal tĩnh lấy từ mock data tổng quát của sách | Hệ thống trích xuất tự động 3–5 điểm mấu chốt cho từng phân đoạn video, hiển thị dưới dạng thẻ bài học (Takeaway Cards) kèm công thức tài chính rút ra. |
| **Ghi chú đồng bộ mốc thời gian (Time-synced Notes)** | Tab `notes` là placeholder rỗng | Khi bấm "Thêm ghi chú", hệ thống tự động chụp `timestamp_seconds` hiện tại của video. Danh sách ghi chú hiển thị dạng dòng thời gian; nhấp vào bất kỳ ghi chú nào sẽ điều hướng video đến đúng giây đó. |
| **Dual-Pane AI Companion** | Tách rời thành tab riêng, che khuất video | Khung video và Trợ lý AI hiển thị song song cạnh nhau. Khi người dùng bấm dừng hoặc tua đến mốc nào, AI Companion tự động cập nhật ngữ cảnh phụ đề lân cận để sẵn sàng giải thích Socratic. |

### 3.3. Khóa Học Phân Cấp Đa Module (Hierarchical Multi-Module Courses)

| Tiêu chí | Trạng thái hiện tại | Yêu cầu thiết kế mới (R2/R3 Spec) |
| :--- | :--- | :--- |
| **Cấu trúc dữ liệu** | Bảng phẳng `learning_courses` chỉ lưu 1 URL và thời lượng | Mô hình phân cấp 4 tầng: `Course` -> `Module / Section` -> `Lesson` -> `Checkpoint / Activity`. Hỗ trợ các loại bài học đa dạng trong cùng khóa (`video`, `reading`, `case_study`, `quiz`). |
| **Quản lý tiến độ** | Lưu trong `localStorage` của trình duyệt | Lưu trữ trên máy chủ theo bảng `learning_course_enrollments` và `learning_lesson_progress`. Cung cấp tỷ lệ phần trăm hoàn thành theo module và toàn khóa. |
| **Cơ chế mở khóa điều kiện (Gating & Prerequisites)** | Tất cả bài học đều mở sẵn | Cho phép thiết lập điều kiện: Phải vượt qua Checkpoint của Module 1 (đạt >= 70%) thì Module 2 mới được mở khóa (`unlocked_at`). |
| **Chứng chỉ / Huy hiệu hoàn thành** | Không có | Cấp chứng từ hoàn thành khóa học dựa trên chuỗi các `verified_event_id` không thể giả mạo. |

### 3.4. BCTC Case-Studies Thực Chiến (Financial Statement Case Studies)

| Tiêu chí | Trạng thái hiện tại | Yêu cầu thiết kế mới (R2/R3 Spec) |
| :--- | :--- | :--- |
| **Tích hợp trong Learn Hub** | Không có trong Learn Hub (nằm ở `/bctc` tách biệt) | Trở thành một định dạng học liệu chính thức trong danh mục Learn Hub (`kind: bctc_case`). |
| **Liên kết mã cổ phiếu thực tế** | Sử dụng cache độc lập, không gắn với bài học | Gắn thẻ mã cổ phiếu trực tiếp (`ticker: FPT, VNM, HPG, VCB...`) lấy dữ liệu từ `data/financials/cache/` và tích hợp công cụ `vnstock`. |
| **Kịch bản tình huống (Narrative Scenario)** | Bài tập thực hành tự do | Thiết kế kịch bản học tập theo tình huống cụ thể của doanh nghiệp: <br>• *HPG*: Phân tích chu kỳ đầu tư Capex khu liên hợp Dung Quất và tác động đến dòng tiền CFO/FCF. <br>• *VNM*: Đánh giá biên lợi nhuận gộp và chính sách chi trả cổ tức trong giai đoạn bão hòa thị trường. <br>• *FPT*: Đánh giá chất lượng doanh thu mảng công nghệ thông tin toàn cầu và cơ cấu tài sản ngắn hạn. |
| **Sandbox tính toán & Thách thức dữ liệu thô** | Có trong `features/bctc` nhưng chưa chấm điểm vào tiến độ học | Nhúng trực tiếp `RawDataChallenge` và `RatioPracticeLab` vào bài học. Người học phải bóc tách khoản mục từ BCTC gốc, tự tính chỉ số và giải trình nhận định để đạt Checkpoint. |

---

## 4. Kiến Trúc Phân Loại (Taxonomy), Gắn Thẻ & Liên Kết Chéo

### 4.1. Chuẩn hóa Độ Khó (Difficulty Levels)

Hiện tại, codebase bị xung đột giữa các chuỗi tiếng Việt (`Cơ bản`, `Trung bình`, `Nâng cao`) và tiếng Anh (`beginner`, `intermediate`, `advanced`). Cần chuẩn hóa toàn diện theo Enum:

```python
class DifficultyTier(str, Enum):
    BEGINNER = "beginner"          # Cơ bản: Dành cho người mới bắt đầu, kiến thức nền tảng
    INTERMEDIATE = "intermediate"  # Trung bình: Phân tích báo cáo, mô hình định giá cơ bản
    ADVANCED = "advanced"          # Nâng cao: Định lượng tài chính, mô hình rủi ro VaR/CVaR, phái sinh
```
Frontend sử dụng helper ánh xạ song ngữ để hiển thị đồng bộ trên thẻ bài học và bộ lọc.

### 4.2. Cấu trúc Cây Chủ Đề (Topic Hierarchies)

Mở rộng 19 topics hiện tại thành cấu trúc phân cấp 2 tầng gắn kết chặt chẽ với chương trình CFA và thực tế thị trường chứng khoán Việt Nam:

```text
├── Category 1: Tài chính Doanh nghiệp & Phân tích BCTC (FSA & Corporate Finance)
│   ├── financial_statements (Đọc hiểu 3 Báo cáo Tài chính)
│   ├── cashflow_quality (Chất lượng Dòng tiền & Lợi nhuận)
│   ├── financial_ratios (Hệ thống Chỉ số Tài chính: DuPont, ROE, Thanh khoản)
│   └── corporate_governance (Quản trị Công ty & Đạo đức Kế toán)
├── Category 2: Phân tích Đầu tư & Định giá Cổ phiếu (Equity & Valuation)
│   ├── stocks (Thị trường Cổ phiếu & Tiêu chí Lựa chọn)
│   ├── valuation_dcf (Định giá Chiết khấu Dòng tiền DCF)
│   ├── valuation_multiples (Định giá Tương đối P/E, P/B, EV/EBITDA)
│   └── vietnam_market (Đặc thù Giao dịch HOSE/HNX, Biên độ & Quy chế)
├── Category 3: Quản lý Danh mục & Phân tích Rủi ro (Portfolio & Risk Management)
│   ├── portfolio_theory (Lý thuyết Danh mục Hiện đại MPT & Đa dạng hóa)
│   ├── asset_allocation (Phân bổ Lớp Tài sản: Cổ phiếu, Trái phiếu, Tiền mặt)
│   ├── risk_management (Quản trị Rủi ro: VaR, Max Drawdown, Stop-loss)
│   └── behavioral_finance (Tài chính Hành vi & Tâm lý Giao dịch)
└── Category 4: Kinh tế Vĩ mô & Công cụ Nâng cao (Macro & Quantitative Tools)
    ├── macroeconomics (Kinh tế Vĩ mô: Lạm phát, Lãi suất, Chu kỳ Kinh tế)
    ├── bonds_fixed_income (Thị trường Trái phiếu & Lãi suất)
    ├── derivatives (Công cụ Phái sinh: Hợp đồng Tương lai VN30, Quyền chọn)
    └── quantitative_finance (Mô phỏng Monte Carlo, Backtest & Định lượng)
```

### 4.3. Cơ chế Gắn Thẻ Đa Chiều & Liên Kết Chéo Cổ Phiếu Thực Tế (Stock Ticker Cross-Linking)

Mỗi tài nguyên học tập (Bài học, Sách, Video, Case-study) được gắn thẻ thông qua hệ thống Tag đa chiều:
1. `topic_tags`: Danh sách ID chủ đề (`["financial_statements", "cashflow_quality"]`).
2. `cfa_mapping`: Ánh xạ học phần CFA (`"CFA_L1_FSA_READING_19"`).
3. `ticker_symbols`: Danh sách mã cổ phiếu liên quan (`["HPG", "VNM", "FPT"]`).

**Cơ chế liên kết chéo trên giao diện (Cross-linking UX)**:
- Khi người học đọc bài học hoặc xem video về **"Hàng tồn kho & Chu kỳ tiền mặt"**, giao diện sẽ hiển thị widget **"Dữ liệu Thực chiến Doanh nghiệp"**.
- Widget cung cấp các pill mã cổ phiếu có thể click (ví dụ: `[HPG: Thép]`, `[VNM: Sữa]`).
- Nhấp vào mã sẽ mở trực tiếp bản trích xuất BCTC của mã đó từ kho dữ liệu, minh họa sinh động ngay lập tức khái niệm vừa học trên số liệu kiểm toán thật.

---

## 5. Tích Hợp AI Tutor & Socratic Companion Chuyên Sâu

### 5.1. Kiến Trúc Giao Diện Chia Đôi (Dual-Pane Split Layout)

Learn Hub mới loại bỏ hoàn toàn các tab con rời rạc để chuyển sang kiến trúc **Dual-Pane Workspaces**:

```
+---------------------------------------------------------------------------------------+
|  LEARN HUB HEADER: [Trở về] [Tiêu đề Tài liệu/Bài giảng] [Tiến độ: 65%] [Bookmarks]   |
+-----------------------------------------------------------+---------------------------+
|  LEFT PRIMARY PANE (Nội dung Học liệu)                    |  RIGHT COMPANION PANE     |
|                                                           |  (AI Socratic & Notes)    |
|  [Định dạng tự thích ứng]:                               |                           |
|  - Chế độ Ebook: PDF Canvas + Thanh công cụ trang         |  [Tab: 🤖 AI Tutor]       |
|    (Hỗ trợ bôi đen văn bản, highlight màu)                |  [Tab: 📝 Ghi chú mốc]    |
|                                                           |  [Tab: 💡 Key Takeaways]  |
|  - Chế độ Video: 16:9 Video Player + Chapter timeline     |                           |
|    (Hiển thị transcript song ngữ chạy theo playback)      |  Khung hội thoại          |
|                                                           |  Socratic với streaming   |
|  - Chế độ BCTC Case: Split Table 3 Báo cáo                |  token theo thời gian     |
|    (Bảng cân đối, P&L, Lưu chuyển tiền tệ tương tác)      |  thực.                    |
|                                                           |                           |
|  - Chế độ Checkpoint: Thẻ câu hỏi trắc nghiệm / Lab       |  Nút Quick Prompt         |
|    (Zero-Leakage radio buttons & Rubric giải thích)       |  gợi ý theo đúng ngữ      |
|                                                           |  cảnh hiện tại.           |
+-----------------------------------------------------------+---------------------------+
```

### 5.2. Giao thức Neo Ngữ Cảnh Đa Chiều (Multi-Modal Context Grounding Protocol)

Khi người học tương tác trên Left Pane, ngữ cảnh được tự động đóng gói và truyền sang AI Tutor:

```typescript
interface TutorContextPayload {
  surface: 'learn';
  resource_id: string;                    // ID của Sách, Video, Khóa học hoặc Case BCTC
  resource_kind: 'book' | 'video' | 'course_lesson' | 'bctc_case';
  
  // Neo ngữ cảnh khi đang đọc Ebook / PDF
  document_context?: {
    page_number: number;
    selected_text?: string;               // Đoạn văn bản vừa bôi đen
    section_title?: string;
  };
  
  // Neo ngữ cảnh khi đang xem Video
  video_context?: {
    playback_seconds: number;             // Giây hiện tại của video
    chapter_id?: string;
    nearby_transcript_snippet?: string;  // Phụ đề xung quanh mốc xem
  };
  
  // Neo ngữ cảnh khi đang làm BCTC Case-study
  bctc_context?: {
    ticker: string;                       // 'HPG', 'FPT', 'VNM'
    period: string;                       // '2024-Q3'
    statement_type: 'balance' | 'income' | 'cashflow' | 'ratio';
    focused_line_item?: string;           // 'inventories', 'operating_cash_flow'
    focused_value?: number;               // 38500000000000
  };
}
```

### 5.3. Phản Hồi Dạng Dòng (SSE Streaming) & Kỷ Cương Socratic

1. **Server-Sent Events (SSE)**:
   - Endpoint: `POST /api/v1/public/ai-tutor/conversations/{id}/messages/stream`
   - Header: `Content-Type: text/event-stream`, `Cache-Control: no-cache`.
   - Các loại sự kiện gửi về:
     - `event: token`: Gửi từng phần token văn bản (`data: {"chunk": "Chào anh, "}`).
     - `event: citation`: Gửi các trích dẫn tài liệu/video được chứng thực.
     - `event: check_question`: Gửi câu hỏi gợi mở tiếp theo của gia sư.
     - `event: done`: Hoàn tất xử lý, gửi kèm `message_id`, `trace_id`.
2. **Kỷ cương Socratic & Chống Lộ Đáp Án (Zero-Leakage Guardrail)**:
   - AI Tutor tuyệt đối không đưa ra đáp án trực tiếp cho các câu hỏi kiểm tra hoặc bài tập thực hành.
   - Thay vào đó áp dụng **Mô hình Khơi gợi 3 Cấp độ**:
     - *Cấp 1 (Định hướng Khái niệm)*: Nhắc lại nguyên lý cốt lõi hoặc ý nghĩa kinh tế đằng sau chỉ số.
     - *Cấp 2 (Gợi ý Phân tích)*: Chỉ ra thành phần tử số/mẫu số cần chú ý hoặc hướng dẫn loại trừ các phương án vô lý.
     - *Cấp 3 (Tự Đánh Giá)*: Đặt câu hỏi phản biện để người học tự kết luận và tự bấm chọn đáp án trên màn hình.

---

## 6. Thiết Kế Mô Hình Dữ Liệu & Sơ Đồ Quan Hệ Thực Thể (ERD)

### 6.1. Sơ Đồ Quan Hệ Thực Thể (ERD Overview)

```text
[learning_topics] 1 ────< M [learning_resource_topics] M >──── 1 [learning_resources]
                                                                        │
        ┌───────────────────────────────┬───────────────────────────────┴──────────────────────────────┐
        │ (kind='course')               │ (kind='book')                 │ (kind='video')               │ (kind='bctc_case')
        ▼                               ▼                               ▼                              ▼
 [learning_courses]              [learning_books]                [learning_videos]              [learning_bctc_cases]
        │                               │                               │                              │
        │ 1                             │ 1                             │ 1                            │ 1
        ▼ M                             ▼ M                             ▼ M                            ▼ M
 [learning_course_modules]       [learning_book_annotations]     [learning_video_chapters]      [bctc_case_investigations]
        │                               │                               │
        │ 1                             │ 1                             │ 1
        ▼ M                             ▼ M                             ▼ M
 [learning_course_lessons]       [learning_book_bookmarks]       [learning_video_notes]
        │
        │ 1
        ▼ M
 [learning_checkpoints]
        │
        │ 1
        ▼ M
 [learning_verified_events]
        │
        │ 1
        ▼ M
 [learning_progress_receipts]
```

### 6.2. Thiết Kế DDL Relational (Tương thích SQLite & PostgreSQL)

```sql
-- 1. Bảng khóa học phân cấp (Hierarchical Courses)
CREATE TABLE IF NOT EXISTS learning_courses_v2 (
  course_id VARCHAR(64) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(128) UNIQUE NOT NULL,
  description TEXT,
  instructor VARCHAR(128),
  tier VARCHAR(32) NOT NULL DEFAULT 'beginner', -- beginner, intermediate, advanced
  category VARCHAR(64) NOT NULL DEFAULT 'finance',
  total_duration_minutes INTEGER NOT NULL DEFAULT 0,
  thumbnail_url TEXT,
  prerequisites_json TEXT NOT NULL DEFAULT '[]',
  status VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng module của khóa học
CREATE TABLE IF NOT EXISTS learning_course_modules (
  module_id VARCHAR(64) PRIMARY KEY,
  course_id VARCHAR(64) NOT NULL REFERENCES learning_courses_v2(course_id) ON DELETE CASCADE,
  sequence_order INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  learning_outcomes_json TEXT NOT NULL DEFAULT '[]',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_course_modules_course ON learning_course_modules(course_id, sequence_order);

-- 3. Bảng bài học trong module
CREATE TABLE IF NOT EXISTS learning_course_lessons (
  lesson_id VARCHAR(64) PRIMARY KEY,
  module_id VARCHAR(64) NOT NULL REFERENCES learning_course_modules(module_id) ON DELETE CASCADE,
  course_id VARCHAR(64) NOT NULL REFERENCES learning_courses_v2(course_id) ON DELETE CASCADE,
  sequence_order INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  lesson_type VARCHAR(32) NOT NULL, -- 'video', 'reading', 'bctc_case', 'quiz'
  content_ref_id VARCHAR(128) NOT NULL, -- ID trỏ sang video_id, book_id, case_id...
  duration_minutes INTEGER NOT NULL DEFAULT 5,
  is_free_preview BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_course_lessons_module ON learning_course_lessons(module_id, sequence_order);

-- 4. Bảng tiến độ người học cho khóa học (Server-Side Persistence)
CREATE TABLE IF NOT EXISTS learning_user_course_progress (
  user_id VARCHAR(64) NOT NULL,
  course_id VARCHAR(64) NOT NULL REFERENCES learning_courses_v2(course_id) ON DELETE CASCADE,
  lesson_id VARCHAR(64) NOT NULL REFERENCES learning_course_lessons(lesson_id) ON DELETE CASCADE,
  status VARCHAR(32) NOT NULL DEFAULT 'in_progress', -- 'in_progress', 'completed'
  progress_pct INTEGER NOT NULL DEFAULT 0,
  last_position_seconds INTEGER DEFAULT 0,
  completed_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, course_id, lesson_id)
);
CREATE INDEX IF NOT EXISTS idx_user_course_prog_user ON learning_user_course_progress(user_id, course_id);

-- 5. Bảng bookmark & highlight của sách PDF
CREATE TABLE IF NOT EXISTS learning_book_annotations (
  annotation_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  book_id VARCHAR(64) NOT NULL,
  page_number INTEGER NOT NULL,
  selected_text TEXT NOT NULL,
  rects_json TEXT NOT NULL, -- Toạ độ bounding box trên canvas PDF
  color VARCHAR(16) NOT NULL DEFAULT '#FFE066',
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_book_anno_user ON learning_book_annotations(user_id, book_id, page_number);

CREATE TABLE IF NOT EXISTS learning_book_bookmarks (
  bookmark_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  book_id VARCHAR(64) NOT NULL,
  page_number INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_book_bookmarks_unique ON learning_book_bookmarks(user_id, book_id, page_number);

-- 6. Bảng chương và ghi chú video
CREATE TABLE IF NOT EXISTS learning_video_chapters (
  chapter_id VARCHAR(64) PRIMARY KEY,
  video_id VARCHAR(64) NOT NULL,
  start_seconds REAL NOT NULL,
  end_seconds REAL NOT NULL,
  title VARCHAR(255) NOT NULL,
  summary TEXT,
  key_takeaways_json TEXT NOT NULL DEFAULT '[]',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_video_chapters ON learning_video_chapters(video_id, start_seconds);

CREATE TABLE IF NOT EXISTS learning_video_notes (
  note_id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) NOT NULL,
  video_id VARCHAR(64) NOT NULL,
  timestamp_seconds REAL NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_video_notes_user ON learning_video_notes(user_id, video_id, timestamp_seconds);

-- 7. Bảng BCTC Case-Studies
CREATE TABLE IF NOT EXISTS learning_bctc_cases (
  case_id VARCHAR(64) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(128) UNIQUE NOT NULL,
  ticker VARCHAR(20) NOT NULL, -- 'HPG', 'VNM', 'FPT'
  period VARCHAR(20) NOT NULL, -- '2024-Q3'
  industry VARCHAR(64) NOT NULL,
  difficulty VARCHAR(32) NOT NULL DEFAULT 'intermediate',
  narrative_scenario TEXT NOT NULL,
  key_focus_ratios_json TEXT NOT NULL DEFAULT '[]',
  investigation_steps_json TEXT NOT NULL DEFAULT '[]',
  status VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_bctc_cases_ticker ON learning_bctc_cases(ticker);
```

### 6.3. Pydantic v2 Schemas Thiết Kế Mới (Trích dẫn minh họa)

```python
# File thiết kế đề xuất: src/risk_dashboard/modules/learning/schemas/domain_v2.py
from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class DifficultyTier(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ContentKind(str, Enum):
    COURSE = "course"
    BOOK = "book"
    VIDEO = "video"
    BCTC_CASE = "bctc_case"
    PAPER = "paper"

class CourseModuleSchema(BaseModel):
    module_id: str
    course_id: str
    sequence_order: int
    title: str
    description: str | None = None
    learning_outcomes: list[str] = Field(default_factory=list)

class CourseLessonSchema(BaseModel):
    lesson_id: str
    module_id: str
    course_id: str
    sequence_order: int
    title: str
    lesson_type: Literal["video", "reading", "bctc_case", "quiz"]
    content_ref_id: str
    duration_minutes: int = 5
    is_free_preview: bool = False

class BctcCaseStudySchema(BaseModel):
    case_id: str
    title: str
    ticker: str
    period: str
    industry: str
    difficulty: DifficultyTier
    narrative_scenario: str
    key_focus_ratios: list[str]
    investigation_steps: list[dict]
```

---

## 7. Đặc Tả Bộ Hợp Đồng API (API Contract Specifications)

### 7.1. Nhóm API Học Liệu Đa Định Dạng (Catalog & Content Delivery)

- **`GET /api/v1/public/learning/courses/{course_id}/hierarchy`**
  - **Mô tả**: Lấy đầy đủ cấu trúc phân cấp của khóa học (Course -> Modules -> Lessons -> Checkpoints) kèm trạng thái hoàn thành của tài khoản người dùng hiện tại.
  - **Phản hồi (200 OK)**:
    ```json
    {
      "course_id": "course_cfa_fsa_101",
      "title": "Phân Tích Báo Cáo Tài Chính Chuẩn CFA Level I",
      "tier": "intermediate",
      "total_lessons": 12,
      "completed_lessons": 4,
      "completion_pct": 33,
      "modules": [
        {
          "module_id": "mod_01",
          "title": "Module 1: Cấu trúc Ba Báo Cáo Cốt Lõi",
          "is_unlocked": true,
          "lessons": [
            {
              "lesson_id": "les_01_01",
              "title": "Bảng Cân Đối Kế Toán & Bản chất Nợ/VCSH",
              "lesson_type": "video",
              "duration_minutes": 15,
              "content_ref_id": "vid_yt_balance_sheet",
              "status": "completed"
            },
            {
              "lesson_id": "les_01_02",
              "title": "Case Study HPG: Đọc hiểu tài sản dở dang Dung Quất",
              "lesson_type": "bctc_case",
              "duration_minutes": 25,
              "content_ref_id": "case_hpg_capex_2024",
              "status": "in_progress"
            }
          ]
        }
      ]
    }
    ```

- **`GET /api/v1/public/learning/bctc-cases/{case_id}`**
  - **Mô tả**: Tải dữ liệu toàn diện của một tình huống thực hành BCTC, kết nối trực tiếp với cache tài chính của mã cổ phiếu.
  - **Phản hồi (200 OK)**:
    ```json
    {
      "case_id": "case_hpg_capex_2024",
      "title": "HPG: Chu Kỳ Tồn Kho & Dòng Tiền Tự Do (FCF) Giai Đoạn Mở Rộng",
      "ticker": "HPG",
      "period": "2024-Q3",
      "industry": "Thép & Vật liệu Xây dựng",
      "difficulty": "intermediate",
      "narrative": "Tập đoàn Hòa Phát đẩy mạnh giải ngân dự án Dung Quất 2. Người học hãy kiểm tra tài sản cố định dở dang, dòng tiền CFO và tính toán FCF để đánh giá áp lực thanh khoản.",
      "financial_snapshot": {
        "balance_sheet": { "total_assets": 195000000000000, "inventories": 38500000000000, "capex_wip": 45000000000000 },
        "cash_flow": { "cfo": 12500000000000, "capex": -18000000000000, "fcf": -5500000000000 }
      },
      "tasks": [
        { "task_id": "t1", "prompt": "Tính FCF kỳ 2024-Q3 = CFO + Capex", "expected_metric": "fcf" },
        { "task_id": "t2", "prompt": "Đánh giá tỷ số Nợ Vay / VCSH", "expected_metric": "debt_to_equity" }
      ]
    }
    ```

### 7.2. Nhóm API Trình Đọc Sách & Đồng Bộ Tiến Độ (PDF Sync & Annotations)

- **`POST /api/v1/public/learning/books/{book_id}/progress`**
  - **Payload**:
    ```json
    {
      "current_page": 45,
      "total_pages": 320,
      "read_percentage": 14
    }
    ```
- **`GET /api/v1/public/learning/books/{book_id}/annotations`**
  - **Phản hồi**: Danh sách các highlight, tọa độ khung chữ và comment đã lưu.
- **`POST /api/v1/public/learning/books/{book_id}/annotations`**
  - **Payload**:
    ```json
    {
      "page_number": 45,
      "selected_text": "Biên an toàn là khoản chênh lệch giữa giá trị nội tại và thị giá.",
      "rects": [{ "x": 120.5, "y": 340.2, "width": 450.0, "height": 18.5 }],
      "color": "#FFE066",
      "comment": "Nguyên lý mấu chốt của Graham"
    }
    ```

### 7.3. Nhóm API Phản Hồi Dòng Trợ Lý AI (AI Tutor Streaming API)

- **`POST /api/v1/public/ai-tutor/conversations/{conversation_id}/messages/stream`**
  - **Headers**: `Accept: text/event-stream`, `X-Session-ID: ...`
  - **Payload**:
    ```json
    {
      "content": "Giải thích tại sao FCF của HPG lại âm dù lợi nhuận sau thuế vẫn dương?",
      "surface": "learn",
      "context": {
        "resource_id": "case_hpg_capex_2024",
        "resource_kind": "bctc_case",
        "bctc_context": {
          "ticker": "HPG",
          "period": "2024-Q3",
          "focused_line_item": "fcf",
          "focused_value": -5500000000000
        }
      },
      "idempotency_key": "idemp_stream_0192"
    }
    ```
  - **Dòng dữ liệu SSE trả về**:
    ```text
    event: token
    data: {"chunk": "Chào anh, "}

    event: token
    data: {"chunk": "điều này hoàn toàn bình thường trong các doanh nghiệp đang ở chu kỳ đầu tư lớn. "}

    event: token
    data: {"chunk": "Lợi nhuận sau thuế được ghi nhận theo nguyên tắc dồn tích, trong khi FCF phản ánh dòng tiền thực tế sau khi trừ đi chi phí vốn mua sắm tài sản (Capex)..."}

    event: citation
    data: {"source_type": "bctc", "source_id": "HPG:2024-Q3:cash_flow", "label": "BCTC Hòa Phát Q3/2024 - Capex 18.000 tỷ"}

    event: check_question
    data: {"prompt": "Anh có muốn xem xét tỷ lệ Nợ vay/Vốn chủ sở hữu của HPG trong cùng kỳ để đánh giá nguồn bù đắp cho khoản FCF âm này không?"}

    event: done
    data: {"message_id": "msg_89f0a2", "trace_id": "tr_11029"}
    ```

---

## 8. Lộ Trình Triển Khai Phân Đoạn (Tracer-Bullet Implementation Roadmap)

Để đảm bảo nguyên tắc **First Principles & Tracer Bullet** (triển khai đến đâu, có automated test kiểm chứng đến đó, không làm hỏng tính năng hiện hữu), lộ trình được chia thành 5 giai đoạn:

```
[Giai đoạn 1] Schema & Data Migration (Courses V2, BCTC Cases, Book Progress)
       │ (Kiểm thử: migration script + unit test DB DDL)
       ▼
[Giai đoạn 2] Nâng cấp Ebook/PDF & Video Player với Dual-Pane Layout
       │ (Kiểm thử: component contract tests + page coordinate syncing)
       ▼
[Giai đoạn 3] Đóng gói & Tích hợp BCTC Case-Studies vào Learn Hub
       │ (Kiểm thử: real ticker integration test FPT/VNM/HPG + sandbox tests)
       ▼
[Giai đoạn 4] Xây dựng AI Tutor SSE Streaming & Context Grounding Engine
       │ (Kiểm thử: SSE event stream test + Zero-Leakage Socratic policy)
       ▼
[Giai đoạn 5] Tích hợp Toàn diện & Đối chuẩn CFA Learning Ecosystem
       │ (Kiểm thử: E2E Playwright test + Full regression test suite)
```

| Giai đoạn | Nhiệm vụ chính | Deliverables / Files bị ảnh hưởng | Quality Gate & Verification |
| :--- | :--- | :--- | :--- |
| **P1: Schema & Data Migration** | Thiết lập bảng dữ liệu phân cấp `learning_courses_v2`, `learning_course_modules`, `learning_course_lessons`, `learning_bctc_cases`, `learning_book_annotations`. Đảm bảo tương thích ngược với bảng cũ. | `src/risk_dashboard/platform/database/migrate.py`<br>`src/risk_dashboard/modules/learning/schemas/domain_v2.py` | Chạy migration thành công, không làm gián đoạn các test suite `test_learning.py` cũ. |
| **P2: Dual-Pane UI: Ebook & Video** | Tái cấu trúc layout Dual-Pane. Tích hợp PDF canvas reader có theo dõi số trang, bookmark và neo highlight; Video player có chapter markers và synchronized notes. | `frontend/src/features/learn-hub/pages/BookReaderWorkspace.jsx`<br>`frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx`<br>`frontend/src/features/learn-hub/pages/DualPaneLayout.jsx` | `npm run test:unit` pass, các component render đúng tokens.css, không layout shift. |
| **P3: BCTC Case-Study Engine** | Đóng gói bài học tình huống thực tế cho FPT, VNM, HPG. Kết nối trực tiếp `data/financials/cache` vào Learn Hub. Nhúng `RawDataChallenge` vào Checkpoint bài học. | `src/risk_dashboard/modules/learning/api/public.py`<br>`frontend/src/features/learn-hub/pages/BctcCaseStudyPlayer.jsx` | Tải dữ liệu thật của 3 mã FPT, VNM, HPG thành công, kiểm thử tính toán chỉ số FCF, ROE, Debt/Equity chính xác. |
| **P4: AI Socratic Streaming** | Phát triển endpoint SSE streaming cho AI Tutor. Bổ sung `TutorContextPayload` cho phép bôi đen text trong sách hoặc chọn ô BCTC để hỏi ngay. Giữ vững Zero-Leakage. | `src/risk_dashboard/modules/ai_tutor/api/public.py`<br>`src/risk_dashboard/modules/ai_tutor/application/tutor_graph.py`<br>`frontend/src/features/learn-hub/services/aiTutorApi.js` | Test SSE stream nhận đủ event token và event done; thử câu hỏi gian lận đáp án bị chặn 100%. |
| **P5: CFA Ecosystem & Regression** | Hoàn thiện mapping cây chủ đề CFA Level I. Chạy toàn bộ regression test suites của hệ thống. | `tests/test_learning_v2_e2e.py`<br>`frontend/src/__tests__/learnHubV2.test.js` | Toàn bộ các test suite backend và frontend chạy PASS 100%. |

---

## 9. Kết Luận Khảo Sát

Hệ thống Northstar Finance Lab đã sở hữu đầy đủ các "viên gạch nền móng" cực kỳ chất lượng: cơ chế bảo mật Zero-Leakage, kiểm soát 2-phase commit, dữ liệu BCTC thực chiến phong phú của thị trường Việt Nam và trợ lý đối soát phụ đề video. 

Việc tái thiết kế Tab Learn Hub theo kiến trúc **Đa định dạng 4 trụ cột**, giao diện **Dual-Pane Workspaces** và trợ lý **Socratic Streaming có neo ngữ cảnh** là hoàn toàn khả thi, mang tính đột phá và nâng tầm sản phẩm lên chuẩn mực nền tảng công nghệ giáo dục tài chính chuyên nghiệp.
