# Bỏ thanh nhãn tài liệu

- Date: 2026-10-31. Status: **verified**.
- Request: bỏ luôn thanh “PDF toàn văn / Đọc được”.
- Change: bỏ toàn bộ heading trong BookDocumentPane, state/callback chỉ phục vụ badge và CSS tương ứng. PDF bắt đầu ngay đầu khung; loading/error/retry và sổ ghi chú vẫn hoạt động. Thay thế trạng thái giữ nhãn trong session reader-without-summary.
- Verification: 145 frontend unit, ESLint, CSS50 và build đạt. Chromium desktop/mobile: PDF có signature đúng, top gap chỉ 1px viền, không tràn ngang; ghi chú lưu/khôi phục; retry phục hồi sau lỗi tải. [Evidence](../../../../output/playwright/reader-no-header/evidence.json), [ảnh](../../../../output/playwright/reader-no-header/reader-top.png), [logs](../../../../output/qa/reader-no-header/).
- QA dùng DB/build tạm; staging giữ nguyên; chưa deploy. Không sửa các lỗi logic đã ghi nhận ở lượt review trước.
