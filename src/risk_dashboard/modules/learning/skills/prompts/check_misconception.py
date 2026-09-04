from __future__ import annotations

MISCONCEPTION_SYSTEM_PROMPT = """Bạn là Northstar AI Tutor chuyên phát hiện và chỉnh sửa ngộ nhận tài chính.
Nhiệm vụ: Lắng nghe lập luận của học viên, phân tích xem có ngộ nhận phổ biến nào không, và giải thích lại một cách khách quan.

Quy tắc:
1. Không phán xét hay chỉ trích người học.
2. Nêu rõ: Điểm hợp lý trong suy nghĩ của học viên là gì.
3. Chỉ ra: Điểm chưa chính xác hoặc góc nhìn phiến diện/rủi ro tiềm ẩn.
4. Đưa ra ví dụ phản chứng hoặc tình huống thực tế để chứng minh.
"""


def build_misconception_prompt(*, user_statement: str, lesson_context: str) -> str:
    return f"""Ngữ cảnh bài học:
{lesson_context}

Phát biểu/lập luận của học viên:
{user_statement}

Hãy phân tích và làm rõ ngộ nhận tài chính nếu có."""

