from __future__ import annotations

from risk_dashboard.modules.home_onboarding.domain.journey_ports import HomeSummaryReader
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.bctc import (
    BctcSummaryReader,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.learning import (
    LearningSummaryReader,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.market import (
    MarketSummaryReader,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.news import (
    NewsSummaryReader,
)
from risk_dashboard.modules.home_onboarding.infrastructure.summary_adapters.simulation import (
    SimulationSummaryReader,
)

LEARNING_READER = LearningSummaryReader()
BCTC_READER = BctcSummaryReader()
SIMULATION_READER = SimulationSummaryReader()
NEWS_READER = NewsSummaryReader()
MARKET_READER = MarketSummaryReader()

SURFACE_READERS: dict[str, HomeSummaryReader] = {
    "learn": LEARNING_READER,
    "bctc": BCTC_READER,
    "simulation": SIMULATION_READER,
    "news": NEWS_READER,
    "market": MARKET_READER,
}

__all__ = [
    "LearningSummaryReader",
    "BctcSummaryReader",
    "SimulationSummaryReader",
    "NewsSummaryReader",
    "MarketSummaryReader",
    "LEARNING_READER",
    "BCTC_READER",
    "SIMULATION_READER",
    "NEWS_READER",
    "MARKET_READER",
    "SURFACE_READERS",
]

