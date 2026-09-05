"""Compatibility and rollout verification tests (QF4 Exit Gate & Dual-Run Parity)."""
from __future__ import annotations

import re
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.app.registry.registry import get_registered_modules
from risk_dashboard.engines.agents.graph import run_eod_narrative
from risk_dashboard.engines.quant.research_report import build_model_research_report
from risk_dashboard.engines.quant.scenario import rerun_with_macro_override
from risk_dashboard.modules.quant_research.infrastructure.engine_adapter import (
    QuantEngineAdapter,
)
from risk_dashboard.modules.quant_risk.api.public import router as quant_risk_router
from risk_dashboard.platform.runtime.panel_store import set_panel_for_testing


@pytest.fixture(autouse=True)
def setup_panel(synthetic_panel):
    set_panel_for_testing(synthetic_panel)
    return synthetic_panel


@pytest.fixture
def quant_risk_client():
    app = FastAPI(title="Quant Risk Compatibility App")
    app.include_router(quant_risk_router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Dual-Run Parity: run_eod_narrative (old wrapper) vs QuantEngineAdapter
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_dual_run_eod_parity(synthetic_panel, as_of_date) -> None:
    """Unwrap run_eod_narrative.quant and exact-compare with adapter output."""
    run_id = "dual-run-parity-001"

    # Old wrapper call
    manifest = run_eod_narrative(synthetic_panel, as_of_date, run_id=run_id)
    core_quant = manifest.quant

    # New adapter call
    adapter = QuantEngineAdapter()
    tool_result = await adapter.run_eod_analysis(as_of=as_of_date, run_id=run_id)
    payload = tool_result.payload

    # Exact comparison of core output fields
    assert payload["run_id"] == run_id
    assert payload["decision_score"] == core_quant.decision_score
    assert payload["risk_regime"] == core_quant.risk_regime
    assert payload["horizons"]["p_decline_1w"] == core_quant.horizons.p_decline_1w
    assert payload["horizons"]["p_decline_2w"] == core_quant.horizons.p_decline_2w
    assert payload["horizons"]["p_decline_1m"] == core_quant.horizons.p_decline_1m
    assert payload["dominant_feature"] == core_quant.dominant_feature
    assert payload["provenance"]["benchmark_dir"] == core_quant.provenance.benchmark_dir
    assert payload["provenance"]["panel_rows"] == core_quant.provenance.panel_rows


@pytest.mark.anyio
async def test_dual_run_scenario_parity(synthetic_panel, as_of_date) -> None:
    """Compare rerun_with_macro_override with adapter compare_macro_scenario."""
    direct = rerun_with_macro_override(
        synthetic_panel,
        as_of_date,
        usd_vnd_rate=25800.0,
        sbv_interest_rate_pct=5.0,
    )
    adapter = QuantEngineAdapter()
    tool_result = await adapter.compare_macro_scenario(
        as_of=as_of_date,
        usd_vnd_rate=25800.0,
        sbv_interest_rate_pct=5.0,
    )
    payload = tool_result.payload

    assert payload["decision_score"] == direct.decision_score
    assert payload["risk_regime"] == direct.risk_regime
    assert payload["horizons"]["p_decline_1w"] == direct.horizons.p_decline_1w
    assert payload["horizons"]["p_decline_2w"] == direct.horizons.p_decline_2w
    assert payload["horizons"]["p_decline_1m"] == direct.horizons.p_decline_1m


# ---------------------------------------------------------------------------
# 2. Existing quant_risk routes remain 100% functional and unchanged
# ---------------------------------------------------------------------------


def test_existing_quant_risk_eod_route(quant_risk_client, as_of_date) -> None:
    res = quant_risk_client.post(
        "/eod/run",
        json={"as_of": as_of_date.isoformat(), "run_id": "legacy-eod-test"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "quant" in data
    assert "narrative" in data
    assert "review" in data
    assert data["quant"]["decision_score"] is not None


def test_existing_quant_risk_scenario_route(quant_risk_client, as_of_date) -> None:
    res = quant_risk_client.post(
        "/scenario/rerun",
        json={
            "as_of": as_of_date.isoformat(),
            "usd_vnd_rate": 25500.0,
            "sbv_interest_rate_pct": 4.5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "decision_score" in data
    assert "risk_regime" in data


def test_existing_quant_risk_model_report_route(quant_risk_client) -> None:
    res = quant_risk_client.get("/research/model-report")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# 3. Import Purity & Quantum Computing Checks (DoD Verification)
# ---------------------------------------------------------------------------


def test_zero_imports_from_deprecated_quant_shim() -> None:
    """Verify that zero imports in quant_research use the deprecated risk_dashboard.quant shim."""
    pkg_root = Path("src/risk_dashboard/modules/quant_research")
    pattern = re.compile(r"risk_dashboard\.quant(?!\.engines|\.modules)")

    violations: list[str] = []
    for file in pkg_root.rglob("*.py"):
        text = file.read_text(encoding="utf-8")
        for idx, line in enumerate(text.splitlines(), start=1):
            if "from risk_dashboard.quant " in line or "import risk_dashboard.quant " in line:
                violations.append(f"{file}:{idx} - {line}")
            elif pattern.search(line) and not line.strip().startswith("#"):
                violations.append(f"{file}:{idx} - {line}")

    assert not violations, f"Found deprecated shim imports:\n" + "\n".join(violations)


def test_zero_quantum_computing_dependencies_and_claims() -> None:
    """Verify zero QC dependencies or claims in quant_research module."""
    pkg_root = Path("src/risk_dashboard/modules/quant_research")
    forbidden_terms = ["qiskit", "cirq", "qubit", "qaoa", "vqe", "quantum advantage"]

    violations: list[str] = []
    for file in pkg_root.rglob("*.py"):
        text = file.read_text(encoding="utf-8")
        for idx, line in enumerate(text.splitlines(), start=1):
            lower_line = line.lower()
            # Allow the reviewer regex definitions themselves
            if "forbidden_quantum_patterns" in lower_line or "pattern.pattern" in lower_line:
                continue
            for term in forbidden_terms:
                if term in lower_line:
                    violations.append(f"{file}:{idx} - contains '{term}': {line.strip()}")

    assert not violations, f"Found forbidden QC terms:\n" + "\n".join(violations)
