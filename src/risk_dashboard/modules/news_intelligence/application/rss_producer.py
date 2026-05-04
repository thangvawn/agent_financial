from __future__ import annotations

import hashlib
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from risk_dashboard.modules.news_intelligence.application.enrichment import enrich_article
from risk_dashboard.modules.news_intelligence.domain.entities import NewsArticle, NewsSource, utc_now_iso


DEFAULT_NEWS_SOURCES: tuple[NewsSource, ...] = (
    NewsSource("fed_press", "Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml", "macro", "US", 1, "official", "global_macro"),
    NewsSource("sec_press", "SEC", "https://www.sec.gov/news/pressreleases.rss", "regulation", "US", 1, "official", "us_markets"),
    NewsSource("imf_news", "IMF", "https://www.imf.org/en/News/rss?language=eng", "macro", "global", 1, "official", "global_macro"),
    NewsSource("ecb_press", "ECB", "https://www.ecb.europa.eu/rss/press.html", "macro", "EU", 1, "official", "global_macro"),
    NewsSource("bbc_business", "BBC Business", "http://feeds.bbci.co.uk/news/business/rss.xml", "markets", "global", 2, "major_media", "global_markets"),
    NewsSource("bbc_world", "BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml", "geopolitics", "global", 2, "major_media", "global_macro"),
    NewsSource("wsj_markets", "WSJ Markets", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "markets", "US", 2, "major_media", "us_markets"),
    NewsSource("marketwatch", "MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", "markets", "US", 2, "major_media", "us_markets"),
    NewsSource("oilprice", "OilPrice", "https://oilprice.com/rss/main", "commodities", "global", 3, "specialist", "commodities_energy"),
    NewsSource("coindesk", "CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/", "crypto", "global", 3, "specialist", "crypto"),
    NewsSource("techcrunch", "TechCrunch", "https://techcrunch.com/feed/", "technology", "US", 3, "specialist", "technology"),
    NewsSource("cafef_stock", "CafeF Chứng khoán", "https://cafef.vn/thi-truong-chung-khoan.rss", "markets", "VN", 3, "local_media", "vn_markets"),
    NewsSource("cafef_bank", "CafeF Tài chính - Ngân hàng", "https://cafef.vn/tai-chinh-ngan-hang.rss", "markets", "VN", 3, "local_media", "vn_markets"),
    NewsSource("cafef_macro", "CafeF Vĩ mô", "https://cafef.vn/vi-mo-dau-tu.rss", "macro", "VN", 3, "local_media", "vn_macro"),
    NewsSource("vneconomy_stock", "VnEconomy Chứng khoán", "https://vneconomy.vn/rss/chung-khoan.rss", "markets", "VN", 3, "local_media", "vn_markets"),
    NewsSource("vneconomy_finance", "VnEconomy Tài chính", "https://vneconomy.vn/rss/tai-chinh.rss", "markets", "VN", 3, "local_media", "vn_markets"),
    NewsSource("vneconomy_world", "VnEconomy Thế giới", "https://vneconomy.vn/rss/the-gioi.rss", "geopolitics", "VN", 3, "local_media", "vn_macro"),
    NewsSource("vietnamplus_economy", "VietnamPlus Kinh tế", "https://www.vietnamplus.vn/rss/kinhte.rss", "macro", "VN", 3, "local_media", "vn_macro"),
    NewsSource("vietnamplus_finance", "VietnamPlus Tài chính", "https://www.vietnamplus.vn/rss/kinhte/taichinh.rss", "markets", "VN", 3, "local_media", "vn_markets"),
)


class NewsRssProducer:
    def __init__(self, sources: tuple[NewsSource, ...] = DEFAULT_NEWS_SOURCES, timeout_seconds: float = 5.0) -> None:
        self.sources = sources
        self.timeout_seconds = timeout_seconds

    def fetch(self, *, max_sources: int | None = None) -> tuple[list[NewsArticle], dict]:
        articles: list[NewsArticle] = []
        errors: list[dict[str, str]] = []
        selected_sources = self.sources[:max_sources] if max_sources else self.sources
        with ThreadPoolExecutor(max_workers=min(6, max(1, len(selected_sources)))) as executor:
            futures = {executor.submit(self._fetch_source, source): source for source in selected_sources}
            for future in as_completed(futures):
                source = futures[future]
                try:
                    articles.extend(future.result())
                except Exception as exc:  # noqa: BLE001 - feed failures should not break the dashboard.
                    errors.append({"source_id": source.source_id, "error": str(exc)[:180]})
        return articles, {
            "source_count": len(selected_sources),
            "successful_source_count": len(selected_sources) - len(errors),
            "errors": errors[:10],
        }

    def _fetch_source(self, source: NewsSource) -> list[NewsArticle]:
        request = urllib.request.Request(
            source.url,
            headers={
                "User-Agent": "risk-dashboard-news-intelligence/0.1",
                "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            body = response.read(1_500_000)
        root = ET.fromstring(body)
        fetched_at = utc_now_iso()
        return [enrich_article(article) for article in self._parse_items(root=root, source=source, fetched_at=fetched_at)]

    def _parse_items(self, *, root: ET.Element, source: NewsSource, fetched_at: str) -> list[NewsArticle]:
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        articles: list[NewsArticle] = []
        for item in items[:30]:
            headline = _clean(_find_text(item, ("title", "{http://www.w3.org/2005/Atom}title")))
            if not headline:
                continue
            summary = _clean(
                _find_text(
                    item,
                    (
                        "description",
                        "summary",
                        "{http://www.w3.org/2005/Atom}summary",
                        "{http://purl.org/rss/1.0/modules/content/}encoded",
                    ),
                )
            )
            url = _find_link(item)
            published_at, sort_ts = _published_at(item)
            article_id = _article_id(source.source_id, url or headline)
            articles.append(
                NewsArticle(
                    article_id=article_id,
                    headline=headline[:280],
                    summary=summary[:600],
                    source=source.name,
                    source_id=source.source_id,
                    source_tier=source.tier,
                    source_flag=source.flag,
                    region=source.region,
                    category=source.category,
                    url=url,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    sort_ts=sort_ts,
                )
            )
        return articles


def _find_text(item: ET.Element, names: tuple[str, ...]) -> str:
    for name in names:
        node = item.find(name)
        if node is not None and node.text:
            return node.text
    return ""


def _find_link(item: ET.Element) -> str:
    link = _find_text(item, ("link",))
    if link:
        return link.strip()
    atom_link = item.find("{http://www.w3.org/2005/Atom}link")
    if atom_link is not None:
        return str(atom_link.attrib.get("href") or "")
    return ""


def _published_at(item: ET.Element) -> tuple[str, int]:
    value = _find_text(item, ("pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"))
    parsed: datetime
    try:
        parsed = parsedate_to_datetime(value).astimezone(timezone.utc) if value else datetime.now(timezone.utc)
    except Exception:  # noqa: BLE001
        parsed = datetime.now(timezone.utc)
    return parsed.isoformat(), int(parsed.timestamp())


def _clean(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _article_id(source_id: str, raw: str) -> str:
    return hashlib.sha1(f"{source_id}:{raw}".encode("utf-8")).hexdigest()[:24]
