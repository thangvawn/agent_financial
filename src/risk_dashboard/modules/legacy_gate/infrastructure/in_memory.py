"""Thread-safe in-memory repository for legacy gate statuses and decision records."""
from __future__ import annotations

from collections import OrderedDict
import threading

from risk_dashboard.modules.legacy_gate.domain.entities import (
    ModuleGateStatus,
    ReactivationDecisionRecord,
)
from risk_dashboard.modules.legacy_gate.domain.ports import GateRepositoryPort


class InMemoryGateRepository(GateRepositoryPort):
    """Thread-safe in-memory implementation of GateRepositoryPort using RLock."""

    def __init__(self, max_size: int = 1000) -> None:
        self._lock = threading.RLock()
        self._statuses: OrderedDict[str, ModuleGateStatus] = OrderedDict()
        self._decisions_by_id: OrderedDict[str, ReactivationDecisionRecord] = OrderedDict()
        self._module_decision_ids: dict[str, list[str]] = {}
        self._max_size = max_size

    def get_module_status(self, module_slug: str) -> ModuleGateStatus | None:
        with self._lock:
            status = self._statuses.get(module_slug)
            if status is not None:
                self._statuses.move_to_end(module_slug)
            return status

    def save_module_status(self, status: ModuleGateStatus) -> None:
        with self._lock:
            slug = status.module_slug
            if slug in self._statuses:
                self._statuses.move_to_end(slug)
            self._statuses[slug] = status
            while len(self._statuses) > self._max_size:
                self._statuses.popitem(last=False)

    def list_module_statuses(self) -> tuple[ModuleGateStatus, ...]:
        with self._lock:
            return tuple(self._statuses.values())

    def save_decision_record(self, record: ReactivationDecisionRecord) -> None:
        with self._lock:
            self._decisions_by_id[record.record_id] = record
            if record.module_slug not in self._module_decision_ids:
                self._module_decision_ids[record.module_slug] = []
            self._module_decision_ids[record.module_slug].append(record.record_id)
            while len(self._decisions_by_id) > self._max_size:
                oldest_id, oldest_rec = self._decisions_by_id.popitem(last=False)
                if oldest_rec.module_slug in self._module_decision_ids:
                    try:
                        self._module_decision_ids[oldest_rec.module_slug].remove(oldest_id)
                    except ValueError:
                        pass

    def get_decision_record(self, module_slug: str) -> ReactivationDecisionRecord | None:
        with self._lock:
            ids = self._module_decision_ids.get(module_slug)
            if not ids:
                return None
            return self._decisions_by_id.get(ids[-1])

    def list_decision_records(
        self, module_slug: str | None = None
    ) -> tuple[ReactivationDecisionRecord, ...]:
        with self._lock:
            if module_slug is None:
                return tuple(self._decisions_by_id.values())
            ids = self._module_decision_ids.get(module_slug, [])
            return tuple(
                self._decisions_by_id[rid] for rid in ids if rid in self._decisions_by_id
            )

    def clear(self) -> None:
        with self._lock:
            self._statuses.clear()
            self._decisions_by_id.clear()
            self._module_decision_ids.clear()
