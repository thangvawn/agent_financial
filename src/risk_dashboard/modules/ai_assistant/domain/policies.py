from __future__ import annotations

ROLE_TUTOR = "tutor"
ROLE_COACH = "coach"
ROLE_ANALYST = "analyst"
ROLE_PRO_ASSISTANT = "pro_assistant"

PROMPT_VERSION = "assistant_v1"
POLICY_VERSION = "trust_education_v1"


def classify_intent(prompt: str, *, surface: str, trigger: str | None = None) -> str:
    lowered = prompt.strip().lower()
    if trigger:
        return trigger.strip().lower()
    if any(keyword in lowered for keyword in ("mua", "ban", "all in", "margin", "pick", "entry", "exit")):
        return "risky_investing_prompt"
    if any(keyword in lowered for keyword in ("giai thich", "nghia la gi", "tom tat", "what is", "define")):
        return "explain"
    if any(keyword in lowered for keyword in ("tiep theo", "nen lam gi", "next step", "what next")):
        return "next_step"
    if surface in {"learning", "financial_health", "goals", "home", "community"}:
        return "coachable_action"
    if surface in {"guided_investing", "insights"}:
        return "market_explanation"
    if surface == "pro_lab":
        return "research_assist"
    return "general_help"


def detect_risk_labels(prompt: str) -> tuple[str, ...]:
    lowered = prompt.strip().lower()
    labels: list[str] = []
    if any(keyword in lowered for keyword in ("mua", "ban", "chac tang", "all in", "margin", "top pick", "entry", "exit")):
        labels.append("risky_investing_prompt")
    if any(keyword in lowered for keyword in ("telegram", "whatsapp", "x2", "x3", "bao lai", "guaranteed", "room rieng")):
        labels.append("scam_or_pump")
    if any(keyword in lowered for keyword in ("toi hoang", "mat het tien", "panic", "khong muon song", "tuyet vong")):
        labels.append("emotional_vulnerability")
    return tuple(dict.fromkeys(labels))


def resolve_role(
    *,
    surface: str,
    role_hint: str | None,
    intent: str,
    has_pro_scope: bool = False,
) -> str:
    if role_hint:
        return role_hint
    if surface == "pro_lab" and has_pro_scope:
        return ROLE_PRO_ASSISTANT
    if surface == "learning":
        return ROLE_TUTOR if intent == "explain" else ROLE_COACH
    if surface in {"financial_health", "goals", "home", "community"}:
        return ROLE_COACH
    if surface in {"guided_investing", "insights"}:
        return ROLE_ANALYST
    return ROLE_TUTOR


def build_guardrails(*, role: str, risk_labels: tuple[str, ...], surface: str) -> tuple[str, ...]:
    guardrails: list[str] = []
    if role in {ROLE_ANALYST, ROLE_PRO_ASSISTANT}:
        guardrails.append("Giải thích này nhằm hỗ trợ hiểu rủi ro và bối cảnh, không phải khuyến nghị mua bán.")
    if "risky_investing_prompt" in risk_labels:
        guardrails.append("Hệ thống sẽ không chọn mã hay đưa certainty về kết quả đầu tư.")
    if "scam_or_pump" in risk_labels:
        guardrails.append("Nội dung có dấu hiệu thao túng hoặc lôi kéo sẽ bị chặn và chuyển sang cảnh báo an toàn.")
    if surface in {"financial_health", "goals"}:
        guardrails.append("Đây là hướng dẫn giáo dục và hành động nhỏ, không thay thế tư vấn tài chính cá nhân hóa đầy đủ.")
    return tuple(dict.fromkeys(guardrails))
