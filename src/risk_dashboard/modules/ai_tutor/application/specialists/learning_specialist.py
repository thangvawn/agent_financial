from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from risk_dashboard.modules.agentic_core.application.tool_grants import resolve_grant
from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.ai_tutor.application.specialists.learning_templates import (
    build_lesson_explanation,
    build_socratic_hint,
    build_unauthorized_response,
    infer_resource_id,
    sanitize_socratic_leakage,
)
from risk_dashboard.modules.ai_tutor.infrastructure.adapters.learning_adapter import (
    LearningLessonContextTool,
    LearningProgressTool,
    LearningQuizContextTool,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import CitationRef, ToolCallRef
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
        target_res = resource_id or infer_resource_id(user_query)

        is_quiz = "quiz" in lowered or "gợi ý" in lowered or "đáp án" in lowered or intent == "checkpoint"
        target_tool = self.quiz_tool if is_quiz else self.lesson_tool

        active_grant = grant
        if active_grant is None and envelope is not None:
            active_grant = resolve_grant(envelope, target_tool.manifest)

        if active_grant is None:
            return build_unauthorized_response(target_tool.manifest.tool_id)

        if is_quiz:
            quiz_ev = await self.quiz_tool.execute(active_grant, quiz_id=target_res)
            tool_calls.append(
                ToolCallRef(tool_name=self.quiz_tool.manifest.tool_id, status="success", summary="Đã lấy ngữ cảnh quiz")
            )
            citations.append(
                CitationRef(source_type="lesson", source_id="quiz_bank", label="Ngân hàng câu hỏi trắc nghiệm")
            )

            prompt_text = quiz_ev.get("question_prompt", "Câu hỏi kiểm tra kiến thức")
            hint = quiz_ev.get("hint_guidance", "Xem xét lại nguyên lý cốt lõi và các công thức liên quan.")

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
                    logger.warning("LLM Socratic hint generation failed, using dynamic template: %s", exc)

            if not answer:
                answer = build_socratic_hint(prompt_text, hint)

            answer = sanitize_socratic_leakage(answer, prompt_text, hint)

            return {
                "answer": answer,
                "citations": tuple(citations),
                "numeric_claims": (),
                "evidence": quiz_ev,
                "assumptions": ("Giả định câu hỏi thuộc chuyên đề phân tích tài chính và kiến thức đầu tư.",),
                "limitations": ("Gợi ý phương pháp giải theo chuẩn Socratic, tuyệt đối không cung cấp đáp án trực tiếp.",),
                "check_question": "Anh đã nắm được hướng loại trừ phương án sai dựa trên gợi ý chưa?",
                "next_action": "Suy luận và chọn đáp án phù hợp để hoàn thành bài kiểm tra.",
                "tool_calls": tuple(tool_calls),
            }

        # Lesson explanation flow
        lesson_ev = await self.lesson_tool.execute(active_grant, lesson_id=target_res)
        tool_calls.append(
            ToolCallRef(
                tool_name=self.lesson_tool.manifest.tool_id, status="success", summary="Đã lấy ngữ cảnh giáo trình"
            )
        )
        title = lesson_ev.get("lesson_title") or "Bài học tài chính"
        lesson_id = lesson_ev.get("lesson_id", "lesson_general")
        citations.append(CitationRef(source_type="lesson", source_id=lesson_id, label=f"Bài học: {title}"))

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
                                "Bạn là AI Tutor tài chính cao cấp của Northstar Finance Lab.\n"
                                "Quy tắc ứng xử và phong cách sư phạm:\n"
                                "1. Xưng hô: Bắt buộc xưng 'em' và gọi người dùng là 'anh'.\n"
                                "2. Trực diện & bám sát bài học: BẮT BUỘC trả lời trực tiếp câu hỏi dựa trên đúng bài học hiện tại trong `lesson_context`. Tuyệt đối không tự ý chuyển sang chỉ số hoặc chủ đề khác (như ROE, P/E...) nếu bài học không đề cập đến.\n"
                                "3. Về công thức tài chính: Nếu bài học có công thức định lượng (như Lãi kép, P/E, Định giá), hãy phân tích công thức đó. Nếu bài học thuộc nhóm nền tảng kinh tế/tư duy (như Máy kinh tế của Ray Dalio, Quản lý tiền, Dòng tiền), hãy chỉ rõ: bài học tập trung vào nguyên lý vận hành vĩ mô/tư duy, và phân tích phương trình nguyên lý/quy tắc cốt lõi tương ứng (ví dụ: Dòng tiền ròng = Thu nhập - Chi phí, Chi tiêu của người này là thu nhập của người khác, Chu kỳ tín dụng).\n"
                                "4. Cấu trúc trình bày cô đọng, sư phạm:\n"
                                "   - Mục 1: Nguyên lý / Công thức cốt lõi của bài học (trình bày công thức trong khối $$ ... $$ nếu có).\n"
                                "   - Mục 2: Ý nghĩa tài chính và bài học thực tế.\n"
                                "   - Mục 3: Gợi ý áp dụng nhanh cho nhà đầu tư.\n"
                                "5. Độ dài & Tốc độ: Trình bày súc tích, đi thẳng vào trọng tâm trong khoảng 350-500 từ, không dùng lời chào hỏi rườm rà."
                            ),
                        ),
                        ModelMessage(
                            role="user",
                            content=json.dumps({"question": user_query, "lesson_context": lesson_ev}, ensure_ascii=False),
                        ),
                    ),
                    settings=ModelSettings(temperature=0.2, max_output_tokens=700, response_format="text"),
                    correlation_id=envelope.run_id if envelope else f"tutor_{uuid4().hex[:8]}",
                    deadline_seconds=15.0,
                )
                res = await provider.generate(task)
                if res and res.text:
                    answer = res.text
            except Exception as exc:
                logger.warning("LLM Lesson explanation generation failed, using dynamic template: %s", exc)

        if not answer:
            answer = build_lesson_explanation(lesson_ev)

        check_q = (
            "Anh có muốn em làm rõ thêm về sự khác biệt giữa CFO và LNST không?"
            if ("cfo" in title.lower() or "dòng tiền" in title.lower())
            else f"Anh có muốn em làm rõ thêm nội dung bài học {title} không?"
        )

        return {
            "answer": answer,
            "citations": tuple(citations),
            "numeric_claims": (),
            "evidence": lesson_ev,
            "assumptions": ("Áp dụng nguyên lý và chuẩn mực tài chính kế toán hiện hành.",),
            "limitations": ("Cần kết hợp phân tích đa chiều các chỉ số định tính và định lượng để đánh giá toàn diện.",),
            "check_question": check_q,
            "next_action": "Thực hành áp dụng kiến thức vào phân tích số liệu thực tế.",
            "tool_calls": tuple(tool_calls),
        }
