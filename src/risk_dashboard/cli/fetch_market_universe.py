from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from risk_dashboard.data.universe_fetch import fetch_market_universe_bundle
from risk_dashboard.pipeline.settings import PipelinePaths


def main() -> None:
    p = argparse.ArgumentParser(
        description="Crawl VNINDEX + VN30 raw data và sinh training panel dùng cho model/dashboard."
    )
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--out", type=Path, default=None, help="Thư mục cache output")
    p.add_argument("--macro", choices=("auto", "csv", "official"), default="auto")
    p.add_argument("--macro-csv", help="CSV vĩ mô khi --macro csv|official")
    p.add_argument("--yfinance-fx", default="USDVND=X")
    p.add_argument("--vnstock-source", default="DNSE")

    args = p.parse_args()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    if args.macro in ("csv", "official") and not args.macro_csv:
        p.error(f"--macro {args.macro} cần --macro-csv")

    paths = PipelinePaths.defaults(Path.cwd())
    out_dir = (args.out or paths.cache_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = fetch_market_universe_bundle(
            start=start,
            end=end,
            output_dir=out_dir,
            macro_mode=args.macro,
            macro_csv_path=args.macro_csv,
            yfinance_fx_ticker=args.yfinance_fx,
            vnstock_source=args.vnstock_source,
        )
    except Exception as exc:
        print(f"Lỗi crawl universe: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: VN30 {result.vn30_symbol_count} mã, {result.vn30_rows} dòng")
    print(f"VNINDEX rows: {result.vnindex_rows}")
    print(f"VN30 parquet: {result.vn30_parquet}")
    print(f"VNINDEX parquet: {result.vnindex_parquet}")
    print(f"Training panel: {result.training_panel_parquet}")
    print(f"Training manifest: {result.training_panel_manifest}")
    print(f"Universe manifest: {result.universe_manifest}")


if __name__ == "__main__":
    main()
