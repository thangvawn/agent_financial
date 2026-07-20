from risk_dashboard.app.registry.product_domains import (
    LEGACY_MODULES,
    describe_domains,
    get_product_domain_for_module,
    is_legacy_module,
    resolve_module_slug,
)
from risk_dashboard.app.registry.registry import (
    get_enabled_modules,
    get_module_by_slug,
    get_registered_modules,
)
from risk_dashboard.platform.feature_flags.service import FeatureFlagService


def test_resolve_simulation_lab_and_home_aliases():
    assert resolve_module_slug("pro_lab") == "simulation_lab"
    assert resolve_module_slug("simulation_lab") == "simulation_lab"
    assert resolve_module_slug("home_onboarding") == "home"
    assert resolve_module_slug("home") == "home"
    assert get_product_domain_for_module("pro_lab") == "simulation_lab"
    assert get_product_domain_for_module("simulation_lab") == "simulation_lab"
    assert get_product_domain_for_module("home_onboarding") == "home"
    assert get_product_domain_for_module("home") == "home"


def test_legacy_modules_are_marked_and_unmounted():
    registered = {module.slug for module in get_registered_modules()}
    for slug in ("community", "goals", "financial_health"):
        assert is_legacy_module(slug)
        assert slug not in registered
        assert get_module_by_slug(slug) is None


def test_guided_investing_retired_disabled_by_default():
    assert is_legacy_module("guided_investing")
    module = get_module_by_slug("guided_investing")
    assert module is not None
    assert module.enabled_by_default is False
    enabled_slugs = {m.slug for m in get_enabled_modules(FeatureFlagService())}
    assert "guided_investing" not in enabled_slugs


def test_enabled_modules_use_product_slugs():
    enabled_slugs = {module.slug for module in get_enabled_modules(FeatureFlagService())}
    assert "simulation_lab" in enabled_slugs
    assert "home" in enabled_slugs
    assert "market_portfolio" in enabled_slugs
    assert "learning" in enabled_slugs
    assert "data_hub" in enabled_slugs
    assert "pro_lab" not in enabled_slugs
    assert "home_onboarding" not in enabled_slugs
    for slug in LEGACY_MODULES:
        if slug == "guided_investing":
            continue
        assert slug not in enabled_slugs


def test_describe_domains_has_six_product_surfaces():
    domains = {row["domain"] for row in describe_domains()}
    assert {
        "home",
        "market_portfolio",
        "learn_hub",
        "bctc",
        "news",
        "simulation_lab",
        "auth",
    } <= domains
    bctc = next(row for row in describe_domains() if row["domain"] == "bctc")
    assert bctc["modules"] == ["financials_product"]
    assert "guided_investing" in bctc["retired_modules"]
