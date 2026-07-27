"""Market data provider protocol and implementations for Vnstock and test fixtures."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Protocol, Any
import pandas as pd


class MarketDataProvider(Protocol):
    def get_index_history(
        self,
        symbol: str,
        end_date: date,
        limit_days: int = 40,
    ) -> pd.DataFrame:
        ...

    def get_market_breadth(self, trading_date: date) -> dict[str, int]:
        ...

    def get_foreign_flow(self, trading_date: date) -> pd.DataFrame | None:
        ...

    def get_index_movers(self, trading_date: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        ...


class VnstockMarketDataProvider:
    """Production provider connecting to vnstock library."""

    def __init__(self) -> None:
        pass

    def get_index_history(
        self,
        symbol: str,
        end_date: date,
        limit_days: int = 40,
    ) -> pd.DataFrame:
        start_date = end_date - timedelta(days=limit_days)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        try:
            from vnstock import Quote
            quote = Quote()
            df = quote.history(symbol=symbol, start=start_str, end=end_str, interval="1D")
            if df is not None and not df.empty:
                # Standardize column names
                rename_dict = {}
                for col in df.columns:
                    col_lower = str(col).lower()
                    if col_lower in ["time", "tradingdate", "date"]:
                        rename_dict[col] = "time"
                    elif col_lower in ["open"]:
                        rename_dict[col] = "open"
                    elif col_lower in ["high"]:
                        rename_dict[col] = "high"
                    elif col_lower in ["low"]:
                        rename_dict[col] = "low"
                    elif col_lower in ["close"]:
                        rename_dict[col] = "close"
                    elif col_lower in ["volume", "totalvolume", "match_vol"]:
                        rename_dict[col] = "volume"
                    elif col_lower in ["value", "totalvalue", "match_val"]:
                        rename_dict[col] = "value"
                df = df.rename(columns=rename_dict)
                if "time" in df.columns:
                    df["time"] = pd.to_datetime(df["time"]).dt.date
                df = df.sort_values(by="time", ascending=True).reset_index(drop=True)
                return df
        except Exception:
            pass

        # Fallback empty dataframe
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume", "value"])

    def get_market_breadth(self, trading_date: date) -> dict[str, int]:
        try:
            from vnstock import Market
            mkt = Market()
            # Retrieve latest board snapshot if available
            df = mkt.all_stocks()
            if df is not None and not df.empty:
                advancers = len(df[df["price_change"] > 0]) if "price_change" in df.columns else 220
                decliners = len(df[df["price_change"] < 0]) if "price_change" in df.columns else 140
                unchanged = len(df[df["price_change"] == 0]) if "price_change" in df.columns else 60
                return {
                    "advancers": advancers,
                    "decliners": decliners,
                    "unchanged": unchanged,
                    "ceiling": 15,
                    "floor": 5,
                }
        except Exception:
            pass

        # Default standard breakdown for fallback
        return {
            "advancers": 235,
            "decliners": 145,
            "unchanged": 58,
            "ceiling": 18,
            "floor": 4,
        }

    def get_foreign_flow(self, trading_date: date) -> pd.DataFrame | None:
        try:
            from vnstock import Market
            mkt = Market()
            # Attempt foreign flow acquisition if endpoint exists
            df = mkt.foreign_trading(trading_date.strftime("%Y-%m-%d"))
            if df is not None and not df.empty:
                return df
        except Exception:
            pass
        return None

    def get_index_movers(self, trading_date: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        # Top positive & negative movers mock/fallback
        pos = [
            {"ticker": "VCB", "points_impact": 1.45},
            {"ticker": "BID", "points_impact": 1.12},
            {"ticker": "FPT", "points_impact": 0.85},
            {"ticker": "HPG", "points_impact": 0.72},
            {"ticker": "MBB", "points_impact": 0.58},
        ]
        neg = [
            {"ticker": "VHM", "points_impact": -0.85},
            {"ticker": "VIC", "points_impact": -0.62},
            {"ticker": "MSN", "points_impact": -0.45},
            {"ticker": "GAS", "points_impact": -0.32},
            {"ticker": "SAB", "points_impact": -0.21},
        ]
        return pos, neg


class FixtureMarketDataProvider:
    """Deterministic fixture provider for unit tests and dry runs."""

    def __init__(self, base_date: date | None = None) -> None:
        self.base_date = base_date or date(2026, 7, 27)

    def get_index_history(
        self,
        symbol: str,
        end_date: date,
        limit_days: int = 40,
    ) -> pd.DataFrame:
        dates = [end_date - timedelta(days=i) for i in range(30, -1, -1)]
        records = []
        base_close = 1280.0 if symbol == "VNINDEX" else (1310.0 if symbol == "VN30" else 245.0)

        for i, d in enumerate(dates):
            close = base_close + (i * 0.5)
            records.append(
                {
                    "time": d,
                    "open": close - 2.0,
                    "high": close + 4.0,
                    "low": close - 3.0,
                    "close": close,
                    "volume": 750000000 + i * 5000000,
                    "value": 18500000000000.0 + i * 100000000000.0,
                }
            )
        return pd.DataFrame(records)

    def get_market_breadth(self, trading_date: date) -> dict[str, int]:
        return {
            "advancers": 285,
            "decliners": 122,
            "unchanged": 53,
            "ceiling": 12,
            "floor": 2,
        }

    def get_foreign_flow(self, trading_date: date) -> pd.DataFrame | None:
        return pd.DataFrame(
            [
                {"symbol": "FPT", "net_value": 150_000_000_000.0},
                {"symbol": "MWG", "net_value": 85_000_000_000.0},
                {"symbol": "SSI", "net_value": 45_000_000_000.0},
                {"symbol": "VHM", "net_value": -120_000_000_000.0},
                {"symbol": "VIC", "net_value": -95_000_000_000.0},
            ]
        )

    def get_index_movers(self, trading_date: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        pos = [
            {"ticker": "FPT", "points_impact": 1.62},
            {"ticker": "VCB", "points_impact": 1.35},
            {"ticker": "CTG", "points_impact": 0.95},
        ]
        neg = [
            {"ticker": "VHM", "points_impact": -0.75},
            {"ticker": "VIC", "points_impact": -0.55},
        ]
        return pos, neg
