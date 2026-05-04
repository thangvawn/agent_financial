from __future__ import annotations

from risk_dashboard.modules.financial_health.domain.entities import (
    FinancialHealthAction,
    FinancialHealthCoachReply,
    FinancialHealthFlag,
    FinancialHealthInput,
    FinancialHealthSnapshot,
    FinancialHealthSubScore,
)

_WEIGHTS = {
    "income_stability": 0.15,
    "expense_discipline": 0.12,
    "emergency_fund": 0.18,
    "debt_load": 0.16,
    "savings_rate": 0.12,
    "liquidity_stress": 0.12,
    "protection_basics": 0.08,
    "investment_readiness": 0.07,
}


def _score_band(score: int) -> str:
    if score < 40:
        return "needs_stabilization"
    if score < 60:
        return "fragile_foundation"
    if score < 80:
        return "building_strength"
    return "healthy_foundation"


def _lookup(level: str, mapping: dict[str, int], default: int = 50) -> int:
    return int(mapping.get(level, default))


def compute_subscores(payload: FinancialHealthInput) -> list[FinancialHealthSubScore]:
    income_stability = _lookup(
        payload.income_stability_level,
        {"unstable": 25, "variable": 50, "mostly_stable": 75, "stable": 90},
    )
    expense_discipline = _lookup(
        payload.expense_discipline_level,
        {"no_tracking": 25, "inconsistent": 50, "mostly_disciplined": 75, "disciplined": 90},
    )
    emergency_fund = _lookup(
        payload.emergency_fund_months_band,
        {"none": 10, "lt_1m": 25, "1_to_3m": 60, "3_to_6m": 85, "gt_6m": 95},
    )
    debt_load_base = _lookup(
        payload.monthly_debt_payment_ratio_band,
        {"none": 90, "lt_10pct": 80, "10_to_30pct": 60, "30_to_50pct": 35, "gt_50pct": 15},
    )
    debt_load = max(0, debt_load_base - (20 if payload.has_high_interest_debt else 0))
    savings_rate = _lookup(
        payload.savings_rate_band,
        {"none": 15, "lt_10pct": 35, "10_to_20pct": 60, "20_to_30pct": 80, "gt_30pct": 95},
    )
    liquidity_stress = _lookup(
        payload.liquidity_stress_level,
        {"frequent": 20, "sometimes": 45, "rare": 75, "comfortable": 90},
    )
    protection_basics = 70 if payload.has_basic_insurance else 30

    investment_readiness = round(
        (
            emergency_fund * 0.35
            + debt_load * 0.2
            + savings_rate * 0.2
            + liquidity_stress * 0.15
            + (70 if payload.wants_to_start_investing else 50) * 0.1
        )
    )

    return [
        FinancialHealthSubScore(
            key="income_stability",
            label="Income stability",
            score=income_stability,
            reason="Thu nhập càng ổn định, khả năng duy trì kế hoạch tài chính càng tốt.",
            improvement_hint="Ưu tiên tạo đệm an toàn lớn hơn nếu thu nhập chưa ổn định.",
        ),
        FinancialHealthSubScore(
            key="expense_discipline",
            label="Expense discipline",
            score=expense_discipline,
            reason="Mức độ theo dõi và kiểm soát chi tiêu ảnh hưởng trực tiếp đến khả năng tích lũy.",
            improvement_hint="Bắt đầu bằng việc theo dõi chi tiêu đều trong 2 tuần.",
        ),
        FinancialHealthSubScore(
            key="emergency_fund",
            label="Emergency fund",
            score=emergency_fund,
            reason="Quỹ dự phòng giúp bạn không phải ra quyết định tài chính vội khi có sự cố.",
            improvement_hint="Đặt mục tiêu đệm tối thiểu 1 tháng trước khi nghĩ đến bước lớn hơn.",
        ),
        FinancialHealthSubScore(
            key="debt_load",
            label="Debt load",
            score=debt_load,
            reason="Áp lực nợ cao làm giảm khả năng chịu rủi ro tài chính.",
            improvement_hint="Rà lại nghĩa vụ nợ hàng tháng và ưu tiên xử lý nợ lãi cao trước.",
        ),
        FinancialHealthSubScore(
            key="savings_rate",
            label="Savings rate",
            score=savings_rate,
            reason="Tỷ lệ tiết kiệm đều cho thấy bạn có khả năng tạo đệm tài chính lâu dài.",
            improvement_hint="Chỉ cần tăng tiết kiệm một chút đều đặn trước khi tối ưu đầu tư.",
        ),
        FinancialHealthSubScore(
            key="liquidity_stress",
            label="Liquidity stress",
            score=liquidity_stress,
            reason="Áp lực thanh khoản phản ánh mức độ căng cuối tháng và khả năng xoay xở ngắn hạn.",
            improvement_hint="Ưu tiên làm giảm các tình huống thiếu tiền ngắn hạn lặp lại.",
        ),
        FinancialHealthSubScore(
            key="protection_basics",
            label="Protection basics",
            score=protection_basics,
            reason="Các lớp bảo vệ cơ bản giúp giảm sốc tài chính khi gặp biến cố.",
            improvement_hint="Rà lại bảo hiểm/y tế cơ bản và kế hoạch xử lý khẩn cấp.",
        ),
        FinancialHealthSubScore(
            key="investment_readiness",
            label="Investment readiness",
            score=investment_readiness,
            reason="Đây là mức sẵn sàng nền tảng, không phải đánh giá bạn đầu tư giỏi đến đâu.",
            improvement_hint="Chỉ bước vào guided investing khi nền tài chính đủ ổn định.",
        ),
    ]


def compute_health_score(subscores: list[FinancialHealthSubScore]) -> int:
    score_map = {item.key: item.score for item in subscores}
    total = 0.0
    for key, weight in _WEIGHTS.items():
        total += score_map[key] * weight
    return round(total)


def build_flags(payload: FinancialHealthInput, subscores: list[FinancialHealthSubScore]) -> list[FinancialHealthFlag]:
    score_map = {item.key: item.score for item in subscores}
    flags: list[FinancialHealthFlag] = []
    if score_map["emergency_fund"] < 50:
        flags.append(
            FinancialHealthFlag(
                code="low_emergency_buffer",
                severity="high",
                title="Đệm khẩn cấp còn mỏng",
                description="Bạn chưa có nhiều khoảng an toàn nếu thu nhập gián đoạn hoặc phát sinh chi phí bất ngờ.",
            )
        )
    if score_map["debt_load"] < 45:
        flags.append(
            FinancialHealthFlag(
                code="high_debt_pressure",
                severity="high",
                title="Áp lực nợ đang cao",
                description="Nghĩa vụ nợ hiện tại có thể làm giảm khả năng tích lũy và chịu rủi ro.",
            )
        )
    if score_map["liquidity_stress"] < 50:
        flags.append(
            FinancialHealthFlag(
                code="liquidity_stress",
                severity="medium",
                title="Thanh khoản ngắn hạn cần chú ý",
                description="Dòng tiền ngắn hạn có dấu hiệu căng ở một số thời điểm.",
            )
        )
    if score_map["income_stability"] < 50:
        flags.append(
            FinancialHealthFlag(
                code="income_instability",
                severity="medium",
                title="Thu nhập chưa ổn định",
                description="Khi thu nhập biến động, bạn nên ưu tiên lớp đệm an toàn hơn là tăng rủi ro.",
            )
        )
    if score_map["protection_basics"] < 50:
        flags.append(
            FinancialHealthFlag(
                code="protection_gap",
                severity="medium",
                title="Thiếu lớp bảo vệ cơ bản",
                description="Một sự cố nhỏ cũng có thể gây áp lực tài chính lớn hơn mức cần thiết.",
            )
        )
    if score_map["investment_readiness"] < 60 and payload.wants_to_start_investing:
        flags.append(
            FinancialHealthFlag(
                code="not_ready_for_guided_investing",
                severity="medium",
                title="Chưa nên đi quá nhanh vào đầu tư",
                description="Nền tảng hiện tại cần chắc hơn trước khi mở rộng sang guided investing.",
            )
        )
    return flags[:3]


def build_actions(flags: list[FinancialHealthFlag]) -> list[FinancialHealthAction]:
    action_map = {
        "low_emergency_buffer": FinancialHealthAction(
            code="start_emergency_fund_goal",
            priority=1,
            title="Tạo mục tiêu quỹ dự phòng đầu tiên",
            description="Bắt đầu từ một mốc nhỏ, ví dụ đủ 1 tháng chi phí thiết yếu.",
            related_lesson_id="emergency-fund-101",
            cta_path="/goals",
        ),
        "high_debt_pressure": FinancialHealthAction(
            code="review_monthly_debt",
            priority=1,
            title="Rà lại nghĩa vụ nợ hàng tháng",
            description="Xác định khoản nợ nào đang tạo áp lực lớn nhất, nhất là nợ lãi cao.",
            related_lesson_id="debt-basics-101",
            cta_path="/learn",
        ),
        "liquidity_stress": FinancialHealthAction(
            code="track_cashflow_for_two_weeks",
            priority=2,
            title="Theo dõi dòng tiền trong 2 tuần",
            description="Mục tiêu là nhận ra thời điểm tiền bắt đầu căng, không phải tối ưu ngay lập tức.",
            related_lesson_id="cashflow-basics-101",
            cta_path="/health",
        ),
        "income_instability": FinancialHealthAction(
            code="increase_safety_buffer",
            priority=2,
            title="Tăng mức an toàn ngắn hạn",
            description="Khi thu nhập chưa đều, ưu tiên đệm an toàn trước khi mở rộng rủi ro.",
            related_lesson_id="income-stability-101",
            cta_path="/learn",
        ),
        "protection_gap": FinancialHealthAction(
            code="review_protection_basics",
            priority=3,
            title="Rà lại lớp bảo vệ cơ bản",
            description="Kiểm tra lại bảo hiểm/y tế cơ bản và kế hoạch xử lý khi có sự cố.",
            related_lesson_id="protection-basics-101",
            cta_path="/learn",
        ),
        "not_ready_for_guided_investing": FinancialHealthAction(
            code="complete_risk_basics_before_investing",
            priority=3,
            title="Học Risk Basics trước khi vào Guided Investing",
            description="Đi chậm hơn một bước thường giúp bạn ra quyết định tốt hơn về sau.",
            related_lesson_id="risk-basics-101",
            cta_path="/learn",
        ),
    }
    actions = [action_map[flag.code] for flag in flags if flag.code in action_map]
    unique: dict[str, FinancialHealthAction] = {}
    for action in actions:
        unique[action.code] = action
    return sorted(unique.values(), key=lambda item: item.priority)[:3]


def build_educational_links(flags: list[FinancialHealthFlag]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    if any(flag.code == "low_emergency_buffer" for flag in flags):
        links.append({"kind": "lesson", "id": "emergency-fund-101", "title": "Quỹ dự phòng là gì?"})
    if any(flag.code == "high_debt_pressure" for flag in flags):
        links.append({"kind": "lesson", "id": "debt-basics-101", "title": "Nợ ảnh hưởng đến tài chính thế nào?"})
    if any(flag.code == "liquidity_stress" for flag in flags):
        links.append({"kind": "lesson", "id": "cashflow-basics-101", "title": "Đọc áp lực thanh khoản ngắn hạn"})
    if not links:
        links.append({"kind": "lesson", "id": "financial-health-101", "title": "Financial Health Basics"})
    return links[:3]


def build_snapshot(payload: FinancialHealthInput) -> FinancialHealthSnapshot:
    subscores = compute_subscores(payload)
    health_score = compute_health_score(subscores)
    flags = build_flags(payload, subscores)
    actions = build_actions(flags)
    educational_links = build_educational_links(flags)
    score_map = {item.key: item.score for item in subscores}
    guided_eligible = (
        score_map["investment_readiness"] >= 60
        and score_map["emergency_fund"] >= 60
        and score_map["debt_load"] >= 50
        and score_map["liquidity_stress"] >= 50
    )
    return FinancialHealthSnapshot(
        session_id=payload.session_id,
        health_score=health_score,
        score_band=_score_band(health_score),
        guided_investing_eligible=guided_eligible,
        subscores=subscores,
        flags=flags,
        actions=actions,
        educational_links=educational_links,
        transparency_note="Điểm này được tính từ dữ liệu bạn tự khai và các quy tắc minh bạch, không phải black-box AI.",
        compliance_note="Đây là công cụ giáo dục và định hướng chung, không thay thế tư vấn tài chính cá nhân hóa đầy đủ.",
    )


def build_coach_reply(snapshot: FinancialHealthSnapshot, *, focus: str | None = None) -> FinancialHealthCoachReply:
    weakest = sorted(snapshot.subscores, key=lambda item: item.score)[:2]
    weakest_labels = ", ".join(item.label for item in weakest)
    if focus == "investment_readiness":
        explanation = (
            "Investment readiness ở đây chỉ phản ánh mức sẵn sàng nền tảng. "
            "Nếu quỹ dự phòng, thanh khoản hoặc áp lực nợ còn yếu, hệ thống sẽ ưu tiên an toàn trước."
        )
    else:
        explanation = (
            f"Điểm hiện tại bị kéo xuống nhiều nhất bởi: {weakest_labels}. "
            "Bạn không cần sửa mọi thứ cùng lúc; hãy ưu tiên 1-2 bước dễ làm nhất trước."
        )
    return FinancialHealthCoachReply(
        summary=f"Financial Health Score hiện tại là {snapshot.health_score}/100.",
        explanation=explanation,
        next_small_actions=[action.title for action in snapshot.actions[:2]]
        or ["Bắt đầu bằng một bước nhỏ: tạo baseline và học bài nền tảng đầu tiên."],
        confidence_note="Công cụ này dùng dữ liệu tự khai và nên được xem như hướng dẫn học và hành động nhỏ, không phải kết luận chắc chắn về tài chính của bạn.",
    )
