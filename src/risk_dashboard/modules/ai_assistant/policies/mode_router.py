from __future__ import annotations

from risk_dashboard.modules.ai_assistant.domain.contracts import IntentDecision, ModeDecision
from risk_dashboard.modules.ai_assistant.domain.policies import ROLE_ANALYST, ROLE_COACH, ROLE_PRO_ASSISTANT, ROLE_TUTOR


MODE_ROUTER_VERSION = "mode_router_v2_surface_intent"


class ModeRouter:
    def resolve(
        self,
        *,
        surface: str,
        intent: IntentDecision,
        role_hint: str | None,
        has_pro_scope: bool,
    ) -> ModeDecision:
        if intent.intent == "smalltalk_greeting":
            return ModeDecision(role=ROLE_COACH, confidence=0.88, reason="greeting_lightweight_assistant", allowed_tools=())

        if role_hint in {ROLE_TUTOR, ROLE_COACH, ROLE_ANALYST, ROLE_PRO_ASSISTANT}:
            if role_hint == ROLE_PRO_ASSISTANT and not has_pro_scope:
                return ModeDecision(
                    role=ROLE_ANALYST,
                    confidence=0.78,
                    reason="pro_hint_without_scope_downgraded",
                    allowed_tools=("market_context", "learning_catalog"),
                )
            return ModeDecision(role=role_hint, confidence=0.9, reason="explicit_role_hint", allowed_tools=_tools_for(role_hint))

        if surface == "pro_lab" and has_pro_scope:
            return ModeDecision(role=ROLE_PRO_ASSISTANT, confidence=0.9, reason="pro_surface_with_scope", allowed_tools=_tools_for(ROLE_PRO_ASSISTANT))

        if intent.intent == "educational":
            return ModeDecision(role=ROLE_TUTOR, confidence=0.86, reason="educational_intent", allowed_tools=_tools_for(ROLE_TUTOR))
        if intent.intent in {"financial_health", "goal_planning", "coachable_action", "product_navigation"}:
            return ModeDecision(role=ROLE_COACH, confidence=0.84, reason="action_or_planning_intent", allowed_tools=_tools_for(ROLE_COACH))
        if intent.intent in {"investing_explanation", "market_insight", "risky_high_stakes"}:
            return ModeDecision(role=ROLE_ANALYST, confidence=0.86, reason="market_or_risk_intent", allowed_tools=_tools_for(ROLE_ANALYST))
        if intent.intent == "research_assist":
            return ModeDecision(
                role=ROLE_PRO_ASSISTANT if has_pro_scope else ROLE_ANALYST,
                confidence=0.78,
                reason="research_intent_scope_checked",
                allowed_tools=_tools_for(ROLE_PRO_ASSISTANT if has_pro_scope else ROLE_ANALYST),
            )

        if surface == "learning":
            return ModeDecision(role=ROLE_TUTOR, confidence=0.72, reason="surface_default_learning", allowed_tools=_tools_for(ROLE_TUTOR))
        if surface in {"home", "financial_health", "goals", "community"}:
            return ModeDecision(role=ROLE_COACH, confidence=0.72, reason="surface_default_coach", allowed_tools=_tools_for(ROLE_COACH))
        if surface in {"insights", "guided_investing"}:
            return ModeDecision(role=ROLE_ANALYST, confidence=0.76, reason="surface_default_analyst", allowed_tools=_tools_for(ROLE_ANALYST))

        return ModeDecision(role=ROLE_TUTOR, confidence=0.5, reason="safe_default_tutor", allowed_tools=_tools_for(ROLE_TUTOR))


def _tools_for(role: str) -> tuple[str, ...]:
    if role == ROLE_TUTOR:
        return ("learning_catalog", "glossary")
    if role == ROLE_COACH:
        return ("onboarding_profile", "financial_health", "goals", "learning_progress")
    if role == ROLE_ANALYST:
        return ("market_context", "guided_eligibility", "company_health", "learning_catalog")
    if role == ROLE_PRO_ASSISTANT:
        return ("pro_workspace", "experiment_log", "audit_summary")
    return ()
