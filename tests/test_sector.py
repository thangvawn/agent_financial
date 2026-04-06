from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.data.sector_connector import load_sector_panel_csv, sector_winners_losers

FIX = Path(__file__).resolve().parent / "fixtures"


def test_sector_winners_losers():
    panel = load_sector_panel_csv(FIX / "sample_sector.csv")
    wl = sector_winners_losers(panel, date(2024, 2, 29), window_months=6, top_k=2)
    assert wl.winners
    codes_w = [w[0] for w in wl.winners]
    assert "EXPORT" in codes_w or "BANK" in codes_w
