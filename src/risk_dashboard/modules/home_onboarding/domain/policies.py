from __future__ import annotations

from risk_dashboard.modules.home_onboarding.domain.entities import HomeBlock, HomeState, RouteDecision


def decide_persona(*, primary_goal: str, knowledge_level: str, primary_interest: str) -> str:
    if knowledge_level == "advanced" or primary_goal == "deep_analysis_tools":
        return "advanced_pro"
    if primary_goal == "manage_household_money" or primary_interest in {"cashflow", "emergency_fund"}:
        return "household_manager"
    if primary_goal == "learn_investing_safely" or primary_interest in {"markets", "investing_basics"}:
        return "beginner_investor"
    return "starter"


def decide_route(
    *,
    primary_goal: str,
    knowledge_level: str,
    risk_tolerance_prelim: str,
    primary_interest: str,
    current_state: str,
) -> RouteDecision:
    persona = decide_persona(
        primary_goal=primary_goal,
        knowledge_level=knowledge_level,
        primary_interest=primary_interest,
    )

    if persona == "advanced_pro":
        return RouteDecision(
            persona_segment=persona,
            primary_route="insights",
            guided_investing_eligible=True,
            pro_eligible=True,
            trust_message="Công cụ chuyên sâu chỉ xuất hiện khi phù hợp; public mode vẫn ưu tiên giải thích trước.",
        )

    if primary_goal == "manage_household_money" or primary_interest in {"cashflow", "emergency_fund"}:
        return RouteDecision(
            persona_segment="household_manager",
            primary_route="financial_health",
            guided_investing_eligible=False,
            pro_eligible=False,
            trust_message="Bắt đầu từ sức khỏe tài chính giúp mọi quyết định đầu tư sau này an toàn hơn.",
        )

    if (
        primary_goal == "learn_investing_safely"
        and knowledge_level in {"basic", "intermediate"}
        and current_state in {"already_saving_wants_to_invest", "already_investing_wants_structure"}
        and risk_tolerance_prelim != "very_cautious"
    ):
        return RouteDecision(
            persona_segment="beginner_investor",
            primary_route="guided_investing",
            guided_investing_eligible=True,
            pro_eligible=False,
            trust_message="Chúng tôi giải thích rủi ro và công cụ trước khi đi vào quyết định đầu tư.",
        )

    if persona == "beginner_investor":
        return RouteDecision(
            persona_segment=persona,
            primary_route="learn",
            guided_investing_eligible=False,
            pro_eligible=False,
            trust_message="Bạn sẽ vào Learn trước để xây nền tảng đủ vững trước khi dùng Guided Investing.",
        )

    return RouteDecision(
        persona_segment="starter",
        primary_route="learn",
        guided_investing_eligible=False,
        pro_eligible=False,
        trust_message="Sản phẩm này giúp bạn hiểu trước, rồi mới dùng công cụ tài chính phù hợp.",
    )


def build_home_state(*, session_id: str, decision: RouteDecision) -> HomeState:
    next_action_by_route = {
        "learn": ("start_first_lesson", "risk-basics-101", "Bắt đầu bài học đầu tiên", "/learn"),
        "financial_health": (
            "setup_financial_health",
            "financial-health-baseline",
            "Thiết lập sức khỏe tài chính",
            "/financial-health",
        ),
        "guided_investing": (
            "open_guided_watchlist",
            "/guided-investing",
            "Mở Guided Investing Lite",
            "/guided-investing",
        ),
        "insights": ("view_market_explainer", "/insights", "Xem market explainer", "/insights"),
    }
    action_type, action_ref, action_label, action_path = next_action_by_route[decision.primary_route]

    blocks = [
        HomeBlock(
            block_id="next_best_action",
            title="What should I do next?",
            description=action_label,
            cta_label=action_label,
            cta_path=action_path,
        ),
        HomeBlock(
            block_id="health_snapshot",
            title="Health snapshot",
            description="Bắt đầu từ các bước nền tảng để giảm sai lầm tài chính cơ bản.",
            cta_label="Xem snapshot",
            cta_path="/financial-health",
        ),
        HomeBlock(
            block_id="goals_snapshot",
            title="Goals snapshot",
            description="Thiết lập mục tiêu đầu tiên để sản phẩm cá nhân hóa tốt hơn.",
            cta_label="Tạo goal đầu tiên",
            cta_path="/goals",
        ),
        HomeBlock(
            block_id="learning_recommendation",
            title="Learning recommendation",
            description="Một bài học ngắn giúp bạn hiểu đúng trước khi dùng công cụ.",
            cta_label="Tiếp tục học",
            cta_path="/learn",
        ),
    ]

    if decision.guided_investing_eligible or decision.persona_segment in {"beginner_investor", "advanced_pro"}:
        blocks.append(
            HomeBlock(
                block_id="insight_recommendation",
                title="Insight recommendation",
                description="Giải thích ngắn gọn về thị trường hoặc doanh nghiệp phù hợp với mức độ của bạn.",
                cta_label="Mở Insights",
                cta_path="/insights",
            )
        )

    return HomeState(
        session_id=session_id,
        persona_segment=decision.persona_segment,
        primary_route=decision.primary_route,
        next_best_action_type=action_type,
        next_best_action_ref=action_ref,
        trust_message=decision.trust_message,
        blocks=blocks,
    )
