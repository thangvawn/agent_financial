from __future__ import annotations

EARNINGS_QUALITY_REVIEW_PROMPT = """
## Nhiệm vụ
Đánh giá chất lượng lợi nhuận (Quality of Earnings) cho {company} ({ticker}) kỳ {period}.

## Quy tắc bắt buộc
1. Mọi số liệu dẫn chứng PHẢI được trích xuất từ tool `bctc.build_evidence_table` và `bctc.calculate_ratio`.
2. Tách bạch rõ ràng giữa SỰ THẬT (Fact/Calculation) và NHẬN ĐỊNH (Interpretation).
3. Đánh giá mối tương quan giữa Lợi nhuận sau thuế và Dòng tiền thuần từ HĐKD (Operating Cash Flow).
4. KHÔNG đưa khuyến nghị giao dịch hoặc đầu tư cổ phiếu.

## Cấu trúc trả lời
1. **Bảng bằng chứng cốt lõi**: Doanh thu, Lợi nhuận gộp, LNST, Dòng tiền HĐKD (OCF).
2. **Đối chiếu Lợi nhuận vs Dòng tiền**: Tỷ lệ chuyển đổi LNST thành tiền mặt (OCF / Net Income).
3. **Biên lợi nhuận & Cơ cấu chi phí**: Đánh giá tính bền vững của các biên lợi nhuận.
4. **Các dấu hiệu cần lưu ý (Red Flags / Caveats)**: Khoản phải thu, tồn kho, thu nhập bất thường nếu có.
5. **Tổng kết chất lượng lợi nhuận**: Nhận định tổng quan mang tính sư phạm.
"""
