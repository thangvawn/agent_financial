from __future__ import annotations

import ipaddress
import json
import socket
from datetime import datetime, timezone
from time import monotonic
from urllib.parse import quote, unquote, urljoin, urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["Learning"])
_ALLOWED_HOST_SUFFIXES = (
    "archive.org", "gutenberg.org", "arxiv.org", "openlibrary.org",
    "wikipedia.org", "wikimedia.org", "cloudfront.net", "gutenberg.net.au",
)
_MAX_BYTES = 40 * 1024 * 1024
_MAX_METADATA_BYTES = 4 * 1024 * 1024
_BROWSER_UA = "NorthstarBookReader/1.0 (source availability check)"


def _host_allowed(hostname: str) -> bool:
    host = (hostname or "").lower().rstrip(".")
    return bool(host) and any(host == s or host.endswith(f".{s}") for s in _ALLOWED_HOST_SUFFIXES)


def _assert_public_host(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(502, "Chưa kết nối được nguồn tài liệu.") from exc
    if not infos:
        raise HTTPException(502, "Chưa kết nối được nguồn tài liệu.")
    if any(not ipaddress.ip_address(info[4][0]).is_global for info in infos):
        raise HTTPException(400, "Host nguồn không được phép.")


def _validate_remote_url(url: str) -> str:
    parsed = urlparse(url)
    try:
        valid_port = parsed.port in (None, 80, 443)
    except ValueError:
        valid_port = False
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password or not valid_port:
        raise HTTPException(400, "Liên kết nguồn không hợp lệ.")
    if not _host_allowed(parsed.hostname or ""):
        raise HTTPException(400, "Nguồn sách ngoài danh mục cho phép.")
    _assert_public_host(parsed.hostname or "")
    return url


def _open_remote(client: httpx.Client, url: str, *, probe: bool = False) -> httpx.Response:
    headers = {"User-Agent": _BROWSER_UA, "Accept-Encoding": "identity"}
    if probe:
        headers["Range"] = "bytes=0-1023"
    target = url
    for _ in range(5):
        target = _validate_remote_url(target)
        response = client.send(client.build_request("GET", target, headers=headers), stream=True)
        if response.status_code not in {301, 302, 303, 307, 308}:
            return response
        location = response.headers.get("location")
        response.close()
        if not location:
            raise HTTPException(502, "Nguồn chuyển hướng không hợp lệ.")
        target = urljoin(target, location)
    raise HTTPException(502, "Nguồn chuyển hướng quá nhiều lần.")


def _state(status: str, message: str, **extra) -> dict:
    return {"ok": status == "ready", "status": status, "message": message,
            "checked_at": datetime.now(timezone.utc).isoformat(), **extra}


def _http_state(status: int) -> dict | None:
    if status in (404, 410):
        return _state("missing", "Tài liệu không còn tồn tại tại liên kết này.")
    if status in (401, 403, 451):
        return _state("restricted", "Nguồn đang hạn chế truy cập. Có thể cần đăng nhập hoặc mượn sách tại nguồn.")
    if status >= 400:
        return _state("unavailable", "Nguồn tạm thời không phản hồi. Vui lòng thử lại sau.")
    return None


def _kind(url: str, content_type: str, prefix: bytes) -> str:
    path = urlparse(url).path.lower()
    if prefix.lstrip().startswith(b"%PDF-"):
        return "pdf"
    if path.endswith(".pdf") or content_type == "application/pdf":
        return "invalid"
    if content_type in {"text/html", "application/xhtml+xml"}:
        return "html"
    if content_type.startswith("text/plain"):
        return "text"
    return "unsupported"


def _size(response: httpx.Response) -> int | None:
    value = response.headers.get("content-range", "").rsplit("/", 1)[-1]
    if not value.isdigit():
        value = response.headers.get("content-length", "")
    return int(value) if value.isdigit() else None


def _truthy(value) -> bool:
    return value is True or str(value).lower() in {"true", "1"}


def _archive_id(url: str) -> str | None:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if parsed.hostname not in {"archive.org", "www.archive.org"} or len(parts) < 2:
        return None
    if parts[0] not in {"details", "download", "embed"}:
        return None
    identifier = unquote(parts[1])
    if identifier in {".", ".."} or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-" for c in identifier):
        raise HTTPException(400, "Mã tài liệu không hợp lệ.")
    return identifier


def _archive_source(client: httpx.Client, identifier: str) -> tuple[str | None, dict | None]:
    response = _open_remote(client, f"https://archive.org/metadata/{quote(identifier, safe='')}")
    try:
        failure = _http_state(response.status_code)
        if failure:
            return None, failure
        chunks, total = [], 0
        deadline = monotonic() + 10
        for chunk in response.iter_bytes(4096):
            if monotonic() > deadline:
                return None, _state("unavailable", "Nguồn phản hồi quá chậm. Hãy thử lại sau.")
            total += len(chunk)
            if total > _MAX_METADATA_BYTES:
                return None, _state("unavailable", "Thông tin nguồn quá lớn để kiểm tra.")
            chunks.append(chunk)
        try:
            payload = json.loads(b"".join(chunks))
        except (ValueError, TypeError):
            return None, _state("unavailable", "Nguồn trả thông tin chưa hợp lệ. Hãy thử lại sau.")
    finally:
        response.close()
    if not isinstance(payload, dict):
        return None, _state("unavailable", "Nguồn trả thông tin chưa hợp lệ. Hãy thử lại sau.")
    metadata = payload.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return None, _state("unavailable", "Nguồn trả thông tin chưa hợp lệ. Hãy thử lại sau.")
    if _truthy(payload.get("is_dark")) or _truthy((metadata or {}).get("access-restricted-item")):
        return None, _state("restricted", "Sách được giới hạn truy cập. Hãy xem điều kiện đăng nhập hoặc mượn sách tại Internet Archive.")
    if not isinstance(metadata, dict) or not metadata:
        return None, _state("missing", "Mục sách không còn tồn tại trên Internet Archive.")
    files = payload.get("files") or []
    if not isinstance(files, list):
        return None, _state("unavailable", "Nguồn trả danh sách file chưa hợp lệ.")
    candidates = []
    for item in files:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        if not isinstance(name, str) or _truthy(item.get("private")) or "encrypted" in name.lower():
            continue
        if "/" in name or "\\" in name or name in {".", ".."}:
            continue  # Do not mistake page fragments for an entire book.
        kind = "pdf" if name.lower().endswith(".pdf") else "text" if name.lower().endswith("_djvu.txt") else None
        if not kind:
            continue
        try:
            size = int(item.get("size") or 0)
        except (TypeError, ValueError):
            continue
        if size > _MAX_BYTES:
            continue
        candidates.append((kind != "pdf", item.get("format") != "Text PDF", name))
    if not candidates:
        return None, _state("external", "Chưa có bản PDF/văn bản công khai phù hợp để đọc trong ứng dụng. Bạn vẫn có thể xem thông tin tại nguồn.")
    preferred = [candidate for candidate in candidates if not candidate[0]] or candidates
    if len(preferred) > 1:
        return None, _state("external", "Mục nguồn chứa nhiều file sách. Hãy mở trang nguồn để chọn đúng tài liệu cần đọc.")
    name = preferred[0][2]
    return f"https://archive.org/download/{quote(identifier, safe='')}/{quote(name, safe='')}", None


@router.get("/reader/check")
def check_reader_content(url: str = Query(..., min_length=8, max_length=2000)) -> dict:
    target = _validate_remote_url(url.strip())
    identifier = _archive_id(target)
    open_url = f"https://archive.org/details/{identifier}" if identifier else target
    try:
        with httpx.Client(timeout=httpx.Timeout(12, connect=5), follow_redirects=False) as client:
            if identifier:
                target, failure = _archive_source(client, identifier)
                if failure:
                    return {**failure, "open_url": open_url}
            response = _open_remote(client, target, probe=True)
            try:
                failure = _http_state(response.status_code)
                if failure:
                    return {**failure, "open_url": open_url}
                size = _size(response)
                if size is not None and size > _MAX_BYTES:
                    return _state("too_large", "Tài liệu vượt giới hạn 40 MB của trình đọc. Vui lòng mở tại nguồn.", open_url=open_url)
                content_type = response.headers.get("content-type", "").split(";")[0].lower()
                prefix = next(response.iter_bytes(1024), b"")
                kind = _kind(str(response.url), content_type, prefix)
                if kind in {"invalid", "unsupported"} or not prefix:
                    return _state("invalid", "Nguồn chưa trả về nội dung đọc hợp lệ.", open_url=open_url)
                return _state("ready", "Đã kiểm tra nguồn tài liệu.", kind=kind, content_type=content_type,
                              resolved_url=target, view_url=f"/api/v1/public/learning/reader/stream?url={quote(target, safe='')}",
                              open_url=open_url, size_bytes=size)
            finally:
                response.close()
    except httpx.HTTPError:
        return _state("unavailable", "Chưa kết nối được nguồn. Vui lòng thử lại sau.", open_url=open_url)


@router.get("/reader/stream")
def stream_reader_content(url: str = Query(..., min_length=8, max_length=2000)):
    target = _validate_remote_url(url.strip())
    client = httpx.Client(timeout=httpx.Timeout(30, connect=5), follow_redirects=False)
    upstream = None
    try:
        upstream = _open_remote(client, target)
        failure = _http_state(upstream.status_code)
        if failure:
            status = upstream.status_code if upstream.status_code in {401, 403, 404, 410, 451} else 502
            raise HTTPException(status, failure["message"])
        size = _size(upstream)
        if size is not None and size > _MAX_BYTES:
            raise HTTPException(413, "Tài liệu vượt giới hạn 40 MB của trình đọc.")
        chunks = upstream.iter_bytes(65536)
        first = next(chunks, b"")
        content_type = upstream.headers.get("content-type", "").split(";")[0].lower()
        kind = _kind(str(upstream.url), content_type, first)
        if kind in {"invalid", "unsupported"} or not first:
            raise HTTPException(502, "Nguồn chưa trả về nội dung đọc hợp lệ.")
    except Exception as exc:
        if upstream is not None:
            upstream.close()
        client.close()
        if isinstance(exc, httpx.HTTPError):
            raise HTTPException(502, "Không tải được nội dung tài liệu.") from exc
        raise

    def content():
        total = len(first)
        try:
            yield first
            for chunk in chunks:
                total += len(chunk)
                if total > _MAX_BYTES:
                    raise RuntimeError("Reader size limit exceeded")
                yield chunk
        finally:
            upstream.close()
            client.close()

    headers = {"Content-Disposition": "inline", "Cache-Control": "private, max-age=300",
               "X-Content-Type-Options": "nosniff", "Accept-Ranges": "none"}
    if size is not None and not upstream.headers.get("content-encoding"):
        headers["Content-Length"] = str(size)
    if kind == "html":
        headers["Content-Security-Policy"] = "sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src https: data:"
    media_type = {"pdf": "application/pdf", "html": "text/html", "text": "text/plain"}[kind]
    return StreamingResponse(content(), media_type=media_type, headers=headers)
