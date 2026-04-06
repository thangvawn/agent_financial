import json

import numpy as np
import pandas as pd

from risk_dashboard.quant.model_benchmark import (
    build_vn30_breadth_features,
    default_model_factories,
    default_feature_variants,
    load_best_feature_variants,
    load_best_hgb_estimator_params,
    resolve_benchmark_training_config,
    run_feature_variant_benchmark,
    run_model_benchmark,
    save_feature_benchmark_results,
    save_benchmark_results,
    summarize_best_feature_variants,
    summarize_best_models,
)


def test_run_model_benchmark_returns_results_for_each_horizon(synthetic_panel):
    factories = {
        "gradient_boosting": __import__("sklearn.ensemble").ensemble.GradientBoostingClassifier,
        "logistic_regression": lambda: __import__("sklearn.pipeline").pipeline.Pipeline(
            [
                ("scaler", __import__("sklearn.preprocessing").preprocessing.StandardScaler()),
                (
                    "clf",
                    __import__("sklearn.linear_model").linear_model.LogisticRegression(
                        max_iter=200, class_weight="balanced"
                    ),
                ),
            ]
        ),
    }
    results = run_model_benchmark(synthetic_panel, model_factories=factories)
    assert not results.empty
    assert set(results["horizon"]) == {"1w", "2w", "1m"}
    assert set(results["model_name"]) == {"gradient_boosting", "logistic_regression"}


def test_summarize_best_models_returns_one_row_per_horizon():
    frame = pd.DataFrame(
        [
            {"horizon": "1w", "model_name": "a", "auc": 0.51, "brier": 0.2},
            {"horizon": "1w", "model_name": "b", "auc": 0.61, "brier": 0.21},
            {"horizon": "2w", "model_name": "c", "auc": 0.55, "brier": 0.19},
        ]
    )
    best = summarize_best_models(frame)
    assert list(best["horizon"]) == ["1w", "2w"]
    assert list(best["model_name"]) == ["b", "c"]


def test_default_model_factories_include_dummy_baselines():
    factories = default_model_factories()
    assert "dummy_prior" in factories
    assert "dummy_stratified" in factories
    assert "hist_gradient_boosting_tuned" in factories


def test_save_benchmark_results_serializes_missing_as_null(tmp_path):
    results = pd.DataFrame([{"horizon": "1w", "model_name": "dummy_prior", "auc": 0.5, "brier": 0.2, "precision_high_risk": None}])
    paths = save_benchmark_results(results, tmp_path)
    payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    assert payload["results"][0]["precision_high_risk"] is None


def test_build_vn30_breadth_features_returns_daily_aggregates():
    dates = pd.date_range("2024-01-01", periods=80, freq="B")
    frames = []
    for ticker, scale in [("AAA", 1.0), ("BBB", 1.2), ("CCC", 0.8)]:
        close = np.linspace(10 * scale, 15 * scale, len(dates))
        frames.append(
            pd.DataFrame(
                {
                    "time": dates,
                    "open": close,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": np.linspace(1_000_000, 1_500_000, len(dates)),
                    "ticker": ticker,
                }
            )
        )
    breadth = build_vn30_breadth_features(pd.concat(frames, ignore_index=True))
    assert "date" in breadth.columns
    assert "breadth_advancers_pct" in breadth.columns
    assert "breadth_above_ma20_pct" in breadth.columns
    assert len(breadth) == len(dates)


def test_run_feature_variant_benchmark_returns_variants(synthetic_panel):
    variants = default_feature_variants(include_breadth=False)
    results = run_feature_variant_benchmark(synthetic_panel, feature_variants=variants)
    assert not results.empty
    assert set(results["horizon"]) == {"1w", "2w", "1m"}
    assert {"legacy_baseline", "current_stack", "current_no_macro"} <= set(results["variant_name"])


def test_save_feature_benchmark_results_serializes_output(tmp_path):
    results = pd.DataFrame(
        [
            {
                "horizon": "1w",
                "variant_name": "legacy_baseline",
                "n_features": 10,
                "auc": 0.6,
                "brier": 0.2,
                "precision_high_risk": None,
            }
        ]
    )
    paths = save_feature_benchmark_results(results, tmp_path)
    payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    assert payload["results"][0]["precision_high_risk"] is None
    best = summarize_best_feature_variants(results)
    assert list(best["variant_name"]) == ["legacy_baseline"]


def test_load_best_feature_variants_uses_latest_payload(tmp_path):
    older = {
        "best_variants": [
            {"horizon": "1w", "variant_name": "legacy_baseline"},
        ]
    }
    latest = {
        "best_variants": [
            {"horizon": "1w", "variant_name": "current_stack"},
            {"horizon": "2w", "variant_name": "legacy_plus_breadth"},
        ]
    }
    (tmp_path / "feature_benchmark_20260330T010000Z.json").write_text(json.dumps(older), encoding="utf-8")
    (tmp_path / "feature_benchmark_20260330T020000Z.json").write_text(json.dumps(latest), encoding="utf-8")

    loaded = load_best_feature_variants(tmp_path)

    assert loaded is not None
    variants, source = loaded
    assert source.endswith("feature_benchmark_20260330T020000Z.json")
    assert variants["1w"] == default_feature_variants(include_breadth=True)["current_stack"]
    assert variants["2w"] == default_feature_variants(include_breadth=True)["legacy_plus_breadth"]


def test_load_best_hgb_estimator_params_skips_unsupported_best_model(tmp_path):
    payload = {
        "results": [
            {"horizon": "1w", "model_name": "xgboost", "auc": 0.91, "brier": 0.18},
            {"horizon": "1w", "model_name": "hist_gradient_boosting_tuned", "auc": 0.82, "brier": 0.19},
            {"horizon": "2w", "model_name": "gradient_boosting", "auc": 0.88, "brier": 0.17},
            {"horizon": "2w", "model_name": "hist_gradient_boosting", "auc": 0.81, "brier": 0.18},
        ]
    }
    (tmp_path / "model_benchmark_20260330T020000Z.json").write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_best_hgb_estimator_params(tmp_path)

    assert loaded is not None
    params, source = loaded
    assert source.endswith("model_benchmark_20260330T020000Z.json")
    assert params["1w"]["max_iter"] == 300
    assert params["2w"]["max_iter"] == 250


def test_resolve_benchmark_training_config_combines_model_and_feature_sources(tmp_path):
    feature_payload = {
        "best_variants": [
            {"horizon": "1m", "variant_name": "current_no_macro"},
        ]
    }
    model_payload = {
        "results": [
            {"horizon": "1m", "model_name": "hist_gradient_boosting_tuned", "auc": 0.7, "brier": 0.12},
        ]
    }
    (tmp_path / "feature_benchmark_20260330T020000Z.json").write_text(json.dumps(feature_payload), encoding="utf-8")
    (tmp_path / "model_benchmark_20260330T020000Z.json").write_text(json.dumps(model_payload), encoding="utf-8")

    config = resolve_benchmark_training_config(tmp_path)

    assert config is not None
    assert config.feature_cols_by_horizon["1m"] == default_feature_variants(include_breadth=True)["current_no_macro"]
    assert config.estimator_params_by_horizon["1m"]["max_iter"] == 300
    assert set(config.sources) == {"feature_benchmark", "model_benchmark"}
