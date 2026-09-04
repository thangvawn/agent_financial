from __future__ import annotations

RATIO_WALKTHROUGH_PROMPT = """
## Nhiệm vụ
Hướng dẫn tính toán từng bước chỉ số tài chính "{formula_name}" ({formula_id}) cho {company} ({ticker}) kỳ {period}.

## Quy tắc bắt buộc
1. Công thức và kết quả tính toán PHẢI đến từ tool `bctc.calculate_ratio`.
2. Trình bày rõ công thức tổng quát, phép thay số cụ thể và đơn vị đo lường (%, lần, ngày).
3. Đính kèm trích dẫn nguồn số liệu đầu vào (inputs provenance).
4. KHÔNG đưa khuyến nghị giao dịch.

## Cấu trúc trả lời
1. **Khái niệm & Ý nghĩa**: Chỉ số đo lường khía cạnh tài chính nào.
2. **Công thức chuẩn**: Biểu thức toán học theo registry approved.
3. **Phép thế số cụ thể**: Tử số / Mẫu số lấy từ báo cáo kỳ {period}.
4. **Kết quả & Đơn vị**: Con số tính toán chính xác kèm đơn vị.
5. **Ý nghĩa kinh tế & Giới hạn**: Cách diễn giải kết quả và các điểm cần thận trọng.
"""

