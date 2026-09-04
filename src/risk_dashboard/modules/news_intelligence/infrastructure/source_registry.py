from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from risk_dashboard.modules.news_intelligence.domain.ports import SourceRegistryPort
from risk_dashboard.modules.news_intelligence.domain.source_health import SourceHealthRecord
from risk_dashboard.modules.news_intelligence.infrastructure.source_inventory import DEFAULT_PILOT_SOURCES
from risk_dashboard.modules.news_intelligence.schemas.agent_tools import (
    SourceHealthRow,
    SourceRef,
)


class InMemorySourceRegistry(SourceRegistryPort):
    def __init__(self, initial_sources: list[dict[str, Any]] | None = None) -> None:
        self._sources: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        items = initial_sources if initial_sources is not None else DEFAULT_PILOT_SOURCES
        for item in items:
            self._sources[item["source_id"]] = dict(item)

    def register_source(self, **source_kwargs: Any) -> None:
        source_id = source_kwargs["source_id"]
        with self._lock:
            self._sources[source_id] = dict(source_kwargs)

    def get_source(self, source_id: str) -> SourceRef | None:
        with self._lock:
            raw = self._sources.get(source_id)
        if not raw:
            return None
        return SourceRef(
            source_id=raw["source_id"],
            name=raw["name"],
            url=raw["url"],
            tier=raw["tier"],
            region=raw["region"],
            category=raw["category"],
            license_class=raw["license_class"],
            attribution_text=raw.get("attribution_text"),
        )

    def list_sources(self, **filters: Any) -> list[SourceRef]:
        results: list[SourceRef] = []
        with self._lock:
            sources_copy = list(self._sources.values())

        for raw in sources_copy:
            match = True
            for k, v in filters.items():
                if raw.get(k) != v:
                    match = False
                    break
            if match:
                results.append(
                    SourceRef(
                        source_id=raw["source_id"],
                        name=raw["name"],
                        url=raw["url"],
                        tier=raw["tier"],
                        region=raw["region"],
                        category=raw["category"],
                        license_class=raw["license_class"],
                        attribution_text=raw.get("attribution_text"),
                    )
                )
        return results

    def get_health(self, source_ids: tuple[str, ...] = ()) -> list[SourceHealthRecord]:
        with self._lock:
            target_ids = source_ids if source_ids else tuple(self._sources.keys())
            sources_map = {k: dict(v) for k, v in self._sources.items()}

        records: list[SourceHealthRecord] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for sid in target_ids:
            raw = sources_map.get(sid)
            if not raw:
                records.append(
                    SourceHealthRecord(
                        source_id=sid,
                        name=sid,
                        tier=5,
                        region="UNKNOWN",
                        category="unknown",
                        license_class="restricted",
                        attribution_text=None,
                        is_available=False,
                        last_success_at=None,
                        staleness_minutes=9999,
                        error_rate_24h=1.0,
                        quality_flag="unreliable",
                        redistribution_allowed=False,
                    )
                )
                continue

            last_success = raw.get("last_success_at") or now_iso
            records.append(
                SourceHealthRecord(
                    source_id=raw["source_id"],
                    name=raw["name"],
                    tier=raw["tier"],
                    region=raw["region"],
                    category=raw["category"],
                    license_class=raw["license_class"],
                    attribution_text=raw.get("attribution_text"),
                    is_available=raw.get("is_available", True),
                    last_success_at=last_success,
                    staleness_minutes=raw.get("staleness_minutes", 0),
                    error_rate_24h=raw.get("error_rate_24h", 0.0),
                    quality_flag=raw.get("quality_flag", "ok"),
                    redistribution_allowed=raw.get("redistribution_allowed", True),
                )
            )
        return records

    def evaluate_coverage(self, source_ids: tuple[str, ...] = ()) -> bool:
        health_records = self.get_health(source_ids)
        if not health_records:
            return False

        for rec in health_records:
            if not rec.is_available:
                return False
            if rec.license_class == "restricted" or not rec.redistribution_allowed:
                return False
            if rec.quality_flag == "unreliable":
                return False
            if rec.error_rate_24h >= 0.5:
                return False
            if rec.staleness_minutes > 1440 * 3:
                return False

        return True


SourceRegistry = InMemorySourceRegistry
_DEFAULT_REGISTRY: InMemorySourceRegistry | None = None
_REGISTRY_LOCK = threading.Lock()


def get_default_source_registry() -> InMemorySourceRegistry:
    global _DEFAULT_REGISTRY
    with _REGISTRY_LOCK:
        if _DEFAULT_REGISTRY is None:
            _DEFAULT_REGISTRY = InMemorySourceRegistry()
        return _DEFAULT_REGISTRY


def reset_default_source_registry() -> None:
    global _DEFAULT_REGISTRY
    with _REGISTRY_LOCK:
        _DEFAULT_REGISTRY = None
