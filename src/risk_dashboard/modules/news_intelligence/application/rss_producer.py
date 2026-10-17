from __future__ import annotations

import gzip
import hashlib
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from threading import Lock
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from risk_dashboard.modules.news_intelligence.application.enrichment import enrich_article
from risk_dashboard.modules.news_intelligence.domain.entities import (
    NewsArticle,
    NewsSource,
    utc_now_iso,
)

DEFAULT_NEWS_SOURCES: tuple[NewsSource, ...] = (
    NewsSource("fed_press", "Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml", "macro", "US", 1, "official", "global_macro"),
    NewsSource("sec_press", "SEC", "https://www.sec.gov/news/pressreleases.rss", "regulation", "US", 1, "official", "us_markets"),
    NewsSource("bloomberg_markets", "Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss", "markets", "global", 2, "major_media", "global_macro"),
    NewsSource("ecb_press", "ECB", "https://www.ecb.europa.eu/rss/press.html", "macro", "EU", 1, "official", "global_macro"),
    NewsSource("bbc_business", "BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml", "markets", "global", 2, "major_media", "global_markets"),
    NewsSource("bbc_world", "BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", "geopolitics", "global", 2, "major_media", "global_macro"),
    NewsSource("ft_markets", "Financial Times Markets", "https://www.ft.com/markets?format=rss", "markets", "global", 2, "major_media", "us_markets"),
    NewsSource("marketwatch", "MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", "markets", "US", 2, "major_media", "us_markets"),
    NewsSource("oilprice", "OilPrice", "https://oilprice.com/rss/main", "commodities", "global", 3, "specialist", "commodities_energy"),
    NewsSource("coindesk", "CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss", "crypto", "global", 3, "specialist", "crypto"),
    NewsSource("techcrunch", "TechCrunch", "https://techcrunch.com/feed/", "technology", "US", 3, "specialist", "technology"),
    NewsSource("cafef_stock", "CafeF Chứng khoán", "https://cafef.vn/thi-truong-chung-khoan.rss", "markets", "VN", 3, "local_media", "vn_markets"),
    NewsSource("cafef_bank", "CafeF Tài chính - Ngân hàng", "https://cafef.vn/tai-chinh-ngan-hang.rss", "markets", "VN", 3, "local_media", "vn_markets"),
    NewsSource("cafef_macro", "CafeF Vĩ mô", "https://cafef.vn/vi-mo-dau-tu.rss", "macro", "VN", 3, "local_media", "vn_macro"),
    NewsSource("thanhnien_kinhte", "Thanh Niên Kinh tế", "https://thanhnien.vn/rss/kinh-te.rss", "markets", "VN", 3, "local_media", "vn_markets"),
    NewsSource("tuoitre_kinhdoanh", "Tuổi Trẻ Kinh doanh", "https://tuoitre.vn/rss/kinh-doanh.rss", "markets", "VN", 3, "local_media", "vn_markets"),
    NewsSource("nhandan_kinhte", "Nhân Dân Kinh tế", "https://nhandan.vn/rss/kinh-te.rss", "macro", "VN", 3, "local_media", "vn_macro"),
    NewsSource("vietnamplus_economy", "VietnamPlus Kinh tế", "https://www.vietnamplus.vn/rss/kinhte.rss", "macro", "VN", 3, "local_media", "vn_macro"),
    NewsSource("vietnamplus_finance", "VietnamPlus Tài chính", "https://www.vietnamplus.vn/rss/kinhte/taichinh.rss", "markets", "VN", 3, "local_media", "vn_markets"),
)


@dataclass(frozen=True)
class _FeedCacheEntry:
    """The last successful response for one feed URL.

    The cache deliberately stores the raw XML, rather than parsed articles.  A
    ``304 Not Modified`` response can therefore reuse the exact source payload
    and still run the normal parser/enrichment pipeline on every refresh.  This
    keeps conditional requests transparent to the rest of the news system.
    """

    body: bytes
    etag: str = ""
    last_modified: str = ""
    final_url: str = ""


# API handlers construct a short-lived producer for each request, so the HTTP
# validators must live at module scope to survive between requests in a worker.
# The lock protects concurrent source fetches and keeps the cache safe when
# several browser requests arrive at the same time.
_FEED_HTTP_CACHE: dict[str, _FeedCacheEntry] = {}
_FEED_HTTP_CACHE_LOCK = Lock()
_FEED_HTTP_CACHE_MAX_ENTRIES = 64


@dataclass(frozen=True)
class _FeedHttpResponse:
    body: bytes
    etag: str = ""
    last_modified: str = ""
    final_url: str = ""
    not_modified: bool = False


class NewsRssProducer:
    def __init__(self, sources: tuple[NewsSource, ...] = DEFAULT_NEWS_SOURCES, timeout_seconds: float = 5.0) -> None:
        self.sources = sources
        self.timeout_seconds = timeout_seconds

    def fetch(self, *, max_sources: int | None = None) -> tuple[list[NewsArticle], dict]:
        articles: list[NewsArticle] = []
        errors: list[dict[str, str]] = []
        not_modified_source_ids: list[str] = []
        conditional_request_source_ids: list[str] = []
        selected_sources = self.sources[:max_sources] if max_sources else self.sources
        with ThreadPoolExecutor(max_workers=min(6, max(1, len(selected_sources)))) as executor:
            futures = {
                executor.submit(self._fetch_source_with_meta, source): source
                for source in selected_sources
            }
            for future in as_completed(futures):
                source = futures[future]
                try:
                    source_articles, source_meta = future.result()
                    articles.extend(source_articles)
                    if source_meta.get("not_modified"):
                        not_modified_source_ids.append(source.source_id)
                    if source_meta.get("conditional_request"):
                        conditional_request_source_ids.append(source.source_id)
                except Exception as exc:  # noqa: BLE001 - feed failures should not break the dashboard.
                    errors.append({"source_id": source.source_id, "error": str(exc)[:180]})
        return articles, {
            "source_count": len(selected_sources),
            "successful_source_count": len(selected_sources) - len(errors),
            "source_ids": [source.source_id for source in selected_sources],
            "errors": errors[:10],
            "not_modified_source_ids": sorted(not_modified_source_ids),
            "not_modified_source_count": len(not_modified_source_ids),
            "conditional_request_source_ids": sorted(conditional_request_source_ids),
            "conditional_request_source_count": len(conditional_request_source_ids),
        }

    def _fetch_source(self, source: NewsSource) -> list[NewsArticle]:
        """Fetch one source, preserving the historical list-only helper contract."""
        articles, _ = self._fetch_source_with_meta(source)
        return articles

    def _fetch_source_with_meta(self, source: NewsSource) -> tuple[list[NewsArticle], dict[str, bool]]:
        cached = _get_feed_cache(source.url)
        request_url = (cached.final_url or source.url) if cached else source.url
        response = _http_get_feed(
            request_url,
            timeout=self.timeout_seconds,
            user_agent="risk-dashboard-news-intelligence/0.1",
            etag=cached.etag if cached else "",
            last_modified=cached.last_modified if cached else "",
            cached_body=cached.body if cached else None,
        )
        _set_feed_cache(
            source.url,
            _FeedCacheEntry(
                body=response.body,
                etag=response.etag or (cached.etag if cached else ""),
                last_modified=response.last_modified or (cached.last_modified if cached else ""),
                final_url=response.final_url or (cached.final_url if cached else source.url),
            ),
        )
        root = ET.fromstring(response.body)
        fetched_at = utc_now_iso()
        return (
            [enrich_article(article) for article in self._parse_items(root=root, source=source, fetched_at=fetched_at)],
            {
                "not_modified": response.not_modified,
                "conditional_request": bool(cached and (cached.etag or cached.last_modified)),
            },
        )

    def _parse_items(self, *, root: ET.Element, source: NewsSource, fetched_at: str) -> list[NewsArticle]:
        items = [node for node in root.iter() if _local_name(node.tag) in {"item", "entry"}]
        if not items:
            return []
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
            url = _canonical_url(_find_link(item))
            image_url = _find_image_url(item, base_url=url)
            published_at, sort_ts = _published_at(item, region=source.region)
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
                    image_url=image_url,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    sort_ts=sort_ts,
                )
            )
        return articles


def _decode_response_bytes(raw: bytes, headers: object) -> bytes:
    """Decode gzip-compressed response body when needed."""
    if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
        try:
            return gzip.decompress(raw)
        except OSError:
            return raw
    enc = ""
    if hasattr(headers, "get"):
        enc = (headers.get("Content-Encoding") or "").lower()
    if "gzip" in enc and len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
        try:
            return gzip.decompress(raw)
        except OSError:
            return raw
    return raw


def _http_get_bytes(url: str, *, timeout: float, user_agent: str) -> bytes:
    """Compatibility wrapper for callers that only need response bytes."""
    return _http_get_feed(url, timeout=timeout, user_agent=user_agent).body


def _http_get_feed(
    url: str,
    *,
    timeout: float,
    user_agent: str,
    etag: str = "",
    last_modified: str = "",
    cached_body: bytes | None = None,
) -> _FeedHttpResponse:
    """GET a feed with redirects and HTTP validators.

    RSS providers commonly expose ``ETag`` or ``Last-Modified``.  Sending the
    validators lets an unchanged source return ``304`` without transferring
    the feed again.  A 304 is only accepted when a previous body is available;
    otherwise the caller receives the original error instead of silently
    dropping a source.
    """
    current = url.strip()
    initial_url = current
    seen: set[str] = set()
    for _ in range(8):
        if current in seen:
            raise ValueError("redirect loop")
        seen.add(current)
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
        }
        # Do not forward validators to a different host after a redirect.
        if current == initial_url:
            if etag:
                headers["If-None-Match"] = etag
            if last_modified:
                headers["If-Modified-Since"] = last_modified
        request = urllib.request.Request(current, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = getattr(response, "status", getattr(response, "code", None))
                if status == 304:
                    if cached_body is None:
                        raise ValueError(
                            "feed returned 304 without a cached body; retry without validators"
                        )
                    return _FeedHttpResponse(
                        body=cached_body,
                        etag=str(response.headers.get("ETag") or etag).strip(),
                        last_modified=str(response.headers.get("Last-Modified") or last_modified).strip(),
                        final_url=str(response.geturl() or current),
                        not_modified=True,
                    )
                raw = response.read(1_500_000)
                return _FeedHttpResponse(
                    body=_decode_response_bytes(raw, response.headers),
                    etag=str(response.headers.get("ETag") or "").strip(),
                    last_modified=str(response.headers.get("Last-Modified") or "").strip(),
                    final_url=str(response.geturl() or current),
                )
        except HTTPError as exc:
            if exc.code == 304:
                if cached_body is None:
                    raise ValueError(
                        "feed returned 304 without a cached body; retry without validators"
                    ) from exc
                return _FeedHttpResponse(
                    body=cached_body,
                    etag=str(exc.headers.get("ETag") or etag).strip() if exc.headers else etag,
                    last_modified=(
                        str(exc.headers.get("Last-Modified") or last_modified).strip()
                        if exc.headers
                        else last_modified
                    ),
                    final_url=current,
                    not_modified=True,
                )
            if exc.code in (301, 302, 303, 307, 308):
                loc = exc.headers.get("Location") if exc.headers else None
                if not loc:
                    raise
                current = urljoin(exc.url, loc)
                continue
            raise
    raise ValueError("too many redirects")


def _get_feed_cache(url: str) -> _FeedCacheEntry | None:
    with _FEED_HTTP_CACHE_LOCK:
        return _FEED_HTTP_CACHE.get(url.strip())


def _set_feed_cache(url: str, entry: _FeedCacheEntry) -> None:
    with _FEED_HTTP_CACHE_LOCK:
        key = url.strip()
        if key not in _FEED_HTTP_CACHE and len(_FEED_HTTP_CACHE) >= _FEED_HTTP_CACHE_MAX_ENTRIES:
            # Dicts retain insertion order on supported Python versions; drop
            # the oldest feed so user-configured source lists cannot grow the
            # process cache without bound.
            _FEED_HTTP_CACHE.pop(next(iter(_FEED_HTTP_CACHE)))
        _FEED_HTTP_CACHE[key] = entry


def _find_text(item: ET.Element, names: tuple[str, ...]) -> str:
    local_names = {_local_name(name) for name in names}
    for node in item.iter():
        if _local_name(node.tag) in local_names and node.text:
            return node.text
    return ""


def _find_link(item: ET.Element) -> str:
    for node in item.iter():
        if _local_name(node.tag) != "link":
            continue
        href = str(node.attrib.get("href") or "").strip()
        rel = str(node.attrib.get("rel") or "alternate").lower()
        if href and rel in {"alternate", "canonical", ""}:
            return href
        if node.text and node.text.strip():
            return node.text.strip()
    return ""


def _find_image_url(item: ET.Element, *, base_url: str = "") -> str:
    """Extract a safe image URL from common RSS/Atom media conventions.

    Feeds use several shapes: Media RSS attributes, image enclosures, an
    ``<image><url>`` child, or an HTML ``img`` inside ``content:encoded``.
    The first usable HTTPS/HTTP URL wins; malformed or data URLs are ignored.
    """
    candidates: list[str] = []
    for node in item.iter():
        local = _local_name(node.tag)
        attrs = {str(key).lower().rsplit('}', 1)[-1]: str(value or '').strip() for key, value in node.attrib.items()}
        media_type = attrs.get("type", "").lower()
        medium = attrs.get("medium", "").lower()
        if local in {"content", "thumbnail", "enclosure"}:
            candidate = attrs.get("url") or attrs.get("href")
            if candidate and (local != "enclosure" or not media_type or media_type.startswith("image/")):
                if local != "content" or not medium or medium == "image" or media_type.startswith("image/"):
                    candidates.append(candidate)
        elif local == "url" and node.text and any(_local_name(parent.tag) == "image" for parent in item.iter() for _ in [parent] if node in list(parent)):
            candidates.append(node.text)

    for encoded in _find_all_text(item, ("encoded", "description", "summary")):
        candidates.extend(re.findall(r"<img[^>]+(?:src|data-src)=[\"']([^\"']+)", html.unescape(encoded), flags=re.IGNORECASE))
        candidates.extend(re.findall(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)", html.unescape(encoded), flags=re.IGNORECASE))

    for candidate in candidates:
        value = _asset_url(candidate, base_url=base_url)
        if value:
            return value[:1200]
    return ""


def _find_all_text(item: ET.Element, names: tuple[str, ...]) -> list[str]:
    local_names = {_local_name(name) for name in names}
    return [node.text for node in item.iter() if _local_name(node.tag) in local_names and node.text]


def _asset_url(value: str, *, base_url: str = "") -> str:
    raw = html.unescape(str(value or "")).strip()
    if not raw or raw.startswith(("data:", "javascript:", "#")):
        return ""
    if base_url:
        raw = urljoin(base_url, raw)
    try:
        parts = urlsplit(raw)
    except ValueError:
        return ""
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        return ""
    return urlunsplit((parts.scheme.lower(), parts.netloc, parts.path, parts.query, ""))


def _local_name(tag: str) -> str:
    """Return an XML local name for both RSS and namespaced Atom feeds."""

    return str(tag).rsplit("}", 1)[-1].lower()


def _canonical_url(value: str) -> str:
    """Remove tracking-only URL differences before persisting an article."""

    raw = (value or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw
    if not parts.scheme or not parts.netloc:
        return raw
    tracking = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}
    query = urlencode(
        [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True) if key.lower() not in tracking]
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def _default_tz_for_naive_region(region: str) -> ZoneInfo:
    """When RSS pubDate has no usable tzinfo (e.g. malformed 'GMT+7'), treat wall clock in this zone."""
    if region == "VN":
        return ZoneInfo("Asia/Ho_Chi_Minh")
    return ZoneInfo("UTC")


def _published_at(item: ET.Element, *, region: str) -> tuple[str, int]:
    value = _find_text(item, ("pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"))
    parsed: datetime
    try:
        parsed = parsedate_to_datetime(value) if value else datetime.now(timezone.utc)
    except Exception:  # noqa: BLE001
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_default_tz_for_naive_region(region))
    parsed_utc = parsed.astimezone(timezone.utc)
    return parsed_utc.isoformat(), int(parsed_utc.timestamp())


def _clean(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _article_id(source_id: str, raw: str) -> str:
    return hashlib.sha1(f"{source_id}:{_canonical_url(raw)}".encode("utf-8")).hexdigest()[:24]
