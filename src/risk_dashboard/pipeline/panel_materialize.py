from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from risk_dashboard.data.ingest import run_ingest_to_parquet
from risk_dashboard.pipeline.macro_factory import MacroMode, create_macro_source, macro_label
from risk_dashboard.pipeline.market_factory import MarketMode, create_market_source, market_label
from risk_dashboard.storage.sqlite_store import IngestRegistry


@dataclass(frozen=True)
class MaterializeResult:
    parquet_path: Path
    manifest_path: Path
    ingest_id: str | None
    n_rows: int


def materialize_training_panel(
    *,
    start: date,
    end: date,
    output_dir: str | Path,
    market_mode: MarketMode,
    macro_mode: MacroMode,
    register_sqlite: Path | None = None,
    csv_path: str | None = None,
    vnindex_symbol: str = "VNINDEX",
    vnstock_source: str = "VCI",
    yfinance_ticker: str | None = None,
    macro_csv_path: str | None = None,
    yfinance_fx_ticker: str = "USDVND=X",
) -> MaterializeResult:
    """
    Điểm vào pipeline: factory thị trường + vĩ mô → Parquet/manifest → (tuỳ chọn) SQLite.
    """
    market = create_market_source(
        market_mode,
        csv_path=csv_path,
        vnindex_symbol=vnindex_symbol,
        vnstock_source=vnstock_source,
        yfinance_ticker=yfinance_ticker,
    )
    macro = create_macro_source(
        macro_mode,
        macro_csv_path=macro_csv_path,
        yfinance_fx_ticker=yfinance_fx_ticker,
    )

    ml = market_label(
        market_mode,
        csv_path=csv_path or "",
        vnindex_symbol=vnindex_symbol,
        vnstock_source=vnstock_source,
        yfinance_ticker=yfinance_ticker or "",
    )
    xl = macro_label(
        macro_mode,
        macro_csv_path=macro_csv_path or "",
        yfinance_fx_ticker=yfinance_fx_ticker,
    )

    pq, mj = run_ingest_to_parquet(market, macro, start, end, output_dir, market_label=ml, macro_label=xl)

    man = json.loads(Path(mj).read_text(encoding="utf-8"))
    rid = man.get("ingest_id")
    n_rows = int(man.get("n_rows", 0))

    if register_sqlite is not None:
        reg = IngestRegistry(register_sqlite)
        reg.register(
            parquet_path=pq,
            manifest_path=mj,
            market_label=ml,
            macro_label=xl,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            n_rows=n_rows,
            meta={"ingest_id": rid},
            run_id=rid,
        )
        reg.close()

    return MaterializeResult(
        parquet_path=Path(pq),
        manifest_path=Path(mj),
        ingest_id=rid,
        n_rows=n_rows,
    )
