from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from risk_dashboard.data.ingest import run_ingest_to_parquet
from risk_dashboard.data.market_connector import DataFrameMarketSource
from risk_dashboard.pipeline.macro_factory import create_macro_source, macro_label


def extract_vn30_tickers(listings: pd.DataFrame) -> list[str]:
    if "ticker" not in listings.columns or "VN30" not in listings.columns:
        raise ValueError("listing dataframe must contain ticker and VN30 columns")
    tickers = listings.loc[listings["VN30"] == True, "ticker"]  # noqa: E712
    return sorted(tickers.dropna().astype(str).unique().tolist())


def _fetch_company_listing() -> pd.DataFrame:
    from vnstock import Listing

    # Use KBS because it supports all_symbols and symbols_by_group
    listing = Listing(source='KBS')
    df = listing.all_symbols()
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise RuntimeError("all_symbols returned empty data")
    
    # Rename column 'symbol' to 'ticker'
    if 'symbol' in df.columns:
        df = df.rename(columns={'symbol': 'ticker'})
    
    # Ensure 'ticker' column exists
    if 'ticker' not in df.columns:
        raise RuntimeError("ticker column not found in company listing")

    # Get VN30 group symbols
    try:
        vn30_series = listing.symbols_by_group('VN30')
        vn30_tickers = set(vn30_series.dropna().astype(str).tolist())
    except Exception:
        vn30_tickers = set()

    df['VN30'] = df['ticker'].isin(vn30_tickers)
    return df


def _fetch_history(
    symbol: str,
    start: date,
    end: date,
    *,
    instrument_type: str,
    source: str,
    retries: int = 3,
) -> pd.DataFrame:
    from vnstock.api.quote import Quote

    # Map DNSE or other unsupported sources to 'vci' since DNSE is removed in vnstock v4
    src = source.lower()
    allowed_sources = ['vci', 'kbs', 'msn', 'fmp']
    if src not in allowed_sources:
        src = 'vci'

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            q = Quote(symbol=symbol, source=src)
            out = q.history(
                start=start.isoformat(),
                end=end.isoformat(),
                interval="1D",
            )
            if isinstance(out, pd.DataFrame) and not out.empty:
                return out
            raise RuntimeError(f"Empty history for {symbol}")
        except Exception as exc:  # pragma: no cover - network dependent
            last_err = exc
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"Cannot fetch {symbol}: {last_err}") from last_err


@dataclass
class UniverseFetchManifest:
    fetch_id: str
    created_at: str
    start: str
    end: str
    market_source: str
    macro_source: str
    vn30_symbol_count: int
    vn30_rows: int
    vnindex_rows: int
    errors: dict[str, str]
    constituents_csv: str
    vn30_parquet: str
    vnindex_parquet: str
    training_panel_parquet: str
    training_panel_manifest: str


@dataclass
class UniverseFetchResult:
    constituents_csv: Path
    vn30_parquet: Path
    vnindex_parquet: Path
    training_panel_parquet: Path
    training_panel_manifest: Path
    universe_manifest: Path
    vn30_symbol_count: int
    vn30_rows: int
    vnindex_rows: int


def fetch_market_universe_bundle(
    *,
    start: date,
    end: date,
    output_dir: str | Path,
    macro_mode: str = "auto",
    macro_csv_path: str | None = None,
    yfinance_fx_ticker: str = "USDVND=X",
    vnstock_source: str = "DNSE",
) -> UniverseFetchResult:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fetch_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    compact_start = start.strftime("%Y%m%d")
    compact_end = end.strftime("%Y%m%d")

    listings = _fetch_company_listing()
    vn30_tickers = extract_vn30_tickers(listings)

    constituents_csv = out_dir / f"vn30_constituents_{ts}_{fetch_id[:8]}.csv"
    listings.loc[listings["ticker"].astype(str).isin(vn30_tickers)].to_csv(constituents_csv, index=False)

    vn30_frames: list[pd.DataFrame] = []
    errors: dict[str, str] = {}
    for ticker in vn30_tickers:
        try:
            frame = _fetch_history(
                ticker,
                start,
                end,
                instrument_type="stock",
                source=vnstock_source,
            ).copy()
            frame["ticker"] = ticker
            vn30_frames.append(frame)
        except Exception as exc:  # pragma: no cover - network dependent
            errors[ticker] = str(exc)

    if not vn30_frames:
        raise RuntimeError("No VN30 history fetched")

    vn30_df = pd.concat(vn30_frames, ignore_index=True)
    vn30_df["time"] = pd.to_datetime(vn30_df["time"], errors="coerce")
    vn30_df = vn30_df.dropna(subset=["time"]).sort_values(["ticker", "time"]).reset_index(drop=True)
    vn30_parquet = out_dir / f"vn30_daily_{compact_start}_{compact_end}_{fetch_id[:8]}.parquet"
    vn30_df.to_parquet(vn30_parquet, index=False)

    vnindex_df = _fetch_history(
        "VNINDEX",
        start,
        end,
        instrument_type="index",
        source=vnstock_source,
    ).copy()
    vnindex_df["time"] = pd.to_datetime(vnindex_df["time"], errors="coerce")
    vnindex_df = vnindex_df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    vnindex_parquet = out_dir / f"vnindex_daily_{compact_start}_{compact_end}_{fetch_id[:8]}.parquet"
    vnindex_df.to_parquet(vnindex_parquet, index=False)

    market = DataFrameMarketSource(vnindex_df)
    macro = create_macro_source(
        macro_mode,
        macro_csv_path=macro_csv_path,
        yfinance_fx_ticker=yfinance_fx_ticker,
    )
    training_panel_parquet, training_panel_manifest = run_ingest_to_parquet(
        market,
        macro,
        start,
        end,
        out_dir,
        ingest_id=fetch_id,
        market_label=f"vnstock:VNINDEX:{vnstock_source}",
        macro_label=macro_label(
            macro_mode,
            macro_csv_path=macro_csv_path or "",
            yfinance_fx_ticker=yfinance_fx_ticker,
        ),
    )

    universe_manifest = out_dir / f"market_universe_manifest_{ts}_{fetch_id[:8]}.json"
    manifest = UniverseFetchManifest(
        fetch_id=fetch_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        start=start.isoformat(),
        end=end.isoformat(),
        market_source=f"vnstock:{vnstock_source}",
        macro_source=macro_label(
            macro_mode,
            macro_csv_path=macro_csv_path or "",
            yfinance_fx_ticker=yfinance_fx_ticker,
        ),
        vn30_symbol_count=len(vn30_tickers),
        vn30_rows=len(vn30_df),
        vnindex_rows=len(vnindex_df),
        errors=errors,
        constituents_csv=str(constituents_csv),
        vn30_parquet=str(vn30_parquet),
        vnindex_parquet=str(vnindex_parquet),
        training_panel_parquet=str(training_panel_parquet),
        training_panel_manifest=str(training_panel_manifest),
    )
    universe_manifest.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")

    return UniverseFetchResult(
        constituents_csv=constituents_csv,
        vn30_parquet=vn30_parquet,
        vnindex_parquet=vnindex_parquet,
        training_panel_parquet=training_panel_parquet,
        training_panel_manifest=training_panel_manifest,
        universe_manifest=universe_manifest,
        vn30_symbol_count=len(vn30_tickers),
        vn30_rows=len(vn30_df),
        vnindex_rows=len(vnindex_df),
    )
