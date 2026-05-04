from __future__ import annotations

from fastapi import APIRouter

from risk_dashboard.modules.analytics_monitoring.application.services import IngestAnalyticsEvents
from risk_dashboard.modules.analytics_monitoring.infrastructure.repositories.sqlite import (
    SqliteAnalyticsMonitoringRepository,
)
from risk_dashboard.modules.analytics_monitoring.schemas.requests import AnalyticsIngestRequest
from risk_dashboard.modules.analytics_monitoring.schemas.responses import AnalyticsIngestResponse

router = APIRouter(tags=["Analytics Monitoring"])


def _repo() -> SqliteAnalyticsMonitoringRepository:
    return SqliteAnalyticsMonitoringRepository()


@router.post("/analytics/events", response_model=AnalyticsIngestResponse)
def ingest_analytics_events(req: AnalyticsIngestRequest) -> AnalyticsIngestResponse:
    return IngestAnalyticsEvents(repo=_repo()).execute(req)
