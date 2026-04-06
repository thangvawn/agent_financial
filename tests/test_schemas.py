from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from risk_dashboard.schemas.snapshots import (
    HorizonBacktestMetrics,
    QuantProvenance,
    QuantEngineOutput,
    ShapContribution,
    TargetHorizons,
    VarSummary,
)


def test_quant_output_shap_must_sum():
    with pytest.raises(ValidationError):
        QuantEngineOutput(
            run_id="r1",
            as_of=datetime(2026, 1, 1, tzinfo=timezone.utc),
            model_version="t",
            decision_score=0.55,
            risk_score_2w=0.5,
            risk_regime="neutral",
            horizons=TargetHorizons(
                p_decline_1w=0.4,
                p_decline_2w=0.5,
                p_decline_1m=0.45,
                expected_drawdown_pct=-3.0,
            ),
            shap_top=[
                ShapContribution(feature_name="a", share=0.4, direction="increases_risk"),
                ShapContribution(feature_name="b", share=0.3, direction="decreases_risk"),
            ],
            var_summary=VarSummary(fitted=True, n_obs=100, max_lag=2, note=""),
            backtest={"metrics_by_horizon": {"2w": HorizonBacktestMetrics(auc=0.6, brier=0.2)}},
            dominant_feature="a",
            narrative_inputs={},
            provenance=QuantProvenance(panel_rows=100),
        )
