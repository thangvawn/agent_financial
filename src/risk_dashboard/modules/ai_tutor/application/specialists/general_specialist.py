from __future__ import annotations

from typing import Any
from risk_dashboard.modules.ai_tutor.schemas.conversation import ToolCallRef


class GeneralSpecialist:
    async def handle(self, *, user_query: str) -> dict[str, Any]:
        answer = (
            "Chào anh, em là Northstar AI Tutor — trợ lý học tập và nghiên cứu tài chính định lượng.\n\n"
            "Em có thể hỗ trợ anh:\n"
            "- Giải thích các khái niệm, công thức và bài học trên **Learn Hub**.\n"
            "- Gợi ý phương pháp giải các câu hỏi trắc nghiệm (Socratic hint).\n"
            "- Tính toán và giải thích các chỉ số rủi ro định lượng như **VaR**, **CVaR**, **Monte Carlo**.\n\n"
            "Anh có thể chọn một bài học hoặc đặt câu hỏi cụ thể để em đồng hành cùng anh nhé!"
        )

        return {
            "answer": answer,
            "citations": (),
            "numeric_claims": (),
            "assumptions": (),
            "limitations": ("AI Tutor không cung cấp lời khuyên đầu tư cá nhân hóa hoặc khuyến nghị mua/bán cổ phiếu.",),
            "check_question": "Anh đang quan tâm đến chủ đề Định giá doanh nghiệp hay Quản trị rủi ro định lượng ạ?",
            "next_action": "Mở một bài học trên Learn Hub để bắt đầu trải nghiệm.",
            "tool_calls": (),
            "evidence": {},
        }

