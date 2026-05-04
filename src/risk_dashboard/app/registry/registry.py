from __future__ import annotations

from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.analytics_monitoring.module import module as analytics_monitoring_module
from risk_dashboard.modules.agent_orchestration.module import module as agent_orchestration_module
from risk_dashboard.modules.ai_assistant.module import module as ai_assistant_module
from risk_dashboard.modules.admin_cms.module import module as admin_cms_module
from risk_dashboard.modules.community.module import module as community_module
from risk_dashboard.modules.data_hub.module import module as data_hub_module
from risk_dashboard.modules.financial_health.module import module as financial_health_module
from risk_dashboard.modules.financials_product.module import module as financials_product_module
from risk_dashboard.modules.goals.module import module as goals_module
from risk_dashboard.modules.guided_investing.module import module as guided_investing_module
from risk_dashboard.modules.home_onboarding.module import module as home_onboarding_module
from risk_dashboard.modules.insights.module import module as insights_module
from risk_dashboard.modules.learning.module import module as learning_module
from risk_dashboard.modules.news_intelligence.module import module as news_intelligence_module
from risk_dashboard.modules.portfolio_product.module import module as portfolio_product_module
from risk_dashboard.modules.pro_lab.module import module as pro_lab_module
from risk_dashboard.modules.quant_risk.module import module as quant_risk_module
from risk_dashboard.modules.system_surface.module import module as system_surface_module
from risk_dashboard.modules.trust_safety.module import module as trust_safety_module
from risk_dashboard.modules.watchlist_product.module import module as watchlist_product_module
from risk_dashboard.platform.feature_flags.service import FeatureFlagService


def get_registered_modules() -> tuple[ModuleDefinition, ...]:
    return (
        system_surface_module,
        quant_risk_module,
        agent_orchestration_module,
        ai_assistant_module,
        analytics_monitoring_module,
        trust_safety_module,
        admin_cms_module,
        news_intelligence_module,
        data_hub_module,
        community_module,
        financial_health_module,
        goals_module,
        insights_module,
        guided_investing_module,
        financials_product_module,
        watchlist_product_module,
        portfolio_product_module,
        pro_lab_module,
        home_onboarding_module,
        learning_module,
    )


def get_enabled_modules(feature_flags: FeatureFlagService) -> list[ModuleDefinition]:
    enabled: list[ModuleDefinition] = []
    for module in get_registered_modules():
        flag_name = f"module.{module.slug}.enabled"
        if feature_flags.is_enabled(flag_name, default=module.enabled_by_default):
            enabled.append(module)
    return enabled
