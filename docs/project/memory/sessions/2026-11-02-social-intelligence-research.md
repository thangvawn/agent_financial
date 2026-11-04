# Social Intelligence — 02/11/2026

Status: **proposed**, nghiên cứu đã đối chiếu source; chưa triển khai/live-test.

Cập nhật cùng ngày: nội dung này là lịch sử trước triển khai; xem [session triển khai và bằng chứng hiện hành](2026-11-02-social-implementation.md).

- **Accepted:** người dùng yêu cầu nghiên cứu tổng hợp Social riêng, trả lời phạm vi “Kết hợp Việt Nam và quốc tế”.
- [Đặc tả và nguồn bằng chứng](../../engineering/specs/social-intelligence.md): route Social trong News, dữ liệu/worker riêng, adapter Agent-Reach có thể thay thế; YouTube VN/quốc tế và Reddit ở giai đoạn đầu, X sau probe, Facebook cần nghiên cứu thêm.
- **Verified by source inspection:** CLI upstream có JSON envelope; Facebook chỉ expose search/profile; YouTube search thiếu published_at, read chỉ có ngày, subtitle loại timestamp; Reddit read có thể ghép bình luận. Đây không phải kiểm chứng nguồn chạy thành công.
- **Verified by source inspection:** News GET có thể refresh trong lock/DB; clustering Jaccard tiêu đề, sentiment keyword, ticker regex. `impact.map_impact` lower-case trước regex chữ hoa; không thể dùng nguyên các đường này cho Social. Source là bằng chứng chính, không dựa vào số test lịch sử.
- **Proposed:** scope public/account xuyên suốt post/topic/brief/cache; định lượng dựa cohort quan sát được, có gate sampling/coverage/time precision và baseline. Các ngưỡng chưa được kiểm định; không quảng bá số mẫu search là mức quan tâm toàn thị trường.
- Lượt này chỉ thêm tài liệu nghiên cứu và cập nhật chỉ mục memory. Không cài dependency, đổi app, chạm DB, login, push/deploy. Không chạy test ứng dụng vì không thay runtime; kiểm tra liên kết local và whitespace tài liệu trước bàn giao.
- Kiểm chứng tài liệu: 3 file Markdown, 36 liên kết local đều tồn tại; không có whitespace cuối dòng hoặc code fence chưa đóng. `git diff --check` trên chỉ mục đạt.
- CodeGraph `explore` không được binary hỗ trợ; dùng source trực tiếp. Web đọc upstream main được, shell GitHub DNS thất bại; chưa có commit SHA, chưa chạy collector thật.
- Bước tiếp theo khi triển khai: S0 probe công khai trên môi trường riêng, ghi phiên bản/payload/lỗi thật, rồi S1 feed VN + quốc tế. Chưa có danh sách kênh cụ thể hoặc kết nối tài khoản được xác nhận.
