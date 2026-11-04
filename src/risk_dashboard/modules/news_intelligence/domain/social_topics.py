"""Conservative entity and discussion grouping with attributed extractive briefs."""

from __future__ import annotations

import json
import re
from functools import lru_cache

from risk_dashboard.modules.news_intelligence.domain.social_content import duplicate_digest
from risk_dashboard.platform.database.config import project_root

EVENTS = {
    "earnings": ("lợi nhuận", "kết quả kinh doanh", "earnings", "revenue"),
    "rates": ("lãi suất", "interest rate", "fed rate", "fomc"),
    "inflation": ("lạm phát", "inflation", "cpi"),
    "dividend": ("cổ tức", "dividend"),
    "market": ("thị trường", "vnindex", "vn-index", "stock market"),
}
STOP = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "của",
    "và",
    "trong",
    "với",
    "những",
    "các",
    "một",
}


@lru_cache(maxsize=1)
def instruments() -> dict[str, str]:
    try:
        rows = json.loads((project_root() / "data/vn_market/universe.json").read_text())["tickers"]
        catalog = {str(r["symbol"]): f"equity:{r['exchange']}:{r['symbol']}" for r in rows}
    except (OSError, KeyError, ValueError, TypeError):
        catalog = {}
    # Explicit namespaces for the small set of international assets with unambiguous aliases.
    catalog.update(
        {
            "BTC": "crypto:BTC",
            "ETH": "crypto:ETH",
            "XAUUSD": "commodity:XAUUSD",
            "EURUSD": "forex:EURUSD",
            "USDVND": "forex:USDVND",
        }
    )
    return catalog


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    aliases = {
        "BTC-USD": "BTC",
        "BTC/USD": "BTC",
        "ETH-USD": "ETH",
        "ETH/USD": "ETH",
        "EURUSD=X": "EURUSD",
        "EUR/USD": "EURUSD",
        "VND=X": "USDVND",
        "USD/VND": "USDVND",
        "XAU/USD": "XAUUSD",
    }
    return aliases.get(value, value)


def entities(text: str) -> list[dict]:
    result = []
    catalog = instruments()
    for match in re.finditer(
        r"(?<![\w])(?:\$|HOSE:|HSX:|HNX:|UPCOM:)?[A-Z][A-Z0-9]{1,6}(?![\w])", text
    ):
        raw = match.group()
        symbol = raw.split(":")[-1].lstrip("$")
        identifier = catalog.get(symbol)
        # A finance term elsewhere in a long description does not turn every
        # acronym (VTV, VIP, USD, etc.) into a Vietnamese listed company.
        prefix = text[max(0, match.start() - 90) : match.start()]
        context = bool(
            re.search(
                r"(?i:cổ phiếu|mã(?: chứng khoán)?|stock|shares|ticker)\s*[:(]?\s*"
                r"(?:[A-Z]{2,6}\s*[,/&]\s*)*$",
                prefix,
            )
        )
        if identifier and (
            context
            or raw.startswith("$")
            or ":" in raw
            or symbol in {"BTC", "ETH", "XAUUSD", "EURUSD", "USDVND"}
        ):
            if not any(x["id"] == identifier for x in result):
                result.append(
                    {
                        "id": identifier,
                        "symbol": symbol,
                        "evidence": raw,
                        "match": "explicit" if raw != symbol else "contextual",
                    }
                )
    for name, symbol in (("bitcoin", "BTC"), ("ethereum", "ETH")):
        if re.search(rf"\b{name}\b", text, re.I) and not any(x["symbol"] == symbol for x in result):
            result.append(
                {"id": catalog[symbol], "symbol": symbol, "evidence": name, "match": "explicit"}
            )
    return result[:12]


def enrich(payload: dict) -> dict:
    text = payload["title"] + " " + payload["text"] + " " + payload.get("transcript", "")[:6000]
    return {
        **payload,
        "entities": entities(text),
        "events": [key for key, words in EVENTS.items() if any(w in text.lower() for w in words)],
        "stance": "unknown",
    }


def same_discussion(left: dict, right: dict) -> bool:
    a = {x["id"] for x in left.get("entities", [])}
    b = {x["id"] for x in right.get("entities", [])}
    if a != b or left["market"] != right["market"]:
        return False
    if set(left.get("events", [])) != set(right.get("events", [])):
        return False
    x = set(re.findall(r"\w+", left["title"].casefold())) - STOP
    y = set(re.findall(r"\w+", right["title"].casefold())) - STOP
    return bool(x and y) and len(x & y) / len(x | y) >= (0.55 if a else 0.7)


def build_topics(posts: list[dict]) -> list[dict]:
    groups: list[list[dict]] = []
    for post in sorted(posts, key=lambda p: (p["first_seen_at"], p["id"])):
        for group in groups:
            anchor = group[0]
            first = post.get("published_ts") or post["first_seen_at"]
            other = anchor.get("published_ts") or anchor["first_seen_at"]
            if abs(first - other) <= 172800 and same_discussion(post, anchor):
                group.append(post)
                break
        else:
            groups.append([post])
    topics = []
    for group in groups:
        evidence, hashes = [], set()
        for p in group:
            digest = duplicate_digest(p)
            if digest in hashes:
                continue
            hashes.add(digest)
            excerpt = (p.get("transcript") or p["text"]).strip()[:420]
            if excerpt:
                evidence.append(
                    {
                        "post_id": p["id"],
                        "revision": p["revision"],
                        "url": p["url"],
                        "author": p["author"],
                        "platform": p["platform"],
                        "excerpt": excerpt,
                        "kind": "source_excerpt",
                        "content_kind": "transcript" if p.get("transcript") else p["content_kind"],
                    }
                )
        topics.append(
            {
                "id": group[0]["id"],
                "title": group[0]["title"],
                "posts": group,
                "post_count": len(group),
                "original_count": len(hashes),
                "author_count": len({(p["platform"], p["author"]) for p in group if p["author"]}),
                "entities": group[0].get("entities", []),
                "evidence": evidence[:5],
                "method": "source_excerpts_v1",
                "verification": "unverified",
                "sort_ts": max(p.get("published_ts") or p["first_seen_at"] for p in group),
            }
        )
    return sorted(topics, key=lambda t: (t["sort_ts"], t["id"]), reverse=True)
