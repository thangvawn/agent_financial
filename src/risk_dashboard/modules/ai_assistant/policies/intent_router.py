from __future__ import annotations

import re

from risk_dashboard.modules.ai_assistant.domain.contracts import IntentDecision


INTENT_VERSION = "intent_router_v2_rule_hybrid"


class IntentRouter:
    """Small, testable intent router before any response building.

    This is intentionally rule-hybrid rather than LLM-based for public fintech
    safety: deterministic high-risk routes beat creative classification.
    """

    def classify(self, *, prompt: str, surface: str, trigger: str | None = None) -> IntentDecision:
        lowered = _normalize(prompt)
        if trigger and not lowered:
            return IntentDecision(intent=trigger.strip().lower(), confidence=0.92, reason="explicit_trigger")

        risky = _risk_labels(lowered)
        if risky:
            return IntentDecision(
                intent="risky_high_stakes",
                confidence=0.95,
                reason="high_risk_keyword",
                risk_labels=risky,
            )

        if _is_greeting(lowered):
            return IntentDecision(intent="smalltalk_greeting", confidence=0.9, reason="greeting")

        candidates: list[tuple[str, float, str]] = []
        _score(candidates, "educational", 0.84, "concept_keywords", lowered, ("giải thích", "giai thich", "nghĩa là gì", "nghia la gi", "tóm tắt", "tom tat", "học", "learn", "define", "what is"))
        _score(candidates, "goal_planning", 0.86, "goal_keywords", lowered, ("goal", "mục tiêu", "muc tieu", "kế hoạch", "ke hoach", "tiết kiệm", "tiet kiem", "deadline"))
        _score(candidates, "financial_health", 0.86, "health_keywords", lowered, ("financial health", "sức khỏe tài chính", "suc khoe tai chinh", "dòng tiền", "dong tien", "nợ", "no", "quỹ dự phòng", "quy du phong"))
        _score(candidates, "investing_explanation", 0.84, "investing_keywords", lowered, ("risk score", "drawdown", "volatility", "biến động", "bien dong", "watchlist", "portfolio", "danh mục", "danh muc"))
        _score(candidates, "market_insight", 0.84, "market_keywords", lowered, ("market", "thị trường", "thi truong", "vĩ mô", "vi mo", "macro", "scenario", "insight", "driver"))
        _score(candidates, "product_navigation", 0.82, "navigation_keywords", lowered, ("mở", "mo", "ở đâu", "o dau", "đi tới", "di toi", "module", "trang nào", "trang nao"))
        _score(candidates, "troubleshooting", 0.82, "troubleshooting_keywords", lowered, ("lỗi", "loi", "không chạy", "khong chay", "bug", "fail", "không thấy", "khong thay"))

        if candidates:
            intent, confidence, reason = max(candidates, key=lambda item: item[1])
            return IntentDecision(intent=intent, confidence=confidence, reason=reason)

        if surface == "learning":
            return IntentDecision(intent="educational", confidence=0.72, reason="surface_default_learning")
        if surface in {"financial_health", "goals", "home", "community"}:
            return IntentDecision(intent="coachable_action", confidence=0.7, reason="surface_default_coach")
        if surface in {"guided_investing", "insights"}:
            return IntentDecision(intent="market_insight", confidence=0.74, reason="surface_default_analyst")
        if surface == "pro_lab":
            return IntentDecision(intent="research_assist", confidence=0.76, reason="surface_default_pro")

        return IntentDecision(intent="general_help", confidence=0.45, reason="low_signal", needs_clarification=True)


def _normalize(prompt: str) -> str:
    return re.sub(r"\s+", " ", (prompt or "").strip().lower())


def _is_greeting(text: str) -> bool:
    normalized = re.sub(r"[!?.。,]+", "", text).strip()
    return normalized in {
        "hi",
        "hello",
        "hey",
        "chào",
        "chao",
        "xin chào",
        "xin chao",
        "alo",
    }


def _score(
    candidates: list[tuple[str, float, str]],
    intent: str,
    confidence: float,
    reason: str,
    text: str,
    keywords: tuple[str, ...],
) -> None:
    if any(keyword in text for keyword in keywords):
        candidates.append((intent, confidence, reason))


def _risk_labels(text: str) -> tuple[str, ...]:
    labels: list[str] = []
    if any(keyword in text for keyword in ("all in", "margin", "chắc thắng", "chac thang", "không thể thua", "khong the thua", "x2", "x3")):
        labels.append("overconfident_investing_language")
    if any(keyword in text for keyword in ("mua mã", "mua ma", "nên mua", "nen mua", "bán mã", "ban ma", "entry", "exit", "top pick")):
        labels.append("implicit_personalized_financial_advice")
    if any(keyword in text for keyword in ("telegram", "whatsapp", "room riêng", "room rieng", "bao lãi", "bao lai", "guaranteed")):
        labels.append("fraud_or_scam_content")
    if any(keyword in text for keyword in ("otp", "cccd", "cmnd", "số tài khoản", "so tai khoan", "password", "mật khẩu", "mat khau")):
        labels.append("pii_or_privacy_issue")
    if any(keyword in text for keyword in ("tuyệt vọng", "tuyet vong", "hoảng", "hoang", "panic", "mất hết tiền", "mat het tien", "không muốn sống", "khong muon song")):
        labels.append("emotional_vulnerability")
    return tuple(dict.fromkeys(labels))
