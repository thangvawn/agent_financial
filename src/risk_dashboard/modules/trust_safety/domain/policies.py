from __future__ import annotations

import re
from datetime import date

from risk_dashboard.modules.trust_safety.domain.entities import TrustDisclaimer

RISK_MISINFORMATION = "misinformation"
RISK_OVERCONFIDENT_INVESTING = "overconfident_investing_language"
RISK_IMPLICIT_ADVICE = "implicit_personalized_financial_advice"
RISK_FRAUD_SCAM = "fraud_or_scam_content"
RISK_COMMUNITY_ABUSE = "community_abuse"
RISK_STALE_DATA = "stale_data_risk"
RISK_MODEL_HALLUCINATION = "model_hallucination"
RISK_MISSING_DISCLAIMER = "missing_disclaimer"
RISK_PII_PRIVACY = "pii_or_privacy_issue"
RISK_EMOTIONAL_VULNERABILITY = "emotional_vulnerability"

_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (RISK_OVERCONFIDENT_INVESTING, re.compile(r"\b(chắc tăng|chắc ăn|bao lời|all in|full margin|pick mã|mua ngay|bán ngay|top pick)\b", re.I)),
    (RISK_FRAUD_SCAM, re.compile(r"\b(telegram|whatsapp|zalo|room riêng|x2|x3|guaranteed|bao lợi nhuận|cam kết lãi)\b", re.I)),
    (RISK_IMPLICIT_ADVICE, re.compile(r"\b(nên mua|nên bán|phù hợp riêng với tôi|danh mục của tôi nên)\b", re.I)),
    (RISK_PII_PRIVACY, re.compile(r"\b(cccd|cmnd|số tài khoản|account number|otp|mật khẩu|password|phone number|số điện thoại)\b", re.I)),
    (RISK_EMOTIONAL_VULNERABILITY, re.compile(r"\b(panic|hoảng|tuyệt vọng|không muốn sống|mất hết tiền|revenge trade)\b", re.I)),
    (RISK_COMMUNITY_ABUSE, re.compile(r"\b(ngu ngốc|lừa đảo|đồ điên|idiot|stupid|moron)\b", re.I)),
)


def detect_risk_classes(*, text: str, surface: str) -> tuple[str, ...]:
    lowered = text.strip()
    labels: list[str] = []
    for label, pattern in _TEXT_PATTERNS:
        if pattern.search(lowered):
            labels.append(label)
    if surface in {"guided_investing", "insights", "pro_lab"} and any(
        keyword in lowered.lower() for keyword in ("predict", "chắc chắn", "guarantee", "không thể sai")
    ):
        labels.append(RISK_MODEL_HALLUCINATION)
    return tuple(dict.fromkeys(labels))


def severity_for_risks(risk_classes: tuple[str, ...]) -> str:
    if any(label in risk_classes for label in (RISK_FRAUD_SCAM, RISK_PII_PRIVACY)):
        return "critical"
    if any(label in risk_classes for label in (RISK_OVERCONFIDENT_INVESTING, RISK_IMPLICIT_ADVICE, RISK_EMOTIONAL_VULNERABILITY)):
        return "high"
    if any(label in risk_classes for label in (RISK_COMMUNITY_ABUSE, RISK_MODEL_HALLUCINATION, RISK_STALE_DATA, RISK_MISSING_DISCLAIMER)):
        return "medium"
    return "low"


def moderation_action(*, surface: str, risk_classes: tuple[str, ...]) -> str:
    if any(label in risk_classes for label in (RISK_FRAUD_SCAM, RISK_PII_PRIVACY)):
        return "block"
    if surface == "community" and any(label in risk_classes for label in (RISK_COMMUNITY_ABUSE, RISK_IMPLICIT_ADVICE, RISK_OVERCONFIDENT_INVESTING)):
        return "hold"
    if any(label in risk_classes for label in (RISK_OVERCONFIDENT_INVESTING, RISK_IMPLICIT_ADVICE, RISK_EMOTIONAL_VULNERABILITY)):
        return "warn"
    return "allow"


def build_moderation_explanation(*, surface: str, action: str, risk_classes: tuple[str, ...]) -> str:
    if action == "block":
        if RISK_PII_PRIVACY in risk_classes:
            return "Nội dung bị chặn vì có dấu hiệu lộ thông tin nhạy cảm hoặc dữ liệu riêng tư."
        return "Nội dung bị chặn vì có dấu hiệu scam, thao túng hoặc lôi kéo không an toàn."
    if action == "hold":
        return "Nội dung đã được giữ lại để review vì có dấu hiệu advice quá tay, certainty claim hoặc hành vi cộng đồng không an toàn."
    if action == "warn":
        return "Hệ thống sẽ trả lời ở chế độ an toàn hơn vì câu hỏi đang chạm vùng rủi ro cao."
    if surface in {"insights", "guided_investing", "pro_lab"}:
        return "Nội dung đang được đọc theo hướng giải thích rủi ro và bối cảnh, không phải khuyến nghị đầu tư."
    return "Nội dung ở trong vùng an toàn hiện tại."


def normalize_freshness_status(*, freshness_value: str | None, quality_state: str | None) -> str:
    if freshness_value is None or freshness_value == "":
        return "unavailable" if quality_state in {"fallback", "unavailable"} else "unknown"
    lowered = freshness_value.strip().lower()
    if lowered in {"fresh", "delayed", "stale", "unknown"}:
        return lowered
    if lowered in {"unavailable", "fallback"}:
        return "unavailable"
    try:
        days_old = (date.today() - date.fromisoformat(freshness_value[:10])).days
    except ValueError:
        return "unknown"
    if days_old <= 1:
        return "fresh"
    if days_old <= 3:
        return "delayed"
    return "stale"


def confidence_label_for_quality(*, quality_state: str | None, freshness_status: str) -> str:
    if quality_state in {"fallback", "unavailable"} or freshness_status in {"stale", "unavailable"}:
        return "low_confidence"
    if quality_state in {"low_confidence", "mixed"} or freshness_status == "delayed":
        return "moderate_confidence"
    return "high_confidence"


def build_risk_banner(
    *,
    freshness_status: str,
    quality_state: str | None,
    disclaimer_injected: bool,
    existing_banner: str | None = None,
) -> str | None:
    if existing_banner:
        return existing_banner
    if freshness_status == "stale":
        return "Dữ liệu đang stale. Hãy đọc insight này như bối cảnh tham khảo, không phải trạng thái mới nhất."
    if freshness_status == "unavailable" or quality_state in {"fallback", "unavailable"}:
        return "Hệ thống đang ở chế độ fallback. Phần giải thích dưới đây ưu tiên an toàn và giáo dục hơn độ nhạy thời gian thực."
    if disclaimer_injected:
        return "Disclaimer mặc định đã được chèn vào vì bản content runtime chưa có bản đã duyệt riêng cho bề mặt này."
    return None


def freeze_banner_for_surface(*, surface: str, reason: str) -> str:
    return f"Bề mặt {surface} đang tạm freeze do incident critical. Chỉ nên đọc nội dung này như fallback an toàn. Lý do: {reason}"


def degrade_banner_for_surface(*, surface: str, reason: str) -> str:
    return f"Bề mặt {surface} đang ở chế độ degraded do incident đang mở. Hãy đọc nội dung này thận trọng hơn bình thường. Lý do: {reason}"


def what_this_is(*, surface: str) -> str:
    mapping = {
        "insights": "Lớp giải thích bối cảnh thị trường và dữ liệu theo hướng dễ hiểu.",
        "guided_investing": "Lớp hướng dẫn đọc rủi ro, company health và watchlist theo kiểu retail-friendly.",
        "community": "Không gian học và trao đổi có kiểm soát, ưu tiên trust-first.",
        "financial_health": "Công cụ giáo dục để hiểu nền tảng tài chính cá nhân và bước nhỏ tiếp theo.",
        "goals": "Công cụ lập kế hoạch mục tiêu tài chính với giả định minh bạch.",
        "pro_lab": "Workspace research có cấu trúc, nhiều caveat và audit trail.",
    }
    return mapping.get(surface, "Công cụ giáo dục và giải thích trong sản phẩm.")


def what_this_is_not(*, surface: str) -> str:
    mapping = {
        "insights": "Không phải feed giật gân hay khuyến nghị mua bán.",
        "guided_investing": "Không phải engine chọn mã hoặc tín hiệu giao dịch.",
        "community": "Không phải room phím hàng, room kéo kênh ngoài hoặc forum toxic.",
        "financial_health": "Không phải tư vấn tài chính cá nhân hóa đầy đủ.",
        "goals": "Không phải cam kết chắc chắn bạn sẽ đạt mục tiêu.",
        "pro_lab": "Không phải bằng chứng chắc chắn về kết quả đầu tư tương lai.",
    }
    return mapping.get(surface, "Không phải khuyến nghị đầu tư cá nhân hóa.")


def default_disclaimer(*, surface: str, topic: str | None = None) -> TrustDisclaimer:
    if surface == "guided_investing":
        return TrustDisclaimer(
            title="Guided Investing",
            short_text="Context này để giải thích rủi ro và bối cảnh, không phải khuyến nghị mua bán.",
            full_text="Context này nhằm hỗ trợ hiểu rủi ro, company health và market context. Nó không phải khuyến nghị mua bán, cũng không thay thế đánh giá phù hợp cá nhân.",
            severity="high",
        )
    if surface == "community":
        return TrustDisclaimer(
            title="Community Safety",
            short_text="Community này để học và chia sẻ có kiểm soát, không phải room tín hiệu.",
            full_text="Nội dung cộng đồng nhằm hỗ trợ học tập và trao đổi có kiểm soát. Bài đăng người dùng không phải khuyến nghị đầu tư, và nội dung thao túng hoặc lôi kéo sẽ bị chặn hoặc review.",
            severity="high",
        )
    if surface == "insights":
        return TrustDisclaimer(
            title="Insights",
            short_text="Insight này để đọc bối cảnh và độ nhạy của dữ liệu, không phải nội dung giật gân hay pick cổ phiếu.",
            full_text="Insight này giúp đọc điều đang diễn ra trong dữ liệu thị trường, vĩ mô, cross-asset hoặc company health. Nó không phải dự báo chắc chắn và không phải khuyến nghị đầu tư cá nhân hóa.",
            severity="medium",
        )
    if surface == "pro_lab":
        return TrustDisclaimer(
            title="Research Caveat",
            short_text="Backtest và scenario chỉ để nghiên cứu giả định, không phải dự báo chắc chắn cho tương lai.",
            full_text="Pro Lab là sandbox research có assumptions, caveats và audit trail. Mọi output nên được đọc như workspace nghiên cứu có cấu trúc, không phải advisory output.",
            severity="high",
        )
    return TrustDisclaimer(
        title=topic or "Trust Note",
        short_text="Nội dung này nhằm hỗ trợ hiểu và hành động an toàn hơn, không phải lời khuyên chắc chắn.",
        full_text="Nội dung này được thiết kế theo trust-first và education-first. Hãy đọc nó như công cụ giải thích và hỗ trợ hành vi tốt hơn, không phải cam kết kết quả.",
        severity="medium",
    )


def extra_guardrails_for_role(*, surface: str, role: str | None, risk_classes: tuple[str, ...]) -> tuple[str, ...]:
    guardrails: list[str] = []
    if surface in {"insights", "guided_investing", "pro_lab"}:
        guardrails.append("Ưu tiên đọc rủi ro, độ nhạy và caveat trước khi nghĩ tới kết luận.")
    if RISK_MISSING_DISCLAIMER in risk_classes:
        guardrails.append("Disclaimer mặc định đã được chèn vào vì content runtime chưa có bản riêng đã review.")
    if RISK_PII_PRIVACY in risk_classes:
        guardrails.append("Không chia sẻ thông tin nhận diện cá nhân, số tài khoản, OTP hay dữ liệu tài chính nhạy cảm.")
    if role == "coach":
        guardrails.append("Coach ưu tiên bước nhỏ an toàn, không đẩy hành động rủi ro khi dữ liệu nền chưa đủ.")
    return tuple(dict.fromkeys(guardrails))
