import pytest
from pathlib import Path
from unittest.mock import patch

from risk_dashboard.modules.data_hub.application.global_market_feed import _atomic_write_json, GlobalMarketFeedProducer


def test_atomic_write_json_success(tmp_path: Path):
    target = tmp_path / "test.json"
    payload = {"status": "ok", "value": 42}
    success = _atomic_write_json(target, payload)
    assert success is True
    assert target.exists()
    assert '"value": 42' in target.read_text(encoding="utf-8")


def test_atomic_write_json_permission_error_fallback(tmp_path: Path):
    target = tmp_path / "protected.json"
    payload = {"status": "ok"}
    with patch("os.replace", side_effect=PermissionError("Permission denied")):
        success = _atomic_write_json(target, payload)
        assert success is False
        # Ensures no unhandled exception is raised


def test_write_history_cache_handles_permission_error(tmp_path: Path):
    producer = GlobalMarketFeedProducer(cache_dir=tmp_path)
    with patch("risk_dashboard.modules.data_hub.application.global_market_feed._atomic_write_json", return_value=False):
        # Must not raise any exception
        producer._write_history_cache("FPT", "6mo", "1d", {"price": 100})
