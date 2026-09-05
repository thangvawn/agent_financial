from __future__ import annotations

import sqlite3
import time
from unittest.mock import MagicMock
import pytest

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.internal_ops.application.investigation_service import InvestigationService
from risk_dashboard.modules.internal_ops.domain.contracts import (
    EvidenceBatch,
    EvidenceItem,
    EvidenceRef,
    InvestigationRequest,
)
from risk_dashboard.modules.internal_ops.infrastructure.sqlite import (
    SqliteInternalOpsRepository,
    init_ops_tables,
)


@pytest.fixture
def test_repo():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    init_ops_tables(conn)

    class InMemoryFactory:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return SqliteInternalOpsRepository(conn_factory=InMemoryFactory)


def test_resilience_adapter_timeout_fails_safe(test_repo):
    failing_analytics = MagicMock()
    failing_analytics.get_source_health.side_effect = TimeoutError("Analytics service timeout")

    service = InvestigationService(adapters={"analytics": failing_analytics}, repository=test_repo)
    principal = AuthPrincipal(account_id="admin-001", session_id="s1", scopes=("admin:internal_ops:support_viewer",), resolved_at="2026-09-05T10:00:00Z")
    req = InvestigationRequest(
        investigation_type="data_freshness",
        purpose="Check pipeline with failing upstream",
        time_from="2026-09-05T00:00:00Z",
        time_to="2026-09-05T10:00:00Z",
    )
    report = service.run_investigation(principal, req)
    assert report.status in ("incomplete", "draft", "failed")


def test_resilience_evidence_cap_enforced():
    mock_analytics = MagicMock()
    items = [
        EvidenceItem(
            ref=EvidenceRef(source_module="analytics_monitoring", resource_type="kpi", resource_id=f"kpi-{i}", observed_at="2026-09-05T10:00:00Z"),
            classification="aggregate",
            fields={"idx": i},
        )
        for i in range(150)
    ]
    mock_analytics.get_source_health.return_value = EvidenceBatch(items=tuple(items), source_module="analytics_monitoring", fetched_at="2026-09-05T10:00:00Z", status="available")
    mock_analytics.get_alert_context.return_value = EvidenceBatch(items=(), source_module="analytics_monitoring", fetched_at="2026-09-05T10:00:00Z", status="available")

    service = InvestigationService(adapters={"analytics": mock_analytics})
    principal = AuthPrincipal(account_id="admin-001", session_id="s1", scopes=("admin:internal_ops:support_viewer",), resolved_at="2026-09-05T10:00:00Z")
    req = InvestigationRequest(
        investigation_type="data_freshness",
        purpose="Test evidence capping",
        time_from="2026-09-05T00:00:00Z",
        time_to="2026-09-05T10:00:00Z",
        max_evidence_items=25,
    )
    report = service.run_investigation(principal, req)
    assert len(report.verified_findings) <= 25


def test_eval_zero_unauthorized_executions():
    service = InvestigationService(adapters={})
    principal = AuthPrincipal(account_id="admin-001", session_id="s1", scopes=("admin:internal_ops:security_admin",), resolved_at="2026-09-05T10:00:00Z")
    req = InvestigationRequest(investigation_type="incident", purpose="Verify zero unauthorized executions", time_from="2026-09-05T00:00:00Z", time_to="2026-09-05T10:00:00Z")
    report = service.run_investigation(principal, req)
    for rec in report.recommendations:
        assert rec.executable is False
        assert rec.status == "draft"
        assert rec.risk_class == "proposal"


def test_eval_100_percent_citations():
    service = InvestigationService(adapters={})
    principal = AuthPrincipal(account_id="admin-001", session_id="s1", scopes=("admin:internal_ops:security_admin",), resolved_at="2026-09-05T10:00:00Z")
    req = InvestigationRequest(investigation_type="incident", purpose="Verify 100 percent citations", time_from="2026-09-05T00:00:00Z", time_to="2026-09-05T10:00:00Z")
    report = service.run_investigation(principal, req)
    for finding in report.verified_findings:
        assert len(finding.evidence_refs) >= 1


def test_performance_slo_under_5_seconds(test_repo):
    service = InvestigationService(adapters={}, repository=test_repo)
    principal = AuthPrincipal(account_id="admin-001", session_id="s1", scopes=("admin:internal_ops:security_admin",), resolved_at="2026-09-05T10:00:00Z")
    req = InvestigationRequest(investigation_type="incident", purpose="Test performance latency SLO", time_from="2026-09-05T00:00:00Z", time_to="2026-09-05T10:00:00Z")
    start = time.perf_counter()
    service.run_investigation(principal, req)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"Investigation took {elapsed:.2f}s, exceeding 5s SLO"


def test_performance_p50_and_p95_latency(test_repo):
    mock_analytics = MagicMock()
    mock_analytics.get_source_health.return_value = EvidenceBatch(
        items=(
            EvidenceItem(
                ref=EvidenceRef(source_module="analytics_monitoring", resource_type="kpi", resource_id="kpi-metric-1", observed_at="2026-09-05T10:00:00Z"),
                classification="aggregate",
                fields={"val": 42},
            ),
        ),
        source_module="analytics_monitoring",
        fetched_at="2026-09-05T10:00:00Z",
        status="available",
    )
    mock_analytics.get_alert_context.return_value = EvidenceBatch(items=(), source_module="analytics_monitoring", fetched_at="2026-09-05T10:00:00Z", status="available")
    service = InvestigationService(adapters={"analytics": mock_analytics}, repository=test_repo)
    principal = AuthPrincipal(account_id="admin-perf", session_id="s1", scopes=("admin:internal_ops:security_admin",), resolved_at="2026-09-05T10:00:00Z")
    req = InvestigationRequest(investigation_type="incident", purpose="Measure p50 and p95 latency under load", time_from="2026-09-05T00:00:00Z", time_to="2026-09-05T10:00:00Z")

    durations: list[float] = []
    iterations = 40
    for _ in range(iterations):
        t0 = time.perf_counter()
        rep = service.run_investigation(principal, req)
        elapsed = time.perf_counter() - t0
        durations.append(elapsed)
        assert rep.status == "draft"

    durations.sort()
    p50 = durations[int(len(durations) * 0.50)]
    p95 = durations[int(len(durations) * 0.95)]

    assert p50 < 5.0, f"p50 latency {p50:.4f}s exceeded 5.0s SLO"
    assert p95 < 15.0, f"p95 latency {p95:.4f}s exceeded 15.0s SLO"

