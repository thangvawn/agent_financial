from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from risk_dashboard.api.main import app
from risk_dashboard.modules.analytics_monitoring.infrastructure.repositories.sqlite import (
    reset_analytics_monitoring_state,
)


def _headers() -> dict[str, str]:
    return {"X-Admin-Analytics-Key": "analytics-test"}


def test_analytics_monitoring_ingest_rollups_and_alerts(monkeypatch):
    reset_analytics_monitoring_state()
    monkeypatch.setenv("ADMIN_ANALYTICS_KEY", "analytics-test")
    client = TestClient(app)
    base = datetime.now(timezone.utc)

    ingest = client.post(
        "/api/v1/public/analytics/events",
        json={
            "events": [
                {
                    "event_name": "onboarding_started",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=33)).isoformat(),
                    "module": "home_onboarding",
                    "surface": "onboarding",
                    "session_id": "sess_1",
                    "properties": {"step_key": "intro"},
                },
                {
                    "event_name": "onboarding_completed",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=31)).isoformat(),
                    "module": "home_onboarding",
                    "surface": "onboarding",
                    "session_id": "sess_1",
                    "properties": {"persona": "starter"},
                },
                {
                    "event_name": "financial_health_input_completed",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=23)).isoformat(),
                    "module": "financial_health",
                    "surface": "financial_health",
                    "session_id": "sess_1",
                    "properties": {"score_band": "building"},
                },
                {
                    "event_name": "goal_created",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=18)).isoformat(),
                    "module": "goals",
                    "surface": "goals",
                    "session_id": "sess_1",
                    "properties": {"goal_type": "emergency_fund"},
                },
                {
                    "event_name": "learning_lesson_completed",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=13)).isoformat(),
                    "module": "learning",
                    "surface": "learning",
                    "session_id": "sess_1",
                    "properties": {"lesson_id": "money-basics-01"},
                },
                {
                    "event_name": "guided_market_context_viewed",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=8)).isoformat(),
                    "module": "guided_investing",
                    "surface": "guided_investing",
                    "session_id": "sess_1",
                    "properties": {"eligible": True},
                },
                {
                    "event_name": "insight_card_opened",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=7)).isoformat(),
                    "module": "insights",
                    "surface": "insights",
                    "session_id": "sess_1",
                    "properties": {"insight_id": "market_regime_snapshot"},
                },
                {
                    "event_name": "community_space_joined",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=6)).isoformat(),
                    "module": "community",
                    "surface": "community",
                    "session_id": "sess_1",
                    "properties": {"space_id": "risk-basics-circle"},
                },
                {
                    "event_name": "pro_lab_experiment_run",
                    "event_category": "product",
                    "timestamp": (base - timedelta(minutes=5)).isoformat(),
                    "module": "pro_lab",
                    "surface": "pro_lab",
                    "user_id": "user_pro",
                    "properties": {"experiment_id": "exp_1"},
                },
                {
                    "event_name": "ops_api_request_logged",
                    "event_category": "ops",
                    "timestamp": (base - timedelta(minutes=3)).isoformat(),
                    "module": "api",
                    "surface": "public_api",
                    "properties": {"endpoint_group": "public", "success": False, "latency_ms": 1200},
                },
                {
                    "event_name": "ops_api_request_logged",
                    "event_category": "ops",
                    "timestamp": (base - timedelta(minutes=2)).isoformat(),
                    "module": "api",
                    "surface": "public_api",
                    "properties": {"endpoint_group": "public", "success": True, "latency_ms": 800},
                },
                {
                    "event_name": "ops_model_call_logged",
                    "event_category": "ops",
                    "timestamp": (base - timedelta(minutes=1)).isoformat(),
                    "module": "ai_assistant",
                    "surface": "ai_assistant",
                    "properties": {"role": "analyst", "success": True, "latency_ms": 5001},
                },
                {
                    "event_name": "ops_data_refresh_logged",
                    "event_category": "ops",
                    "timestamp": base.isoformat(),
                    "module": "insights",
                    "surface": "insights",
                    "properties": {"source": "insight_snapshot", "freshness_status": "stale"},
                },
            ]
        },
    )
    assert ingest.status_code == 200
    assert ingest.json() == {"accepted": 13, "rejected": 0}

    status = client.get("/admin/analytics/status", headers=_headers())
    assert status.status_code == 200
    assert status.json()["total_events"] == 13

    kpi_rollup = client.post(
        "/admin/analytics/jobs/run-kpi-rollup",
        headers=_headers(),
        json={"window_grain": "day"},
    )
    assert kpi_rollup.status_code == 200
    assert any(item["kpi_name"] == "onboarding_completion_rate" for item in kpi_rollup.json())

    kpis = client.get("/admin/analytics/kpis?window=day", headers=_headers())
    assert kpis.status_code == 200
    kpi_map = {item["kpi_name"]: item["value"] for item in kpis.json()}
    assert kpi_map["onboarding_completion_rate"] == 1.0
    assert kpi_map["goal_created_count"] == 1.0
    assert kpi_map["insight_open_count"] == 1.0

    queried_events = client.get(
        "/admin/analytics/events?event_category=product&module=learning&limit=10",
        headers=_headers(),
    )
    assert queried_events.status_code == 200
    assert [item["event_name"] for item in queried_events.json()] == ["learning_lesson_completed"]

    ops_snapshot = client.post(
        "/admin/analytics/jobs/run-ops-snapshot",
        headers=_headers(),
        json={"window_hours": 24},
    )
    assert ops_snapshot.status_code == 200
    metric_map = {item["metric_name"]: item["value"] for item in ops_snapshot.json()}
    assert metric_map["api_error_rate"] == 0.5
    assert metric_map["model_latency_p95_ms"] == 5001.0
    assert metric_map["stale_insight_rate"] == 1.0

    api_health = client.get("/admin/analytics/ops/api-health", headers=_headers())
    assert api_health.status_code == 200
    assert any(item["metric_name"] == "api_p95_latency_ms" for item in api_health.json())

    moderation = client.get("/admin/analytics/ops/moderation", headers=_headers())
    assert moderation.status_code == 200
    assert any(item["metric_name"] == "moderation_queue_volume" for item in moderation.json())

    alerts = client.post(
        "/admin/analytics/jobs/evaluate-alerts",
        headers=_headers(),
        json={"force_reopen": False},
    )
    assert alerts.status_code == 200
    rule_names = {item["rule_name"] for item in alerts.json()}
    assert "api_error_rate_high" in rule_names
    assert "stale_insight_rate_high" in rule_names
    assert "model_latency_high" in rule_names

    alert_list = client.get("/admin/analytics/alerts?status=open", headers=_headers())
    assert alert_list.status_code == 200
    assert len(alert_list.json()) >= 3

    product_dashboard = client.get("/admin/analytics/dashboards/product?window=day", headers=_headers())
    assert product_dashboard.status_code == 200
    product_metric_map = {item["key"]: item["value"] for item in product_dashboard.json()["summary_metrics"]}
    assert product_metric_map["onboarding_completion_rate"] == 1.0
    assert product_metric_map["goal_created_count"] == 1.0
    assert any(item["module"] == "home_onboarding" for item in product_dashboard.json()["module_activity"])

    trust_dashboard = client.get("/admin/analytics/dashboards/trust", headers=_headers())
    assert trust_dashboard.status_code == 200
    trust_metric_map = {item["key"]: item["value"] for item in trust_dashboard.json()["summary_metrics"]}
    assert trust_metric_map["stale_insight_rate"] == 1.0
    assert trust_metric_map["api_error_rate"] == 0.5
    assert any(item["rule_name"] == "stale_insight_rate_high" for item in trust_dashboard.json()["open_alerts"])
