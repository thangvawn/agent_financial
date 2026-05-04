from __future__ import annotations

import logging
import os
import threading
import time

from risk_dashboard.modules.analytics_monitoring.application.services import (
    EvaluateAlerts,
    RunKpiRollups,
    RunOpsSnapshots,
)
from risk_dashboard.modules.analytics_monitoring.infrastructure.repositories.sqlite import (
    SqliteAnalyticsMonitoringRepository,
)
from risk_dashboard.modules.analytics_monitoring.schemas.requests import (
    AlertEvaluationRequest,
    KpiRollupRequest,
    OpsSnapshotRequest,
)

_START_LOCK = threading.Lock()
_STARTED = False


def start_analytics_scheduler(logger: logging.Logger) -> None:
    global _STARTED
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    enabled = os.getenv("ENABLE_ANALYTICS_SCHEDULER", "1").strip().lower() not in {"0", "false", "off"}
    if not enabled:
        return
    with _START_LOCK:
        if _STARTED:
            return
        _STARTED = True
    thread = threading.Thread(target=_run_scheduler_loop, args=(logger,), daemon=True, name="analytics-scheduler")
    thread.start()
    logger.info("analytics_monitoring scheduler started")


def _run_scheduler_loop(logger: logging.Logger) -> None:
    repo = SqliteAnalyticsMonitoringRepository()
    kpi_interval = int(os.getenv("ANALYTICS_KPI_ROLLUP_INTERVAL_SEC", "300"))
    ops_interval = int(os.getenv("ANALYTICS_OPS_SNAPSHOT_INTERVAL_SEC", "300"))
    alert_interval = int(os.getenv("ANALYTICS_ALERT_EVAL_INTERVAL_SEC", "300"))
    next_kpi = 0.0
    next_ops = 0.0
    next_alert = 0.0
    while True:
        now = time.time()
        try:
            if now >= next_kpi:
                RunKpiRollups(repo=repo).execute(KpiRollupRequest(window_grain="day"))
                next_kpi = now + max(kpi_interval, 60)
            if now >= next_ops:
                RunOpsSnapshots(repo=repo).execute(OpsSnapshotRequest(window_hours=24))
                next_ops = now + max(ops_interval, 60)
            if now >= next_alert:
                EvaluateAlerts(repo=repo).execute(AlertEvaluationRequest(force_reopen=False))
                next_alert = now + max(alert_interval, 60)
        except Exception as exc:
            logger.exception("analytics_monitoring scheduler iteration failed: %s", exc)
            next_kpi = now + max(kpi_interval, 60)
            next_ops = now + max(ops_interval, 60)
            next_alert = now + max(alert_interval, 60)
        time.sleep(15)
