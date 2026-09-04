from __future__ import annotations

NEXT_STEP_SYSTEM_PROMPT = """Bạn là Northstar Learning Journey Coach.
Nhiệm vụ: Tổng kết tiến trình học tập của học viên và đề xuất bài học tiếp theo tối ưu nhất theo lộ trình cá nhân hóa.

Quy tắc:
1. Nêu rõ tiến độ hiện tại (tỷ lệ hoàn thành, số bài đã học).
2. Trình bày bài học tiếp theo cùng lý do xác đáng (rationale).
3. Đưa ra lời khuyên thiết thực để duy trì thói quen học tập.
"""


def build_next_step_prompt(*, path_title: str, completion_pct: int, recommendations: list[dict[str, str]]) -> str:
    recs_fmt = "\n".join(f"{i+1}. **{r.get('title', '')}**: {r.get('rationale', '')}" for i, r in enumerate(recommendations))
    return f"""Lộ trình học tập: {path_title}
Tiến độ hiện tại: {completion_pct}%

Danh sách bài học đề xuất:
{recs_fmt}

Hãy tổng kết và đề xuất kế hoạch học tiếp theo cho học viên."""

