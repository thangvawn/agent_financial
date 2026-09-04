from __future__ import annotations

import re
from typing import Literal

FORBIDDEN_FINANCIAL_PATTERNS = (
    r"\b(mua ngay|bán ngay|chắc chắn lãi|cam kết lợi nhuận|khuyến nghị mua|khuyến nghị bán|tất tay|all in|target giá)\b",
)


def contains_investment_advice(text: str) -> bool:
    lowered = text.lower()
    for pattern in FORBIDDEN_FINANCIAL_PATTERNS:
        if re.search(pattern, lowered):
            return True
    return False


def sanitize_conversation_input(content: str) -> str:
    # Strip dangerous HTML and prompt injection markers
    cleaned = content.replace("<script>", "").replace("</script>", "")
    cleaned = cleaned.replace("system:", "").replace("assistant:", "")
    return cleaned.strip()


def check_hint_leakage(hint_text: str, answer_keys: tuple[str, ...]) -> bool:
    """Returns True if the hint leaks any answer key explicitly."""
    lowered = hint_text.lower()
    for key in answer_keys:
        if not key:
            continue
        # Exact match or obvious leak like 'đáp án là A' or exact answer text
        if key.lower() in lowered:
            return True
    return False


def format_pedagogical_disclaimer(surface: str) -> str:
    if surface == "quant":
        return "Thông tin tính toán định lượng và quản trị rủi ro chỉ phục vụ mục đích nghiên cứu & học tập."
    return "Nội dung mang tính chất giáo dục và giải thích kiến thức tài chính."

