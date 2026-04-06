from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.data.interfaces import MarketSource


def _first_col(df: pd.DataFrame, patterns: tuple[str, ...]) -> str | None:
    for c in df.columns:
        cl = str(c).strip().lower()
        for p in patterns:
            if re.match(p, cl):
                return c
    return None


def normalize_index_ohlcv_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hoá DataFrame OHLCV từ vnstock/CSV về: date, vn_index, volume.
    """
    if df is None or df.empty:
        raise ValueError("Empty market dataframe")
    work = df.copy()
    date_col = _first_col(work, (r"^time$", r"^date$", r"^tradingdate$"))
    close_col = _first_col(work, (r"^close$", r"^adj[_]?close$"))
    vol_col = _first_col(work, (r"^volume$", r"^vol$"))
    if not date_col:
        raise ValueError(f"Không tìm được cột ngày trong: {list(work.columns)}")
    if not close_col:
        raise ValueError(f"Không tìm được cột close trong: {list(work.columns)}")
    if not vol_col:
        work["_volume"] = 0.0
        vol_col = "_volume"
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(work[date_col], errors="coerce"),
            "vn_index": pd.to_numeric(work[close_col], errors="coerce"),
            "volume": pd.to_numeric(work[vol_col], errors="coerce").fillna(0.0),
        }
    )
    out = out.dropna(subset=["date", "vn_index"]).sort_values("date").reset_index(drop=True)
    if out.empty:
        raise ValueError("Sau chuẩn hoá không còn dòng hợp lệ")
    return out


class CsvMarketSource(MarketSource):
    """Đọc chỉ số từ CSV (cột thời gian + close + volume)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_index_series(self, start: date, end: date) -> pd.DataFrame:
        raw = pd.read_csv(self.path)
        df = normalize_index_ohlcv_to_daily(raw)
        mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
        return df.loc[mask].reset_index(drop=True)


class DataFrameMarketSource(MarketSource):
    """Dùng DataFrame đã có sẵn để tái sử dụng ingest/panel pipeline."""

    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = normalize_index_ohlcv_to_daily(frame)

    def load_index_series(self, start: date, end: date) -> pd.DataFrame:
        df = self.frame.copy()
        mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
        return df.loc[mask].reset_index(drop=True)


class VnstockMarketSource(MarketSource):
    """
    Lấy lịch sử chỉ số qua vnstock (cần `pip install vnstock` hoặc `pip install -e '.[vnstock]'`).
    """

    def __init__(self, symbol: str = "VNINDEX", *, source: str = "VCI") -> None:
        self.symbol = symbol
        self.source = source

    def load_index_series(self, start: date, end: date) -> pd.DataFrame:
        df = _fetch_index_history_vnstock(self.symbol, start, end, source=self.source)
        return normalize_index_ohlcv_to_daily(df)


def _fetch_index_history_vnstock(symbol: str, start: date, end: date, *, source: str) -> pd.DataFrame:
    start_s = start.isoformat()
    end_s = end.isoformat()
    errors: list[str] = []

    try:
        from vnstock import stock_historical_data  # type: ignore

        for api_source in ("TCBS", "DNSE"):
            try:
                out = stock_historical_data(
                    symbol=symbol,
                    start_date=start_s,
                    end_date=end_s,
                    resolution="1D",
                    type="index",
                    beautify=False,
                    decor=False,
                    source=api_source,
                )
                if isinstance(out, pd.DataFrame) and out is not None and not out.empty:
                    return out
                errors.append(f"stock_historical_data({api_source}) rỗng")
            except Exception as e:
                errors.append(f"stock_historical_data {api_source}: {e!r}")

    except Exception as e:
        errors.append(f"import stock_historical_data: {e!r}")

    try:
        from vnstock import Quote  # type: ignore

        q = Quote(symbol=symbol, source=source)
        out = q.history(start=start_s, end=end_s, interval="1D")
        if isinstance(out, pd.DataFrame) and not out.empty:
            return out
        errors.append("Quote.history trả về rỗng")
    except Exception as e:
        errors.append(f"Quote: {e!r}")

    try:
        from vnstock import Vnstock  # type: ignore

        stock = Vnstock().stock(symbol=symbol, source=source)
        out = stock.quote.history(start=start_s, end=end_s, interval="1D")
        if isinstance(out, pd.DataFrame) and not out.empty:
            return out
        errors.append("Vnstock.quote.history trả về rỗng")
    except Exception as e:
        errors.append(f"Vnstock: {e!r}")

    raise RuntimeError(
        "Không lấy được dữ liệu từ vnstock. Cài: pip install vnstock + ipython (extra). "
        f"Hoặc dùng --market yfinance / --market csv. Chi tiết: {'; '.join(errors)}"
    )


class YfinanceMarketSource(MarketSource):
    """
    Chỉ số/cổ phiếu qua Yahoo (`yfinance`) — dùng khi vnstock lỗi hoặc cần so sánh.
    Ticker VN-Index trên Yahoo không ổn định; thường dùng **vnstock** cho VNINDEX.
    """

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker

    def load_index_series(self, start: date, end: date) -> pd.DataFrame:
        try:
            import yfinance as yf  # type: ignore
        except ImportError as e:
            raise RuntimeError('Cần yfinance: pip install -e ".[auto]"') from e
        t = yf.Ticker(self.ticker)
        ts_start = pd.Timestamp(start).normalize()
        ts_end = pd.Timestamp(end).normalize() + pd.Timedelta(days=1)
        raw = t.history(start=ts_start, end=ts_end, auto_adjust=True, interval="1d")
        if raw is None or raw.empty:
            raise RuntimeError(f"yfinance không có dữ liệu cho {self.ticker} trong khoảng đã chọn.")
        if isinstance(raw.columns, pd.MultiIndex):
            raw = raw.copy()
            raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
        # history() để ngày ở index — chuẩn hoá cần cột date/time (bỏ TZ để merge_asof khớp macro)
        raw = raw.reset_index()
        tcol = raw.columns[0]
        ts = pd.to_datetime(raw[tcol], errors="coerce", utc=True)
        raw[tcol] = ts.dt.strftime("%Y-%m-%d %H:%M:%S")
        raw[tcol] = pd.to_datetime(raw[tcol])
        return normalize_index_ohlcv_to_daily(raw)
