import pandas as pd

from risk_dashboard.engines.quant.shap_explain import contributions_from_tree_model
from risk_dashboard.engines.quant.xgb_engine import prepare_features, train_risk_model, row_at_date


def test_shap_sums_to_one(synthetic_panel, as_of_date):
    model, _ = train_risk_model(synthetic_panel)
    df = prepare_features(synthetic_panel)
    row = row_at_date(df, pd.Timestamp(as_of_date))
    top = contributions_from_tree_model(model.estimators["2w"], row, model.feature_names_by_horizon["2w"])
    assert top
    assert abs(sum(t.share for t in top) - 1.0) < 1e-6
