"""Script to download and export full Financial Statements (BCTC) for VN stocks.

Usage:
    .venv/bin/python scripts/fetch_bctc.py FPT
    .venv/bin/python scripts/fetch_bctc.py FPT VNM HPG
    .venv/bin/python scripts/fetch_bctc.py --vn30
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd

from risk_dashboard.data.financials import get_financial_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORTS_DIR = PROJECT_ROOT / "data" / "financials" / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

VN30_TICKERS = [
    "ACB", "BCM", "BID", "BSR", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB",
    "HPG", "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI",
    "STB", "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB",
]


def fetch_and_export_bctc(ticker: str, period: str = "quarter") -> dict[str, str | None]:
    ticker = ticker.upper().strip()
    print(f"\n=======================================================")
    print(f"📊 Đang tải BCTC cho mã: {ticker} (kỳ: {period})...")
    print(f"=======================================================")

    # 1. Update project native dataset cache
    try:
        ds = get_financial_dataset(ticker, refresh=True)
        print(f"  ✓ Đã cập nhật cache hệ thống ({len(ds.periods)} kỳ lịch sử).")
    except Exception as exc:
        print(f"  ⚠ Cảnh báo cache: {exc}")

    def raw_statement_to_df(statement_dict: dict) -> pd.DataFrame:
        if not statement_dict or "rows" not in statement_dict:
            return pd.DataFrame()
        periods = statement_dict.get("periods", [])
        rows = []
        for r in statement_dict.get("rows", []):
            row_dict = {
                "Chỉ tiêu": r.get("label"),
                "Tiếng Anh": r.get("label_en") or "",
            }
            val_map = {v["period"]: v["value"] for v in r.get("values", [])}
            # Latest periods first
            for p in reversed(periods):
                row_dict[p] = val_map.get(p)
            rows.append(row_dict)
        return pd.DataFrame(rows)

    is_df = raw_statement_to_df(ds.raw_statements.get("income", {}))
    bs_df = raw_statement_to_df(ds.raw_statements.get("balance", {}))
    cf_df = raw_statement_to_df(ds.raw_statements.get("cash_flow", {}))

    # 2. Export to multi-sheet Excel
    excel_path = EXPORTS_DIR / f"{ticker}_BCTC_{period}.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        if not is_df.empty:
            is_df.to_excel(writer, sheet_name="KetQuaKinhDoanh", index=False)
        if not bs_df.empty:
            bs_df.to_excel(writer, sheet_name="CanDoiKeToan", index=False)
        if not cf_df.empty:
            cf_df.to_excel(writer, sheet_name="LuuChuyenTienTe", index=False)

    print(f"  ✓ Đã xuất file Excel đầy đủ ({len(ds.periods)} kỳ): {excel_path.relative_to(PROJECT_ROOT)}")

    # 4. Print quick summary of latest metrics if available
    try:
        if is_df is not None and not is_df.empty and "item" in is_df.columns:
            rev_row = is_df[is_df["item"].str.contains("Doanh thu thuần", case=False, na=False)]
            profit_row = is_df[is_df["item"].str.contains("Lợi nhuận sau thuế của cổ đông|Lợi nhuận sau thuế", case=False, na=False)]
            
            period_cols = [c for c in is_df.columns if c not in ("item", "item_en", "item_id")][:4]
            if period_cols:
                print("\n  [Tóm tắt số liệu kinh doanh gần nhất]")
                print(f"  {'Chỉ tiêu':<25} | " + " | ".join(f"{str(c):>12}" for c in period_cols))
                print("  " + "-" * 75)
                if not rev_row.empty:
                    vals = [f"{rev_row.iloc[0].get(c, 0)/1e9:>12.1f}" if pd.notna(rev_row.iloc[0].get(c)) else "          N/A" for c in period_cols]
                    print(f"  {'Doanh thu (tỷ VND)':<25} | " + " | ".join(vals))
                if not profit_row.empty:
                    vals = [f"{profit_row.iloc[0].get(c, 0)/1e9:>12.1f}" if pd.notna(profit_row.iloc[0].get(c)) else "          N/A" for c in period_cols]
                    print(f"  {'LNST (tỷ VND)':<25} | " + " | ".join(vals))
    except Exception as exc:
        pass

    return {
        "ticker": ticker,
        "excel": str(excel_path),
        "cache": f"data/financials/cache/{ticker}.json",
    }


def main():
    parser = argparse.ArgumentParser(description="Tải và xuất Báo cáo tài chính (BCTC) các mã cổ phiếu VN.")
    parser.add_argument("tickers", nargs="*", default=["FPT"], help="Danh sách mã cổ phiếu (ví dụ: FPT VNM HPG)")
    parser.add_argument("--period", choices=["quarter", "year"], default="quarter", help="Kỳ báo cáo: quarter (quý) hoặc year (năm)")
    parser.add_argument("--vn30", action="store_true", help="Tải toàn bộ 30 mã trong rổ VN30")

    args = parser.parse_args()

    target_tickers = VN30_TICKERS if args.vn30 else args.tickers

    print(f">>> Bắt đầu tải BCTC cho {len(target_tickers)} mã: {', '.join(target_tickers[:10])}{'...' if len(target_tickers)>10 else ''}")
    for ticker in target_tickers:
        fetch_and_export_bctc(ticker, period=args.period)

    print("\n🎉 Hoàn thành tải BCTC! Tất cả file Excel đã sẵn sàng tại data/financials/exports/.")


if __name__ == "__main__":
    main()
