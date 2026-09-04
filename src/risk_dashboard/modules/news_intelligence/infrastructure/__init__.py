from __future__ import annotations

from risk_dashboard.modules.news_intelligence.infrastructure.source_registry import (
    InMemorySourceRegistry,
    SourceRegistry,
    get_default_source_registry,
)

__all__ = [
    "InMemorySourceRegistry",
    "SourceRegistry",
    "get_default_source_registry",
]

