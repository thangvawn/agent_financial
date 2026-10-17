# Báo Cáo Chuyển Giao: Khảo Sát Kiến Trúc Domain & Đặc Tả Nâng Cấp Tab Learn Hub (Handoff Report)

**Mã Agent**: `explorer_survey_domain`  
**Thư mục làm việc**: `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_domain`  
**Người nhận**: Điều phối viên hệ thống (Orchestrator Conversation ID: `97a90bba-b298-4ab1-be4b-07eacc3cdf32`)  
**Ngày báo cáo**: 2026-10-10  
**Tài liệu phân tích chi tiết**: `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_domain/analysis.md`

---

## 1. Quan Sát Thực Tế (Observation)

### 1.1. Hiện trạng Kho Học Liệu, Dữ Liệu Thực Tế và Mocks
- **Kho học liệu đa phương tiện cục bộ**: Được đặt tại `data/learning_assets/` với các thư mục con `videos/`, `audios/`, `books/`, `images/`. Endpoint phục vụ static assets là `/learning-assets/{kind}/{filename}` tại `src/risk_dashboard/modules/learning/api/public.py:96-144`.
- **Dữ liệu BCTC thực tế**: Đã có 120+ file JSON chuẩn hóa trong `data/financials/cache/` (như `FPT.json`, `VNM.json`, `HPG.json`, `VCB.json`...). Các hàm phân giải khoản mục chuẩn tại `src/risk_dashboard/data/financials.py:38-68`.
- **Dữ liệu Mock & Catalog tĩnh trong Frontend**:
  - `frontend/src/features/learn-hub/content/demoCourses.js` lưu trữ các khóa học mẫu YouTube với cấu trúc 2 sections.
  - `frontend/src/features/learn-hub/content/demoBooks.js` lưu trữ sách kinh điển kèm `download_url` từ Internet Archive.
  - `frontend/src/features/learn-hub/content/courseCatalogData.js:57-100` chứa hàm `normalizeDbCourse` - khi đọc từ SQLite chỉ có 1 bản ghi phẳng, frontend buộc phải tự sinh 1 section và 1 lesson giả lập.
  - `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx:15-22` lưu trữ tiến độ khóa học trong `localStorage` với key `northstar.learn-hub.progress:${sessionId}`, không đồng bộ về server.
- **Bảng Catalog SQLite hiện tại**: Trong `src/risk_dashboard/modules/learning/crawlers/common.py:23-143`, bảng `learning_courses` được thiết kế phẳng (chỉ có `course_id`, `url`, `duration_minutes`), thiếu hoàn toàn mô hình phân cấp Course -> Modules -> Lessons.

### 1.2. Hiện trạng Trình Đọc Sách, Video Player và Phân hệ BCTC
- **Trình đọc sách (`BookReaderWorkspace.jsx` & `BookDocumentPane.jsx:26-84`)**: Sử dụng `iframe` thô sơ trỏ tới Google Docs Viewer hoặc `/api/v1/public/learning/reader/stream`. Split pane bên phải là `NotePaper` (vẽ tay tự do canvas và upload ảnh), không có liên kết trang PDF, không có đánh dấu trang (Bookmarks), không có theo dõi trang hiện tại (`current_page`), và không thể bôi đen văn bản để hỏi AI Tutor.
- **Trình phát video (`CoursePlayerPage.jsx:24-31` & `CoursePlayerTabContent.jsx:62-65`)**: Bố cục dạng tab đơn lẻ (`PLAYER_TABS`). Tab `notes` chỉ chứa dòng chữ: `<p className="lhp-notes__placeholder">Ghi chú bài học đang phát triển.</p>`. Không có dòng thời gian ghi chú neo mốc giây, không có chapter marker trên thanh tua.
- **Phân hệ BCTC (`frontend/src/features/bctc/`)**: Đã có `BctcAnalysisWorkspace.jsx`, `RatioPracticeLab.jsx`, `RawDataChallenge.jsx` và công cụ backend `BctcResolveReportTool`, `BctcResolveLineItemTool` (`src/risk_dashboard/modules/financials_product/agent_tools/report_tools.py:18-100`), nhưng **bị cô lập hoàn toàn** ở đường dẫn `/bctc`, chưa được tích hợp vào Learn Hub thành BCTC Case-studies có lộ trình và chứng từ hoàn thành.

### 1.3. Trạng thái AI Tutor & Context Grounding
- `src/risk_dashboard/modules/ai_tutor/api/public.py:60-74`: Endpoint gửi câu hỏi `POST /ai-tutor/conversations/{id}/messages` xử lý bất đồng bộ nhưng trả về JSON tĩnh, **chưa hỗ trợ Server-Sent Events (SSE) streaming**.
- `src/risk_dashboard/modules/ai_tutor/schemas/requests.py:14-23`: Schema `SendMessageRequest` chỉ nhận `video_time_seconds: float | None`. Hoàn toàn thiếu trường neo ngữ cảnh văn bản được chọn trong PDF (`text_selection`, `page_number`) hoặc chỉ tiêu tài chính BCTC (`ticker`, `period`, `line_item`).
- `src/risk_dashboard/modules/ai_tutor/application/specialists/learning_specialist.py:141-216`: Đã có luồng trích xuất transcript video qua `VideoLearningAgentService`, đảm bảo Zero-Leakage cho quiz.

### 1.4. Kết Quả Chạy Kiểm Thử Thực Tế (Verbatim Test Executions)
- **Backend Test Suite**:
  - Lệnh thực thi: `.venv/bin/pytest tests/test_learning.py tests/test_video_learning_agent.py tests/test_learning_agent_checkpoint.py tests/test_ai_tutor_learning.py`
  - Kết quả: `20 passed in 22.41s` (Mã thoát 0, 100% pass).
  - Ghi chú: Chạy bằng Python hệ thống (`/opt/homebrew/Cellar/python@3.14/`) bị lỗi `ModuleNotFoundError: No module named 'langgraph'`; bắt buộc phải dùng `.venv/bin/pytest` đúng theo hiến pháp Vibe Coding của dự án.
- **Frontend Test Suite**:
  - Lệnh thực thi: `npm run test:unit` (trong thư mục `frontend/`)
  - Kết quả: `20 pass, 0 fail, 6 suites in 2.10s` (Mã thoát 0, 100% pass).

---

## 2. Chuỗi Suy Luận (Logic Chain)

1. **Từ Quan sát 1.1 & 1.2 về Cấu trúc dữ liệu và Giao diện**:
   - Khi bảng `learning_courses` trong database chỉ là bảng phẳng, hệ thống không thể lưu trữ metadata của từng module, danh sách bài học, bài tập thực hành hay checkpoint theo từng chặng.
   - Việc frontend lưu tiến độ khóa học trong `localStorage` khiến dữ liệu phân tán, không đồng bộ đa thiết bị, và không thể tích hợp vào bảng tổng kết tiến độ người học (`learning_progress`).
   - Do đó, cần thiết kế lại DDL phân cấp: `learning_courses_v2` -> `learning_course_modules` -> `learning_course_lessons` -> `learning_checkpoints`.

2. **Từ Quan sát 1.2 về Ebook Reader và Video Player**:
   - Việc nhúng `iframe` tài liệu rời rạc với thanh ghi chú canvas tự do khiến người học không thể định vị mình đang đọc trang nào trong cuốn sách 300 trang của Benjamin Graham.
   - Khi không có tọa độ bounding box hoặc neo đoạn chữ, người học không thể highlight hoặc hỏi trợ lý AI về đoạn văn bản vừa đọc.
   - Tương tự, trong video, nếu ghi chú không gắn với `timestamp_seconds`, người học không thể ôn tập nhanh lại khoảnh khắc giảng viên giải thích công thức phức tạp.
   - Do đó, bắt buộc phải nâng cấp mô hình lưu trữ Annotations/Bookmarks (`learning_book_annotations`, `learning_video_notes`) và chuyển đổi giao diện sang **Dual-Pane Split Workspace**.

3. **Từ Quan sát 1.1 & 1.2 về BCTC**:
   - Dự án đã có sẵn kho cache BCTC chất lượng cao của hơn 120 mã cổ phiếu Việt Nam (HPG, VNM, FPT...) và công cụ phân giải chỉ số `financials_product`.
   - Tuy nhiên, việc để phân hệ này tách biệt tại `/bctc` làm lãng phí giá trị thực chiến của Learn Hub.
   - Khi đóng gói các bài toán thực tế (như chu kỳ Capex HPG, biên lãi gộp VNM) thành **BCTC Case-study** trong Learn Hub, kết hợp sandbox `RawDataChallenge`, người học sẽ có trải nghiệm học tài chính thực chiến độc nhất vô nhị.

4. **Từ Quan sát 1.3 về AI Tutor**:
   - Việc chờ đợi 5–10 giây cho một phản hồi hoàn chỉnh qua HTTP POST truyền thống tạo ra cảm giác lag và giảm trải nghiệm người dùng.
   - Việc thiếu neo ngữ cảnh khiến người học phải copy-paste nội dung câu chữ vào khung chat.
   - Do đó, giải pháp tối ưu là bổ sung endpoint SSE Streaming (`/messages/stream`) và hợp đồng dữ liệu `TutorContextPayload` đa chiều (nhận cả `document_context`, `video_context`, và `bctc_context`).

---

## 3. Các Giới Hạn & Giả Định (Caveats)

- **Môi trường Python Runtime**: Toàn bộ các gói phụ thuộc phục vụ Agentic Core và LangGraph được cài đặt trong môi trường ảo cục bộ `.venv` (Python 3.10/3.11). Khi chạy lệnh qua CLI phải dùng `.venv/bin/...`.
- **Nguồn tài nguyên PDF**: Hiện tại một số sách PDF ngoại văn được trích xuất từ Internet Archive qua `/learning/reader/stream` có dung lượng tương đối lớn (10MB–40MB). Cần cân nhắc giải pháp lazy loading từng trang hoặc chuyển sang Cloudflare R2 / S3 CDN khi triển khai quy mô lớn.
- **Dữ liệu BCTC**: Các mã cổ phiếu niêm yết trong `data/financials/cache` phản ánh dữ liệu lịch sử đến các quý gần nhất. Đối với mã mới hoặc kỳ báo cáo mới phát hành, hệ thống phụ thuộc vào việc gọi cập nhật qua `vnstock` hoặc tải lên BCTC thủ công.

---

## 4. Kết Luận (Conclusion)

- Kiến trúc Learn Hub hiện tại có nền tảng kiểm thử và bảo mật Socratic rất tốt (100% pass trên 40 automated tests), nhưng đang bị nghẽn bởi giao diện tab đơn lập, schema khóa học bị phẳng hóa, và sự chia cắt giữa giáo trình lý thuyết với dữ liệu BCTC thực chiến.
- Giải pháp tái thiết kế toàn diện theo 4 trụ cột đa định dạng (Ebook neo trang, Video đồng bộ mốc giây, Khóa học phân cấp 4 tầng, BCTC Case-study thực chiến) cùng giao diện Dual-Pane và AI Tutor Socratic Streaming là chuẩn xác, khả thi và đã có đầy đủ đặc tả chi tiết trong `analysis.md`.

---

## 5. Phương Pháp Kiểm Chứng Độc Lập (Verification Method)

Người nhận chuyển giao có thể kiểm chứng độc lập toàn bộ các kết luận trên bằng các bước:

1. **Kiểm tra trạng thái chạy của Test Suites hiện có**:
   ```bash
   cd "/Users/mac/Documents/Dự án Agent Tài chính"
   # Kiểm thử backend learning & ai tutor
   .venv/bin/pytest tests/test_learning.py tests/test_video_learning_agent.py tests/test_learning_agent_checkpoint.py tests/test_ai_tutor_learning.py -v
   # Kiểm thử frontend components & mock catalogs
   cd frontend && npm run test:unit
   ```
   *Điều kiện thành công*: Cả 2 bộ test đều thoát với mã 0, 100% test passed (20 tests backend, 20 tests frontend).

2. **Kiểm tra sự tồn tại của cache dữ liệu BCTC thực tế**:
   ```bash
   ls -la "/Users/mac/Documents/Dự án Agent Tài chính/data/financials/cache" | grep -E "FPT|HPG|VNM"
   ```
   *Điều kiện thành công*: Thấy các file `FPT.json`, `HPG.json`, `VNM.json` với dung lượng đầy đủ.

3. **Đối soát tài liệu đặc tả kiến trúc chi tiết**:
   - Mở và đọc `/Users/mac/Documents/Dự án Agent Tài chính/.agents/teamwork/explorer_survey_domain/analysis.md`.
   - Kiểm tra các phần DDL Relational (Mục 6.2), Pydantic Schemas (Mục 6.3), API Contracts (Mục 7), và Phased Roadmap (Mục 8).
