"""Product domain map for Northstar backend modules.

Phase 4: registered slugs match product domains (home, simulation_lab).
Legacy packages stay on disk but are unmounted from the app registry.
"""

from __future__ import annotations

from typing import Any

PRODUCT_DOMAINS: dict[str, dict[str, Any]] = {
    "home": {
        "label": "Home",
        "modules": ("home",),
        "status": "active",
        "fe_feature": "features/home",
        "package": "home_onboarding",
    },
    "market_portfolio": {
        "label": "Market & Portfolio",
        "modules": ("market_portfolio", "data_hub", "watchlist_product", "portfolio_product"),
        "status": "active_facade",
        "fe_feature": "features/market-portfolio",
        "api_prefix": "/api/v1/market-portfolio",
    },
    "learn_hub": {
        "label": "Learn Hub",
        "modules": ("learning",),
        "status": "active",
        "fe_feature": "features/learn-hub",
    },
    "bctc": {
        "label": "BCTC Analysis",
        "modules": ("financials_product",),
        "status": "active",
        "fe_feature": "features/bctc",
        "retired_modules": ("guided_investing",),
    },
    "news": {
        "label": "News & Intelligence",
        "modules": ("news_intelligence",),
        "status": "active",
        "fe_feature": "features/news",
    },
    "simulation_lab": {
        "label": "Simulation Lab",
        "modules": ("simulation_lab",),
        "status": "active",
        "fe_feature": "features/simulation-lab",
        "package": "pro_lab",
        "http_prefix": "/api/v1/public/pro-lab",
    },
    "auth": {
        "label": "Auth",
        "modules": ("auth",),
        "status": "active",
        "fe_feature": "features/auth",
    },
}

# Legacy / alternate slugs → registered *module* slug (not product-domain id).
# Domain ids like "bctc"/"news" also appear here when used as module aliases.
MODULE_SLUG_ALIASES: dict[str, str] = {
    "pro_lab": "simulation_lab",
    "home_onboarding": "home",
    "market": "market_portfolio",
    "learn": "learning",
    "learn_hub": "learning",
    "bctc": "financials_product",
    "news": "news_intelligence",
}

# Unmounted from registry (Phase 4). Packages + SQLite tables retained.
LEGACY_MODULES: tuple[str, ...] = (
    "community",
    "goals",
    "financial_health",
    "guided_investing",
)

PLATFORM_MODULES: tuple[str, ...] = (
    "system_surface",
    "quant_risk",
    "analytics_monitoring",
    "trust_safety",
    "admin_cms",
)


def resolve_module_slug(slug: str) -> str:
    """Resolve alias or product-domain id to the registered module slug."""
    if slug in MODULE_SLUG_ALIASES:
        return MODULE_SLUG_ALIASES[slug]
    return slug


def get_product_domain_for_module(module_slug: str) -> str | None:
    canonical = resolve_module_slug(module_slug)
    for domain_id, meta in PRODUCT_DOMAINS.items():
        if canonical in meta["modules"]:
            return domain_id
    return None


def iter_product_module_slugs() -> tuple[str, ...]:
    slugs: list[str] = []
    for meta in PRODUCT_DOMAINS.values():
        for slug in meta["modules"]:
            if slug not in slugs:
                slugs.append(slug)
    return tuple(slugs)


def is_legacy_module(slug: str) -> bool:
    return resolve_module_slug(slug) in LEGACY_MODULES or slug in LEGACY_MODULES


def is_platform_module(slug: str) -> bool:
    return resolve_module_slug(slug) in PLATFORM_MODULES


def describe_domains() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain_id, meta in PRODUCT_DOMAINS.items():
        rows.append(
            {
                "domain": domain_id,
                "label": meta["label"],
                "modules": list(meta["modules"]),
                "status": meta["status"],
                "fe_feature": meta.get("fe_feature"),
                "package": meta.get("package"),
                "http_prefix": meta.get("http_prefix"),
                "retired_modules": list(meta.get("retired_modules") or ()),
            }
        )
    return rows
