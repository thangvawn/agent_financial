import numpy as np
import pandas as pd

from risk_dashboard.modules.market_portfolio.api.public import _json_safe_provider_value


def test_provider_values_are_safe_for_fastapi_json_serialization():
    assert _json_safe_provider_value(np.int64(42)) == 42
    assert isinstance(_json_safe_provider_value(np.int64(42)), int)
    assert _json_safe_provider_value(np.float64(3.5)) == 3.5
    assert _json_safe_provider_value(pd.NA) is None
    assert _json_safe_provider_value(pd.Timestamp("2026-07-20")) == "2026-07-20T00:00:00"
