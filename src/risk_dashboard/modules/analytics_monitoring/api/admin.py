from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from risk_dashboard.modules.analytics_monitoring.application.services import (
    EvaluateAlerts,
    GetAnalyticsStatus,
    GetProductDashboard,
    GetTrustDashboard,
    ListAlerts,
    ListAnalyticsEvents,
    ListKpiSnapshots,
    ListOpsMetrics,
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
from risk_dashboard.modules.analytics_monitoring.schemas.responses import (
    AnalyticsDashboardResponse,
    AnalyticsEventResponse,
    AnalyticsKpiSnapshotResponse,
    AnalyticsStatusResponse,
    OpsAlertEventResponse,
    OpsMetricSnapshotResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics Monitoring (Admin)"])

ADMIN_HEADER = "X-Admin-Analytics-Key"
ADMIN_ENV = "ADMIN_ANALYTICS_KEY"


async def verify_analytics_admin(
    x_admin_analytics_key: str | None = Header(default=None, alias=ADMIN_HEADER),
) -> bool:
    expected = os.getenv(ADMIN_ENV, "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Analytics admin chưa bật: đặt ADMIN_ANALYTICS_KEY và restart backend.")
    if not x_admin_analytics_key or x_admin_analytics_key.strip() != expected:
        raise HTTPException(status_code=401, detail=f"Thiếu hoặc sai khóa {ADMIN_HEADER}.")
    return True


def _repo() -> SqliteAnalyticsMonitoringRepository:
    return SqliteAnalyticsMonitoringRepository()


@router.get("/status", response_model=AnalyticsStatusResponse)
def analytics_status(_: bool = Depends(verify_analytics_admin)) -> AnalyticsStatusResponse:
    return GetAnalyticsStatus(repo=_repo()).execute(enabled=bool(os.getenv(ADMIN_ENV, "").strip()))


@router.get("/kpis", response_model=list[AnalyticsKpiSnapshotResponse])
def analytics_kpis(
    window: str | None = Query(default=None),
    _: bool = Depends(verify_analytics_admin),
) -> list[AnalyticsKpiSnapshotResponse]:
    return ListKpiSnapshots(repo=_repo()).execute(window_grain=window)


@router.get("/kpis/{kpi_name}", response_model=list[AnalyticsKpiSnapshotResponse])
def analytics_kpi_detail(
    kpi_name: str,
    window: str | None = Query(default=None),
    _: bool = Depends(verify_analytics_admin),
) -> list[AnalyticsKpiSnapshotResponse]:
    return ListKpiSnapshots(repo=_repo()).execute(kpi_name=kpi_name, window_grain=window)


@router.get("/events", response_model=list[AnalyticsEventResponse])
def analytics_events(
    event_category: str | None = Query(default=None),
    module: str | None = Query(default=None),
    surface: str | None = Query(default=None),
    event_name: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    _: bool = Depends(verify_analytics_admin),
) -> list[AnalyticsEventResponse]:
    return ListAnalyticsEvents(repo=_repo()).execute(
        event_category=event_category,
        module=module,
        surface=surface,
        event_name=event_name,
        search=search,
        limit=limit,
    )


@router.get("/dashboards/product", response_model=AnalyticsDashboardResponse)
def analytics_product_dashboard(
    window: str = Query(default="day"),
    _: bool = Depends(verify_analytics_admin),
) -> AnalyticsDashboardResponse:
    return GetProductDashboard(repo=_repo()).execute(window_grain=window)


@router.get("/dashboards/trust", response_model=AnalyticsDashboardResponse)
def analytics_trust_dashboard(_: bool = Depends(verify_analytics_admin)) -> AnalyticsDashboardResponse:
    return GetTrustDashboard(repo=_repo()).execute()


@router.get("/ops/freshness", response_model=list[OpsMetricSnapshotResponse])
def analytics_ops_freshness(_: bool = Depends(verify_analytics_admin)) -> list[OpsMetricSnapshotResponse]:
    return ListOpsMetrics(repo=_repo()).execute(metric_group="data_freshness")


@router.get("/ops/api-health", response_model=list[OpsMetricSnapshotResponse])
def analytics_ops_api_health(_: bool = Depends(verify_analytics_admin)) -> list[OpsMetricSnapshotResponse]:
    return ListOpsMetrics(repo=_repo()).execute(metric_group="api_health")


@router.get("/ops/moderation", response_model=list[OpsMetricSnapshotResponse])
def analytics_ops_moderation(_: bool = Depends(verify_analytics_admin)) -> list[OpsMetricSnapshotResponse]:
    return ListOpsMetrics(repo=_repo()).execute(metric_group="moderation")


@router.get("/alerts", response_model=list[OpsAlertEventResponse])
def analytics_alerts(
    status: str | None = Query(default=None),
    _: bool = Depends(verify_analytics_admin),
) -> list[OpsAlertEventResponse]:
    return ListAlerts(repo=_repo()).execute(status=status)


@router.post("/jobs/run-kpi-rollup", response_model=list[AnalyticsKpiSnapshotResponse])
def analytics_run_kpi_rollup(
    req: KpiRollupRequest,
    _: bool = Depends(verify_analytics_admin),
) -> list[AnalyticsKpiSnapshotResponse]:
    return RunKpiRollups(repo=_repo()).execute(req)


@router.post("/jobs/run-ops-snapshot", response_model=list[OpsMetricSnapshotResponse])
def analytics_run_ops_snapshot(
    req: OpsSnapshotRequest,
    _: bool = Depends(verify_analytics_admin),
) -> list[OpsMetricSnapshotResponse]:
    return RunOpsSnapshots(repo=_repo()).execute(req)


@router.post("/jobs/evaluate-alerts", response_model=list[OpsAlertEventResponse])
def analytics_evaluate_alerts(
    req: AlertEvaluationRequest,
    _: bool = Depends(verify_analytics_admin),
) -> list[OpsAlertEventResponse]:
    return EvaluateAlerts(repo=_repo()).execute(req)
