from __future__ import annotations

import json
from datetime import datetime, timezone

from risk_dashboard.modules.analytics_monitoring.domain.events import AnalyticsEvent
from risk_dashboard.modules.analytics_monitoring.infrastructure.repositories.sqlite import (
    SqliteAnalyticsMonitoringRepository,
    new_analytics_event_id,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit_analytics_event(
    *,
    event_name: str,
    event_category: str,
    module: str,
    surface: str,
    properties: dict[str, object] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    persona_segment: str | None = None,
    route: str | None = None,
    locale: str | None = None,
    device_type: str | None = None,
    source_surface: str | None = None,
    target_surface: str | None = None,
    timestamp: str | None = None,
) -> None:
    try:
        SqliteAnalyticsMonitoringRepository().save_events(
            [
                AnalyticsEvent(
                    event_id=new_analytics_event_id(),
                    event_name=event_name,
                    event_category=event_category,
                    schema_version=1,
                    timestamp=timestamp or utc_now_iso(),
                    module=module,
                    surface=surface,
                    user_id=user_id,
                    session_id=session_id,
                    persona_segment=persona_segment,
                    route=route,
                    locale=locale,
                    device_type=device_type,
                    source_surface=source_surface,
                    target_surface=target_surface,
                    properties_json=json.dumps(properties or {}, ensure_ascii=False),
                )
            ]
        )
    except Exception:
        return


def emit_product_event(
    *,
    event_name: str,
    module: str,
    surface: str,
    properties: dict[str, object] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    persona_segment: str | None = None,
    route: str | None = None,
    source_surface: str | None = None,
    target_surface: str | None = None,
) -> None:
    emit_analytics_event(
        event_name=event_name,
        event_category="product",
        module=module,
        surface=surface,
        properties=properties,
        user_id=user_id,
        session_id=session_id,
        persona_segment=persona_segment,
        route=route,
        source_surface=source_surface,
        target_surface=target_surface,
    )


def emit_ops_event(
    *,
    event_name: str,
    module: str,
    surface: str,
    properties: dict[str, object] | None = None,
    source_surface: str | None = None,
    target_surface: str | None = None,
) -> None:
    emit_analytics_event(
        event_name=event_name,
        event_category="ops",
        module=module,
        surface=surface,
        properties=properties,
        source_surface=source_surface,
        target_surface=target_surface,
    )
