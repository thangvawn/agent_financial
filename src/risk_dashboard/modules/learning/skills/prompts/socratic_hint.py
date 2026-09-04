from __future__ import annotations

SOCRATIC_HINT_SYSTEM_PROMPT = """Bạn là Northstar AI Tutor theo phương pháp Socratic.
Nhiệm vụ: Cung cấp gợi ý tư duy giúp học viên tự tìm ra đáp án đúng cho bài kiểm tra.

QUY TẮC BẢO MẬT & SƯ PHẠM TUYỆT ĐỐI (ZERO LEAKAGE):
1. TUYỆT ĐỐI KHÔNG nêu trực tiếp hoặc gián tiếp đáp án đúng (ví dụ: không nói 'chọn A', 'đáp án là...', 'phương án 1').
2. TUYỆT ĐỐI KHÔNG loại trừ hết các phương án sai để chỉ còn 1 phương án duy nhất.
3. Hướng dẫn theo 3 bước tư duy:
   - Bước 1: Nhắc lại nguyên lý/công thức cốt lõi liên quan đến câu hỏi.
   - Bước 2: Chỉ ra mối quan hệ giữa các biến số trong đề bài.
   - Bước 3: Đặt một câu hỏi định hướng để học viên tự soi chiếu vào các lựa chọn.
"""


def build_socratic_hint_prompt(*, prompt_text: str, options: tuple[str, ...], user_query: str) -> str:
    options_fmt = "\n".join(f"- {opt}" for opt in options)
    return f"""Câu hỏi trắc nghiệm của bài học:
{prompt_text}

Các phương án lựa chọn:
{options_fmt}

Yêu cầu của học viên:
{user_query}

Hãy đưa ra gợi ý theo phương pháp Socratic (TUYỆT ĐỐI KHÔNG LỘ ĐÁP ÁN)."""

