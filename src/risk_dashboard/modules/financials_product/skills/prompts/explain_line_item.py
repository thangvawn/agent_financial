from __future__ import annotations

EXPLAIN_LINE_ITEM_PROMPT = """
## Nhiệm vụ
Giải thích dòng mục "{line_item}" trong báo cáo {statement} của {company} ({ticker}) kỳ {period}.

## Quy tắc bắt buộc
1. Mọi con số PHẢI đến từ tool `bctc.resolve_line_item` hoặc `bctc.resolve_report`.
2. Phải kèm: report_id, revision_id, period, currency, unit, source, fetched_at.
3. KHÔNG đưa khuyến nghị giao dịch cổ phiếu.
4. KHÔNG tự tạo số liệu giả định.
5. Giải thích bằng tiếng Việt chuẩn mực sư phạm tài chính.

## Cấu trúc trả lời
1. **Định nghĩa**: Dòng mục này là gì theo chuẩn mực kế toán.
2. **Giá trị ghi nhận**: Con số + đơn vị + kỳ báo cáo + trích dẫn nguồn.
3. **Thành phần cấu thành**: Các khoản mục con (composition) nếu có.
4. **Lưu ý & Sai lầm thường gặp**: Caveats và limitations khi đọc hiểu chỉ tiêu.
5. **Câu hỏi tự kiểm tra**: Một câu hỏi ôn tập cho người học.
"""

