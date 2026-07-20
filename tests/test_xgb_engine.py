import numpy as np
import pandas as pd

from risk_dashboard.engines.quant.xgb_engine import (
    BREADTH_FEATURE_COLS,
    FEATURE_COLS,
    FEATURE_COLS_BY_HORIZON,
    HORIZON_SPECS,
    build_decision_score,
    summarize_best_hgb_candidates,
    tune_hist_gradient_boosting,
    prepare_features,
    train_risk_model,
)


def test_prepare_features_creates_labels(synthetic_panel):
    df = prepare_features(synthetic_panel)
    assert "label_decline_1w" in df.columns
    assert "label_decline_2w" in df.columns
    assert "label_decline_1m" in df.columns
    assert "volume_1w_trend_pct" in df.columns
    assert "cpi_yoy_pct_is_missing" in df.columns
    assert df["ret_5d"].notna().sum() > 0
    assert df["ma_gap_50"].notna().sum() > 0
    assert df["ret_3d"].notna().sum() > 0
    assert df["realized_vol_5d"].notna().sum() > 0
    assert df["vol_regime_5d_20d"].notna().sum() > 0
    assert df["drawdown_10d"].notna().sum() > 0
    assert df["ma_spread_10_20"].notna().sum() > 0
    for col in BREADTH_FEATURE_COLS:
        assert col in df.columns
        assert df[col].eq(0.0).all()
    for spec in HORIZON_SPECS.values():
        assert df[spec.label_col].notna().sum() > 0


def test_train_risk_model_returns_metrics(synthetic_panel):
    model, metrics = train_risk_model(synthetic_panel)
    assert set(model.estimators) == {"1w", "2w", "1m"}
    assert set(model.calibrators) == {"1w", "2w", "1m"}
    assert "volume_1w_trend_pct" in model.feature_names
    assert "ret_3d" in model.feature_names
    assert "ma_gap_10" in model.feature_names
    assert set(model.feature_names_by_horizon) == {"1w", "2w", "1m"}
    assert model.feature_names_by_horizon["1w"] == FEATURE_COLS
    assert model.feature_names_by_horizon["2w"] == FEATURE_COLS_BY_HORIZON["2w"]
    assert model.feature_names_by_horizon["1m"] == FEATURE_COLS
    assert set(model.estimator_params) == {"1w", "2w", "1m"}
    assert isinstance(metrics, dict)
    assert "auc_2w" in metrics
    assert "precision_high_risk_1m" in metrics


def test_decision_score_weights_short_horizons_more():
    score = build_decision_score({"1w": 0.9, "2w": 0.5, "1m": 0.1})
    assert 0.0 <= score <= 1.0
    assert score > 0.5


def test_prepare_features_keeps_missing_macro_information(synthetic_panel):
    panel = synthetic_panel.copy()
    panel.loc[10:20, "usd_vnd_rate"] = None
    panel.loc[:, "cpi_yoy_pct"] = None
    panel.loc[0:5, "volume_1w_trend_pct"] = None

    df = prepare_features(panel)

    assert "usd_vnd_rate_is_missing" in FEATURE_COLS
    assert "cpi_yoy_pct_is_missing" in FEATURE_COLS
    assert df["usd_vnd_rate_is_missing"].sum() > 0
    assert df["cpi_yoy_pct_is_missing"].eq(1.0).all()
    assert df["usd_vnd_rate"].notna().all()
    assert df["cpi_yoy_pct"].notna().all()


def test_short_horizon_labels_capture_worst_drawdown_not_only_terminal_return():
    dates = pd.date_range("2024-01-01", periods=80, freq="B")
    price = np.full(len(dates), 100.0)
    price[25] = 100.0
    price[26] = 94.0
    price[27] = 96.0
    price[28] = 101.0
    price[29] = 103.0
    price[30] = 104.0
    panel = pd.DataFrame(
        {
            "date": dates,
            "vn_index": price,
            "volume": np.linspace(1_000_000, 1_100_000, len(dates)),
            "usd_vnd_rate": np.linspace(24_000, 24_100, len(dates)),
            "usd_vnd_1m_change_pct": np.linspace(0.1, 0.2, len(dates)),
            "sbv_interest_rate_pct": np.full(len(dates), 4.5),
            "cpi_yoy_pct": np.full(len(dates), 3.5),
        }
    )
    df = prepare_features(panel)
    row = df.iloc[25]
    assert row["future_worst_ret_1w"] < -0.01
    assert row["label_decline_1w"] == 1.0


def test_2w_horizon_uses_terminal_return_configuration():
    spec = HORIZON_SPECS["2w"]
    assert spec.event_mode == "terminal_return"
    assert spec.decline_threshold == -0.010
    assert spec.future_return_col == "future_ret_2w"


def test_tune_hist_gradient_boosting_returns_best_config_per_horizon(synthetic_panel):
    candidates = [
        {
            "candidate_name": "fast",
            "learning_rate": 0.08,
            "max_depth": 3,
            "max_iter": 120,
            "min_samples_leaf": 20,
            "l2_regularization": 0.0,
        },
        {
            "candidate_name": "steady",
            "learning_rate": 0.04,
            "max_depth": 4,
            "max_iter": 180,
            "min_samples_leaf": 15,
            "l2_regularization": 0.05,
        },
    ]
    results = tune_hist_gradient_boosting(synthetic_panel, candidate_params=candidates)
    assert set(results["horizon"]) == {"1w", "2w", "1m"}
    assert set(results["candidate_name"]) == {"fast", "steady"}
    best = summarize_best_hgb_candidates(results)
    assert set(best) == {"1w", "2w", "1m"}
    assert all("learning_rate" in params for params in best.values())
