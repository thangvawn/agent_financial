# Trạng thái dự án

**2026-10-31 · verified.** U01–U11 trong đợt dùng thử đã có bản sửa và kiểm chứng trên workspace; xem [báo cáo chi tiết và lệnh chạy lại](../qa/results/USAGE_FIXES_2026_10_31.md).

- Account ID từ backend là owner của API thị trường riêng và cache blueprint/bookmark/mock exam. Session chỉ là credential; revoke phải trả 401. Nguồn: `modules/market_portfolio/application/identity.py`, `shared/auth/accountContext.js`.
- Thiếu quote không được suy ra PnL; AST tính warmup và truyền trạng thái chưa xác định. Draft BCTC giữ base revision, khôi phục khi online và yêu cầu lựa chọn khi xung đột.
- Copilot là kiểm tra quy tắc cục bộ; chưa có AI provider. Cache legacy chưa xác định owner không tự gán. Các danh mục cũ có vốn riêng giữ tách biệt, chỉ đọc nếu không thể nhận an toàn vào danh mục chính.
- Verified: frontend 96 test, backend 78 test theo phạm vi, lint/build/CSS và browser được ghi trong báo cáo. Không phải kiểm chứng toàn bộ backend hay provider live; a11y chỉ là DOM smoke.
- Working tree còn công việc sẵn có và 116 mục stage của người dùng. Không stage/commit toàn bộ. Chưa push/deploy.

Đề xuất chưa triển khai: hợp đồng chất lượng dữ liệu chung, chart theo indicator của chiến lược, provider AI thật, thay fixture trong các widget prototype trước khi gắn route chính.
