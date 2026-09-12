from __future__ import annotations

from typing import Any


class MultiAgentTelemetryCollector:
    """Telemetry collector tracking performance, reliability, and errors for Multi-Agent Engine."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._total_runs: int = 0
        self._successful_runs: int = 0
        self._failed_runs: int = 0
        self._latencies_ms: list[float] = []
        self._error_types: dict[str, int] = {}

    def record_run(self, result: Any) -> None:
        """Record an individual evaluation run, summary snapshot, or error event."""
        if hasattr(result, "passed") and hasattr(result, "latency_ms"):
            self._total_runs += 1
            lat = float(result.latency_ms)
            if lat > 0:
                self._latencies_ms.append(lat)
            if result.passed:
                self._successful_runs += 1
            else:
                self._failed_runs += 1
                violations = getattr(result, "violations", ())
                if violations:
                    for v in violations:
                        self._error_types[str(v)] = self._error_types.get(str(v), 0) + 1
                else:
                    cat = getattr(result, "category", "evaluation_failure")
                    self._error_types[str(cat)] = self._error_types.get(str(cat), 0) + 1

        elif hasattr(result, "total_cases") and hasattr(result, "passed_cases"):
            if self._total_runs == 0:
                self._total_runs = int(result.total_cases)
                self._successful_runs = int(result.passed_cases)
                self._failed_runs = int(result.total_cases - result.passed_cases)
            p95 = getattr(result, "p95_latency_ms", 0.0)
            if p95 > 0 and not self._latencies_ms:
                self._latencies_ms.append(float(p95))

        elif isinstance(result, Exception):
            self._total_runs += 1
            self._failed_runs += 1
            err_type = type(result).__name__
            self._error_types[err_type] = self._error_types.get(err_type, 0) + 1

        elif isinstance(result, dict):
            if "passed" in result:
                self._total_runs += 1
                if result["passed"]:
                    self._successful_runs += 1
                else:
                    self._failed_runs += 1
                if "latency_ms" in result and result["latency_ms"] > 0:
                    self._latencies_ms.append(float(result["latency_ms"]))
                for err in result.get("violations", []):
                    self._error_types[str(err)] = self._error_types.get(str(err), 0) + 1
            elif "total_runs" in result:
                self._total_runs += int(result.get("total_runs", 0))
                self._successful_runs += int(result.get("successful_runs", 0))
                self._failed_runs += int(result.get("failed_runs", 0))
                if "latency_ms_p95" in result and result["latency_ms_p95"] > 0:
                    self._latencies_ms.append(float(result["latency_ms_p95"]))
                for err, cnt in result.get("error_types", {}).items():
                    self._error_types[str(err)] = self._error_types.get(str(err), 0) + int(cnt)

    def get_summary(self) -> dict[str, Any]:
        """Return snapshot dictionary of current multi-agent telemetry metrics."""
        total = self._total_runs
        successful = self._successful_runs
        failed = self._failed_runs
        rate = (successful / total) if total > 0 else 0.0

        p95 = 0.0
        if self._latencies_ms:
            sorted_lat = sorted(self._latencies_ms)
            idx = min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)
            p95 = float(sorted_lat[idx])

        return {
            "total_runs": total,
            "successful_runs": successful,
            "failed_runs": failed,
            "success_rate": round(rate, 4),
            "latency_ms_p95": round(p95, 2),
            "error_types": dict(self._error_types),
        }


_global_collector = MultiAgentTelemetryCollector()


def get_multi_agent_collector() -> MultiAgentTelemetryCollector:
    return _global_collector


def record_multi_agent_run(result: Any) -> None:
    _global_collector.record_run(result)


def get_multi_agent_telemetry() -> dict[str, Any]:
    return _global_collector.get_summary()


def reset_multi_agent_telemetry() -> None:
    _global_collector.reset()


__all__ = [
    "MultiAgentTelemetryCollector",
    "get_multi_agent_collector",
    "get_multi_agent_telemetry",
    "record_multi_agent_run",
    "reset_multi_agent_telemetry",
]
