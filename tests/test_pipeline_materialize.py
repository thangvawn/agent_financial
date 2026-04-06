from datetime import date
from pathlib import Path

from risk_dashboard.pipeline.panel_materialize import materialize_training_panel

FIX = Path(__file__).resolve().parent / "fixtures"


def test_materialize_with_csv_sources(tmp_path):
    r = materialize_training_panel(
        start=date(2024, 1, 1),
        end=date(2024, 2, 29),
        output_dir=tmp_path,
        market_mode="csv",
        macro_mode="csv",
        csv_path=str(FIX / "sample_market.csv"),
        macro_csv_path=str(FIX / "sample_macro.csv"),
    )
    assert r.parquet_path.exists()
    assert r.n_rows >= 1
