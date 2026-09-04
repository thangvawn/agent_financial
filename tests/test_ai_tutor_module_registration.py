from __future__ import annotations

from risk_dashboard.app.registry.product_domains import get_product_domain_for_module
from risk_dashboard.app.registry.registry import get_enabled_modules, get_module_by_slug, get_registered_modules
from risk_dashboard.platform.feature_flags.service import FeatureFlagService


def test_ai_tutor_module_registration() -> None:
    mod = get_module_by_slug("ai_tutor")
    assert mod is not None
    assert mod.id == "ai_tutor"
    assert mod.slug == "ai_tutor"
    assert mod.enabled_by_default is True
    assert "ai_tutor:conversation:read" in mod.permission_scopes
    assert "ai_tutor:conversation:write" in mod.permission_scopes
    assert "ai_tutor:feedback:write" in mod.permission_scopes
    assert mod.public_router is not None
    assert mod.public_mount_prefix == "/api/v1/public"


def test_ai_tutor_domain_mapping() -> None:
    domain = get_product_domain_for_module("ai_tutor")
    assert domain == "learn_hub"


def test_ai_tutor_feature_flag_control(monkeypatch) -> None:
    ff = FeatureFlagService()
    # Default is enabled
    enabled = get_enabled_modules(ff)
    assert any(m.slug == "ai_tutor" for m in enabled)

    # Disable via env var
    monkeypatch.setenv("RISK_FLAG__MODULE__AI_TUTOR__ENABLED", "0")
    disabled_run = get_enabled_modules(ff)
    assert not any(m.slug == "ai_tutor" for m in disabled_run)

