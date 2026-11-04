from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.learning.api.reader_proxy import _host_allowed


def test_host_allowed_whitelist():
    assert _host_allowed("archive.org") is True
    assert _host_allowed("ia800100.us.archive.org") is True
    assert _host_allowed("www.gutenberg.org") is True
    assert _host_allowed("arxiv.org") is True
    assert _host_allowed("evil.com") is False
    assert _host_allowed("archive.org.attacker.com") is False


@patch("risk_dashboard.modules.learning.api.reader_proxy._assert_public_host")
@patch("risk_dashboard.modules.learning.api.reader_proxy.httpx.Client")
def test_stream_reader_archive_503_is_a_retryable_error(mock_client_cls, mock_assert_public):
    mock_assert_public.return_value = None

    mock_client = MagicMock()
    mock_upstream = MagicMock()
    mock_upstream.status_code = 503
    mock_upstream.close = MagicMock()
    mock_client.send.return_value = mock_upstream
    mock_client_cls.return_value = mock_client

    client = TestClient(app)
    url = "https://archive.org/download/wealthofnations00smit/wealthofnations00smit.pdf"
    res = client.get(
        f"/api/v1/public/learning/reader/stream?url={url}",
        follow_redirects=False,
    )

    assert res.status_code == 502
    assert "location" not in res.headers


@patch("risk_dashboard.modules.learning.api.reader_proxy._assert_public_host")
@patch("risk_dashboard.modules.learning.api.reader_proxy.httpx.Client")
def test_stream_reader_non_archive_503_is_a_retryable_error(mock_client_cls, mock_assert_public):
    mock_assert_public.return_value = None

    mock_client = MagicMock()
    mock_upstream = MagicMock()
    mock_upstream.status_code = 503
    mock_upstream.close = MagicMock()
    mock_client.send.return_value = mock_upstream
    mock_client_cls.return_value = mock_client

    client = TestClient(app)
    url = "https://www.gutenberg.org/files/1234/1234-pdf.pdf"
    res = client.get(
        f"/api/v1/public/learning/reader/stream?url={url}",
        follow_redirects=False,
    )

    assert res.status_code == 502
    assert "application/json" in res.headers["content-type"]
    assert "tạm thời" in res.json()["detail"]
