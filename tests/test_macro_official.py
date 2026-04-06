from pathlib import Path

from risk_dashboard.data.macro_official import OfficialCsvMacroSource, read_official_macro_csv

FIX = Path(__file__).resolve().parent / "fixtures"


def test_read_official_macro_csv():
    df = read_official_macro_csv(FIX / "sample_official_macro.csv")
    assert "usd_vnd_rate" in df.columns
    assert len(df) == 2


def test_official_source_load():
    src = OfficialCsvMacroSource(FIX / "sample_official_macro.csv")
    from datetime import date

    out = src.load_macro_monthly(date(2024, 1, 1), date(2024, 12, 31))
    assert not out.empty
