from __future__ import annotations

from risk_dashboard.app.config.settings import get_settings


def model_runtime_health() -> dict[str, object]:
    settings = get_settings()
    return {
        "available": settings.default_model_path.exists(),
        "path": str(settings.default_model_path),
    }
