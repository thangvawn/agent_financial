from __future__ import annotations

from dataclasses import replace
import os
import re
from time import perf_counter

from risk_dashboard.modules.analytics_monitoring.application.emitter import emit_ops_event
from risk_dashboard.modules.ai_assistant.adapters.llm_agent import AIAgentRuntime
from risk_dashboard.modules.ai_assistant.domain.entities import (
    AssistantConversationSession,
    AssistantEventLog,
    AssistantFeedback,
    AssistantMessage,
    AssistantReply,
    utc_now_iso,
)
from risk_dashboard.modules.ai_assistant.domain.policies import (
    POLICY_VERSION,
    PROMPT_VERSION,
    ROLE_ANALYST,
    ROLE_COACH,
    ROLE_PRO_ASSISTANT,
    ROLE_TUTOR,
    build_guardrails,
)
from risk_dashboard.modules.ai_assistant.domain.ports import AssistantConversationRepository
from risk_dashboard.modules.ai_assistant.infrastructure.repositories.sqlite import (
    new_conversation_id,
    new_event_id,
    new_feedback_id,
    new_message_id,
)
from risk_dashboard.modules.ai_assistant.orchestration.context_builder import AssistantContextBuilder
from risk_dashboard.modules.ai_assistant.orchestration.response_composer import AssistantResponseComposer
from risk_dashboard.modules.ai_assistant.policies.intent_router import IntentRouter
from risk_dashboard.modules.ai_assistant.policies.mode_router import ModeRouter
from risk_dashboard.modules.ai_assistant.prompts.registry import get_prompt_policy
from risk_dashboard.modules.ai_assistant.safety.safety_gate import AssistantSafetyGate
from risk_dashboard.modules.ai_assistant.schemas.responses import AssistantFeedbackResponse, AssistantRespondResponse
from risk_dashboard.modules.financial_health.domain.policies import build_coach_reply
from risk_dashboard.modules.financial_health.infrastructure.repositories.sqlite import SqliteFinancialHealthSnapshotRepository
from risk_dashboard.modules.guided_investing.application.services import GetGuidedEligibility, GetGuidedMarketContext
from risk_dashboard.modules.guided_investing.domain.policies import build_safe_reply
from risk_dashboard.modules.learning.domain.policies import build_coach_nudge, build_tutor_reply
from risk_dashboard.modules.learning.infrastructure.catalog_reader import SqliteLearningCatalog
from risk_dashboard.modules.learning.infrastructure.repositories.sqlite import SqliteLearningHomeRepository
from risk_dashboard.modules.pro_lab.application.services import GetProLabWorkspace
from risk_dashboard.modules.pro_lab.infrastructure.repositories.sqlite import (
    SqliteProLabBlueprintRepository,
    SqliteProLabExperimentRepository,
)
from risk_dashboard.modules.trust_safety.application.services import TrustSafetyService


class RespondWithAssistant:
    def __init__(self, conversations: AssistantConversationRepository) -> None:
        self.conversations = conversations
        self.context_builder = AssistantContextBuilder()
        self.intent_router = IntentRouter()
        self.mode_router = ModeRouter()
        self.safety_gate = AssistantSafetyGate()
        self.response_composer = AssistantResponseComposer()
        self.agent_runtime = AIAgentRuntime()
        self.trust = TrustSafetyService()

    def execute(
        self,
        *,
        session_id: str,
        surface: str,
        prompt: str,
        role_hint: str | None = None,
        lesson_id: str | None = None,
        trigger: str | None = None,
        focus: str | None = None,
        knowledge_level: str | None = None,
        conversation_id: str | None = None,
        has_pro_scope: bool = False,
    ) -> AssistantRespondResponse:
        started = perf_counter()
        conv_id = conversation_id or new_conversation_id()
        history = self.conversations.list_recent_messages(conversation_id=conversation_id, limit=8) if conversation_id else ()
        context_pack = self.context_builder.build(session_id=session_id, surface=surface)
        context = context_pack.compact_context
        intent_decision = self.intent_router.classify(prompt=prompt, surface=surface, trigger=trigger)
        trust_review = self.trust.analyze_text(surface=surface, text=prompt)
        safety_decision = self.safety_gate.evaluate(
            intent=intent_decision,
            trust_risk_classes=tuple(trust_review.risk_classes),
            surface=surface,
        )
        risk_labels = _normalize_risk_labels(safety_decision.risk_labels)
        mode_decision = self.mode_router.resolve(
            surface=surface,
            intent=intent_decision,
            role_hint=role_hint,
            has_pro_scope=has_pro_scope,
        )
        role = mode_decision.role
        prompt_policy = get_prompt_policy(role)
        base_guardrails = build_guardrails(role=role, risk_labels=risk_labels, surface=surface)
        guardrails = self.trust.build_guardrails(
            surface=surface,
            role=role,
            risk_classes=risk_labels,
            existing_guardrails=base_guardrails,
        )
        reply = self._build_reply(
            session_id=session_id,
            surface=surface,
            prompt=prompt,
            role=role,
            lesson_id=lesson_id,
            trigger=trigger,
            focus=focus,
            knowledge_level=knowledge_level or str(context.get("knowledge_level") or "beginner"),
            context=context,
            risk_labels=risk_labels,
            guardrails=guardrails,
        )
        reply = self.agent_runtime.compose(
            draft=reply,
            user_prompt=prompt or trigger or focus or "",
            surface=surface,
            context=context,
            history=history,
            prompt_policy=prompt_policy,
            guardrails=guardrails,
        )
        if risk_labels and not reply.risk_labels:
            reply = replace(reply, risk_labels=risk_labels)
        structured_payload = self.response_composer.compose(
            reply=reply,
            intent=intent_decision,
            mode=mode_decision,
            context=context_pack,
            safety=safety_decision,
        )

        session = AssistantConversationSession(
            conversation_id=conv_id,
            user_id=session_id,
            role=reply.role,
            surface=surface,
            context={
                **context,
                "intent_decision": {
                    "intent": intent_decision.intent,
                    "confidence": intent_decision.confidence,
                    "reason": intent_decision.reason,
                    "needs_clarification": intent_decision.needs_clarification,
                },
                "mode_decision": {
                    "role": mode_decision.role,
                    "confidence": mode_decision.confidence,
                    "reason": mode_decision.reason,
                    "allowed_tools": list(mode_decision.allowed_tools),
                },
                "prompt_policy": {
                    "version": prompt_policy.version,
                    "system_rule": prompt_policy.system_rule,
                    "output_rule": prompt_policy.output_rule,
                },
                "missing_context": list(context_pack.missing_context),
            },
            prompt_version=prompt_policy.version or PROMPT_VERSION,
            policy_version=POLICY_VERSION,
            updated_at=utc_now_iso(),
        )
        if conversation_id:
            existing = self.conversations.get_session(conversation_id=conversation_id)
            if existing is not None:
                session = replace(existing, role=reply.role, surface=surface, context=context, updated_at=utc_now_iso())
        self.conversations.save_session(session)

        user_message = AssistantMessage(
            message_id=new_message_id(),
            conversation_id=conv_id,
            sender="user",
            content=prompt or trigger or focus or role,
            classified_intent=intent_decision.intent,
            risk_labels=risk_labels,
            structured_output={
                "surface": surface,
                "role_hint": role_hint,
                "lesson_id": lesson_id,
                "trigger": trigger,
                "focus": focus,
                "intent_confidence": intent_decision.confidence,
                "intent_reason": intent_decision.reason,
                "prompt_policy_version": prompt_policy.version,
            },
        )
        self.conversations.save_message(user_message)
        assistant_message = AssistantMessage(
            message_id=new_message_id(),
            conversation_id=conv_id,
            sender="assistant",
            content=reply.explanation,
            classified_intent=intent_decision.intent,
            risk_labels=reply.risk_labels,
            structured_output={
                "title": reply.title,
                "summary": reply.summary,
                "next_step": reply.next_step,
                "cta_path": reply.cta_path,
                "linked_lesson_id": reply.linked_lesson_id,
                "mode_used": structured_payload.mode_used,
                "intent": structured_payload.intent,
                "confidence_label": structured_payload.confidence_label,
                "data_freshness": structured_payload.data_freshness,
                "warnings": list(structured_payload.warnings),
                "next_actions": [action.__dict__ for action in structured_payload.next_actions],
                "sources": [source.__dict__ for source in structured_payload.sources],
                "response_blocks": list(structured_payload.response_blocks),
            },
        )
        self.conversations.save_message(assistant_message)
        self.conversations.save_event(
            AssistantEventLog(
                event_id=new_event_id(),
                conversation_id=conv_id,
                role=reply.role,
                surface=surface,
                intent=intent_decision.intent,
                route_decision=reply.route_decision,
                guardrail_triggered=bool(risk_labels),
                tool_calls=mode_decision.allowed_tools,
                latency_ms=round((perf_counter() - started) * 1000),
            )
        )
        self.trust.record_audit(
            actor_id=session_id,
            surface=surface,
            topic=reply.role,
            channel="ai_output",
            risk_classes=reply.risk_labels,
            route_decision=reply.route_decision,
            input_summary=prompt or trigger or focus,
            output_summary=reply.summary,
            guardrails=structured_payload.warnings,
            confidence_label=structured_payload.confidence_label,
            escalation_action=trust_review.action if trust_review.action != "allow" else None,
        )
        emit_ops_event(
            event_name="ops_model_call_logged",
            module="ai_assistant",
            surface=surface,
            properties={
                "role": reply.role,
                "intent": intent_decision.intent,
                "intent_confidence": intent_decision.confidence,
                "success": True,
                "latency_ms": round((perf_counter() - started) * 1000),
                "route_decision": reply.route_decision,
                "mode_reason": mode_decision.reason,
                "agent_runtime_enabled": self.agent_runtime.enabled,
                "agent_model_configured": bool(os.getenv("OPENAI_API_KEY")),
                "agent_model": self.agent_runtime.model_name if os.getenv("OPENAI_API_KEY") else None,
            },
        )

        return AssistantRespondResponse(
            conversation_id=conv_id,
            message_id=assistant_message.message_id,
            role=reply.role,
            surface=surface,
            allowed=reply.allowed,
            route_decision=reply.route_decision,
            title=reply.title,
            summary=reply.summary,
            explanation=reply.explanation,
            next_step=reply.next_step,
            cta_path=reply.cta_path,
            confidence_note=reply.confidence_note,
            guardrails=list(reply.guardrails),
            risk_labels=list(reply.risk_labels),
            check_question=reply.check_question,
            linked_lesson_id=reply.linked_lesson_id,
            mode_used=structured_payload.mode_used,
            intent=structured_payload.intent,
            intent_confidence=structured_payload.intent_confidence,
            confidence_label=structured_payload.confidence_label,
            data_freshness=structured_payload.data_freshness,
            warnings=list(structured_payload.warnings),
            next_actions=[action.__dict__ for action in structured_payload.next_actions],
            suggested_modules=list(structured_payload.suggested_modules),
            learning_suggestions=list(structured_payload.learning_suggestions),
            sources=[source.__dict__ for source in structured_payload.sources],
            response_blocks=list(structured_payload.response_blocks),
        )

    def _build_reply(
        self,
        *,
        session_id: str,
        surface: str,
        prompt: str,
        role: str,
        lesson_id: str | None,
        trigger: str | None,
        focus: str | None,
        knowledge_level: str,
        context: dict[str, object],
        risk_labels: tuple[str, ...],
        guardrails: tuple[str, ...],
    ) -> AssistantReply:
        if _is_greeting_prompt(prompt):
            return AssistantReply(
                role=role,
                allowed=True,
                route_decision="greeted_user",
                title="Chào bạn",
                summary="Mình đang sẵn sàng hỗ trợ bạn trong sản phẩm.",
                explanation=(
                    "Bạn có thể hỏi mình giải thích khái niệm tài chính, đọc một insight, xem bước tiếp theo trong app, "
                    "hoặc hướng dẫn cách dùng Financial Health, Goals, Learn Hub và Guided Investing."
                ),
                next_step="Hỏi một câu cụ thể hoặc chọn một gợi ý nhanh bên dưới.",
                cta_path="",
                guardrails=guardrails,
                confidence_note="Đây là phản hồi chào hỏi, chưa dùng dữ liệu cá nhân hay dữ liệu thị trường.",
            )
        if "pii_or_privacy_issue" in risk_labels:
            return AssistantReply(
                role=role,
                allowed=False,
                route_decision="blocked_for_privacy",
                title="Có dấu hiệu lộ thông tin nhạy cảm.",
                summary="Hệ thống sẽ không tiếp tục trên nội dung chứa số tài khoản, OTP, CCCD hoặc dữ liệu nhận diện nhạy cảm.",
                explanation="Hãy xóa thông tin nhận diện hoặc dữ liệu tài chính riêng tư, rồi hỏi lại theo dạng khái quát hơn.",
                next_step="Quay lại câu hỏi nhưng bỏ toàn bộ dữ liệu nhạy cảm.",
                cta_path="/home",
                guardrails=guardrails,
                confidence_note="Trust layer ưu tiên bảo vệ dữ liệu riêng tư trước khi tiếp tục bất kỳ giải thích nào.",
                risk_labels=risk_labels,
            )
        if "scam_or_pump" in risk_labels:
            return AssistantReply(
                role=role,
                allowed=False,
                route_decision="blocked_for_safety",
                title="Nội dung có dấu hiệu thao túng hoặc lôi kéo.",
                summary="Hệ thống không hỗ trợ nội dung spam, guaranteed return hoặc room kéo người dùng ra ngoài.",
                explanation="Bạn có thể quay lại học về risk, market context hoặc đọc cảnh báo scam để tự bảo vệ mình tốt hơn.",
                next_step="Quay lại Learn Hub hoặc đọc explanation an toàn hơn.",
                cta_path="/learn",
                guardrails=guardrails,
                confidence_note="Khi nội dung có dấu hiệu scam/pump, hệ thống sẽ ưu tiên an toàn hơn tương tác.",
                linked_lesson_id="anti-scam-101",
                risk_labels=risk_labels,
            )
        if "emotional_vulnerability" in risk_labels:
            return AssistantReply(
                role=role,
                allowed=False,
                route_decision="deescalate_and_redirect",
                title="Có vẻ bạn đang ở trạng thái áp lực cao.",
                summary="Lúc này điều quan trọng là giảm tốc và tránh quyết định đầu tư khi cảm xúc đang quá mạnh.",
                explanation="Mình có thể giúp bạn quay lại các bước an toàn hơn như Financial Health, goal pacing, hoặc chỉ giải thích khái niệm thay vì thúc đẩy hành động rủi ro.",
                next_step="Tạm dừng phần investing và quay lại một bước nền tảng an toàn hơn.",
                cta_path="/financial-health",
                guardrails=guardrails,
                confidence_note="Hệ thống sẽ không khuếch đại hành vi giao dịch khi phát hiện tín hiệu căng thẳng cảm xúc.",
                linked_lesson_id="risk-basics-101",
                risk_labels=risk_labels,
            )
        if "risky_investing_prompt" in risk_labels and role in {ROLE_ANALYST, ROLE_COACH}:
            return AssistantReply(
                role=ROLE_ANALYST,
                allowed=False,
                route_decision="redirected_for_investing_safety",
                title="Mình không thể hỗ trợ lời khuyên đầu tư liều lĩnh.",
                summary="Public assistant không chọn mã, không khuyến khích all-in/margin và không nói chắc thắng.",
                explanation="Mình có thể giúp bạn hiểu risk score, drawdown, market context hoặc cách rà soát watchlist an toàn hơn.",
                next_step="Chuyển sang đọc risk context hoặc học Risk Basics trước.",
                cta_path="/guided-investing?card=market_context",
                guardrails=guardrails,
                confidence_note="Khi prompt có ngôn ngữ overconfident hoặc high-risk investing, hệ thống chuyển sang giải thích an toàn.",
                linked_lesson_id="risk-basics-101",
                risk_labels=risk_labels,
            )
        if "implicit_personalized_financial_advice" in risk_labels and role in {ROLE_ANALYST, ROLE_COACH}:
            return AssistantReply(
                role=role,
                allowed=False,
                route_decision="redirected_for_suitability",
                title="Câu hỏi đang đi quá gần lời khuyên cá nhân hóa.",
                summary="Public assistant sẽ không đưa khuyến nghị cá nhân hóa dựa trên hoàn cảnh riêng của bạn như một advisory service.",
                explanation="Mình có thể giúp bạn hiểu framework, đọc risk context, hoặc quay lại Financial Health và Goals để có bước an toàn hơn.",
                next_step="Chuyển sang giải thích framework hoặc bước nền tảng phù hợp hơn.",
                cta_path="/financial-health" if role == ROLE_COACH else "/guided-investing",
                guardrails=guardrails,
                confidence_note="Trust-first nghĩa là dừng trước khi câu trả lời bị đọc như lời khuyên tài chính cá nhân hóa.",
                risk_labels=risk_labels,
            )
        if role == ROLE_TUTOR:
            return self._build_tutor_reply(lesson_id=lesson_id, question=prompt, knowledge_level=knowledge_level, guardrails=guardrails)
        if role == ROLE_COACH:
            return self._build_coach_reply(session_id=session_id, surface=surface, trigger=trigger, focus=focus, context=context, guardrails=guardrails)
        if role == ROLE_ANALYST:
            return self._build_analyst_reply(session_id=session_id, prompt=prompt, context=context, risk_labels=risk_labels, guardrails=guardrails)
        return self._build_pro_assistant_reply(session_id=session_id, prompt=prompt, guardrails=guardrails)

    def _build_tutor_reply(self, *, lesson_id: str | None, question: str, knowledge_level: str, guardrails: tuple[str, ...]) -> AssistantReply:
        catalog = SqliteLearningCatalog()
        selected_lesson_id = lesson_id or catalog.get_context_lesson_id(trigger="drawdown")
        lesson = catalog.get_lesson(lesson_id=selected_lesson_id)
        reply = build_tutor_reply(lesson=lesson, question=question or lesson.summary, knowledge_level=knowledge_level)
        return AssistantReply(
            role=ROLE_TUTOR,
            allowed=True,
            route_decision="explained_with_tutor",
            title=lesson.title,
            summary=reply.summary,
            explanation=reply.explanation,
            next_step=reply.next_lesson_hint,
            cta_path="/learn",
            guardrails=guardrails,
            confidence_note="Tutor giúp giải thích khái niệm và kiểm tra hiểu, không thay thế lời khuyên tài chính cá nhân hóa.",
            check_question=reply.check_question,
            linked_lesson_id=selected_lesson_id,
        )

    def _build_coach_reply(
        self,
        *,
        session_id: str,
        surface: str,
        trigger: str | None,
        focus: str | None,
        context: dict[str, object],
        guardrails: tuple[str, ...],
    ) -> AssistantReply:
        if surface == "financial_health":
            snapshot = SqliteFinancialHealthSnapshotRepository().get(session_id)
            if snapshot is None:
                return AssistantReply(
                    role=ROLE_COACH,
                    allowed=True,
                    route_decision="redirect_to_assessment",
                    title="Bạn cần baseline trước.",
                    summary="Coach cần Financial Health snapshot trước khi gợi ý hành động phù hợp.",
                    explanation="Hãy hoàn thành assessment ngắn để hệ thống biết nên ưu tiên quỹ dự phòng, nợ hay học tiếp về investing.",
                    next_step="Hoàn thành Financial Health assessment đầu tiên.",
                    cta_path="/financial-health",
                    guardrails=guardrails,
                    confidence_note="Coach ưu tiên hành động nhỏ dựa trên dữ liệu hiện có, không giả vờ biết quá nhiều khi chưa có baseline.",
                )
            reply = build_coach_reply(snapshot, focus=focus)
            return AssistantReply(
                role=ROLE_COACH,
                allowed=True,
                route_decision="coached_financial_health",
                title=reply.summary,
                summary=reply.summary,
                explanation=reply.explanation,
                next_step=reply.next_small_actions[0] if reply.next_small_actions else "Bắt đầu bằng một bước nhỏ nhất trước.",
                cta_path="/financial-health",
                guardrails=guardrails,
                confidence_note=reply.confidence_note,
                linked_lesson_id=snapshot.educational_links[0]["id"] if snapshot.educational_links else None,
            )

        if surface == "learning":
            try:
                home = SqliteLearningHomeRepository().get_home_state(user_id=session_id)
            except ValueError:
                return AssistantReply(
                    role=ROLE_COACH,
                    allowed=True,
                    route_decision="redirect_to_learning_start",
                    title="Bạn cần bắt đầu learning path trước.",
                    summary="Coach chưa thấy learning path đang hoạt động cho user này.",
                    explanation="Hãy quay lại Learn Hub để hệ thống gán path và bài tiếp theo, rồi Coach sẽ nhắc đúng nhịp hơn.",
                    next_step="Mở Learn Hub.",
                    cta_path="/learn",
                    guardrails=guardrails,
                    confidence_note="Coach chỉ nên nhắc hành động khi đã có path và context tối thiểu.",
                )
            nudge = build_coach_nudge(home_state=home, trigger=trigger or "continue_path")
            return AssistantReply(
                role=ROLE_COACH,
                allowed=True,
                route_decision="coached_learning",
                title=nudge.title,
                summary=nudge.message,
                explanation=nudge.message,
                next_step=nudge.cta_label,
                cta_path=nudge.cta_path,
                guardrails=guardrails,
                confidence_note="Coach sẽ đẩy bạn sang bước nhỏ tiếp theo trong app, không thay Tutor giải thích toàn bộ kiến thức.",
                linked_lesson_id=home.next_lesson_id,
            )

        goal = context.get("goal") or {}
        goal_name = goal.get("goal_name")
        feasibility = goal.get("feasibility_band")
        if goal_name:
            return AssistantReply(
                role=ROLE_COACH,
                allowed=True,
                route_decision="coached_goal_progress",
                title=f"Ưu tiên goal: {goal_name}",
                summary=f"Goal hiện ở trạng thái {feasibility or 'unknown'}. Coach sẽ giữ bạn ở nhịp điều chỉnh đều thay vì ép tiến quá nhanh.",
                explanation="Bước tiếp theo nên là check-in lại current amount, rồi học một bài ngắn về trade-off hoặc pace nếu goal đang căng.",
                next_step="Mở Goals và thực hiện check-in ngắn.",
                cta_path="/goals",
                guardrails=guardrails,
                confidence_note="Coach ưu tiên hành vi đều đặn và thực tế hơn là tối ưu hóa quá tay.",
            )

        next_lesson_id = ((context.get("learning") or {}).get("next_lesson_id"))
        return AssistantReply(
            role=ROLE_COACH,
            allowed=True,
            route_decision="coached_home",
            title="Làm bước nhỏ tiếp theo trong app",
            summary="Coach sẽ ưu tiên một hành động nhỏ, rõ, và phù hợp với hành trình hiện tại thay vì đưa quá nhiều việc cùng lúc.",
            explanation="Nếu bạn chưa rõ nên làm gì, cách an toàn nhất là hoàn thành lesson tiếp theo hoặc quay lại Financial Health trước khi đi sâu hơn.",
            next_step="Mở lesson tiếp theo hoặc quay lại baseline tài chính.",
            cta_path="/learn" if next_lesson_id else "/financial-health",
            guardrails=guardrails,
            confidence_note="Coach nhắm tới tiến bộ hành vi nhỏ và bền, không tối ưu bằng cảm xúc hoặc áp lực.",
            linked_lesson_id=next_lesson_id,
        )

    def _build_analyst_reply(
        self,
        *,
        session_id: str,
        prompt: str,
        context: dict[str, object],
        risk_labels: tuple[str, ...],
        guardrails: tuple[str, ...],
    ) -> AssistantReply:
        try:
            eligibility = GetGuidedEligibility().execute(user_id=session_id)
        except ValueError:
            if _is_public_safe_investing_explainer(prompt):
                market = GetGuidedMarketContext().execute()
                return AssistantReply(
                    role=ROLE_ANALYST,
                    allowed=True,
                    route_decision="explained_guest_market_context",
                    title=market.headline,
                    summary=market.summary,
                    explanation=(
                        f"{market.so_what} {market.now_what} "
                        "Mình chưa có session hợp lệ của bạn, nên phần này chỉ là giải thích giáo dục theo bối cảnh thị trường chung."
                    ),
                    next_step="Hoàn tất onboarding để mở Guided Investing có ngữ cảnh cá nhân.",
                    cta_path="/onboarding",
                    guardrails=guardrails,
                    confidence_note="Assistant đang chạy ở guest-safe analyst mode: không dùng dữ liệu cá nhân, không đưa khuyến nghị mua bán.",
                    linked_lesson_id="tool-risk-score-101",
                    risk_labels=risk_labels,
                )
            return AssistantReply(
                role=ROLE_ANALYST,
                allowed=False,
                route_decision="redirected_missing_user_session",
                title="Cần xác nhận lại phiên người dùng",
                summary="Session hiện tại không còn tồn tại hoặc chưa hoàn tất onboarding, nên mình không nên dùng ngữ cảnh cá nhân để trả lời.",
                explanation=(
                    "Để tránh bịa dữ liệu hoặc cá nhân hóa sai, assistant sẽ dừng phần phân tích có ngữ cảnh cho tới khi bạn tạo lại session."
                ),
                next_step="Quay lại onboarding hoặc Home preview rồi bắt đầu lại phiên mới.",
                cta_path="/onboarding",
                guardrails=guardrails,
                confidence_note="Không có user context hợp lệ; đây là fallback an toàn thay vì suy đoán.",
                linked_lesson_id="tool-risk-score-101",
                risk_labels=risk_labels,
            )
        safe = build_safe_reply(prompt=prompt, eligible=eligibility.eligible)
        if not safe.allowed:
            if not eligibility.eligible and _is_public_safe_investing_explainer(prompt):
                market = GetGuidedMarketContext().execute()
                return AssistantReply(
                    role=ROLE_ANALYST,
                    allowed=True,
                    route_decision="explained_limited_market_context",
                    title=market.headline,
                    summary=market.summary,
                    explanation=(
                        f"{market.so_what} {market.now_what} "
                        "Vì bạn chưa hoàn tất đầy đủ nền tảng, mình chỉ giải thích cách đọc rủi ro ở mức giáo dục."
                    ),
                    next_step="Học Risk Basics trước khi dùng Guided Investing sâu hơn.",
                    cta_path="/learn",
                    guardrails=guardrails,
                    confidence_note="Limited analyst mode cho phép giải thích khái niệm/risk context, nhưng không mở workflow đầu tư sâu khi nền tảng còn thiếu.",
                    linked_lesson_id="tool-risk-score-101",
                    risk_labels=risk_labels,
                )
            return AssistantReply(
                role=ROLE_ANALYST,
                allowed=False,
                route_decision="redirected_by_analyst_guardrail",
                title=safe.headline,
                summary=safe.message,
                explanation=safe.message,
                next_step="Đi theo đường dẫn an toàn hơn để học trước khi hành động.",
                cta_path=safe.suggested_path,
                guardrails=guardrails,
                confidence_note="Analyst trong public mode chỉ giải thích bối cảnh và rủi ro, không đưa pick hay certainty.",
                linked_lesson_id=safe.linked_lesson_id,
                risk_labels=risk_labels,
            )
        market = GetGuidedMarketContext().execute()
        return AssistantReply(
            role=ROLE_ANALYST,
            allowed=True,
            route_decision="explained_market_context",
            title=market.headline,
            summary=market.summary,
            explanation=f"{market.so_what} {market.now_what}",
            next_step="Rà soát market context hoặc company health trước khi tăng cam kết.",
            cta_path="/guided-investing?card=market_context",
            guardrails=guardrails,
            confidence_note="Analyst mô tả điều đang diễn ra và điều không nên overread từ dữ liệu hiện tại.",
            linked_lesson_id="drawdown-basics-101" if "drawdown" in prompt.lower() else "tool-risk-score-101",
            risk_labels=risk_labels,
        )

    def _build_pro_assistant_reply(self, *, session_id: str, prompt: str, guardrails: tuple[str, ...]) -> AssistantReply:
        workspace = GetProLabWorkspace(
            blueprints=SqliteProLabBlueprintRepository(),
            experiments=SqliteProLabExperimentRepository(),
        ).execute(user_id=session_id)
        blueprints = workspace.blueprints
        experiments = workspace.experiments
        lowered = prompt.lower()
        if "backtest" in lowered:
            explanation = "Hãy đọc backtest như một notebook có giả định và caveats, không phải bằng chứng chắc chắn cho tương lai."
        elif "scenario" in lowered:
            explanation = "Scenario lab nên được đọc như một phép đo độ nhạy của blueprint dưới các giả định khác nhau."
        else:
            explanation = "Pro Assistant giúp bạn tóm tắt blueprint, experiment và caveats để research có kỷ luật hơn."
        return AssistantReply(
            role=ROLE_PRO_ASSISTANT,
            allowed=True,
            route_decision="assisted_pro_research",
            title="Pro Assistant summary",
            summary=f"Bạn đang có {len(blueprints)} blueprint và {len(experiments)} experiment trong workspace.",
            explanation=explanation,
            next_step="Review blueprint assumptions hoặc mở experiment gần nhất để kiểm tra caveats.",
            cta_path="/pro-lab",
            guardrails=guardrails,
            confidence_note="Pro Assistant hỗ trợ research workflow và caveat review, không thay thế quyết định đầu tư độc lập.",
        )


def _normalize_risk_labels(labels: tuple[str, ...]) -> tuple[str, ...]:
    alias = {
        "fraud_or_scam_content": "scam_or_pump",
        "overconfident_investing_language": "risky_investing_prompt",
    }
    normalized = [alias.get(label, label) for label in labels]
    return tuple(dict.fromkeys(normalized))


def _is_greeting_prompt(prompt: str) -> bool:
    normalized = re.sub(r"[!?.。,]+", "", (prompt or "").strip().lower())
    return normalized in {"hi", "hello", "hey", "chào", "chao", "xin chào", "xin chao", "alo"}


def _is_public_safe_investing_explainer(prompt: str) -> bool:
    lowered = (prompt or "").strip().lower()
    if not lowered:
        return False

    unsafe_patterns = (
        r"\ball\s+in\b",
        r"\bmargin\b",
        r"\bentry\b",
        r"\bexit\b",
        r"\btop\s+pick\b",
        r"chắc\s+thắng",
        r"chac\s+thang",
        r"chắc\s+tăng",
        r"chac\s+tang",
        r"nên\s+mua",
        r"nen\s+mua",
        r"mua\s+mã",
        r"mua\s+ma",
        r"bán\s+mã",
        r"ban\s+ma",
        r"mã\s+nào",
        r"ma\s+nao",
    )
    if any(re.search(pattern, lowered) for pattern in unsafe_patterns):
        return False

    explainer_markers = (
        "risk score",
        "drawdown",
        "volatility",
        "biến động",
        "bien dong",
        "giải thích",
        "giai thich",
        "nghĩa là gì",
        "nghia la gi",
        "nói điều gì",
        "noi dieu gi",
        "đọc thế nào",
        "doc the nao",
        "vì sao",
        "vi sao",
        "so what",
        "what does",
    )
    return any(marker in lowered for marker in explainer_markers)


class SaveAssistantFeedback:
    def __init__(self, conversations: AssistantConversationRepository) -> None:
        self.conversations = conversations

    def execute(
        self,
        *,
        conversation_id: str,
        message_id: str,
        rating: int,
        reason_code: str,
        free_text: str | None,
    ) -> AssistantFeedbackResponse:
        feedback = AssistantFeedback(
            feedback_id=new_feedback_id(),
            conversation_id=conversation_id,
            message_id=message_id,
            rating=rating,
            reason_code=reason_code,
            free_text=free_text.strip() if free_text else None,
        )
        self.conversations.save_feedback(feedback)
        return AssistantFeedbackResponse(saved=True, feedback_id=feedback.feedback_id)
