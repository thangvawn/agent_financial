from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["Learning"])

_ALLOWED_HOST_SUFFIXES = (
    "archive.org",
    "gutenberg.org",
    "arxiv.org",
    "openlibrary.org",
    "wikipedia.org",
    "wikimedia.org",
    "cloudfront.net",
    "gutenberg.net.au",
)

_MAX_BYTES = 40 * 1024 * 1024
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _host_allowed(hostname: str) -> bool:
    host = (hostname or "").lower().rstrip(".")
    if not host:
        return False
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in _ALLOWED_HOST_SUFFIXES)


def _assert_public_host(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail="Không resolve được host nguồn.") from exc
    for info in infos:
        raw_ip = info[4][0]
        try:
            ip = ipaddress.ip_address(raw_ip)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise HTTPException(status_code=400, detail="Host nguồn không được phép.")


def _validate_remote_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ http/https.")
    if not _host_allowed(parsed.hostname or ""):
        raise HTTPException(status_code=400, detail="Nguồn sách ngoài danh mục cho phép.")
    _assert_public_host(parsed.hostname or "")
    return url


@router.get("/reader/stream")
def stream_reader_content(url: str = Query(..., min_length=8, max_length=2000)):
    """Proxy remote book files so the in-app reader can embed them same-origin."""
    target = _validate_remote_url(url.strip())
    client = httpx.Client(timeout=45.0, follow_redirects=True)
    try:
        upstream = client.send(
            client.build_request(
                "GET",
                target,
                headers={
                    "User-Agent": _BROWSER_UA,
                    "Accept": "application/pdf,application/octet-stream,*/*",
                },
            ),
            stream=True,
        )
    except httpx.HTTPError as exc:
        client.close()
        raise HTTPException(status_code=502, detail="Không tải được nội dung sách.") from exc

    if upstream.status_code >= 400:
        upstream.close()
        client.close()
        raise HTTPException(status_code=502, detail=f"Nguồn trả về HTTP {upstream.status_code}.")

    final_host = urlparse(str(upstream.url)).hostname or ""
    if not _host_allowed(final_host):
        upstream.close()
        client.close()
        raise HTTPException(status_code=400, detail="Redirect tới host không được phép.")

    content_type = (upstream.headers.get("content-type") or "application/octet-stream").split(";")[0].strip().lower()
    if content_type in {"text/html", "application/xhtml+xml"} and ".pdf" in target.lower():
        upstream.close()
        client.close()
        raise HTTPException(status_code=502, detail="File PDF không còn tồn tại ở nguồn.")

    content_length = upstream.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > _MAX_BYTES:
        upstream.close()
        client.close()
        raise HTTPException(status_code=413, detail="File sách quá lớn để đọc trong app.")

    def iter_bytes():
        total = 0
        try:
            for chunk in upstream.iter_bytes():
                total += len(chunk)
                if total > _MAX_BYTES:
                    break
                yield chunk
        finally:
            upstream.close()
            client.close()

    headers = {
        "Content-Disposition": "inline",
        "Cache-Control": "private, max-age=300",
        "X-Content-Type-Options": "nosniff",
        "Accept-Ranges": "none",
    }
    return StreamingResponse(iter_bytes(), media_type=content_type or "application/pdf", headers=headers)


@router.get("/reader/check")
def check_reader_content(url: str = Query(..., min_length=8, max_length=2000)) -> dict:
    """Lightweight probe so the UI can decide proxy vs fallback before embedding."""
    target = _validate_remote_url(url.strip())
    headers = {
        "User-Agent": _BROWSER_UA,
        "Accept": "application/pdf,application/octet-stream,*/*",
    }
    try:
        with httpx.Client(timeout=25.0, follow_redirects=True) as client:
            response = client.get(target, headers={**headers, "Range": "bytes=0-1023"})
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Không kiểm tra được nguồn sách.") from exc

    content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
    ok = response.status_code < 400 and "html" not in content_type
    if not ok:
        raise HTTPException(status_code=502, detail="File PDF không còn tồn tại ở nguồn.")
    return {"ok": True, "content_type": content_type or "application/pdf", "status_code": response.status_code}
