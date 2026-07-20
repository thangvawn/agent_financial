from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.app.registry.product_domains import (
    LEGACY_MODULES,
    MODULE_SLUG_ALIASES,
    PLATFORM_MODULES,
    PRODUCT_DOMAINS,
    describe_domains,
    get_product_domain_for_module,
    is_legacy_module,
    is_platform_module,
    resolve_module_slug,
)
from risk_dashboard.app.registry.registry import (
    get_enabled_modules,
    get_enabled_modules_by_domain,
    get_module_by_slug,
    get_registered_modules,
)

__all__ = [
    "LEGACY_MODULES",
    "MODULE_SLUG_ALIASES",
    "PLATFORM_MODULES",
    "PRODUCT_DOMAINS",
    "ModuleDefinition",
    "describe_domains",
    "get_enabled_modules",
    "get_enabled_modules_by_domain",
    "get_module_by_slug",
    "get_product_domain_for_module",
    "get_registered_modules",
    "is_legacy_module",
    "is_platform_module",
    "resolve_module_slug",
]
