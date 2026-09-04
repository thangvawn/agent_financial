from __future__ import annotations

RESEARCH_CHECKLIST_PROMPT = """
## Nhiệm vụ
Lập danh mục câu hỏi và kiểm tra thẩm định (Research Checklist) cho {company} ({ticker}) kỳ {period}.

## Quy tắc bắt buộc
1. Dựa trên nguồn dữ liệu và các bước xử lý từ tool `bctc.trace_provenance`.
2. Đưa ra các câu hỏi trọng tâm giúp nhà nghiên cứu/sinh viên đào sâu vào thuyết minh BCTC.
3. KHÔNG đưa ra khuyến nghị đầu tư.

## Cấu trúc trả lời
1. **Thông tin báo cáo & Nguồn**: Kỳ báo cáo, ngày thu thập, phiên bản revision và tính cập nhật.
2. **Danh mục câu hỏi trọng tâm**: 3 - 5 câu hỏi then chốt cần làm rõ trong thuyết minh.
3. **Các khoản mục nhạy cảm cần đối chiếu chéo**: Ví dụ: nợ vay ngắn hạn, giao dịch bên liên quan.
4. **Tài liệu khuyến nghị đọc thêm**: Thuyết minh BCTC, Báo cáo thường niên, Nghị quyết ĐHĐCĐ.
"""

