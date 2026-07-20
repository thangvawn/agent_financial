from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import shap

from risk_dashboard.schemas.snapshots import ShapContribution


def contributions_from_tree_model(
    model: Any, row: pd.Series, feature_names: list[str]
) -> list[ShapContribution]:
    X = row[feature_names].astype(float).to_frame().T
    try:
        explainer = shap.TreeExplainer(model)
        raw = explainer.shap_values(X)
    except Exception:
        explainer = shap.Explainer(model, X)
        raw = explainer(X).values
    if isinstance(raw, list):
        sv = raw[1][0] if len(raw) > 1 else raw[0][0]
    else:
        if hasattr(raw, "ndim") and raw.ndim == 3:
            sv = raw[0, :, 1] if raw.shape[-1] > 1 else raw[0, :, 0]
        else:
            sv = raw[0]
    names = feature_names
    abs_vals = np.abs(sv)
    total = abs_vals.sum() + 1e-9
    shares = abs_vals / total
    directions: list[str] = []
    for val in sv:
        directions.append("increases_risk" if val > 0 else "decreases_risk")
    order = np.argsort(-shares)
    top: list[ShapContribution] = []
    for i in order[:5]:
        top.append(
            ShapContribution(feature_name=names[i], share=float(shares[i]), direction=directions[i])  # type: ignore[arg-type]
        )
    ssum = sum(t.share for t in top)
    if ssum <= 0:
        return top
    return [
        ShapContribution(feature_name=t.feature_name, share=t.share / ssum, direction=t.direction) for t in top
    ]
