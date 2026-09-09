import asyncio
import pytest
from risk_dashboard.platform.feature_flags.decorator import feature_flag, FlagRegistry


def test_feature_flag_sync_enabled(monkeypatch):
    monkeypatch.setenv("RISK_FLAG__AGENTIC__MEMORY", "true")

    @feature_flag("agentic.memory", default=False, fallback="fallback_val")
    def compute(x):
        return x * 2

    assert compute(5) == 10


def test_feature_flag_sync_disabled_returns_fallback(monkeypatch):
    monkeypatch.setenv("RISK_FLAG__AGENTIC__MEMORY", "false")

    @feature_flag("agentic.memory", default=True, fallback="fallback_val")
    def compute(x):
        return x * 2

    assert compute(5) == "fallback_val"


def test_feature_flag_async_enabled(monkeypatch):
    monkeypatch.setenv("RISK_FLAG__AGENTIC__RETENTION", "true")

    @feature_flag("agentic.retention", default=False, fallback=None)
    async def async_compute(val):
        return f"async_{val}"

    res = asyncio.run(async_compute("test"))
    assert res == "async_test"


def test_feature_flag_async_disabled_returns_fallback(monkeypatch):
    monkeypatch.setenv("RISK_FLAG__AGENTIC__RETENTION", "0")

    @feature_flag("agentic.retention", default=True, fallback="async_fallback")
    async def async_compute(val):
        return f"async_{val}"

    res = asyncio.run(async_compute("test"))
    assert res == "async_fallback"


def test_feature_flag_toggle_runtime_immediate_refresh(monkeypatch):
    @feature_flag("agentic.dynamic", default=False, fallback="off")
    def dynamic_fn():
        return "on"

    monkeypatch.setenv("RISK_FLAG__AGENTIC__DYNAMIC", "false")
    assert dynamic_fn() == "off"

    monkeypatch.setenv("RISK_FLAG__AGENTIC__DYNAMIC", "true")
    assert dynamic_fn() == "on"

    monkeypatch.setenv("RISK_FLAG__AGENTIC__DYNAMIC", "false")
    assert dynamic_fn() == "off"


def test_flag_registry_records_audit_trail(monkeypatch):
    FlagRegistry.clear()
    monkeypatch.setenv("RISK_FLAG__AGENTIC__AUDIT", "true")

    @feature_flag("agentic.audit", default=False)
    def audited_target():
        return 42

    audited_target()
    entries = FlagRegistry.get_entries()
    assert len(entries) >= 1
    latest = entries[-1]
    assert latest["flag_name"] == "agentic.audit"
    assert latest["enabled"] is True
    assert "evaluated_at" in latest
    assert "caller" in latest
