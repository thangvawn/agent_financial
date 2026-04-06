from __future__ import annotations

import argparse
from datetime import date

from risk_dashboard.data.ingest import run_ingest_to_parquet
from risk_dashboard.data.macro_auto import AutoMacroSource
from risk_dashboard.data.macro_connector import CsvMacroSource
from risk_dashboard.data.macro_official import OfficialCsvMacroSource
from risk_dashboard.data.market_connector import CsvMarketSource, VnstockMarketSource


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest daily index + monthly macro → Parquet")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--output-dir", default="./data_outputs", help="Thư mục ghi Parquet + manifest")
    p.add_argument(
        "--market",
        choices=("vnstock", "csv"),
        default="csv",
        help="vnstock: tải qua thư viện vnstock (cần cài). csv: đọc file OHLCV",
    )
    p.add_argument("--market-csv", help="Đường dẫn CSV thị trường khi --market csv")
    p.add_argument(
        "--macro-csv",
        help="CSV vĩ mô chuẩn cột (period_end, ...). Không dùng cùng --macro-auto / --macro-official-csv.",
    )
    p.add_argument(
        "--macro-official-csv",
        help="CSV vĩ mô tên cột linh hoạt (GSO/SBV) — xem risk_dashboard.data.macro_official.",
    )
    p.add_argument(
        "--macro-auto",
        action="store_true",
        help="Tự động: tỷ giá yfinance + CPI/lãi/FDI proxy (World Bank). Cần pip install -e '.[auto]'.",
    )
    p.add_argument(
        "--yfinance-fx-ticker",
        default="USDVND=X",
        help="Ticker Yahoo cho tỷ giá khi --macro-auto (mặc định USDVND=X).",
    )
    p.add_argument("--vnindex-symbol", default="VNINDEX", help="Mã chỉ số cho vnstock")
    p.add_argument("--vnstock-source", default="VCI", help="Nguồn vnstock (VCI, KBS, ...)")

    args = p.parse_args()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    modes = sum(
        bool(x)
        for x in (args.macro_auto, args.macro_csv, args.macro_official_csv)
    )
    if modes != 1:
        p.error("Chọn đúng một: --macro-auto HOẶC --macro-csv HOẶC --macro-official-csv")

    if args.market == "csv":
        if not args.market_csv:
            p.error("--market-csv là bắt buộc khi --market csv")
        market = CsvMarketSource(args.market_csv)
        mlabel = f"csv:{args.market_csv}"
    else:
        market = VnstockMarketSource(symbol=args.vnindex_symbol, source=args.vnstock_source)
        mlabel = f"vnstock:{args.vnindex_symbol}:{args.vnstock_source}"

    if args.macro_auto:
        macro = AutoMacroSource(yfinance_ticker=args.yfinance_fx_ticker)
        macro_label = f"auto:yfinance:{args.yfinance_fx_ticker}+worldbank"
    elif args.macro_official_csv:
        macro = OfficialCsvMacroSource(args.macro_official_csv)
        macro_label = f"official:{args.macro_official_csv}"
    else:
        macro = CsvMacroSource(args.macro_csv)
        macro_label = f"csv:{args.macro_csv}"

    pq, mj = run_ingest_to_parquet(
        market,
        macro,
        start,
        end,
        args.output_dir,
        market_label=mlabel,
        macro_label=macro_label,
    )
    print(f"Wrote {pq}")
    print(f"Wrote {mj}")


if __name__ == "__main__":
    main()
