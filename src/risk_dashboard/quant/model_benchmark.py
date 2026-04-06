from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from risk_dashboard.quant.xgb_engine import (
    BREADTH_FEATURE_COLS,
    FEATURE_COLS,
    FULL_PLUS_BREADTH_FEATURE_COLS,
    HORIZON_ORDER,
    HORIZON_SPECS,
    LEGACY_PLUS_BREADTH_FEATURE_COLS,
    LEGACY_FEATURE_COLS,
    MACRO_MISSING_FLAG_COLS,
    MACRO_VALUE_COLS,
    MIN_TRAIN_ROWS,
    _apply_calibrator,
    _build_xy,
    _evaluate_predictions,
    _fit_probability_calibrator,
    build_vn30_breadth_features,
    prepare_features,
)

EstimatorFactory = Callable[[], object]


@dataclass(frozen=True)
class BenchmarkArtifactPaths:
    csv_path: Path
    json_path: Path


@dataclass(frozen=True)
class BenchmarkTrainingConfig:
    feature_cols_by_horizon: dict[str, list[str]]
    estimator_params_by_horizon: dict[str, dict[str, object]]
    sources: dict[str, str]


def prepare_feature_benchmark_frame(
    panel: pd.DataFrame, *, vn30_panel: pd.DataFrame | None = None
) -> pd.DataFrame:
    return prepare_features(panel, vn30_panel)


def default_feature_variants(*, include_breadth: bool = False) -> dict[str, list[str]]:
    variants = {
        "legacy_baseline": list(LEGACY_FEATURE_COLS),
        "current_stack": list(FEATURE_COLS),
        "current_no_macro": [col for col in FEATURE_COLS if col not in {*MACRO_VALUE_COLS, *MACRO_MISSING_FLAG_COLS}],
    }
    if include_breadth:
        variants["legacy_plus_breadth"] = list(LEGACY_PLUS_BREADTH_FEATURE_COLS)
        variants["full_plus_breadth"] = list(FULL_PLUS_BREADTH_FEATURE_COLS)
    return variants


def default_model_factories() -> dict[str, EstimatorFactory]:
    factories: dict[str, EstimatorFactory] = {
        "dummy_prior": lambda: DummyClassifier(strategy="prior"),
        "dummy_stratified": lambda: DummyClassifier(strategy="stratified", random_state=42),
        "gradient_boosting": lambda: GradientBoostingClassifier(
            n_estimators=120,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            random_state=42,
        ),
        "hist_gradient_boosting": lambda: HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_depth=4,
            max_iter=250,
            min_samples_leaf=20,
            random_state=42,
        ),
        "hist_gradient_boosting_tuned": lambda: HistGradientBoostingClassifier(
            learning_rate=0.04,
            max_depth=5,
            max_iter=300,
            min_samples_leaf=15,
            l2_regularization=0.1,
            random_state=42,
        ),
        "random_forest": lambda: RandomForestClassifier(
            n_estimators=160,
            max_depth=6,
            min_samples_leaf=10,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        ),
        "extra_trees": lambda: ExtraTreesClassifier(
            n_estimators=160,
            max_depth=6,
            min_samples_leaf=10,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        ),
        "logistic_regression": lambda: Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        solver="lbfgs",
                        random_state=42,
                    ),
                ),
            ]
        ),
    }
    try:
        from xgboost import XGBClassifier  # type: ignore

        factories["xgboost"] = lambda: XGBClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
            n_jobs=1,
        )
    except Exception:
        pass
    return factories


def _rolling_predictions_for_model(
    X: pd.DataFrame,
    y: pd.Series,
    estimator_factory: EstimatorFactory,
    *,
    test_ratio: float = 0.25,
    step: int,
) -> tuple[pd.Series, pd.Series]:
    n_obs = len(y)
    split_idx = max(MIN_TRAIN_ROWS, int(n_obs * (1.0 - test_ratio)))
    pred_parts: list[pd.Series] = []
    truth_parts: list[pd.Series] = []

    for test_start in range(split_idx, n_obs, step):
        test_end = min(n_obs, test_start + step)
        y_train = y.iloc[:test_start]
        if y_train.nunique() < 2:
            continue
        model = estimator_factory()
        model.fit(X.iloc[:test_start], y_train)
        batch_idx = X.iloc[test_start:test_end].index
        batch_proba = model.predict_proba(X.iloc[test_start:test_end])[:, 1]
        pred_parts.append(pd.Series(batch_proba, index=batch_idx))
        truth_parts.append(y.iloc[test_start:test_end])

    if not pred_parts:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    preds = pd.concat(pred_parts).sort_index()
    truths = pd.concat(truth_parts).sort_index()
    return preds, truths


def run_model_benchmark(
    panel: pd.DataFrame,
    *,
    model_factories: dict[str, EstimatorFactory] | None = None,
) -> pd.DataFrame:
    factories = model_factories or default_model_factories()
    feat_df = prepare_features(panel)
    results: list[dict[str, object]] = []

    for horizon in HORIZON_ORDER:
        spec = HORIZON_SPECS[horizon]
        X, y_np, future_ret = _build_xy(feat_df, spec)
        y = pd.Series(y_np, index=X.index)
        step = max(5, spec.days)

        for model_name, factory in factories.items():
            preds_raw, truths = _rolling_predictions_for_model(X, y, factory, step=step)
            if preds_raw.empty or truths.empty or truths.nunique() < 2:
                results.append(
                    {
                        "horizon": horizon,
                        "model_name": model_name,
                        "rows": int(len(y)),
                        "positive_rate": float(y.mean()) if len(y) else None,
                        "auc": None,
                        "brier": None,
                        "precision_high_risk": None,
                        "calibration": "none",
                    }
                )
                continue

            calibrator = _fit_probability_calibrator(preds_raw.values, truths.values.astype(int))
            preds = _apply_calibrator(calibrator, preds_raw.values)
            metrics = _evaluate_predictions(truths.values.astype(int), preds)
            results.append(
                {
                    "horizon": horizon,
                    "model_name": model_name,
                    "rows": int(len(y)),
                    "positive_rate": float(y.mean()),
                    "auc": metrics["auc"],
                    "brier": metrics["brier"],
                    "precision_high_risk": metrics["precision_high_risk"],
                    "calibration": "isotonic" if calibrator is not None else "none",
                }
            )

    return pd.DataFrame(results).sort_values(
        ["horizon", "auc", "brier"], ascending=[True, False, True], na_position="last"
    ).reset_index(drop=True)


def run_feature_variant_benchmark(
    panel: pd.DataFrame,
    *,
    vn30_panel: pd.DataFrame | None = None,
    feature_variants: dict[str, list[str]] | None = None,
    estimator_factory: EstimatorFactory | None = None,
) -> pd.DataFrame:
    feat_df = prepare_feature_benchmark_frame(panel, vn30_panel=vn30_panel)
    variants = feature_variants or default_feature_variants(include_breadth=vn30_panel is not None)
    factory = estimator_factory or default_model_factories()["hist_gradient_boosting_tuned"]
    results: list[dict[str, object]] = []

    for horizon in HORIZON_ORDER:
        spec = HORIZON_SPECS[horizon]
        step = max(5, spec.days)
        for variant_name, feature_cols in variants.items():
            X, y_np, _future_ret = _build_xy(feat_df, spec, feature_cols=feature_cols)
            y = pd.Series(y_np, index=X.index)
            preds_raw, truths = _rolling_predictions_for_model(X, y, factory, step=step)
            if preds_raw.empty or truths.empty or truths.nunique() < 2:
                results.append(
                    {
                        "horizon": horizon,
                        "variant_name": variant_name,
                        "n_features": len(feature_cols),
                        "rows": int(len(y)),
                        "positive_rate": float(y.mean()) if len(y) else None,
                        "auc": None,
                        "brier": None,
                        "precision_high_risk": None,
                        "calibration": "none",
                    }
                )
                continue

            calibrator = _fit_probability_calibrator(preds_raw.values, truths.values.astype(int))
            preds = _apply_calibrator(calibrator, preds_raw.values)
            metrics = _evaluate_predictions(truths.values.astype(int), preds)
            results.append(
                {
                    "horizon": horizon,
                    "variant_name": variant_name,
                    "n_features": len(feature_cols),
                    "rows": int(len(y)),
                    "positive_rate": float(y.mean()),
                    "auc": metrics["auc"],
                    "brier": metrics["brier"],
                    "precision_high_risk": metrics["precision_high_risk"],
                    "calibration": "isotonic" if calibrator is not None else "none",
                }
            )

    return pd.DataFrame(results).sort_values(
        ["horizon", "auc", "brier"], ascending=[True, False, True], na_position="last"
    ).reset_index(drop=True)


def summarize_best_models(results: pd.DataFrame) -> pd.DataFrame:
    ordered = results.sort_values(["horizon", "auc", "brier"], ascending=[True, False, True])
    return ordered.groupby("horizon", as_index=False).first()


def summarize_best_feature_variants(results: pd.DataFrame) -> pd.DataFrame:
    ordered = results.sort_values(["horizon", "auc", "brier"], ascending=[True, False, True])
    return ordered.groupby("horizon", as_index=False).first()


def _read_latest_benchmark_payload(output_dir: str | Path, pattern: str) -> tuple[Path, dict[str, object]] | None:
    out_dir = Path(output_dir)
    candidates = sorted(out_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return path, payload
    return None


def resolve_feature_columns_from_variant_name(variant_name: str) -> list[str]:
    variants = default_feature_variants(include_breadth=True)
    if variant_name not in variants:
        raise KeyError(f"Unknown feature variant: {variant_name}")
    return list(variants[variant_name])


def _supported_hgb_params_for_model_name(model_name: str) -> dict[str, object] | None:
    if model_name == "hist_gradient_boosting":
        return {
            "learning_rate": 0.05,
            "max_depth": 4,
            "max_iter": 250,
            "min_samples_leaf": 20,
            "l2_regularization": 0.0,
        }
    if model_name == "hist_gradient_boosting_tuned":
        return {
            "learning_rate": 0.04,
            "max_depth": 5,
            "max_iter": 300,
            "min_samples_leaf": 15,
            "l2_regularization": 0.1,
        }
    return None


def load_best_feature_variants(output_dir: str | Path) -> tuple[dict[str, list[str]], str] | None:
    loaded = _read_latest_benchmark_payload(output_dir, "feature_benchmark_*.json")
    if loaded is None:
        return None
    path, payload = loaded
    best_variants = payload.get("best_variants")
    if not isinstance(best_variants, list):
        return None

    resolved: dict[str, list[str]] = {}
    for row in best_variants:
        if not isinstance(row, dict):
            continue
        horizon = row.get("horizon")
        variant_name = row.get("variant_name")
        if not isinstance(horizon, str) or not isinstance(variant_name, str):
            continue
        try:
            resolved[horizon] = resolve_feature_columns_from_variant_name(variant_name)
        except KeyError:
            continue
    if not resolved:
        return None
    return resolved, str(path)


def load_best_hgb_estimator_params(output_dir: str | Path) -> tuple[dict[str, dict[str, object]], str] | None:
    loaded = _read_latest_benchmark_payload(output_dir, "model_benchmark_*.json")
    if loaded is None:
        return None
    path, payload = loaded
    rows = payload.get("results")
    if not isinstance(rows, list):
        return None

    best_supported: dict[str, tuple[float, float, dict[str, object]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        horizon = row.get("horizon")
        model_name = row.get("model_name")
        auc = row.get("auc")
        brier = row.get("brier")
        if not isinstance(horizon, str) or not isinstance(model_name, str):
            continue
        params = _supported_hgb_params_for_model_name(model_name)
        if params is None:
            continue
        auc_val = float(auc) if isinstance(auc, (int, float)) else float("-inf")
        brier_val = float(brier) if isinstance(brier, (int, float)) else float("inf")
        current = best_supported.get(horizon)
        if current is None or auc_val > current[0] or (auc_val == current[0] and brier_val < current[1]):
            best_supported[horizon] = (auc_val, brier_val, params)

    if not best_supported:
        return None
    return {horizon: params for horizon, (_auc, _brier, params) in best_supported.items()}, str(path)


def resolve_benchmark_training_config(output_dir: str | Path) -> BenchmarkTrainingConfig | None:
    feature_loaded = load_best_feature_variants(output_dir)
    params_loaded = load_best_hgb_estimator_params(output_dir)
    if feature_loaded is None and params_loaded is None:
        return None

    feature_cols_by_horizon = feature_loaded[0] if feature_loaded is not None else {}
    estimator_params_by_horizon = params_loaded[0] if params_loaded is not None else {}
    sources: dict[str, str] = {}
    if feature_loaded is not None:
        sources["feature_benchmark"] = feature_loaded[1]
    if params_loaded is not None:
        sources["model_benchmark"] = params_loaded[1]
    return BenchmarkTrainingConfig(
        feature_cols_by_horizon=feature_cols_by_horizon,
        estimator_params_by_horizon=estimator_params_by_horizon,
        sources=sources,
    )


def save_benchmark_results(results: pd.DataFrame, output_dir: str | Path) -> BenchmarkArtifactPaths:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = out_dir / f"model_benchmark_{ts}.csv"
    json_path = out_dir / f"model_benchmark_{ts}.json"
    results.to_csv(csv_path, index=False)
    serializable = results.astype(object).where(pd.notna(results), None)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "best_models": summarize_best_models(serializable).to_dict(orient="records"),
        "results": serializable.to_dict(orient="records"),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return BenchmarkArtifactPaths(csv_path=csv_path, json_path=json_path)


def save_feature_benchmark_results(results: pd.DataFrame, output_dir: str | Path) -> BenchmarkArtifactPaths:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = out_dir / f"feature_benchmark_{ts}.csv"
    json_path = out_dir / f"feature_benchmark_{ts}.json"
    results.to_csv(csv_path, index=False)
    serializable = results.astype(object).where(pd.notna(results), None)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "best_variants": summarize_best_feature_variants(serializable).to_dict(orient="records"),
        "results": serializable.to_dict(orient="records"),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return BenchmarkArtifactPaths(csv_path=csv_path, json_path=json_path)
