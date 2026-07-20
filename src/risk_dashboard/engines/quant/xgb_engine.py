from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

MACRO_VALUE_COLS = [
    "usd_vnd_rate",
    "usd_vnd_1m_change_pct",
    "sbv_interest_rate_pct",
    "cpi_yoy_pct",
    "fdi_disbursement_yoy_pct",
]
MACRO_MISSING_FLAG_COLS = [f"{col}_is_missing" for col in MACRO_VALUE_COLS]


def _dedupe_cols(cols: list[str]) -> list[str]:
    return list(dict.fromkeys(cols))


LEGACY_TECHNICAL_FEATURE_COLS = [
    "volume_1w_trend_pct",
    "ret_5d",
    "ret_10d",
    "ret_20d",
    "realized_vol_10d",
    "realized_vol_20d",
    "drawdown_20d",
    "vol_z",
    "ma_gap_20",
    "ma_gap_50",
    "ma_slope_20",
]
LEGACY_FEATURE_COLS = _dedupe_cols([
    *MACRO_VALUE_COLS,
    *MACRO_MISSING_FLAG_COLS,
    *LEGACY_TECHNICAL_FEATURE_COLS,
])
SHORT_TERM_FEATURE_COLS = [
    "ret_1d",
    "ret_3d",
    "ret_7d",
    "realized_vol_5d",
    "drawdown_10d",
    "vol_z_5",
    "ma_gap_10",
    "ma_slope_10",
    "volume_trend_accel",
]
REGIME_FEATURE_COLS = [
    "realized_vol_10d",
    "realized_vol_20d",
    "downside_vol_10d",
    "vol_regime_5d_20d",
    "ma_spread_10_20",
    "ma_spread_20_50",
]
BREADTH_FEATURE_COLS = [
    "breadth_advancers_pct",
    "breadth_above_ma20_pct",
    "breadth_above_ma50_pct",
    "breadth_mean_ret_5d",
    "breadth_dispersion_1d",
    "breadth_volume_pressure",
]
FEATURE_COLS = _dedupe_cols([
    *LEGACY_FEATURE_COLS,
    *SHORT_TERM_FEATURE_COLS,
    *REGIME_FEATURE_COLS,
])
FULL_PLUS_BREADTH_FEATURE_COLS = _dedupe_cols([*FEATURE_COLS, *BREADTH_FEATURE_COLS])
LEGACY_PLUS_BREADTH_FEATURE_COLS = _dedupe_cols([*LEGACY_FEATURE_COLS, *BREADTH_FEATURE_COLS])
FEATURE_COLS_BY_HORIZON = {
    "1w": list(FEATURE_COLS),
    "2w": list(LEGACY_PLUS_BREADTH_FEATURE_COLS),
    "1m": list(FEATURE_COLS),
}

ROLLING_TEST_RATIO = 0.25
MIN_TRAIN_ROWS = 60
HIGH_RISK_THRESHOLD = 0.60
DECISION_SCORE_WEIGHTS = {"1w": 0.45, "2w": 0.35, "1m": 0.20}


@dataclass(frozen=True)
class HorizonSpec:
    name: str
    days: int
    decline_threshold: float
    label_col: str
    future_return_col: str
    event_mode: str


HORIZON_SPECS = {
    "1w": HorizonSpec(
        name="1w",
        days=5,
        decline_threshold=-0.010,
        label_col="label_decline_1w",
        future_return_col="future_worst_ret_1w",
        event_mode="min_drawdown",
    ),
    "2w": HorizonSpec(
        name="2w",
        days=10,
        decline_threshold=-0.010,
        label_col="label_decline_2w",
        future_return_col="future_ret_2w",
        event_mode="terminal_return",
    ),
    "1m": HorizonSpec(
        name="1m",
        days=21,
        decline_threshold=-0.025,
        label_col="label_decline_1m",
        future_return_col="future_ret_1m",
        event_mode="terminal_return",
    ),
}
HORIZON_ORDER = ["1w", "2w", "1m"]
RISK_BUCKETS = [(0.0, 0.35), (0.35, 0.55), (0.55, 0.75), (0.75, 1.01)]
BASE_ESTIMATOR_PARAMS = {
    "learning_rate": 0.05,
    "max_depth": 4,
    "max_iter": 250,
    "min_samples_leaf": 20,
    "l2_regularization": 0.0,
}
DEFAULT_ESTIMATOR_PARAMS_BY_HORIZON = {
    "1w": {
        "learning_rate": 0.04,
        "max_depth": 5,
        "max_iter": 300,
        "min_samples_leaf": 15,
        "l2_regularization": 0.1,
    },
    "2w": {
        "learning_rate": 0.04,
        "max_depth": 5,
        "max_iter": 300,
        "min_samples_leaf": 15,
        "l2_regularization": 0.1,
    },
    "1m": {
        "learning_rate": 0.04,
        "max_depth": 5,
        "max_iter": 300,
        "min_samples_leaf": 15,
        "l2_regularization": 0.1,
    },
}


def _ensure_numeric_column(df: pd.DataFrame, col: str) -> None:
    if col not in df.columns:
        df[col] = np.nan
    df[col] = pd.to_numeric(df[col], errors="coerce")


def _add_volume_trend_pct(df: pd.DataFrame, *, volume_col: str = "volume", window: int = 5) -> None:
    volume = pd.to_numeric(df[volume_col], errors="coerce")
    recent = volume.rolling(window).mean()
    prev = volume.shift(window).rolling(window).mean()
    computed = ((recent - prev) / prev.abs().replace(0, np.nan) * 100.0).replace(
        [np.inf, -np.inf], np.nan
    )
    if "volume_1w_trend_pct" in df.columns:
        existing = pd.to_numeric(df["volume_1w_trend_pct"], errors="coerce")
        df["volume_1w_trend_pct"] = existing.combine_first(computed)
        return
    df["volume_1w_trend_pct"] = computed


def _prepare_macro_features(df: pd.DataFrame) -> None:
    for col in MACRO_VALUE_COLS:
        _ensure_numeric_column(df, col)
        df[f"{col}_is_missing"] = df[col].isna().astype(float)
        if df[col].notna().any():
            df[col] = df[col].ffill().bfill()
        else:
            df[col] = 0.0


def build_vn30_breadth_features(vn30_panel: pd.DataFrame) -> pd.DataFrame:
    df = vn30_panel.copy()
    df["date"] = pd.to_datetime(df["time"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"]).sort_values(["ticker", "date"]).reset_index(drop=True)
    for col in ("close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    grouped = df.groupby("ticker", group_keys=False)
    df["ret_1d"] = grouped["close"].pct_change()
    df["ret_5d"] = grouped["close"].pct_change(5)
    df["ma20"] = grouped["close"].transform(lambda s: s.rolling(20).mean())
    df["ma50"] = grouped["close"].transform(lambda s: s.rolling(50).mean())
    df["volume_avg_5"] = grouped["volume"].transform(lambda s: s.rolling(5).mean())
    df["above_ma20"] = (df["close"] > df["ma20"]).astype(float)
    df["above_ma50"] = (df["close"] > df["ma50"]).astype(float)
    df["advancer"] = (df["ret_1d"] > 0).astype(float)
    df["volume_pressure"] = df["volume"] / (df["volume_avg_5"] + 1e-9) - 1.0

    breadth = (
        df.groupby("date")
        .agg(
            breadth_advancers_pct=("advancer", "mean"),
            breadth_above_ma20_pct=("above_ma20", "mean"),
            breadth_above_ma50_pct=("above_ma50", "mean"),
            breadth_mean_ret_5d=("ret_5d", "mean"),
            breadth_dispersion_1d=("ret_1d", "std"),
            breadth_volume_pressure=("volume_pressure", "mean"),
        )
        .reset_index()
    )
    breadth["breadth_dispersion_1d"] = breadth["breadth_dispersion_1d"].fillna(0.0)
    return breadth


def _attach_breadth_features(df: pd.DataFrame, vn30_panel: pd.DataFrame | None = None) -> None:
    if vn30_panel is not None:
        breadth = build_vn30_breadth_features(vn30_panel)
        merged = df[["date"]].merge(breadth, on="date", how="left")
        for col in BREADTH_FEATURE_COLS:
            df[col] = pd.to_numeric(merged[col], errors="coerce")
    for col in BREADTH_FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def _future_return(price: pd.Series, days: int, *, mode: str) -> pd.Series:
    if mode == "terminal_return":
        return price.shift(-days) / price - 1.0
    if mode == "min_drawdown":
        window = pd.concat([price.shift(-step) for step in range(1, days + 1)], axis=1)
        future_min = window.min(axis=1)
        return future_min / price - 1.0
    raise ValueError(f"Unknown event mode: {mode}")


def prepare_features(panel: pd.DataFrame, vn30_panel: pd.DataFrame | None = None) -> pd.DataFrame:
    """Thêm đặc trưng và nhãn theo horizon cho toàn bộ panel."""
    df = panel.sort_values("date").reset_index(drop=True).copy()
    _prepare_macro_features(df)
    _add_volume_trend_pct(df)
    _attach_breadth_features(df, vn30_panel)

    price = pd.to_numeric(df["vn_index"], errors="coerce")
    volume = pd.to_numeric(df["volume"], errors="coerce")
    daily_ret = price.pct_change()
    downside_ret = daily_ret.clip(upper=0.0)

    df["ret_1d"] = daily_ret
    df["ret_3d"] = price.pct_change(3)
    df["ret_7d"] = price.pct_change(7)
    df["ret_5d"] = price.pct_change(5)
    df["ret_10d"] = price.pct_change(10)
    df["ret_20d"] = price.pct_change(20)
    df["realized_vol_5d"] = daily_ret.rolling(5).std() * np.sqrt(5)
    df["realized_vol_10d"] = daily_ret.rolling(10).std() * np.sqrt(10)
    df["realized_vol_20d"] = daily_ret.rolling(20).std() * np.sqrt(20)
    df["downside_vol_10d"] = downside_ret.pow(2).rolling(10).mean().pow(0.5) * np.sqrt(10)
    df["vol_regime_5d_20d"] = df["realized_vol_5d"] / (df["realized_vol_20d"] + 1e-9) - 1.0
    df["drawdown_10d"] = price / price.rolling(10).max() - 1.0
    df["drawdown_20d"] = price / price.rolling(20).max() - 1.0
    df["vol_z_5"] = (volume - volume.rolling(5).mean()) / (volume.rolling(5).std() + 1e-9)
    df["vol_z"] = (volume - volume.rolling(20).mean()) / (volume.rolling(20).std() + 1e-9)
    ma10 = price.rolling(10).mean()
    ma20 = price.rolling(20).mean()
    ma50 = price.rolling(50).mean()
    df["ma_gap_10"] = price / ma10 - 1.0
    df["ma_gap_20"] = price / ma20 - 1.0
    df["ma_gap_50"] = price / ma50 - 1.0
    df["ma_spread_10_20"] = ma10 / ma20 - 1.0
    df["ma_spread_20_50"] = ma20 / ma50 - 1.0
    df["ma_slope_10"] = ma10.pct_change(3)
    df["ma_slope_20"] = ma20.pct_change(5)
    df["volume_trend_accel"] = df["volume_1w_trend_pct"] - df["volume_1w_trend_pct"].shift(5)

    for spec in HORIZON_SPECS.values():
        future_ret = _future_return(price, spec.days, mode=spec.event_mode)
        df[spec.future_return_col] = future_ret
        df[spec.label_col] = np.where(
            future_ret.notna(),
            (future_ret < spec.decline_threshold).astype(float),
            np.nan,
        )

    return df


def _build_xy(
    df: pd.DataFrame, spec: HorizonSpec, *, feature_cols: list[str] | None = None
) -> tuple[pd.DataFrame, np.ndarray, pd.Series]:
    cols = feature_cols or FEATURE_COLS
    X = df[cols]
    y = df[spec.label_col]
    future_ret = df[spec.future_return_col]
    mask = X.notna().all(axis=1) & y.notna() & future_ret.notna()
    return X.loc[mask], y.loc[mask].values.astype(int), future_ret.loc[mask].astype(float)


def _resolve_estimator_params(
    horizon: str | None = None, estimator_params: dict[str, Any] | None = None
) -> dict[str, Any]:
    params = dict(BASE_ESTIMATOR_PARAMS)
    if horizon in DEFAULT_ESTIMATOR_PARAMS_BY_HORIZON:
        params.update(DEFAULT_ESTIMATOR_PARAMS_BY_HORIZON[horizon])
    if estimator_params:
        params.update(estimator_params)
    return params


def _build_estimator(
    *, horizon: str | None = None, estimator_params: dict[str, Any] | None = None
) -> HistGradientBoostingClassifier:
    params = _resolve_estimator_params(horizon, estimator_params)
    return HistGradientBoostingClassifier(random_state=42, **params)


def _evaluate_predictions(y_true: np.ndarray, proba: np.ndarray) -> dict[str, float | None]:
    if len(y_true) == 0:
        return {"auc": None, "brier": None, "precision_high_risk": None}
    metrics: dict[str, float | None] = {"auc": None, "brier": float(brier_score_loss(y_true, proba))}
    if len(np.unique(y_true)) > 1:
        metrics["auc"] = float(roc_auc_score(y_true, proba))
    high_risk = proba >= HIGH_RISK_THRESHOLD
    if high_risk.any():
        metrics["precision_high_risk"] = float(y_true[high_risk].mean())
    else:
        metrics["precision_high_risk"] = None
    return metrics


def _fit_probability_calibrator(proba: np.ndarray, y_true: np.ndarray) -> IsotonicRegression | None:
    if len(proba) == 0 or len(np.unique(y_true)) < 2:
        return None
    calibrator = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    calibrator.fit(proba, y_true)
    return calibrator


def _apply_calibrator(calibrator: IsotonicRegression | None, proba: np.ndarray) -> np.ndarray:
    if calibrator is None:
        return np.clip(proba, 0.0, 1.0)
    return np.clip(calibrator.predict(proba), 0.0, 1.0)


def _rolling_backtest_predictions(
    X: pd.DataFrame,
    y: np.ndarray,
    future_returns: pd.Series,
    spec: HorizonSpec,
    *,
    estimator_params: dict[str, Any] | None = None,
    test_ratio: float = ROLLING_TEST_RATIO,
    step_override: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n_obs = len(y)
    split_idx = max(MIN_TRAIN_ROWS, int(n_obs * (1.0 - test_ratio)))
    step = step_override or max(5, spec.days)
    preds: list[float] = []
    truths: list[int] = []
    realized: list[float] = []

    for test_start in range(split_idx, n_obs, step):
        test_end = min(n_obs, test_start + step)
        y_train = y[:test_start]
        if len(np.unique(y_train)) < 2:
            continue
        model = _build_estimator(horizon=spec.name, estimator_params=estimator_params)
        model.fit(X.iloc[:test_start], y_train)
        batch_proba = model.predict_proba(X.iloc[test_start:test_end])[:, 1]
        preds.extend(float(x) for x in batch_proba)
        truths.extend(int(x) for x in y[test_start:test_end])
        realized.extend(float(x) for x in future_returns.iloc[test_start:test_end].values)

    return np.asarray(preds, dtype=float), np.asarray(truths, dtype=int), np.asarray(realized, dtype=float)


def _build_drawdown_buckets(proba: np.ndarray, future_returns: np.ndarray) -> list[tuple[float, float, float]]:
    if len(future_returns) == 0:
        return [(lo, hi, -2.0) for lo, hi in RISK_BUCKETS]

    realized_dd = np.minimum(future_returns, 0.0) * 100.0
    global_dd = float(realized_dd.mean())
    buckets: list[tuple[float, float, float]] = []
    for lo, hi in RISK_BUCKETS:
        mask = (proba >= lo) & (proba < hi)
        bucket_dd = float(realized_dd[mask].mean()) if mask.any() else global_dd
        buckets.append((lo, hi, bucket_dd))
    return buckets


def _lookup_expected_drawdown(drawdown_buckets: list[tuple[float, float, float]], score_2w: float) -> float:
    for lo, hi, dd in drawdown_buckets:
        if lo <= score_2w < hi:
            return dd
    return drawdown_buckets[-1][2]


def build_decision_score(probs: dict[str, float]) -> float:
    score = 0.0
    for horizon, weight in DECISION_SCORE_WEIGHTS.items():
        score += weight * probs[horizon]
    return float(np.clip(score, 0.0, 1.0))


@dataclass
class TrainedRiskModel:
    """Multi-horizon risk engine cho decision support."""

    estimators: dict[str, Any]
    calibrators: dict[str, IsotonicRegression | None]
    version: str
    feature_names: list[str]
    feature_names_by_horizon: dict[str, list[str]]
    estimator_params: dict[str, dict[str, Any]]
    backtest_metrics: dict[str, float | None]
    drawdown_buckets_2w: list[tuple[float, float, float]]


def hist_gradient_boosting_candidates() -> list[dict[str, Any]]:
    return [
        {
            "candidate_name": "baseline",
            "learning_rate": 0.05,
            "max_depth": 4,
            "max_iter": 250,
            "min_samples_leaf": 20,
            "l2_regularization": 0.0,
        },
        {
            "candidate_name": "deeper_regularized",
            "learning_rate": 0.04,
            "max_depth": 5,
            "max_iter": 300,
            "min_samples_leaf": 15,
            "l2_regularization": 0.1,
        },
        {
            "candidate_name": "smoother_longer",
            "learning_rate": 0.03,
            "max_depth": 4,
            "max_iter": 400,
            "min_samples_leaf": 15,
            "l2_regularization": 0.05,
        },
        {
            "candidate_name": "shallower_fast",
            "learning_rate": 0.07,
            "max_depth": 3,
            "max_iter": 180,
            "min_samples_leaf": 20,
            "l2_regularization": 0.0,
        },
        {
            "candidate_name": "leaf_regularized",
            "learning_rate": 0.05,
            "max_depth": None,
            "max_iter": 280,
            "min_samples_leaf": 25,
            "l2_regularization": 0.2,
        },
    ]


def tune_hist_gradient_boosting(
    panel: pd.DataFrame, *, candidate_params: list[dict[str, Any]] | None = None
) -> pd.DataFrame:
    df = prepare_features(panel)
    candidates = candidate_params or hist_gradient_boosting_candidates()
    results: list[dict[str, Any]] = []

    for horizon in HORIZON_ORDER:
        spec = HORIZON_SPECS[horizon]
        X, y, future_ret = _build_xy(df, spec)
        for candidate in candidates:
            candidate_name = str(candidate.get("candidate_name", "candidate"))
            estimator_params = {k: v for k, v in candidate.items() if k != "candidate_name"}
            proba_bt_raw, y_bt, _ = _rolling_backtest_predictions(
                X,
                y,
                future_ret,
                spec,
                estimator_params=estimator_params,
                test_ratio=0.20,
                step_override=max(15, spec.days * 2),
            )
            calibrator = _fit_probability_calibrator(proba_bt_raw, y_bt)
            proba_bt = _apply_calibrator(calibrator, proba_bt_raw)
            metrics = _evaluate_predictions(y_bt, proba_bt)
            results.append(
                {
                    "horizon": horizon,
                    "candidate_name": candidate_name,
                    "rows": int(len(y)),
                    "positive_rate": float(y.mean()),
                    "auc": metrics["auc"],
                    "brier": metrics["brier"],
                    "precision_high_risk": metrics["precision_high_risk"],
                    "estimator_params": json.dumps(estimator_params, sort_keys=True),
                }
            )

    return pd.DataFrame(results).sort_values(
        ["horizon", "auc", "brier"], ascending=[True, False, True], na_position="last"
    ).reset_index(drop=True)


def summarize_best_hgb_candidates(results: pd.DataFrame) -> dict[str, dict[str, Any]]:
    ordered = results.sort_values(["horizon", "auc", "brier"], ascending=[True, False, True])
    best = ordered.groupby("horizon", as_index=False).first()
    return {row["horizon"]: json.loads(row["estimator_params"]) for _, row in best.iterrows()}


def train_risk_model(
    panel: pd.DataFrame,
    *,
    version: str = "skhgb-v4-hybrid",
    vn30_panel: pd.DataFrame | None = None,
    feature_cols_by_horizon: dict[str, list[str]] | None = None,
    estimator_params_by_horizon: dict[str, dict[str, Any]] | None = None,
) -> tuple[TrainedRiskModel, dict[str, float | None]]:
    df = prepare_features(panel, vn30_panel)
    estimators: dict[str, Any] = {}
    calibrators: dict[str, IsotonicRegression | None] = {}
    resolved_feature_names: dict[str, list[str]] = {}
    resolved_params: dict[str, dict[str, Any]] = {}
    metrics: dict[str, float | None] = {}
    drawdown_buckets_2w = [(lo, hi, -2.0) for lo, hi in RISK_BUCKETS]

    for horizon in HORIZON_ORDER:
        spec = HORIZON_SPECS[horizon]
        horizon_feature_cols = list((feature_cols_by_horizon or FEATURE_COLS_BY_HORIZON).get(horizon, FEATURE_COLS))
        resolved_feature_names[horizon] = horizon_feature_cols
        X, y, future_ret = _build_xy(df, spec, feature_cols=horizon_feature_cols)
        if len(y) < MIN_TRAIN_ROWS:
            raise ValueError("Need more rows to train")
        if len(np.unique(y)) < 2:
            raise ValueError(f"Need both classes to train horizon {horizon}")

        horizon_params = (estimator_params_by_horizon or {}).get(horizon)
        resolved_params[horizon] = _resolve_estimator_params(horizon, horizon_params)
        proba_bt_raw, y_bt, future_bt = _rolling_backtest_predictions(
            X,
            y,
            future_ret,
            spec,
            estimator_params=horizon_params,
        )
        calibrator = _fit_probability_calibrator(proba_bt_raw, y_bt)
        proba_bt = _apply_calibrator(calibrator, proba_bt_raw)
        horizon_metrics = _evaluate_predictions(y_bt, proba_bt)
        metrics[f"auc_{horizon}"] = horizon_metrics["auc"]
        metrics[f"brier_{horizon}"] = horizon_metrics["brier"]
        metrics[f"precision_high_risk_{horizon}"] = horizon_metrics["precision_high_risk"]
        calibrators[horizon] = calibrator

        if horizon == "2w":
            metrics["last_auc"] = horizon_metrics["auc"]
            metrics["last_brier"] = horizon_metrics["brier"]
            drawdown_buckets_2w = _build_drawdown_buckets(proba_bt, future_bt)

        model = _build_estimator(horizon=horizon, estimator_params=horizon_params)
        model.fit(X, y)
        estimators[horizon] = model

    trained = TrainedRiskModel(
        estimators=estimators,
        calibrators=calibrators,
        version=version,
        feature_names=list(FEATURE_COLS),
        feature_names_by_horizon=resolved_feature_names,
        estimator_params=resolved_params,
        backtest_metrics=metrics,
        drawdown_buckets_2w=drawdown_buckets_2w,
    )
    return trained, metrics


def row_at_date(df: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    sub = df[df["date"] == as_of]
    if sub.empty:
        sub = df[df["date"] <= as_of].tail(1)
    if sub.empty:
        raise ValueError("no rows for as_of")
    return sub.iloc[-1]


def predict_horizons(model: TrainedRiskModel, row: pd.Series) -> tuple[float, float, float, float, float]:
    probs: dict[str, float] = {}
    for horizon in HORIZON_ORDER:
        feature_names = model.feature_names_by_horizon.get(horizon, model.feature_names)
        X = row[feature_names].astype(float).to_frame().T
        raw_proba = np.asarray([float(model.estimators[horizon].predict_proba(X)[0, 1])], dtype=float)
        probs[horizon] = float(_apply_calibrator(model.calibrators.get(horizon), raw_proba)[0])
    decision_score = build_decision_score(probs)
    expected_dd = _lookup_expected_drawdown(model.drawdown_buckets_2w, probs["2w"])
    return probs["1w"], probs["2w"], probs["1m"], expected_dd, decision_score


def risk_regime_from_score(score: float) -> str:
    if score < 0.35:
        return "low"
    if score < 0.55:
        return "neutral"
    if score < 0.75:
        return "high"
    return "very_high"
