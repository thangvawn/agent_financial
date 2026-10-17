# Original User Request

## 2026-10-10T11:03:01Z

Nghiên cứu rà soát toàn diện các tính năng hiện tại của hệ thống Agent Tài chính để phát hiện các lỗ hổng/bottleneck về hiệu năng và kiến trúc, đồng thời tái thiết kế hoàn chỉnh phân hệ Tab Learn thành một nền tảng quản trị và lưu trữ học liệu tài chính đa định dạng (Sách/PDF, Video bài giảng kèm AI Summary & Timestamps, Khóa học phân cấp, BCTC Case-study thực chiến).

Working directory: /Users/mac/Documents/Dự án Agent Tài chính
Integrity mode: demo

## Requirements

### R1. Toàn diện hóa Audit hệ thống hiện tại
Thực hiện rà soát chuyên sâu toàn bộ codebase hiện tại (Frontend React và Backend Python/FastAPI), tập trung vào:
- Các điểm nghẽn hiệu năng, memory leak, re-render lặp, quản lý state và bất đồng bộ.
- Sự nhất quán giữa Backend API contract, schema Pydantic và Frontend services/hooks.
- Độ phủ và tình trạng chạy của các test suite liên quan (`tests/test_learning*.py`, `tests/test_ai_tutor*.py`, `frontend/src/__tests__`).
- Lập báo cáo kiểm toán chi tiết chỉ rõ nguyên nhân gốc rễ (root cause) và mức độ rủi ro (Critical/High/Medium/Low).

### R2. Tái thiết kế kiến trúc Tab Learn & Kho nguồn học liệu đa định dạng
Thiết kế lại toàn diện kiến trúc phân hệ Tab Learn (Learn Hub) để tối ưu hóa việc quản lý, lưu trữ và tương tác với các nguồn học liệu tài chính:
- Mô hình dữ liệu (Data Schema/ERD) lưu trữ đa định dạng: Sách/PDF, Video phân đoạn có timestamps/AI key takeaway, Khóa học nhiều module/checkpoint, và BCTC case-study.
- Cơ chế quản lý metadata, gắn thẻ (taxonomy/tagging), phân cấp độ (difficulty levels) và liên kết chéo với các mã cổ phiếu/dữ liệu thực tế.
- Luồng tích hợp với AI Tutor / Agentic Learning sẵn có để hỗ trợ hỏi đáp ngữ cảnh, gợi ý socratic và tóm tắt học liệu.

### R3. Bộ đặc tả kỹ thuật và Kế hoạch triển khai (Implementation Blueprint)
Cung cấp bộ tài liệu đặc tả đầy đủ phục vụ chuyển giao và thực thi:
- Đặc tả API REST/Streaming (Endpoints, Request/Response payload, Cache policy).
- Thiết kế luồng giao diện người dùng (Component hierarchy, Layout chia đôi tài liệu/video và trợ lý AI, State management machine).
- Kế hoạch triển khai phân đoạn (Phased migration roadmap) đảm bảo tương thích ngược với dữ liệu và test suite hiện hữu.

## Acceptance Criteria

### Audit & Phát hiện vấn đề
- [ ] Báo cáo kiểm toán bao quát ít nhất 3 khía cạnh: Lỗi logic/bất đồng bộ, Hiệu năng frontend/backend, và Lỗ hổng kiểm thử/schema drift.
- [ ] Mọi vấn đề được liệt kê đều có trích dẫn mã nguồn cụ thể (đường dẫn file, phạm vi dòng) kèm bằng chứng thực chứng.
- [ ] Chạy và đối chiếu toàn bộ các bộ kiểm thử tự động hiện có của phân hệ Learn Hub (`pytest tests/test_learning*.py`, `npm test` trong frontend) để báo cáo trạng thái pass/fail thực tế.

### Thiết kế kiến trúc Learn Hub mới
- [ ] Bản thiết kế dữ liệu (Schema definition) hỗ trợ đầy đủ 4 dạng học liệu chính: Ebook/PDF, Video timestamps, Khóa học phân cấp, BCTC case-study.
- [ ] Sơ đồ luồng dữ liệu (Data flow) và đặc tả API contracts rõ ràng giữa Learn Hub UI và AI Tutor/Services.
- [ ] Cấu trúc thành phần UI (Component Architecture) tuân thủ giới hạn mô-đun hóa, phân tách rành mạch giữa Reader/Player và AI Companion.
- [ ] Lộ trình triển khai (Roadmap) có chia nhỏ thành các nhiệm vụ độc lập, có thể kiểm thử tự động từng phần (Tracer bullet approach).
