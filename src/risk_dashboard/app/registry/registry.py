from __future__ import annotations

import os

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.app.registry.product_domains import (
    LEGACY_MODULES,
    PLATFORM_MODULES,
    describe_domains,
    get_product_domain_for_module,
    is_legacy_module,
    iter_product_module_slugs,
    resolve_module_slug,
)
from risk_dashboard.modules.analytics_monitoring.module import module as analytics_monitoring_module
from risk_dashboard.modules.admin_cms.module import module as admin_cms_module
from risk_dashboard.modules.auth.module import module as auth_module
from risk_dashboard.modules.data_hub.module import module as data_hub_module
from risk_dashboard.modules.financials_product.module import module as financials_product_module
from risk_dashboard.modules.guided_investing.module import module as guided_investing_module
from risk_dashboard.modules.home.module import module as home_module
from risk_dashboard.modules.learning.module import module as learning_module
from risk_dashboard.modules.market_portfolio.module import module as market_portfolio_module
from risk_dashboard.modules.news_intelligence.module import module as news_intelligence_module
from risk_dashboard.modules.portfolio_product.module import module as portfolio_product_module
from risk_dashboard.modules.quant_risk.module import module as quant_risk_module
from risk_dashboard.modules.simulation_lab.module import module as simulation_lab_module
from risk_dashboard.modules.system_surface.module import module as system_surface_module
from risk_dashboard.modules.trust_safety.module import module as trust_safety_module
from risk_dashboard.modules.watchlist_product.module import module as watchlist_product_module
from risk_dashboard.platform.feature_flags.service import FeatureFlagService

_MODULE_BY_SLUG: dict[str, ModuleDefinition] | None = None


def get_registered_modules() -> tuple[ModuleDefinition, ...]:
    """Mount order: platform → product domains → retired (disabled by default).

    Phase 4: community / goals / financial_health are unmounted (packages retained on disk).
    Chatbot modules (ai_assistant, agent_orchestration) removed.
    """
    return (
        # Platform
        system_surface_module,
        quant_risk_module,
        auth_module,
        analytics_monitoring_module,
        trust_safety_module,
        admin_cms_module,
        # Product domains
        news_intelligence_module,
        market_portfolio_module,
        data_hub_module,
        watchlist_product_module,
        portfolio_product_module,
        financials_product_module,
        simulation_lab_module,
        home_module,
        learning_module,
        # Retired surface (enabled_by_default=False)
        guided_investing_module,
    )


def _module_index() -> dict[str, ModuleDefinition]:
    global _MODULE_BY_SLUG
    if _MODULE_BY_SLUG is None:
        _MODULE_BY_SLUG = {module.slug: module for module in get_registered_modules()}
    return _MODULE_BY_SLUG


def get_module_by_slug(slug: str) -> ModuleDefinition | None:
    canonical = resolve_module_slug(slug)
    return _module_index().get(canonical)


def get_enabled_modules(feature_flags: FeatureFlagService) -> list[ModuleDefinition]:
    enabled: list[ModuleDefinition] = []
    for module in get_registered_modules():
        flag_name = f"module.{module.slug}.enabled"
        default = module.enabled_by_default
        # Compat: RISK_FLAG__MODULE__PRO_LAB__ENABLED controls simulation_lab when primary unset
        if module.slug == "simulation_lab":
            primary_set = os.getenv("RISK_FLAG__MODULE__SIMULATION_LAB__ENABLED") is not None
            alias_set = os.getenv("RISK_FLAG__MODULE__PRO_LAB__ENABLED") is not None
            if not primary_set and alias_set:
                if feature_flags.is_enabled("module.pro_lab.enabled", default=default):
                    enabled.append(module)
                continue
        # Compat: home_onboarding flag → home
        if module.slug == "home":
            primary_set = os.getenv("RISK_FLAG__MODULE__HOME__ENABLED") is not None
            alias_set = os.getenv("RISK_FLAG__MODULE__HOME_ONBOARDING__ENABLED") is not None
            if not primary_set and alias_set:
                if feature_flags.is_enabled("module.home_onboarding.enabled", default=default):
                    enabled.append(module)
                continue
        if feature_flags.is_enabled(flag_name, default=default):
            enabled.append(module)
    return enabled


def get_enabled_modules_by_domain(feature_flags: FeatureFlagService) -> dict[str, list[str]]:
    """Group enabled module slugs by product domain (plus platform/legacy buckets)."""
    buckets: dict[str, list[str]] = {
        "platform": [],
        "legacy": [],
    }
    for domain_id in (
        "home",
        "market_portfolio",
        "learn_hub",
        "bctc",
        "news",
        "simulation_lab",
        "auth",
    ):
        buckets[domain_id] = []

    for module in get_enabled_modules(feature_flags):
        if is_legacy_module(module.slug):
            buckets["legacy"].append(module.slug)
            continue
        if module.slug in PLATFORM_MODULES or module.slug == "auth":
            if module.slug == "auth":
                buckets["auth"].append(module.slug)
            else:
                buckets["platform"].append(module.slug)
            continue
        domain = get_product_domain_for_module(module.slug)
        if domain:
            buckets.setdefault(domain, []).append(module.slug)
        else:
            buckets["platform"].append(module.slug)
    return buckets


__all__ = [
    "LEGACY_MODULES",
    "PLATFORM_MODULES",
    "describe_domains",
    "get_enabled_modules",
    "get_enabled_modules_by_domain",
    "get_module_by_slug",
    "get_product_domain_for_module",
    "get_registered_modules",
    "iter_product_module_slugs",
    "resolve_module_slug",
]
