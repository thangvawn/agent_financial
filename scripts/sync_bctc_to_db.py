#!/usr/bin/env python3
"""Sync financial statements (BCTC) directly into Northstar SQLite database.

Replaces third-party vnstock dependency with direct, high-speed multi-threaded
ingestion into `company_financial_datasets` and `company_financial_periods`.

Usage:
    python scripts/sync_bctc_to_db.py --ticker HPG
    python scripts/sync_bctc_to_db.py --tickers HPG,VHM,VCB,FPT,SSI
    python scripts/sync_bctc_to_db.py --vn30
    python scripts/sync_bctc_to_db.py --status
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from risk_dashboard.data.financials import get_financial_dataset
from risk_dashboard.platform.database.connection import connect_db

VN30_TICKERS = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]


def show_database_status() -> None:
    conn = connect_db()
    rows = conn.execute(
        """
        SELECT ticker, periods_count, latest_period, latest_revenue, latest_net_income, updated_at
        FROM company_financial_datasets
        ORDER BY updated_at DESC
        """
    ).fetchall()

    if not rows:
        print("Chưa có mã cổ phiếu nào được lưu trong bảng `company_financial_datasets`.")
        return

    print(f"\n{'='*75}")
    print(f"{'MÃ':<6} | {'KỲ':<4} | {'KỲ GẦN NHẤT':<12} | {'DOANH THU (TỶ)':<16} | {'LNST (TỶ)':<14} | {'CẬP NHẬT'}")
    print(f"{'-'*75}")
    for r in rows:
        rev_bil = f"{r['latest_revenue'] / 1e9:,.1f}" if r['latest_revenue'] else "N/A"
        ni_bil = f"{r['latest_net_income'] / 1e9:,.1f}" if r['latest_net_income'] else "N/A"
        updated = str(r['updated_at'])[:19]
        print(f"{r['ticker']:<6} | {r['periods_count']:<4} | {r['latest_period'] or 'N/A':<12} | {rev_bil:<16} | {ni_bil:<14} | {updated}")
    print(f"{'='*75}")
    print(f"Tổng cộng: {len(rows)} doanh nghiệp trong Database.\n")


def sync_ticker(ticker: str, *, refresh: bool = True) -> bool:
    ticker = ticker.upper().strip()
    t0 = time.time()
    try:
        dataset = get_financial_dataset(ticker, refresh=refresh)
        elapsed = time.time() - t0
        latest = dataset.periods[-1] if dataset.periods else None
        rev_str = f"{latest.revenue / 1e9:,.0f} tỷ" if (latest and latest.revenue) else "N/A"
        ni_str = f"{latest.net_income / 1e9:,.0f} tỷ" if (latest and latest.net_income) else "N/A"
        print(f"  [OK] {ticker:<5} | {len(dataset.periods):>2} quý | Kỳ mới nhất: {latest.period if latest else 'N/A':<7} | DThu: {rev_str:<12} | LNST: {ni_str:<10} | {elapsed:.2f}s ({dataset.source})")
        return True
    except Exception as exc:
        elapsed = time.time() - t0
        print(f"  [LỖI] {ticker:<4} | Thất bại sau {elapsed:.2f}s: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Đồng bộ Báo cáo tài chính (BCTC) vào SQLite Database")
    parser.add_argument("--ticker", type=str, help="Mã cổ phiếu cần kéo BCTC (VD: HPG)")
    parser.add_argument("--tickers", type=str, help="Danh sách mã cách nhau bằng dấu phẩy (VD: HPG,VHM,VCB,FPT)")
    parser.add_argument("--vn30", action="store_true", help="Kéo toàn bộ 30 mã trong rổ VN30")
    parser.add_argument("--status", action="store_true", help="Xem danh sách các mã đã có trong Database")
    parser.add_argument("--no-refresh", action="store_true", help="Dùng cache nếu có, không ép tải mới")

    args = parser.parse_args()

    if args.status:
        show_database_status()
        return

    tickers: list[str] = []
    if args.ticker:
        tickers = [args.ticker.strip()]
    elif args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    elif args.vn30:
        tickers = VN30_TICKERS
    else:
        # Default prompt status if no args
        print("Chọn một tùy chọn:")
        print("  --ticker <MÃ>     : Kéo 1 mã cụ thể")
        print("  --tickers <MÃ...> : Kéo nhiều mã")
        print("  --vn30            : Kéo toàn bộ VN30")
        print("  --status          : Xem thống kê database")
        show_database_status()
        return

    print(f"\n[BCTC Sync] Bắt đầu đồng bộ BCTC vào SQLite (`northstar.db`) cho {len(tickers)} mã...")
    refresh = not args.no_refresh
    t_start = time.time()
    success_count = 0

    for idx, ticker in enumerate(tickers, start=1):
        print(f"[{idx}/{len(tickers)}] Đang xử lý {ticker}...")
        if sync_ticker(ticker, refresh=refresh):
            success_count += 1
        # Gentle pacing between requests
        time.sleep(0.1)

    total_time = time.time() - t_start
    print(f"\n[BCTC Sync Hoàn tất] Thành công {success_count}/{len(tickers)} mã trong {total_time:.2f}s!")
    show_database_status()


if __name__ == "__main__":
    main()
