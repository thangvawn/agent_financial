from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from risk_dashboard.pipeline.panel_materialize import materialize_training_panel
from risk_dashboard.pipeline.settings import PipelinePaths


def main() -> None:
    p = argparse.ArgumentParser(
        description="Tải/ghi panel huấn luyện (Parquet) — dùng pipeline module hoá."
    )
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument(
        "--market",
        choices=("vnstock", "yfinance", "csv"),
        default="vnstock",
        help="vnstock: VNINDEX (cần pip install -e '.[vnstock]'). yfinance: cần --yf-ticker.",
    )
    p.add_argument("--yf-ticker", help="Ticker Yahoo khi --market yfinance")
    p.add_argument("--market-csv", help="CSV OHLCV khi --market csv")
    p.add_argument("--vnindex-symbol", default="VNINDEX")
    p.add_argument("--vnstock-source", default="VCI")
    p.add_argument(
        "--macro",
        choices=("auto", "csv", "official"),
        default="auto",
        help="auto: Yahoo FX + World Bank. csv/official: cần --macro-csv",
    )
    p.add_argument("--macro-csv", help="CSV vĩ mô (--macro csv|official)")
    p.add_argument("--yfinance-fx", default="USDVND=X")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Thư mục cache (mặc định: ./data/cache hoặc RISK_DASHBOARD_CACHE)",
    )
    p.add_argument(
        "--sqlite",
        type=Path,
        default=None,
        help="Ghi registry SQLite (mặc định: data/db/northstar.db nếu có --register-db)",
    )
    p.add_argument(
        "--register-db",
        action="store_true",
        help="Đăng ký vào SQLite (đường dẫn --sqlite hoặc mặc định)",
    )

    args = p.parse_args()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    paths = PipelinePaths.defaults(Path.cwd())
    out_dir = (args.out or paths.cache_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    sqlite_path: Path | None = None
    if args.register_db:
        sqlite_path = (args.sqlite or paths.sqlite_path).resolve()
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    if args.market == "csv" and not args.market_csv:
        p.error("--market csv cần --market-csv")
    if args.market == "yfinance" and not args.yf_ticker:
        p.error("--market yfinance cần --yf-ticker")
    if args.macro in ("csv", "official") and not args.macro_csv:
        p.error(f"--macro {args.macro} cần --macro-csv")

    try:
        result = materialize_training_panel(
            start=start,
            end=end,
            output_dir=out_dir,
            market_mode=args.market,
            macro_mode=args.macro,
            register_sqlite=sqlite_path,
            csv_path=args.market_csv,
            vnindex_symbol=args.vnindex_symbol,
            vnstock_source=args.vnstock_source,
            yfinance_ticker=args.yf_ticker,
            macro_csv_path=args.macro_csv,
            yfinance_fx_ticker=args.yfinance_fx,
        )
    except Exception as e:
        print(f"Lỗi ingest: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {result.n_rows} dòng")
    print(f"Parquet: {result.parquet_path}")
    print(f"Manifest: {result.manifest_path}")
    if sqlite_path:
        print(f"SQLite: {sqlite_path}")


if __name__ == "__main__":
    main()
