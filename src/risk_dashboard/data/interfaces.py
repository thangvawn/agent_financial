from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class MarketSource(ABC):
    """Nguồn OHLCV / chỉ số — triển khai thật (vnstock) hoặc fake trong test."""

    @abstractmethod
    def load_index_series(self, start: date, end: date) -> pd.DataFrame:
        """Cột tối thiểu: date, vn_index, volume (hoặc turnover)."""


class MacroSource(ABC):
    """Nguồn vĩ mô — CSV/API; test dùng DataFrame cố định."""

    @abstractmethod
    def load_macro_monthly(self, start: date, end: date) -> pd.DataFrame:
        """Chỉ số theo tháng: period_end (date), usd_vnd_rate, ..."""
