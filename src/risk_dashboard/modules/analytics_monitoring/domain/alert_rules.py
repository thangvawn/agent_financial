from __future__ import annotations

ALERT_RULES: tuple[dict[str, object], ...] = (
    {
        "rule_name": "api_error_rate_high",
        "metric_name": "api_error_rate",
        "threshold": 0.05,
        "comparison": "gt",
        "severity_tier": "SEV1",
        "surface": "public_api",
        "summary": "API error rate vượt ngưỡng an toàn.",
    },
    {
        "rule_name": "stale_insight_rate_high",
        "metric_name": "stale_insight_rate",
        "threshold": 0.20,
        "comparison": "gt",
        "severity_tier": "SEV2",
        "surface": "insights",
        "summary": "Tỷ lệ stale insight vượt ngưỡng.",
    },
    {
        "rule_name": "model_latency_high",
        "metric_name": "model_latency_p95_ms",
        "threshold": 4000.0,
        "comparison": "gt",
        "severity_tier": "SEV3",
        "surface": "ai_assistant",
        "summary": "Model latency p95 đang quá cao.",
    },
    {
        "rule_name": "moderation_queue_high",
        "metric_name": "moderation_queue_volume",
        "threshold": 100.0,
        "comparison": "gt",
        "severity_tier": "SEV2",
        "surface": "community",
        "summary": "Moderation queue volume vượt ngưỡng.",
    },
)
