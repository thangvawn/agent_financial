from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from risk_dashboard.platform.ai_runtime.contracts import ModelMessage, ModelSettings, ModelTask
from risk_dashboard.platform.ai_runtime.factory import get_default_provider
from risk_dashboard.platform.ai_runtime.provider import LLMProvider

logger = logging.getLogger(__name__)


class GeneralSpecialist:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider

    def _get_provider(self) -> LLMProvider | None:
        if self.provider is not None:
            return self.provider
        try:
            return get_default_provider()
        except Exception:
            return None

    async def handle(self, *, user_query: str) -> dict[str, Any]:
        default_answer = (
            "Chào anh, em là Northstar AI Tutor — trợ lý học tập và nghiên cứu tài chính định lượng.\n\n"
            "Em có thể hỗ trợ anh:\n"
            "- Giải thích các khái niệm, công thức và bài học trên **Learn Hub**.\n"
            "- Gợi ý phương pháp giải các câu hỏi trắc nghiệm (Socratic hint).\n"
            "- Tính toán và giải thích các chỉ số rủi ro định lượng như **VaR**, **CVaR**, **Monte Carlo**.\n\n"
            "Anh có thể chọn một bài học hoặc đặt câu hỏi cụ thể để em đồng hành cùng anh nhé!"
        )

        provider = self._get_provider()
        answer = None
        if provider is not None:
            try:
                task = ModelTask(
                    task_type="ai_tutor_general_qa",
                    system_instructions_ref="ai_tutor_general_v1",
                    messages=(
                        ModelMessage(
                            role="system",
                            content=(
                                "Bạn là Northstar AI Tutor — trợ lý gia sư học tập và nghiên cứu tài chính thông minh của Northstar Finance Lab. "
                                "Quy chuẩn giao tiếp: Luôn xưng 'em' và gọi người dùng là 'anh'. "
                                "Nhiệm vụ: Trả lời câu hỏi của người dùng một cách sư phạm, dễ hiểu, trực quan, có ví dụ thực tế minh họa. "
                                "Nếu câu hỏi về khái niệm tài chính (như P/E, ROE, dòng tiền, lạm phát, lãi suất kép, quản lý ngân sách...), hãy phân tích cặn kẽ bản chất kinh tế và ứng dụng thực tiễn. "
                                "Tuyệt đối không đưa ra khuyến nghị mua bán cổ phiếu cụ thể hay cam kết lợi nhuận."
                            ),
                        ),
                        ModelMessage(
                            role="user",
                            content=user_query,
                        ),
                    ),
                    settings=ModelSettings(temperature=0.4, response_format="text"),
                    correlation_id=f"tutor_{uuid4().hex[:8]}",
                    deadline_seconds=20.0,
                )
                res = await provider.generate(task)
                if res and res.text:
                    answer = res.text
            except Exception as exc:
                logger.warning("LLM general QA generation failed, falling back to static prompt: %s", exc)

        if not answer:
            answer = default_answer

        return {
            "answer": answer,
            "citations": (),
            "numeric_claims": (),
            "assumptions": (),
            "limitations": ("AI Tutor không cung cấp lời khuyên đầu tư cá nhân hóa hoặc khuyến nghị mua/bán cổ phiếu.",),
            "check_question": "Anh có cần em lấy thêm ví dụ cụ thể hoặc giải thích sâu hơn về phần nào không ạ?",
            "next_action": "Anh có thể tiếp tục hỏi hoặc chọn một bài học trên Learn Hub để luyện tập.",
            "tool_calls": (),
            "evidence": {},
        }

