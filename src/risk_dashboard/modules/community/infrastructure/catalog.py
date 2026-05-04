from __future__ import annotations

from risk_dashboard.modules.community.domain.entities import CommunitySpace

COMMUNITY_SPACES: tuple[CommunitySpace, ...] = (
    CommunitySpace(
        space_id="risk-literacy-circle",
        space_type="study_circle",
        title="Risk Literacy Circle",
        description="Nhóm học nhỏ để hiểu risk, drawdown và cách phản ứng bình tĩnh với biến động.",
        status="active",
        visibility="public",
        persona_tags=("beginner_investor", "advanced_pro"),
        learning_path_id="beginner-investing-foundations",
        icon_key="shield",
        trust_note="Study circle này chỉ để học framework rủi ro, không bàn lệnh mua bán.",
        join_hint="Phù hợp sau khi bạn học Investing Basics và Risk Basics.",
    ),
    CommunitySpace(
        space_id="goal-planning-circle",
        space_type="themed_room",
        title="Goal Planning Circle",
        description="Không gian chia sẻ có kiểm soát về lập goal, pace tích lũy và trade-off đời sống.",
        status="active",
        visibility="public",
        persona_tags=("starter", "household_manager"),
        goal_tag="financial_planning",
        icon_key="target",
        trust_note="Ưu tiên trao đổi về thói quen và kế hoạch, không hỏi chi tiết tài chính nhạy cảm của nhau.",
        join_hint="Rất hợp nếu bạn vừa hoàn thành Financial Health hoặc mới tạo goal đầu tiên.",
    ),
    CommunitySpace(
        space_id="goal-checkin-challenge",
        space_type="guided_challenge",
        title="14-Day Goal Check-in Challenge",
        description="Challenge nhẹ giúp bạn quay lại app, check-in goal và học thêm một bước nhỏ mỗi tuần.",
        status="active",
        visibility="public",
        persona_tags=("starter", "household_manager", "beginner_investor"),
        goal_tag="goal_checkin",
        icon_key="flag",
        trust_note="Challenge tập trung vào kỷ luật và tiến độ, không so sánh số tiền giữa người dùng.",
        join_hint="Tham gia khi bạn đã có ít nhất một goal trong app.",
    ),
    CommunitySpace(
        space_id="company-case-room",
        space_type="case_discussion",
        title="Company Health Case Room",
        description="Thảo luận case doanh nghiệp theo framework company health và peer comparison mang tính giáo dục.",
        status="active",
        visibility="public",
        persona_tags=("beginner_investor", "advanced_pro"),
        icon_key="bar_chart",
        trust_note="Chỉ thảo luận framework đọc doanh nghiệp, không hô hào mã hay price target.",
        join_hint="Phù hợp sau khi bạn đã dùng Company Health hoặc Guided Investing.",
    ),
    CommunitySpace(
        space_id="ask-an-expert-weekly",
        space_type="ask_expert",
        title="Ask-an-Expert Weekly",
        description="Gửi câu hỏi cho expert đã xác thực; câu hỏi sẽ qua moderation trước khi lên hàng chờ.",
        status="active",
        visibility="public",
        persona_tags=("starter", "household_manager", "beginner_investor", "advanced_pro"),
        icon_key="users",
        trust_note="Expert room là Q&A có kiểm duyệt, không phải kênh nhận khuyến nghị đầu tư cá nhân hóa.",
        join_hint="Nên hỏi theo case học tập hoặc framework, không hỏi mã nên mua.",
    ),
    CommunitySpace(
        space_id="diaspora-money-cohort",
        space_type="learning_cohort",
        title="Diaspora Money Cohort",
        description="Cohort cho người Việt ở nước ngoài về remittance, goal gia đình và literacy song ngữ.",
        status="active",
        visibility="public",
        persona_tags=("diaspora_vn", "starter", "household_manager"),
        learning_path_id="diaspora-crossborder-foundations",
        icon_key="globe",
        trust_note="Tập trung vào planning và literacy xuyên biên giới, không phải room đầu tư theo tin.",
        join_hint="Phù hợp nếu bạn đang quan tâm remittance hoặc goal đa tiền tệ.",
    ),
)


def list_community_spaces() -> list[CommunitySpace]:
    return list(COMMUNITY_SPACES)


def get_community_space(space_id: str) -> CommunitySpace:
    for space in COMMUNITY_SPACES:
        if space.space_id == space_id:
            return space
    raise ValueError(f"Unknown community space: {space_id}")
