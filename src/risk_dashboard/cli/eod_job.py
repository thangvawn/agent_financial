from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from risk_dashboard.data.ingest import run_ingest_to_parquet
from risk_dashboard.data.macro_auto import AutoMacroSource
from risk_dashboard.data.macro_connector import CsvMacroSource
from risk_dashboard.data.macro_official import OfficialCsvMacroSource
from risk_dashboard.data.market_connector import CsvMarketSource, VnstockMarketSource
from risk_dashboard.storage.sqlite_store import IngestRegistry


def main() -> None:
    p = argparse.ArgumentParser(
        description="Job EOD: ingest (tuỳ chọn) + ghi registry SQLite để tra cứu Parquet."
    )
    p.add_argument("--sqlite", default="./data/risk_dashboard.db", help="Đường dẫn file SQLite")
    p.add_argument("--skip-ingest", action="store_true", help="Chỉ đăng ký file Parquet có sẵn")
    p.add_argument("--parquet", help="Khi --skip-ingest: đường dẫn Parquet đã có")
    p.add_argument("--manifest", help="Manifest JSON đi kèm (tuỳ chọn)")
    p.add_argument("--start", help="YYYY-MM-DD (cần khi không --skip-ingest)")
    p.add_argument("--end", help="YYYY-MM-DD")
    p.add_argument("--output-dir", default="./data_outputs")
    p.add_argument("--market", choices=("vnstock", "csv"), default="csv")
    p.add_argument("--market-csv")
    p.add_argument("--macro-csv")
    p.add_argument("--macro-auto", action="store_true")
    p.add_argument("--macro-official-csv")
    p.add_argument("--yfinance-fx-ticker", default="USDVND=X")
    p.add_argument("--vnindex-symbol", default="VNINDEX")
    p.add_argument("--vnstock-source", default="VCI")

    args = p.parse_args()

    reg = IngestRegistry(args.sqlite)

    if args.skip_ingest:
        if not args.parquet:
            p.error("--parquet là bắt buộc khi --skip-ingest")
        pq = Path(args.parquet)
        mj = Path(args.manifest) if args.manifest else None
        n_rows = len(pd.read_parquet(pq))
        meta: dict = {}
        if mj and mj.exists():
            meta = json.loads(mj.read_text(encoding="utf-8"))
        rid = reg.register(
            parquet_path=pq,
            manifest_path=mj,
            market_label=meta.get("market_source", ""),
            macro_label=meta.get("macro_source", ""),
            start_date=meta.get("start", ""),
            end_date=meta.get("end", ""),
            n_rows=n_rows,
            meta={"source": "register_existing"},
        )
        print(f"Registered ingest id={rid} parquet={pq}")
        reg.close()
        return

    if not args.start or not args.end:
        p.error("--start và --end là bắt buộc khi chạy ingest")
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    if args.market == "csv":
        if not args.market_csv:
            p.error("--market-csv cần khi --market csv")
        market = CsvMarketSource(args.market_csv)
        mlabel = f"csv:{args.market_csv}"
    else:
        market = VnstockMarketSource(symbol=args.vnindex_symbol, source=args.vnstock_source)
        mlabel = f"vnstock:{args.vnindex_symbol}:{args.vnstock_source}"

    if args.macro_auto:
        if args.macro_csv or args.macro_official_csv:
            p.error("Không kết hợp --macro-auto với macro CSV khác")
        macro = AutoMacroSource(yfinance_ticker=args.yfinance_fx_ticker)
        macro_label = f"auto:yfinance:{args.yfinance_fx_ticker}+worldbank"
    elif args.macro_official_csv:
        macro = OfficialCsvMacroSource(args.macro_official_csv)
        macro_label = f"official:{args.macro_official_csv}"
    elif args.macro_csv:
        macro = CsvMacroSource(args.macro_csv)
        macro_label = f"csv:{args.macro_csv}"
    else:
        p.error("Cần một trong: --macro-csv, --macro-auto, --macro-official-csv")

    pq, mj = run_ingest_to_parquet(
        market,
        macro,
        start,
        end,
        args.output_dir,
        market_label=mlabel,
        macro_label=macro_label,
    )
    man = json.loads(Path(mj).read_text(encoding="utf-8"))
    rid = reg.register(
        parquet_path=pq,
        manifest_path=mj,
        market_label=mlabel,
        macro_label=macro_label,
        start_date=man.get("start", args.start),
        end_date=man.get("end", args.end),
        n_rows=man.get("n_rows"),
        meta={"manifest": man},
    )
    print(f"Ingest id={rid}")
    print(f"Parquet: {pq}")
    print(f"Manifest: {mj}")
    reg.close()


if __name__ == "__main__":
    main()
