from __future__ import annotations

from risk_dashboard.modules.ai_assistant.domain.contracts import IntentDecision, SafetyDecision


SAFETY_VERSION = "assistant_safety_gate_v2"


class AssistantSafetyGate:
    def evaluate(
        self,
        *,
        intent: IntentDecision,
        trust_risk_classes: tuple[str, ...],
        surface: str,
    ) -> SafetyDecision:
        risk_labels = tuple(dict.fromkeys([*intent.risk_labels, *trust_risk_classes]))
        warnings: list[str] = []

        if "pii_or_privacy_issue" in risk_labels:
            return SafetyDecision(
                action="block",
                risk_labels=risk_labels,
                warnings=("Không nhập OTP, CCCD/CMND, số tài khoản, mật khẩu hoặc dữ liệu nhận diện nhạy cảm.",),
                fallback_title="Có dấu hiệu lộ thông tin nhạy cảm.",
                fallback_summary="Mình không thể tiếp tục với nội dung chứa dữ liệu riêng tư.",
                fallback_next_step="Hãy xóa thông tin nhận diện rồi hỏi lại theo dạng khái quát.",
            )

        if "fraud_or_scam_content" in risk_labels or "scam_or_pump" in risk_labels:
            return SafetyDecision(
                action="block",
                risk_labels=risk_labels,
                warnings=("Không hỗ trợ nội dung guaranteed return, room kéo người dùng ra ngoài, hoặc dấu hiệu pump/scam.",),
                fallback_title="Nội dung có dấu hiệu lôi kéo hoặc thao túng.",
                fallback_summary="Mình sẽ không khuếch đại nội dung có thể gây hại tài chính cho người dùng.",
                fallback_next_step="Chuyển sang học cách nhận diện scam hoặc đọc risk basics.",
            )

        if "emotional_vulnerability" in risk_labels:
            return SafetyDecision(
                action="deescalate",
                risk_labels=risk_labels,
                warnings=("Khi đang căng thẳng, không nên đưa ra quyết định tài chính rủi ro hoặc giao dịch vội.",),
                fallback_title="Mình muốn giúp bạn giảm tốc trước.",
                fallback_summary="Tín hiệu cảm xúc đang cao, nên ưu tiên an toàn và quay lại bước nền tảng.",
                fallback_next_step="Tạm dừng investing và mở Financial Health hoặc Goals để đi chậm hơn.",
            )

        if "implicit_personalized_financial_advice" in risk_labels or "overconfident_investing_language" in risk_labels:
            warnings.append("Mình có thể giải thích framework/rủi ro, nhưng không chọn mã, không nói chắc thắng và không đưa khuyến nghị mua/bán cá nhân hóa.")
            return SafetyDecision(action="redirect", risk_labels=risk_labels, warnings=tuple(warnings))

        if surface in {"insights", "guided_investing", "pro_lab"}:
            warnings.append("Đây là giải thích bối cảnh và rủi ro, không phải khuyến nghị đầu tư cá nhân hóa.")

        return SafetyDecision(action="allow", risk_labels=risk_labels, warnings=tuple(warnings))
