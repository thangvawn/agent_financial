import json
import logging
from typing import Any
from uuid import uuid4

from risk_dashboard.modules.agentic_core.application.tool_grants import resolve_grant
from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.ai_tutor.infrastructure.adapters.learning_adapter import (
    LearningLessonContextTool,
    LearningProgressTool,
    LearningQuizContextTool,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    NumericClaimRef,
    ToolCallRef,
)
from risk_dashboard.platform.ai_runtime.contracts import ModelMessage, ModelSettings, ModelTask
from risk_dashboard.platform.ai_runtime.factory import get_default_provider
from risk_dashboard.platform.ai_runtime.provider import LLMProvider

logger = logging.getLogger(__name__)


class LearningSpecialist:
    def __init__(
        self,
        lesson_tool: LearningLessonContextTool | None = None,
        quiz_tool: LearningQuizContextTool | None = None,
        progress_tool: LearningProgressTool | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self.lesson_tool = lesson_tool or LearningLessonContextTool()
        self.quiz_tool = quiz_tool or LearningQuizContextTool()
        self.progress_tool = progress_tool or LearningProgressTool()
        self.provider = provider

    def _get_provider(self) -> LLMProvider | None:
        if self.provider is not None:
            return self.provider
        try:
            return get_default_provider()
        except Exception:
            return None


    async def handle(
        self,
        *,
        intent: str,
        user_query: str,
        resource_id: str | None = None,
        envelope: TrustedExecutionEnvelope | None = None,
        grant: ToolGrant | None = None,
    ) -> dict[str, Any]:
        lowered = user_query.lower()
        tool_calls: list[ToolCallRef] = []
        citations: list[CitationRef] = []
        numeric_claims: list[NumericClaimRef] = []
        assumptions: list[str] = []
        limitations: list[str] = []

        is_quiz = "quiz" in lowered or "gợi ý" in lowered or "đáp án" in lowered or intent == "checkpoint"
        target_tool = self.quiz_tool if is_quiz else self.lesson_tool

        # Server-side tool grant resolution
        active_grant = grant
        if active_grant is None and envelope is not None:
            active_grant = resolve_grant(envelope, target_tool.manifest)

        if active_grant is None:
            return {
                "answer": "Chào anh, em đã tiếp nhận câu hỏi nhưng công cụ học tập chưa được cấp quyền thực thi theo chính sách bảo mật của Agentic Core.",
                "citations": (),
                "numeric_claims": (),
                "assumptions": (),
                "limitations": ("Công cụ truy xuất dữ liệu học tập bị từ chối do thiếu quyền ToolGrant.",),
                "check_question": "Anh có muốn thử lại sau khi cấp quyền không?",
                "next_action": "Kiểm tra quyền hạn người dùng hoặc thử lại.",
                "tool_calls": (
                    ToolCallRef(
                        tool_name=target_tool.manifest.tool_id,
                        status="error",
                        summary="Tool access not granted by Agentic Core policy",
                    ),
                ),
            }

        if is_quiz:
            # Socratic hint flow
            quiz_ev = await self.quiz_tool.execute(active_grant, quiz_id=resource_id)
            tool_calls.append(
                ToolCallRef(tool_name=self.quiz_tool.manifest.tool_id, status="success", summary="Đã lấy ngữ cảnh quiz")
            )
            citations.append(
                CitationRef(source_type="lesson", source_id="quiz_bank", label="Ngân hàng câu hỏi trắc nghiệm")
            )

            # Attempt Socratic generation via LLMProvider
            provider = self._get_provider()
            answer = None
            if provider is not None:
                try:
                    task = ModelTask(
                        task_type="ai_tutor_socratic_hint",
                        system_instructions_ref="ai_tutor_socratic_v1",
                        messages=(
                            ModelMessage(
                                role="system",
                                content=(
                                    "Bạn là AI Tutor tài chính của Northstar Finance Lab, hướng dẫn theo phương pháp Socratic. "
                                    "Xưng 'em', gọi người dùng là 'anh'. Hướng dẫn phương pháp tư duy và công thức, tuyệt đối không đưa ra đáp án trực tiếp."
                                ),
                            ),
                            ModelMessage(
                                role="user",
                                content=json.dumps({"question": user_query, "quiz_context": quiz_ev}, ensure_ascii=False),
                            ),
                        ),
                        settings=ModelSettings(temperature=0.3, response_format="text"),
                        correlation_id=envelope.run_id if envelope else f"tutor_{uuid4().hex[:8]}",
                        deadline_seconds=15.0,
                    )
                    res = await provider.generate(task)
                    if res and res.text:
                        answer = res.text
                except Exception as exc:
                    logger.warning("LLM Socratic hint generation failed, using deterministic template: %s", exc)

            if not answer:
                answer = (
                    "Chào anh, với câu hỏi này em xin gợi ý hướng tư duy theo các bước sau:\n\n"
                    "1. **Bản chất chỉ số:** ROE đo lường khả năng sinh lời trên mỗi đồng vốn cổ đông tự có (ROE = LNST / Vốn chủ sở hữu).\n"
                    "2. **So sánh tương đối:** Một mức ROE được coi là tốt khi vượt trội hơn chi phí sử dụng vốn (thường > 15% liên tục nhiều năm).\n"
                    "3. **Lưu ý cấu trúc tài chính:** Hãy xem xét liệu ROE cao có đến từ việc dùng đòn bẩy nợ quá mức hay từ biên lợi nhuận thuần thực chất.\n\n"
                    "Anh hãy thử đối chiếu các đáp án xem phương án nào nêu đúng nguyên lý này nhé!"
                )
            return {
                "answer": answer,
                "citations": tuple(citations),
                "numeric_claims": (),
                "evidence": quiz_ev,
                "assumptions": ("Giả định câu hỏi thuộc chuyên đề phân tích báo cáo tài chính.",),
                "limitations": ("Gợi ý phương pháp giải theo chuẩn Socratic, không cung cấp đáp án trực tiếp.",),
                "check_question": "Anh đã hiểu cách loại trừ phương án sai dựa trên công thức chưa?",
                "next_action": "Chọn đáp án phù hợp và hoàn thành bài kiểm tra.",
                "tool_calls": tuple(tool_calls),
            }

        # Standard lesson explanation flow
        lesson_ev = await self.lesson_tool.execute(active_grant, lesson_id=resource_id)
        tool_calls.append(
            ToolCallRef(
                tool_name=self.lesson_tool.manifest.tool_id, status="success", summary="Đã lấy ngữ cảnh giáo trình"
            )
        )
        citations.append(
            CitationRef(
                source_type="lesson",
                source_id=lesson_ev.get("lesson_id", "lesson_roe"),
                label=f"Bài học: {lesson_ev.get('lesson_title', 'Chỉ số ROE')}",
            )
        )

        # Attempt lesson explanation via LLMProvider
        provider = self._get_provider()
        answer = None
        if provider is not None:
            try:
                task = ModelTask(
                    task_type="ai_tutor_lesson_explanation",
                    system_instructions_ref="ai_tutor_learning_v1",
                    messages=(
                        ModelMessage(
                            role="system",
                            content=(
                                "Bạn là AI Tutor tài chính của Northstar Finance Lab. "
                                "Xưng 'em', gọi người dùng là 'anh'. Dựa vào ngữ cảnh bài học được cung cấp, hãy giải thích khái niệm, "
                                "ý nghĩa kinh tế và ví dụ thực tiễn một cách dễ hiểu, sư phạm. Không đưa ra khuyến nghị mua bán cổ phiếu."
                            ),
                        ),
                        ModelMessage(
                            role="user",
                            content=json.dumps({"question": user_query, "lesson_context": lesson_ev}, ensure_ascii=False),
                        ),
                    ),
                    settings=ModelSettings(temperature=0.3, response_format="text"),
                    correlation_id=envelope.run_id if envelope else f"tutor_{uuid4().hex[:8]}",
                    deadline_seconds=15.0,
                )
                res = await provider.generate(task)
                if res and res.text:
                    answer = res.text
            except Exception as exc:
                logger.warning("LLM Lesson explanation generation failed, using deterministic template: %s", exc)

        if not answer:
            answer = (
                f"Chào anh, em xin giải thích nội dung bài học **{lesson_ev.get('lesson_title', 'Chỉ số ROE')}**:\n\n"
                f"- **Tóm tắt:** {lesson_ev.get('summary', '')}\n"
                f"- **Ý nghĩa cốt lõi:** {lesson_ev.get('key_takeaway', '')}\n\n"
                "Chỉ số này giúp anh đánh giá xem doanh nghiệp sử dụng đồng vốn của cổ đông hiệu quả như thế nào qua các năm."
            )

        return {
            "answer": answer,
            "citations": tuple(citations),
            "numeric_claims": (),
            "evidence": lesson_ev,
            "assumptions": ("Áp dụng chuẩn mực kế toán tài chính doanh nghiệp hiện hành.",),
            "limitations": ("Cần kết hợp thêm biên độ lợi nhuận gộp và đòn bẩy tài chính để đánh giá toàn diện.",),
            "check_question": "Anh có muốn em làm rõ thêm về phương pháp phân tích DuPont 3 yếu tố không?",
            "next_action": "Thực hành tính toán với số liệu BCTC mẫu trong phần bài tập.",
            "tool_calls": tuple(tool_calls),
        }
