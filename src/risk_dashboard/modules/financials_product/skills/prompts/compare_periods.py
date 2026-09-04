from __future__ import annotations

COMPARE_PERIODS_PROMPT = """
## Nhiệm vụ
So sánh chỉ tiêu "{line_item}" của {company} ({ticker}) qua các kỳ: {periods}.

## Quy tắc bắt buộc
1. Mọi số liệu biến động và tăng trưởng PHẢI đến từ tool `bctc.compare_periods`.
2. Phải ghi rõ số tuyệt đối (VND) và tỷ lệ phần trăm (%).
3. Trích dẫn đầy đủ report_id, revision_id, nguồn dữ liệu.
4. KHÔNG đưa khuyến nghị giao dịch.
5. Giải thích nguyên nhân biến động dựa trên dữ liệu báo cáo.

## Cấu trúc trả lời
1. **Bảng so sánh kỳ**: Bảng tóm tắt các mốc thời gian và giá trị tương ứng.
2. **Biến động chính (YoY / QoQ)**: Mức tăng/giảm tuyệt đối và phần trăm.
3. **Động lực thúc đẩy**: Phân tích yếu tố đóng góp vào mức thay đổi.
4. **Giới hạn so sánh**: Lưu ý về tính mùa vụ hoặc thay đổi chuẩn mực/kỳ kế toán.
"""

