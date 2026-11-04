"""Public social URLs and source content. No browser credentials or inferred facts."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

from risk_dashboard.modules.news_intelligence.safety.content_boundary import (
    sanitize_article_content,
)

ERRORS = {
    "NEED_SETUP": "Nguồn chưa được cấu hình. Vui lòng kiểm tra kết nối nguồn.",
    "NEED_LOGIN": "Nguồn yêu cầu đăng nhập; kết nối công khai chưa đọc được nội dung này.",
    "TIMEOUT": "Nguồn phản hồi quá lâu. Có thể thử lại sau.",
    "RATE_LIMITED": "Nguồn đang giới hạn truy cập. Hệ thống sẽ chờ trước khi thử lại.",
    "PLATFORM_BLOCKED": "Nguồn đang chặn truy cập tự động.",
    "NOT_FOUND": "Không tìm thấy nội dung tại nguồn.",
    "BAD_INPUT": "Đường dẫn hoặc truy vấn không được hỗ trợ.",
    "UPSTREAM_BROKEN": "Chưa đọc được nguồn. Nội dung đã lưu vẫn được giữ lại.",
    "INVALID_PAYLOAD": "Nguồn trả dữ liệu chưa đọc được.",
}


def canonical_url(value: str) -> tuple[str, str, str]:
    """Allow only individual public posts/video URLs, never arbitrary fetch targets."""
    try:
        parsed = urlsplit(value.strip())
        if (
            parsed.scheme not in {"https", "http"}
            or parsed.username
            or parsed.password
            or parsed.port
        ):
            raise ValueError
        host = (parsed.hostname or "").lower()
        if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
            parts = parsed.path.strip("/").split("/")
            video = (
                parts[0]
                if host == "youtu.be"
                else (
                    parse_qs(parsed.query).get("v", [""])[0]
                    if parsed.path == "/watch"
                    else parts[1]
                    if len(parts) == 2 and parts[0] in {"shorts", "live"}
                    else ""
                )
            )
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video):
                raise ValueError
            return "youtube", video, f"https://www.youtube.com/watch?v={video}"
        if host in {"reddit.com", "www.reddit.com", "old.reddit.com", "new.reddit.com"}:
            match = re.match(
                r"^/r/([A-Za-z0-9_]{2,40})/comments/([a-zA-Z0-9]{4,12})(?:/|$)", parsed.path
            )
            if match:
                sub, post = match.groups()
                return (
                    "reddit",
                    post.lower(),
                    f"https://www.reddit.com/r/{sub}/comments/{post.lower()}/",
                )
    except (ValueError, TypeError):
        pass
    raise ValueError("Hãy dùng liên kết video YouTube hoặc bài viết Reddit công khai.")


def clean(value: object, limit: int = 12000) -> str:
    return sanitize_article_content(str(value or ""), max_length=limit)


def publication(value: object) -> tuple[str | None, float | None, str]:
    raw = str(value or "").strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        precision = "day" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw) else "second"
        if dt.tzinfo is None:
            if precision != "day":
                return None, None, "unknown"
            dt = dt.replace(tzinfo=timezone.utc)
        if dt.timestamp() > datetime.now(timezone.utc).timestamp() + 86400:
            return None, None, "unknown"
        return (raw if precision == "day" else dt.isoformat()), dt.timestamp(), precision
    except (ValueError, OverflowError, OSError):
        return None, None, "unknown"


def normalize_item(
    item: dict, *, platform: str, market: str, backend: str, content_kind: str = "excerpt"
) -> dict:
    actual, native_id, url = canonical_url(str(item.get("url") or ""))
    if actual != platform:
        raise ValueError("Platform mismatch")
    title = clean(item.get("title"), 500)
    source_text = str(item.get("text") or "")
    # Public search can contain a rendered thread. Don't attribute replies to the post author.
    if platform == "reddit":
        source_text = re.split(
            r"(?im)^\s*#{1,4}\s*(?:Top comments|Comments|Replies)\b", source_text
        )[0]
    text = clean(source_text)
    if not title and not text:
        raise ValueError("Empty content")
    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
    # Browser-style Reddit results concatenate comments into text. Preserve only the original post.
    if platform == "reddit" and isinstance(raw.get("post"), dict):
        text = clean(raw["post"].get("selftext") or raw["post"].get("body") or "")
    published_at, published_ts, precision = publication(item.get("published_at"))
    metrics = {}
    for key in ("view_count", "like_count", "comment_count", "score"):
        value = raw.get(key)
        metrics[key] = (
            value
            if isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value >= 0
            else None
        )
    payload = {
        "platform": platform,
        "native_id": native_id,
        "url": url,
        "title": title or text[:180],
        "text": text,
        "author": clean(item.get("author"), 120) or None,
        "published_at": published_at,
        "published_ts": published_ts,
        "time_precision": precision,
        "market": market,
        "language": "vi"
        if re.search(r"[ăâđêôơưĂÂĐÊÔƠƯ]|[\u1ea0-\u1ef9]", title + text)
        else "unknown",
        "content_kind": content_kind,
        "backend": backend,
        "metrics": metrics,
        "transcript_status": "not_requested" if platform == "youtube" else "not_applicable",
        "transcript": "",
        "status": "available",
    }
    return payload


def duplicate_digest(payload: dict) -> str:
    body = (payload.get("transcript") or payload.get("text") or "").strip()
    if len(body) < 80:
        body = payload["title"] + " " + body
    return hashlib.sha256(re.sub(r"\s+", " ", body.casefold()).encode()).hexdigest()


def content_digest(payload: dict) -> str:
    stable = {k: v for k, v in payload.items() if k not in {"metrics", "backend", "market"}}
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
