from types import SimpleNamespace

from risk_dashboard.engines.quant.eod_pipeline import run_quant_eod
from risk_dashboard.engines.quant.scenario import rerun_with_macro_override
from risk_dashboard.schemas.snapshots import ShapContribution, VarSummary


def test_eod_pipeline_roundtrip(synthetic_panel, as_of_date):
    q = run_quant_eod(synthetic_panel, as_of_date, run_id="test-run")
    assert q.run_id == "test-run"
    assert 0 <= q.decision_score <= 1
    assert 0 <= q.horizons.p_decline_1w <= 1
    assert 0 <= q.horizons.p_decline_2w <= 1
    assert 0 <= q.horizons.p_decline_1m <= 1
    assert -100 <= q.horizons.expected_drawdown_pct <= 0
    assert set(q.backtest.metrics_by_horizon) == {"1w", "2w", "1m"}
    assert q.shap_top
    assert abs(sum(s.share for s in q.shap_top) - 1.0) < 0.06
    assert q.provenance.panel_rows > 0
    assert "2w" in q.provenance.train_feature_count_by_horizon


def test_scenario_changes_score(synthetic_panel, as_of_date):
    q0 = run_quant_eod(synthetic_panel, as_of_date, run_id="a")
    q1 = rerun_with_macro_override(synthetic_panel, as_of_date, usd_vnd_rate=5000.0)
    assert q0.decision_score != q1.decision_score or q0.horizons.p_decline_2w != q1.horizons.p_decline_2w


def test_eod_pipeline_uses_benchmark_training_config(monkeypatch, synthetic_panel, as_of_date):
    captured: dict[str, object] = {}

    def fake_resolve(_benchmark_dir):
        return SimpleNamespace(
            feature_cols_by_horizon={"1w": ["usd_vnd_rate"], "2w": ["ret_5d"], "1m": ["ma_gap_20"]},
            estimator_params_by_horizon={"1w": {"max_iter": 111}, "2w": {"max_iter": 222}, "1m": {"max_iter": 333}},
        )

    def fake_train(df, **kwargs):
        captured["rows"] = len(df)
        captured["feature_cols_by_horizon"] = kwargs.get("feature_cols_by_horizon")
        captured["estimator_params_by_horizon"] = kwargs.get("estimator_params_by_horizon")
        return (
            SimpleNamespace(
                estimators={"2w": object()},
                feature_names_by_horizon={"2w": ["ret_5d"]},
                version=kwargs["version"],
            ),
            {
                "last_auc": 0.7,
                "last_brier": 0.2,
                "auc_1w": 0.6,
                "brier_1w": 0.2,
                "precision_high_risk_1w": None,
                "auc_2w": 0.7,
                "brier_2w": 0.2,
                "precision_high_risk_2w": None,
                "auc_1m": 0.8,
                "brier_1m": 0.1,
                "precision_high_risk_1m": None,
            },
        )

    monkeypatch.setattr("risk_dashboard.engines.quant.eod_pipeline.resolve_benchmark_training_config", fake_resolve)
    monkeypatch.setattr("risk_dashboard.engines.quant.eod_pipeline.train_risk_model", fake_train)
    monkeypatch.setattr("risk_dashboard.engines.quant.eod_pipeline.prepare_features", lambda df, vn30_panel=None: df)
    monkeypatch.setattr("risk_dashboard.engines.quant.eod_pipeline.row_at_date", lambda df, as_of: df.iloc[-1])
    monkeypatch.setattr(
        "risk_dashboard.engines.quant.eod_pipeline.predict_horizons",
        lambda model, row: (0.1, 0.2, 0.3, -1.5, 0.19),
    )
    monkeypatch.setattr(
        "risk_dashboard.engines.quant.eod_pipeline.contributions_from_tree_model",
        lambda model, row, features: [
            ShapContribution(feature_name="ret_5d", share=1.0, direction="increases_risk"),
        ],
    )
    monkeypatch.setattr(
        "risk_dashboard.engines.quant.eod_pipeline.fit_var_summary",
        lambda panel: VarSummary(fitted=False, n_obs=len(panel), max_lag=1, note="n/a"),
    )
    monkeypatch.setattr("risk_dashboard.engines.quant.eod_pipeline.var_impulse_note", lambda panel: "n/a")

    q = run_quant_eod(synthetic_panel, as_of_date, benchmark_dir="custom/models")

    assert q.model_version == "skhgb-v4-hybrid"
    assert captured["rows"] > 0
    assert captured["feature_cols_by_horizon"] == {"1w": ["usd_vnd_rate"], "2w": ["ret_5d"], "1m": ["ma_gap_20"]}
    assert captured["estimator_params_by_horizon"] == {
        "1w": {"max_iter": 111},
        "2w": {"max_iter": 222},
        "1m": {"max_iter": 333},
    }
    assert q.provenance.benchmark_dir == "custom/models"
    assert q.provenance.train_feature_count_by_horizon["2w"] == 1
