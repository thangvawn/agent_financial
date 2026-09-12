from __future__ import annotations

import logging
import re
from typing import Any

from risk_dashboard.modules.ai_tutor.domain.teaching_policy import check_hint_leakage
from risk_dashboard.modules.ai_tutor.schemas.conversation import ToolCallRef

logger = logging.getLogger(__name__)

LEAKAGE_TARGETS = (
    "đáp án là a", "đáp án là b", "đáp án là c", "đáp án là d",
    "đáp án chính xác là a", "đáp án chính xác là b", "đáp án chính xác là c", "đáp án chính xác là d",
    "đáp án đúng là a", "đáp án đúng là b", "đáp án đúng là c", "đáp án đúng là d",
    "phương án a", "phương án b", "phương án c", "phương án d",
    "chọn phương án a", "chọn phương án b", "chọn phương án c", "chọn phương án d",
    "chọn a", "chọn b", "chọn c", "chọn d",
    "đáp án a", "đáp án b", "đáp án c", "đáp án d",
)


def infer_resource_id(query: str) -> str | None:
    lowered = query.lower()
    if "cfo" in lowered or "dòng tiền" in lowered:
        return "card_cfo_01"
    if "nợ" in lowered or "đòn bẩy" in lowered or "rủi ro" in lowered:
        return "card_risk_01"
    if "sma" in lowered or "kỹ thuật" in lowered or "xu hướng" in lowered:
        return "card_ta_01"
    if "roe" in lowered or "vốn chủ" in lowered:
        return "card_roe_01"
    return None


def build_unauthorized_response(tool_id: str) -> dict[str, Any]:
    return {
        "answer": "Chào anh, em đã tiếp nhận câu hỏi nhưng công cụ học tập chưa được cấp quyền thực thi theo chính sách bảo mật của Agentic Core.",
        "citations": (),
        "numeric_claims": (),
        "assumptions": (),
        "limitations": ("Công cụ truy xuất dữ liệu học tập bị từ chối do thiếu quyền ToolGrant.",),
        "check_question": "Anh có muốn thử lại sau khi cấp quyền không?",
        "next_action": "Kiểm tra quyền hạn người dùng hoặc thử lại.",
        "tool_calls": (
            ToolCallRef(tool_name=tool_id, status="error", summary="Tool access not granted by Agentic Core policy"),
        ),
    }


def build_socratic_hint(prompt_text: str, hint: str) -> str:
    return (
        f"Chào anh, với câu hỏi: *\"{prompt_text}\"*, em xin gợi ý hướng tư duy theo phương pháp Socratic:\n\n"
        f"1. **Bản chất vấn đề:** Hãy liên hệ với kiến thức trọng tâm đã học để nhận diện khái niệm chủ đạo.\n"
        f"2. **Gợi ý phương pháp:** {hint}\n"
        f"3. **Phân tích loại trừ:** Đối chiếu từng phương án để loại bỏ những nhận định mâu thuẫn với nguyên lý tài chính.\n\n"
        "Anh hãy thử suy luận và lựa chọn phương án mà anh thấy hợp lý nhất nhé!"
    )


def sanitize_socratic_leakage(answer: str, prompt_text: str, hint: str) -> str:
    if check_hint_leakage(answer, LEAKAGE_TARGETS) or re.search(
        r"\b(đáp án|phương án|chọn)\s+(chính xác\s+|đúng\s+)?(là\s+)?[abcdABCD]\b", answer
    ):
        logger.warning("Zero-leakage policy triggered: answer contained direct choice/key. Sanitizing.")
        return (
            f"Chào anh, theo chuẩn giảng dạy Socratic của Northstar Finance Lab, em không thể cung cấp trực tiếp kết quả lựa chọn nhằm giúp anh rèn luyện tư duy phản biện độc lập.\n\n"
            f"Thay vào đó, em xin gợi ý hướng tư duy cho câu hỏi: *\"{prompt_text}\"*:\n"
            f"- **Gợi ý cốt lõi:** {hint}\n"
            f"- **Phương pháp:** Anh hãy đối chiếu định nghĩa và công thức đã học để tự mình suy luận và lựa chọn nhé!"
        )
    return answer


def build_lesson_explanation(lesson_ev: dict[str, str]) -> str:
    title = lesson_ev.get("lesson_title") or "Bài học tài chính"
    summary = lesson_ev.get("summary", "")
    key_takeaway = lesson_ev.get("key_takeaway", "")
    example = lesson_ev.get("example", "")
    topic = lesson_ev.get("lesson_topic", "")
    title_lower = title.lower()

    parts = [f"Chào anh, em xin giải thích nội dung bài học **{title}**:"]
    if summary:
        parts.append(f"- **Tóm tắt:** {summary}")
    if key_takeaway:
        parts.append(f"- **Ý nghĩa cốt lõi:** {key_takeaway}")
    if example:
        parts.append(f"- **Ví dụ thực tiễn:** {example}")

    if "cfo" in title_lower or "dòng tiền" in title_lower or topic == "bctc":
        parts.append("Nắm vững chất lượng dòng tiền CFO sẽ giúp anh nhận diện được sức khỏe tài chính thực chất và khả năng thanh khoản của doanh nghiệp.")
    elif "nợ" in title_lower or topic == "quan_tri_rui_ro":
        parts.append("Việc kiểm soát đòn bẩy tài chính giúp doanh nghiệp duy trì vùng đệm an toàn trước các biến động lãi suất và chu kỳ kinh tế.")
    elif "sma" in title_lower or topic == "phan_tich_ky_thuat":
        parts.append("Sử dụng đường trung bình động giúp anh xác định xu hướng và các điểm hỗ trợ/kháng cự quan trọng trong giao dịch.")
    elif "roe" in title_lower or topic == "dinh_gia":
        parts.append("Chỉ số này giúp anh đánh giá xem doanh nghiệp sử dụng đồng vốn của cổ đông hiệu quả như thế nào qua các năm.")
    else:
        parts.append("Kiến thức này là nền tảng quan trọng giúp anh củng cố tư duy quản trị tài chính và đầu tư bài bản.")

    return "\n\n".join(parts)
