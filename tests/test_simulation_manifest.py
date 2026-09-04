from __future__ import annotations

import json
import pytest
from pydantic import ValidationError

from risk_dashboard.modules.pro_lab.application.helpers import check_metric_compatibility
from risk_dashboard.modules.pro_lab.schemas.simulation_agent import ReproducibilityManifest


def _make_valid_manifest() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        schema_version="1.0.0",
        strategy_id="strat_trend_v1",
        strategy_version="1.0.0",
        dataset_source="cafef_eod",
        dataset_version="v2024.1",
        data_start="2021-01-01",
        data_end="2023-12-31",
        parameters={"sma_fast": 20, "sma_slow": 50, "stop_loss_pct": 5.0},
        commission_pct=0.15,
        slippage_pct=0.20,
        benchmark="VNINDEX",
        random_seed=12345,
        engine_version="1.0.0",
        execution_timestamp="2026-09-02T12:00:00Z",
        metrics_calculation_version="1.0.0",
        warnings=("Test warning",),
        data_gaps=(),
    )


def test_manifest_round_trip():
    manifest = _make_valid_manifest()
    serialized = manifest.model_dump_json()
    data = json.loads(serialized)
    deserialized = ReproducibilityManifest(**data)

    assert deserialized == manifest
    assert deserialized.schema_version == "1.0.0"
    assert deserialized.parameters["sma_fast"] == 20
    assert deserialized.random_seed == 12345


def test_deterministic_replay_hash_and_parameters():
    m1 = _make_valid_manifest()
    m2 = _make_valid_manifest()

    # Same manifest configuration produces exact same hashable dictionary
    assert m1.model_dump() == m2.model_dump()
    assert hash((m1.strategy_id, m1.strategy_version, m1.random_seed)) == hash((m2.strategy_id, m2.strategy_version, m2.random_seed))


def test_missing_required_pins_rejection():
    # Strategy ID missing
    with pytest.raises(ValidationError):
        ReproducibilityManifest(
            strategy_id="",
            strategy_version="1.0.0",
            dataset_source="cafef_eod",
            dataset_version="v2024.1",
            data_start="2021-01-01",
            data_end="2023-12-31",
            commission_pct=0.15,
            slippage_pct=0.2,
            benchmark="VNINDEX",
            engine_version="1.0.0",
            execution_timestamp="2026-09-02T12:00:00Z",
            metrics_calculation_version="1.0.0",
        )

    # Negative commission
    with pytest.raises(ValidationError):
        ReproducibilityManifest(
            strategy_id="strat_1",
            strategy_version="1.0.0",
            dataset_source="cafef_eod",
            dataset_version="v2024.1",
            data_start="2021-01-01",
            data_end="2023-12-31",
            commission_pct=-0.05,
            slippage_pct=0.2,
            benchmark="VNINDEX",
            engine_version="1.0.0",
            execution_timestamp="2026-09-02T12:00:00Z",
            metrics_calculation_version="1.0.0",
        )


def test_metric_calculation_version_compatibility():
    compat, reason = check_metric_compatibility("1.0.0", "1.2.0")
    assert compat is True
    assert reason == ""

    compat_diff, reason_diff = check_metric_compatibility("1.0.0", "2.0.0")
    assert compat_diff is False
    assert "khác major version" in reason_diff

