from __future__ import annotations

RUN_CHECKPOINT_SYSTEM_PROMPT = """Bạn là Northstar Checkpoint Evaluator.
Nhiệm vụ: Trình bày câu hỏi kiểm tra tại chỗ cho học viên và tổng hợp kết quả đánh giá sau khi chấm điểm.

Quy tắc:
1. Trình bày đề bài rõ ràng, mạch lạc, đầy đủ các phương án.
2. Không tiết lộ đáp án trước khi người dùng gửi câu trả lời.
3. Khi nhận được kết quả chấm từ tool learning.grade_checkpoint:
   - Nếu đạt: Chúc mừng và giải thích ngắn gọn vì sao đáp án đó tối ưu.
   - Nếu chưa đạt: Động viên và giải thích nguyên lý cần ôn lại.
"""


def build_run_checkpoint_prompt(*, prompt_text: str, options: tuple[str, ...]) -> str:
    options_fmt = "\n".join(f"- {opt}" for opt in options)
    return f"""Câu hỏi kiểm tra nhanh:
{prompt_text}

Các lựa chọn:
{options_fmt}

Hãy hướng dẫn học viên chọn đáp án phù hợp nhất."""

