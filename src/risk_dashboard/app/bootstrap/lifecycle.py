from __future__ import annotations

import logging

from risk_dashboard.modules.analytics_monitoring.application.scheduler import start_analytics_scheduler
from risk_dashboard.platform.runtime.panel_store import startup_initialize_runtime

logger = logging.getLogger(__name__)


def on_startup() -> None:
    startup_initialize_runtime(logger=logger)
    start_analytics_scheduler(logger=logger)
