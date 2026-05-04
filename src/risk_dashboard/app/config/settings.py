from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    title: str
    version: str
    description: str
    project_root: Path
    app_state_db_path: Path
    legacy_dashboard_html: Path
    frontend_dist: Path
    learning_assets_dir: Path
    default_model_path: Path
    openapi_tags: tuple[dict[str, str], ...]


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    project_root = Path(__file__).resolve().parents[4]
    app_state_db_path = project_root / "data" / "app_state.db"
    legacy_dashboard_html = project_root / "src" / "risk_dashboard" / "api" / "dashboard.html"
    frontend_dist = project_root / "frontend" / "dist"
    learning_assets_dir = project_root / "data" / "learning_assets"
    default_model_path = project_root / "data" / "models" / "latest_model.pkl"
    return AppSettings(
        title="Risk Dashboard API",
        version="0.1.0",
        description="Neural-symbolic risk pipeline for Vietnamese equity market",
        project_root=project_root,
        app_state_db_path=app_state_db_path,
        legacy_dashboard_html=legacy_dashboard_html,
        frontend_dist=frontend_dist,
        learning_assets_dir=learning_assets_dir,
        default_model_path=default_model_path,
        openapi_tags=(
            {"name": "System", "description": "Health checks and system state"},
            {"name": "Dashboard", "description": "Chart data, live feed, money flow"},
            {"name": "Quant", "description": "EOD pipeline and scenario simulation"},
            {"name": "Chat", "description": "Multi-agent LLM chat"},
            {"name": "Financials", "description": "Financial statement analysis"},
            {"name": "Admin", "description": "Panel management"},
            {
                "name": "Trading Lab (Admin)",
                "description": "Sandbox LLM chiến lược — chỉ admin, không broker",
            },
            {"name": "Backtest", "description": "Buy-and-hold backtest danh mục VN (yfinance)"},
            {"name": "Watchlist", "description": "OHLCV cache & đồng bộ giá cho mã theo dõi"},
            {"name": "Learning", "description": "Learn Hub and onboarding surfaces"},
            {"name": "Goals", "description": "Life goals, gap-to-target planning and reminders"},
            {"name": "Pro Lab", "description": "Premium/internal research workspace separated from retail public mode"},
            {"name": "Content Ops (Admin)", "description": "Admin CMS, review flow, publishing and analytics for public-safe content"},
        ),
    )
