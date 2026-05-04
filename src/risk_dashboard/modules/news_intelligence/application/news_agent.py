from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from risk_dashboard.modules.news_intelligence.application.services import NewsIntelligenceService

load_dotenv()


COMMODITY_TERMS = {
    "commodity",
    "commodities",
    "hang hoa",
    "hàng hóa",
    "dau",
    "dầu",
    "oil",
    "gold",
    "vang",
    "vàng",
    "gas",
    "energy",
    "nang luong",
    "năng lượng",
    "copper",
    "dong",
    "đồng",
}
MACRO_TERMS = {"fed", "fomc", "lai suat", "lãi suất", "inflation", "cpi", "usd", "bond", "yield", "rate"}
CRYPTO_TERMS = {"btc", "bitcoin", "crypto", "ethereum", "eth"}
REGULATION_TERMS = {"sec", "regulation", "regulatory", "quy dinh", "quy định", "policy"}
GEOPOLITICS_TERMS = {"war", "chien tranh", "chiến tranh", "geopolitics", "china", "trung quoc", "trung quốc"}
TECH_TERMS = {"ai", "chip", "semiconductor", "technology", "tech", "openai", "nvidia"}


@dataclass(frozen=True)
class NewsChatContext:
    category: str | None = None
    region: str | None = None
    source_group: str | None = None
    preset: str | None = None
    time_range_hours: int = 168
    active_article_id: str | None = None
    history: tuple[dict[str, str], ...] = ()
    user_mode: str = "investor"


class NewsAnalystAgent:
    """Specialized, bounded news analyst.

    The agent intentionally starts from collected news data instead of browsing
    the open web. That keeps answers traceable and prevents the News surface from
    inheriting the broader product coach's scope.
    """

    def __init__(self, service: NewsIntelligenceService | None = None) -> None:
        self.service = service or NewsIntelligenceService()
        self.llm = NewsAnalystLLMRuntime()
        self.external_search = TavilyNewsSearch()

    def respond(self, *, message: str, context: NewsChatContext, conversation_id: str | None = None) -> dict[str, Any]:
        prompt = _clean(message)
        inferred_category = _infer_category(prompt, fallback=context.category)
        search_terms = _search_terms(prompt)
        feed = self.service.get_feed(
            category=inferred_category,
            query=None,
            limit=80,
            time_range_hours=context.time_range_hours,
            region=context.region,
            source_group=context.source_group,
            preset=context.preset,
            force=False,
        )
        articles = feed.get("articles") or []
        ranked_articles = _rank_articles(articles, search_terms)
        active_article = _find_active_article(articles, context.active_article_id)
        evidence = _dedupe_articles([*(ranked_articles[:8]), *([active_article] if active_article else [])])
        if not evidence and articles:
            evidence = articles[:6]

        assumption_warning = _assumption_warning(prompt, evidence)
        external_results = self.external_search.search(prompt) if _should_search_external(prompt, evidence, assumption_warning) else []
        key_points = _build_key_points(prompt=prompt, articles=evidence, category=inferred_category, warning=assumption_warning)
        explanation = _build_explanation(prompt=prompt, articles=evidence, feed=feed, warning=assumption_warning)
        confidence = "moderate" if len(evidence) >= 3 else "limited"
        sources = [
            {
                "article_id": article.get("article_id") or article.get("id"),
                "label": article.get("headline") or article.get("source") or "News article",
                "source": article.get("source") or "Unknown",
                "url": article.get("url") or "",
                "published_at": article.get("published_at") or "",
            }
            for article in evidence[:5]
        ]
        sources.extend(
            {
                "article_id": result.get("url") or result.get("title"),
                "label": result.get("title") or "External source",
                "source": result.get("source") or "Tavily",
                "url": result.get("url") or "",
                "published_at": result.get("published_at") or "",
            }
            for result in external_results[:4]
        )

        affected_markets = sorted(set(
            market for a in evidence for market in (a.get("affected_markets") or [])
        ))[:6]
        what_to_monitor = sorted(set(
            m for a in evidence for m in (a.get("what_to_monitor") or [])
        ))[:5]

        draft = {
            "conversation_id": conversation_id or f"news_chat_{uuid4().hex[:16]}",
            "message_id": f"news_msg_{uuid4().hex[:16]}",
            "role": "news_analyst",
            "title": _title(prompt, inferred_category),
            "summary": _summary(evidence=evidence, warning=assumption_warning),
            "explanation": explanation,
            "key_points": key_points,
            "why_it_matters": _why_it_matters(evidence, assumption_warning),
            "affected_markets": affected_markets,
            "what_to_monitor": what_to_monitor,
            "sources": sources,
            "tools_used": [
                "search_news_articles",
                "get_market_pulse",
                "get_news_clusters",
                *(["tavily_news_search"] if external_results else []),
                *(["openai_news_reasoning"] if self.llm.configured else []),
            ],
            "confidence_label": confidence,
            "data_freshness": feed.get("freshness") or "unknown",
            "safety_note": "Tin tức là bối cảnh phân tích, không phải khuyến nghị mua/bán.",
            "warnings": [assumption_warning] if assumption_warning else [],
            "suggested_questions": _suggested_questions(inferred_category),
            "suggested_followups": _suggested_questions(inferred_category),
        }
        return self.llm.compose(
            draft=draft,
            prompt=prompt,
            feed=feed,
            internal_articles=evidence,
            external_results=external_results,
            category=inferred_category,
            history=context.history,
        )


class NewsAnalystLLMRuntime:
    def __init__(self) -> None:
        self.enabled = os.getenv("NEWS_ANALYST_AGENT_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
        self.model_name = os.getenv("NEWS_ANALYST_MODEL", os.getenv("AI_ASSISTANT_MODEL", "gpt-4o-mini"))
        self.configured = self.enabled and bool(os.getenv("OPENAI_API_KEY"))

    def compose(
        self,
        *,
        draft: dict[str, Any],
        prompt: str,
        feed: dict[str, Any],
        internal_articles: list[dict[str, Any]],
        external_results: list[dict[str, Any]],
        category: str | None,
        history: tuple[dict[str, str], ...] = (),
    ) -> dict[str, Any]:
        if not self.configured:
            return draft
        try:
            payload = self._invoke(
                draft=draft,
                prompt=prompt,
                feed=feed,
                internal_articles=internal_articles,
                external_results=external_results,
                category=category,
                history=history,
            )
        except Exception:
            return {
                **draft,
                "warnings": [
                    *list(draft.get("warnings") or []),
                    "OpenAI reasoning tạm thời không khả dụng; câu trả lời đang dùng lớp phân tích rule-based.",
                ],
            }
        return _merge_llm_payload(draft, payload)

    def _invoke(
        self,
        *,
        draft: dict[str, Any],
        prompt: str,
        feed: dict[str, Any],
        internal_articles: list[dict[str, Any]],
        external_results: list[dict[str, Any]],
        category: str | None,
        history: tuple[dict[str, str], ...],
    ) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=self.model_name, temperature=0.2, timeout=10, max_retries=0)
        response = llm.invoke(
            [
                SystemMessage(content=_llm_system_prompt()),
                HumanMessage(
                    content=json.dumps(
                        {
                            "user_question": prompt,
                            "recent_conversation": _compact_history(history),
                            "inferred_category": category,
                            "feed_freshness": feed.get("freshness"),
                            "selected_filters": feed.get("selected_filters") or {},
                            "market_pulse": feed.get("pulse") or {},
                            "clusters": (feed.get("clusters") or [])[:6],
                            "internal_articles": [_compact_article(article) for article in internal_articles[:8]],
                            "external_results": external_results[:5],
                            "safe_rule_based_draft": {
                                "title": draft.get("title"),
                                "summary": draft.get("summary"),
                                "explanation": draft.get("explanation"),
                                "key_points": draft.get("key_points"),
                                "warnings": draft.get("warnings"),
                            },
                        },
                        ensure_ascii=False,
                    )
                ),
            ]
        )
        return _parse_json_object(str(response.content))


class TavilyNewsSearch:
    def __init__(self) -> None:
        self.api_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.enabled = bool(self.api_key) and os.getenv("NEWS_ANALYST_TAVILY_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
        self.max_results = int(os.getenv("NEWS_ANALYST_TAVILY_MAX_RESULTS", "5") or "5")

    def search(self, query: str) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        payload = {
            "api_key": self.api_key,
            "query": query,
            "topic": "news",
            "search_depth": "advanced",
            "max_results": max(1, min(self.max_results, 8)),
            "include_answer": False,
            "include_raw_content": False,
        }
        request = urllib.request.Request(
            "https://api.tavily.com/search",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "northstar-news-analyst/0.1"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            body = response.read(1_500_000)
        data = json.loads(body.decode("utf-8"))
        results = data.get("results") or []
        compact: list[dict[str, Any]] = []
        for item in results[: self.max_results]:
            if not isinstance(item, dict):
                continue
            compact.append(
                {
                    "title": _clean(str(item.get("title") or ""))[:240],
                    "url": str(item.get("url") or ""),
                    "source": _source_from_url(str(item.get("url") or "")),
                    "content": _clean(str(item.get("content") or ""))[:600],
                    "score": item.get("score"),
                    "published_at": str(item.get("published_date") or item.get("published_at") or ""),
                }
            )
        return compact


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _normalize(value: str) -> str:
    return _clean(value).lower()


def _infer_category(prompt: str, fallback: str | None) -> str | None:
    text = _normalize(prompt)
    if any(term in text for term in COMMODITY_TERMS):
        return "commodities"
    if any(term in text for term in CRYPTO_TERMS):
        return "crypto"
    if any(term in text for term in REGULATION_TERMS):
        return "regulation"
    if any(term in text for term in GEOPOLITICS_TERMS):
        return "geopolitics"
    if any(term in text for term in TECH_TERMS):
        return "technology"
    if any(term in text for term in MACRO_TERMS):
        return "macro"
    if fallback and fallback.lower() != "all":
        return fallback.lower()
    return None


def _search_terms(prompt: str) -> set[str]:
    tokens = re.findall(r"[A-Za-zÀ-ỹ0-9%]{3,}", _normalize(prompt))
    stopwords = {
        "hom",
        "hôm",
        "nay",
        "toi",
        "tôi",
        "thi",
        "thì",
        "len",
        "lên",
        "xuong",
        "xuống",
        "tac",
        "tác",
        "dong",
        "động",
        "khong",
        "không",
        "market",
        "news",
    }
    return {token for token in tokens if token not in stopwords}


def _rank_articles(articles: list[dict[str, Any]], terms: set[str]) -> list[dict[str, Any]]:
    if not terms:
        return articles

    def score(article: dict[str, Any]) -> tuple[int, int]:
        haystack = _normalize(" ".join(str(article.get(key) or "") for key in ("headline", "summary", "source", "category", "region")))
        matched = sum(1 for term in terms if term in haystack)
        impact_bonus = 2 if article.get("impact") == "high" else 0
        return (matched + impact_bonus, int(article.get("sort_ts") or 0))

    return sorted(articles, key=score, reverse=True)


def _find_active_article(articles: list[dict[str, Any]], article_id: str | None) -> dict[str, Any] | None:
    if not article_id:
        return None
    return next((article for article in articles if (article.get("article_id") or article.get("id")) == article_id), None)


def _dedupe_articles(articles: list[dict[str, Any] | None]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for article in articles:
        if not article:
            continue
        article_id = str(article.get("article_id") or article.get("id") or article.get("headline") or "")
        if article_id in seen:
            continue
        seen.add(article_id)
        deduped.append(article)
    return deduped


def _assumption_warning(prompt: str, articles: list[dict[str, Any]]) -> str:
    text = _normalize(prompt)
    mentions_large_fed_cut = "fed" in text and ("2%" in text or "200" in text) and any(term in text for term in {"giam", "giảm", "cut", "cat", "cắt"})
    if not mentions_large_fed_cut:
        return ""
    evidence_text = _normalize(" ".join(str(article.get("headline") or "") for article in articles))
    if "fed" in evidence_text and ("cut" in evidence_text or "giam" in evidence_text or "giảm" in evidence_text):
        return ""
    return "Mình chưa thấy bài trong news feed hiện tại xác nhận Fed giảm 2% lãi suất; nên phần dưới xem đây là giả định cần kiểm chứng trước."


def _should_search_external(prompt: str, articles: list[dict[str, Any]], warning: str) -> bool:
    text = _normalize(prompt)
    recency_terms = {"hom nay", "hôm nay", "today", "latest", "moi nhat", "mới nhất", "vua", "vừa"}
    verification_terms = {"xac nhan", "xác nhận", "co that", "có thật", "official", "nguon", "nguồn"}
    market_terms = {"fed", "fomc", "oil", "dau", "dầu", "gold", "vàng", "vang", "usd", "rate", "lai suat", "lãi suất"}
    return bool(warning) or len(articles) < 3 or (
        any(term in text for term in recency_terms | verification_terms) and any(term in text for term in market_terms)
    )


def _build_key_points(*, prompt: str, articles: list[dict[str, Any]], category: str | None, warning: str) -> list[str]:
    points: list[str] = []
    if warning:
        points.append("Kiểm chứng sự kiện trước: nếu premise sai, kết luận thị trường sẽ đổi mạnh.")
    if category == "commodities":
        points.extend(
            [
                "Hàng hóa thường phản ứng qua ba kênh: USD, kỳ vọng tăng trưởng và chi phí vốn/tồn kho.",
                "Vàng nhạy với real yield; dầu nhạy thêm với nhu cầu, OPEC và rủi ro địa chính trị.",
            ]
        )
    elif category == "macro":
        points.extend(
            [
                "Tin vĩ mô nên đọc cùng bond yield, USD và kỳ vọng lạm phát, không chỉ headline.",
                "Tác động ngắn hạn có thể trái chiều nếu thị trường đã định giá trước quyết định.",
            ]
        )
    elif category == "crypto":
        points.append("Crypto thường phản ứng mạnh với thanh khoản và risk appetite, nhưng độ nhiễu headline cao.")
    else:
        points.append("Ưu tiên đọc cụm tin cùng chủ đề để tránh bị một headline đơn lẻ dẫn dắt.")
    if articles:
        top_sources = ", ".join(dict.fromkeys(str(article.get("source") or "Unknown") for article in articles[:3]))
        points.append(f"Feed liên quan hiện có từ: {top_sources}.")
    return points[:4]


def _build_explanation(*, prompt: str, articles: list[dict[str, Any]], feed: dict[str, Any], warning: str) -> str:
    lines: list[str] = []
    if warning:
        lines.append(warning)
    lines.append("Mình hiểu câu hỏi này là: tin đang nói tới chính sách/lãi suất sẽ truyền sang hàng hóa qua USD, lợi suất và kỳ vọng nhu cầu.")
    if articles:
        lines.append("Trong feed hiện tại, mấy tín hiệu gần nhất mình thấy là:")
        for article in articles[:4]:
            source = article.get("source") or "Unknown"
            headline = article.get("headline") or "Untitled"
            sentiment = article.get("sentiment") or "neutral"
            impact = article.get("impact") or "medium"
            lines.append(f"- {headline} ({source}, {sentiment}, {impact} impact)")
    else:
        lines.append("Mình chưa thấy bài đủ gần trong cache news, nên sẽ xem đây là một kịch bản cần xác minh thêm.")
    lines.append("Nếu Fed thật sự mềm hơn kỳ vọng, vàng thường hưởng lợi trước qua real yield thấp hơn; dầu và hàng hóa công nghiệp thì còn phụ thuộc kỳ vọng tăng trưởng và nguồn cung.")
    lines.append("Điểm mình muốn giữ lại: đừng đọc headline Fed một mình, hãy kiểm tra USD/yield phản ứng ra sao và tin này đã được thị trường định giá trước chưa.")
    return "\n".join(lines)


def _llm_system_prompt() -> str:
    return "\n".join(
        [
            "You are News Analyst, a specialist chatbot for a financial news page.",
            "You are in an ongoing conversation. Prioritize answering the user's latest message in context, not producing a generic report.",
            "Sound like a sharp human market analyst: direct, calm, conversational, and willing to say when evidence is not enough.",
            "Answer in Vietnamese unless the user writes in English.",
            "Use internal_articles first because they are collected by the product pipeline.",
            "Use external_results only as supplementary verification and clearly avoid overclaiming if evidence is thin.",
            "If the user's premise is not confirmed by sources, say that directly and analyze it as a scenario, not a fact.",
            "Explain market impact through transmission channels such as USD, yields, risk appetite, demand, supply, policy, and sector exposure.",
            "Do not recommend buying or selling securities, do not imply certainty, and do not invent sources, prices, dates, or decisions.",
            "Do not mention implementation details like tools, retrieval, JSON, pipeline, or that you 'scanned News Intelligence' unless the user asks how you work.",
            "Keep the response concise but analytical. Start with the answer, then give 2-4 reasons. Mention the strongest caveat.",
            "Return strict JSON only with keys: title, summary, explanation, key_points, confidence_label, suggested_questions.",
        ]
    )


def _compact_history(history: tuple[dict[str, str], ...]) -> list[dict[str, str]]:
    compact: list[dict[str, str]] = []
    for message in history[-8:]:
        sender = str(message.get("sender") or "").strip()
        content = _clean(str(message.get("content") or message.get("body") or ""))
        if sender not in {"user", "assistant"} or not content:
            continue
        compact.append({"sender": sender, "content": content[:700]})
    return compact


def _compact_article(article: dict[str, Any]) -> dict[str, Any]:
    return {
        "article_id": article.get("article_id") or article.get("id"),
        "headline": article.get("headline"),
        "summary": article.get("summary"),
        "source": article.get("source"),
        "url": article.get("url"),
        "published_at": article.get("published_at"),
        "region": article.get("region"),
        "category": article.get("category"),
        "sentiment": article.get("sentiment"),
        "impact": article.get("impact"),
        "tickers": article.get("tickers") or [],
    }


def _merge_llm_payload(draft: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    title = _text(payload.get("title"), fallback=str(draft.get("title") or "News analyst brief"), limit=120)
    summary = _text(payload.get("summary"), fallback=str(draft.get("summary") or ""), limit=280)
    explanation = _text(payload.get("explanation"), fallback=str(draft.get("explanation") or ""), limit=2200)
    key_points = _string_list(payload.get("key_points"), fallback=list(draft.get("key_points") or []), limit=5)
    suggested_questions = _string_list(payload.get("suggested_questions"), fallback=list(draft.get("suggested_questions") or []), limit=3)
    confidence_label = str(payload.get("confidence_label") or draft.get("confidence_label") or "limited").strip().lower()
    if confidence_label not in {"high", "moderate", "limited"}:
        confidence_label = str(draft.get("confidence_label") or "limited")
    return {
        **draft,
        "title": title,
        "summary": summary,
        "explanation": explanation,
        "key_points": key_points,
        "confidence_label": confidence_label,
        "suggested_questions": suggested_questions,
    }


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        cleaned = cleaned[start : end + 1]
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("News analyst model response must be a JSON object.")
    return payload


def _text(value: object, *, fallback: str, limit: int) -> str:
    text = _clean(str(value or ""))
    return (text or fallback)[:limit].rstrip()


def _string_list(value: object, *, fallback: list[str], limit: int) -> list[str]:
    if not isinstance(value, list):
        return fallback[:limit]
    items = [_text(item, fallback="", limit=260) for item in value]
    return [item for item in items if item][:limit] or fallback[:limit]


def _source_from_url(url: str) -> str:
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(1) if match else "Tavily"


def _title(prompt: str, category: str | None) -> str:
    if category == "commodities":
        return "Commodity impact read"
    if category == "macro":
        return "Macro news read"
    if category == "crypto":
        return "Crypto news read"
    if "?" in prompt:
        return "News question review"
    return "News analyst brief"


def _summary(*, evidence: list[dict[str, Any]], warning: str) -> str:
    if warning:
        return "Có một giả định cần kiểm chứng trước, sau đó mới đọc tác động thị trường."
    if evidence:
        return f"Mình tìm thấy {len(evidence)} tin liên quan trong feed hiện tại và tóm tắt theo hướng tác động."
    return "Chưa đủ tin liên quan trong cache hiện tại để kết luận mạnh."


def _why_it_matters(evidence: list[dict[str, Any]], warning: str) -> str:
    if warning:
        return "Cần kiểm chứng sự kiện trước khi đánh giá tác động thị trường."
    if not evidence:
        return "Chưa đủ dữ liệu để đánh giá mức độ ảnh hưởng."
    high_impact = [a for a in evidence if a.get("impact") == "high"]
    if high_impact:
        return f"Có {len(high_impact)}/{len(evidence)} tin high-impact trong feed liên quan. Cần theo dõi phản ứng thị trường."
    return "Tin tức hiện tại ở mức ảnh hưởng trung bình. Theo dõi thêm để đánh giá xu hướng."


def _suggested_questions(category: str | None) -> list[str]:
    if category == "commodities":
        return [
            "Tin này ảnh hưởng tới dầu và vàng khác nhau thế nào?",
            "USD mạnh/yếu sẽ đổi kết luận hàng hóa ra sao?",
            "Có headline nào cùng cụm làm rủi ro tăng không?",
        ]
    return [
        "Tin này ảnh hưởng tới nhóm tài sản nào trước?",
        "Có nguồn chính thống nào xác nhận chưa?",
        "Điều gì thị trường có thể đã định giá trước?",
    ]
