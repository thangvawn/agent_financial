from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from risk_dashboard.api.main import app  # initialize registry before module imports
from risk_dashboard.modules.auth.application.dependencies import resolve_surface_principal
from risk_dashboard.modules.auth.application.services import RegisterAccount
from risk_dashboard.modules.auth.infrastructure.sqlite import SqliteAccountRepository, SqliteAccountSessionRepository
from risk_dashboard.modules.learning.api.reader_proxy import stream_reader_content
from risk_dashboard.platform.database import clear_db_path_cache


@pytest.mark.parametrize('status', ['expired', 'revoked'])
def test_surface_rejects_invalid_account_session(tmp_path, monkeypatch, status):
    monkeypatch.setenv('RISK_DASHBOARD_DB_PATH', str(tmp_path / 'sessions.db'))
    clear_db_path_cache()
    sessions = SqliteAccountSessionRepository()
    _, session = RegisterAccount(SqliteAccountRepository(), sessions).execute(
        name='Review', email='review@example.test', password='review-pass-123')
    if status == 'expired':
        sessions.save(replace(session, expires_at=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat()))
    else:
        sessions.revoke(session_id=session.session_id)
    try:
        with pytest.raises(HTTPException) as error:
            resolve_surface_principal(authorization=None, session_id=session.session_id)
        assert error.value.status_code == 401
    finally:
        clear_db_path_cache()


def test_reader_failure_does_not_reflect_untrusted_url():
    from fastapi import HTTPException
    upstream = MagicMock(status_code=503)
    client = MagicMock()
    client.send.return_value = upstream
    url = "https://www.gutenberg.org/file?x='><span id='injected'>probe</span><a href='"
    with patch('risk_dashboard.modules.learning.api.reader_proxy._assert_public_host'), patch('risk_dashboard.modules.learning.api.reader_proxy.httpx.Client', return_value=client):
        with pytest.raises(HTTPException) as error:
            stream_reader_content(url=url)
    assert error.value.status_code == 502
    assert '<span' not in error.value.detail
