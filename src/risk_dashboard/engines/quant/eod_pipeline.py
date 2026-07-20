from __future__ import annotations

import logging
import pickle
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from risk_dashboard.engines.quant.model_benchmark import resolve_benchmark_training_config
from risk_dashboard.engines.quant.shap_explain import contributions_from_tree_model
from risk_dashboard.engines.quant.var_engine import fit_var_summary, var_impulse_note
from risk_dashboard.engines.quant.xgb_engine import (
    TrainedRiskModel,
    prepare_features,
    predict_horizons,
    risk_regime_from_score,
    row_at_date,
    train_risk_model,
)
from risk_dashboard.schemas.snapshots import (
    BacktestSummary,
    HorizonBacktestMetrics,
    QuantEngineOutput,
    QuantProvenance,
    TargetHorizons,
    VarSummary,
)

logger = logging.getLogger(__name__)

_LOADED_MODEL: tuple[TrainedRiskModel, dict] | None = None
_DEFAULT_MODEL_PATH = Path("data/models/latest_model.pkl")


def _get_cached_trained_model(
    panel: pd.DataFrame,
    as_of: date,
    version: str,
    vn30_panel: pd.DataFrame | None,
    feature_cols_by_horizon: dict | None,
    estimator_params_by_horizon: dict | None,
    *,
    use_model_cache: bool = True,
) -> tuple[TrainedRiskModel, dict]:
    global _LOADED_MODEL
    cache_version = version.replace("-scenario", "")

    if not use_model_cache:
        return train_risk_model(
            panel,
            version=cache_version,
            vn30_panel=vn30_panel,
            feature_cols_by_horizon=feature_cols_by_horizon,
            estimator_params_by_horizon=estimator_params_by_horizon,
        )

    if _LOADED_MODEL is not None:
        return _LOADED_MODEL

    if _DEFAULT_MODEL_PATH.exists():
        with open(_DEFAULT_MODEL_PATH, "rb") as f:
            data = pickle.load(f)  # noqa: S301
            _LOADED_MODEL = (data["model"], data["metrics"])
        logger.info("Loaded pre-trained model from %s", _DEFAULT_MODEL_PATH)
        return _LOADED_MODEL

    logger.warning("No pre-trained model at %s — falling back to dynamic training", _DEFAULT_MODEL_PATH)
    res = train_risk_model(
        panel,
        version=cache_version,
        vn30_panel=vn30_panel,
        feature_cols_by_horizon=feature_cols_by_horizon,
        estimator_params_by_horizon=estimator_params_by_horizon,
    )
    _LOADED_MODEL = res

    try:
        _DEFAULT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_DEFAULT_MODEL_PATH, "wb") as f:
            pickle.dump({"model": res[0], "metrics": res[1]}, f)
        logger.info("Auto-saved trained model to %s", _DEFAULT_MODEL_PATH)
    except OSError as exc:
        logger.error("Failed to persist model: %s", exc)

    return _LOADED_MODEL




def run_quant_eod(
    panel: pd.DataFrame,
    as_of: date,
    *,
    run_id: str | None = None,
    model_version: str = "skhgb-v4-hybrid",
    vn30_panel: pd.DataFrame | None = None,
    benchmark_dir: str | Path | None = "data/models",
) -> QuantEngineOutput:
    """
    panel: cột bắt buộc date, vn_index, volume, usd_vnd_rate, usd_vnd_1m_change_pct, sbv_interest_rate_pct
    """
    rid = run_id or str(uuid.uuid4())
    ts = datetime.now(timezone.utc)
    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] <= pd.Timestamp(as_of)].sort_values("date")

    benchmark_cfg = None
    if benchmark_dir is not None:
        benchmark_cfg = resolve_benchmark_training_config(benchmark_dir)

    use_model_cache = model_version == "skhgb-v4-hybrid" and str(benchmark_dir) == "data/models"
    trained, metrics = _get_cached_trained_model(
        df,
        as_of,
        version=model_version,
        vn30_panel=vn30_panel,
        feature_cols_by_horizon=benchmark_cfg.feature_cols_by_horizon if benchmark_cfg else None,
        estimator_params_by_horizon=benchmark_cfg.estimator_params_by_horizon if benchmark_cfg else None,
        use_model_cache=use_model_cache,
    )
    feat_df = prepare_features(df, vn30_panel=vn30_panel)
    pred_row = row_at_date(feat_df, pd.Timestamp(as_of))
    p1w, p2w, p1m, dd, decision_score = predict_horizons(trained, pred_row)
    regime = risk_regime_from_score(decision_score)

    shap_top = contributions_from_tree_model(
        trained.estimators["2w"], pred_row, trained.feature_names_by_horizon["2w"]
    )
    dominant = shap_top[0].feature_name if shap_top else "unknown"

    var_panel = df[["vn_index", "usd_vnd_rate", "sbv_interest_rate_pct"]].copy()
    vs = fit_var_summary(var_panel)
    var_note = var_impulse_note(var_panel)
    if vs.fitted:
        merged_var = VarSummary(fitted=True, n_obs=vs.n_obs, max_lag=vs.max_lag, note=var_note)
    else:
        merged_var = vs

    narrative_inputs: dict[str, float | str] = {
        "vn_index": float(pred_row["vn_index"]),
        "decision_score": decision_score,
        "p_decline_1w": p1w,
        "p_decline_2w": p2w,
        "p_decline_1m": p1m,
        "expected_drawdown_pct": dd,
        "usd_vnd_rate": float(pred_row["usd_vnd_rate"]),
        "dominant_feature": dominant,
        "var_note": var_note,
    }
    feature_names_by_horizon = {
        horizon: list(features) for horizon, features in trained.feature_names_by_horizon.items()
    }
    estimator_params_by_horizon = {
        horizon: {k: v for k, v in params.items()}
        for horizon, params in getattr(trained, "estimator_params", {}).items()
    }

    return QuantEngineOutput(
        run_id=rid,
        as_of=ts,
        model_version=trained.version,
        decision_score=decision_score,
        risk_score_2w=p2w,
        risk_regime=regime,  # type: ignore[arg-type]
        horizons=TargetHorizons(
            p_decline_1w=p1w,
            p_decline_2w=p2w,
            p_decline_1m=p1m,
            expected_drawdown_pct=dd,
        ),
        shap_top=shap_top,
        var_summary=merged_var,
        backtest=BacktestSummary(
            last_auc=metrics.get("last_auc"),
            last_brier=metrics.get("last_brier"),
            metrics_by_horizon={
                horizon: HorizonBacktestMetrics(
                    auc=metrics.get(f"auc_{horizon}"),
                    brier=metrics.get(f"brier_{horizon}"),
                    precision_high_risk=metrics.get(f"precision_high_risk_{horizon}"),
                )
                for horizon in ("1w", "2w", "1m")
            },
        ),
        dominant_feature=dominant,
        narrative_inputs=narrative_inputs,
        provenance=QuantProvenance(
            panel_rows=int(len(df)),
            benchmark_dir=str(benchmark_dir) if benchmark_dir is not None else None,
            benchmark_sources=dict(getattr(benchmark_cfg, "sources", {})) if benchmark_cfg else {},
            train_feature_count_by_horizon={
                horizon: len(features) for horizon, features in feature_names_by_horizon.items()
            },
            train_feature_names_by_horizon=feature_names_by_horizon,
            estimator_params_by_horizon=estimator_params_by_horizon,
        ),
    )
