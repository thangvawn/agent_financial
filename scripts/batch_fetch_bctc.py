"""Batch-fetch BCTC for all major Vietnamese tickers with rate-limit handling."""
from __future__ import annotations

import argparse
import sys
import time

sys.path.insert(0, "src")

from risk_dashboard.data.financials import (
    FinancialDataError,
    get_financial_dataset,
    load_cached_financial_dataset,
)

CORE_TICKERS = [
    # VN30 core
    "VCB", "BID", "CTG", "TCB", "MBB", "ACB", "VPB", "HDB", "TPB", "STB",
    "FPT", "VNM", "HPG", "VIC", "VHM", "MSN", "MWG", "SAB", "GAS", "PLX",
    "VRE", "SSI", "VND", "HCM", "POW", "BCM", "GVR", "SHB", "SSB", "LPB",
    # Large-cap / sector leaders
    "PNJ", "REE", "DGC", "KDH", "NLG", "VJC", "HVN", "PHR", "DPM", "DCM",
    "PVD", "PVS", "BSR", "ORS", "KBC", "IJC", "DXG", "PDR", "NVL", "HDG",
    "GMD", "HAH", "VTP", "CTR", "FOX", "VGI", "CMG", "ELC", "DHC", "HSG",
    "NKG", "TLG", "SZC", "PC1", "NT2", "VSH", "BWE", "EVF",
    # Banks
    "OCB", "MSB", "EIB", "KLB", "BAB", "ABB", "NAB", "VIB", "BVH",
    # Consumer / Retail / Construction
    "DGW", "FRT", "VGC", "VCG", "HBC",
]

EXTENDED_TICKERS = [
    # Real estate / industrial parks / construction
    "AGG", "CEO", "CII", "CRE", "DIG", "DPG", "HDC", "HUT", "L14", "LDG",
    "SCR", "TCH", "VPI", "DTD", "IDC", "KOS", "LHG", "SIP", "SJS",
    # Materials / steel / chemicals / agriculture
    "AAA", "BMP", "CSV", "DHA", "DRC", "GEX", "GIL", "HAX", "IMP", "LAS",
    "PCH", "PLC", "PTB", "QNS", "SBT", "SFG", "TNG", "VCS", "VHC",
    # Consumer / retail / logistics / aviation
    "ANV", "ASM", "BHN", "DBC", "DBC", "DHC", "DPR", "FMC", "GIL", "HAG",
    "KDC", "MCH", "MPC", "PET", "SCS", "SGN", "SKG", "VHC", "VSC",
    # Financial services / banks / insurers
    "AAS", "AGR", "APG", "BSI", "CTS", "FTS", "MBS", "SHS", "VCI",
    # Utilities / energy / infrastructure
    "CHP", "GEG", "GSP", "HND", "PPC", "PVB", "QTP", "SJD", "TDM",
]

TICKERS = list(dict.fromkeys(CORE_TICKERS + EXTENDED_TICKERS))

BATCH_SIZE = 3      # 3 tickers = 9 API calls (income+balance+cashflow)
BATCH_PAUSE = 65    # seconds between batches (vnstock guest: 20 req/min)
MAX_RETRIES = 2


def fetch_one(ticker: str) -> tuple[bool, str]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ds = get_financial_dataset(ticker, refresh=True)
            return True, f"{len(ds.periods)} periods, src={ds.source}"
        except FinancialDataError as exc:
            msg = str(exc)
            if "rate limit" in msg.lower() or "giới hạn" in msg.lower():
                wait = 70
                print(f"    Rate limited on {ticker}, waiting {wait}s (attempt {attempt})...")
                sys.stdout.flush()
                time.sleep(wait)
                continue
            return False, msg
        except Exception as exc:
            msg = str(exc)
            if "rate limit" in msg.lower() or "giới hạn" in msg.lower():
                wait = 70
                print(f"    Rate limited on {ticker}, waiting {wait}s (attempt {attempt})...")
                sys.stdout.flush()
                time.sleep(wait)
                continue
            return False, msg
    return False, "Max retries exceeded (rate limit)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-fetch BCTC and write normalized JSON cache.")
    parser.add_argument("--tickers", default="", help="Comma-separated ticker override. Default: core + extended universe.")
    parser.add_argument("--limit", type=int, default=0, help="Fetch at most N uncached tickers in this run.")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--pause", type=int, default=BATCH_PAUSE, help="Seconds between batches.")
    parser.add_argument("--refresh-existing", action="store_true", help="Refresh cached tickers too.")
    args = parser.parse_args()

    universe = [t.strip().upper() for t in args.tickers.split(",") if t.strip()] if args.tickers else TICKERS
    universe = list(dict.fromkeys(universe))
    already = [t for t in universe if load_cached_financial_dataset(t) is not None]
    todo = list(universe) if args.refresh_existing else [t for t in universe if t not in already]
    if args.limit and args.limit > 0:
        todo = todo[:args.limit]

    print(f"Already cached: {len(already)} tickers")
    print(f"Need to fetch:  {len(todo)} tickers")
    print(f"Universe size:   {len(universe)} tickers")
    print(f"Batch size: {args.batch_size}, pause: {args.pause}s")
    n_batches = (len(todo) + args.batch_size - 1) // args.batch_size
    est_min = n_batches * args.pause / 60
    print(f"Estimated time: ~{est_min:.0f} minutes ({n_batches} batches)")
    print()
    sys.stdout.flush()

    ok = list(already)
    fail: list[tuple[str, str]] = []
    fetched_in_batch = 0

    for i, ticker in enumerate(todo):
        success, detail = fetch_one(ticker)
        total_done = len(ok) + len(fail) + 1

        if success:
            ok.append(ticker)
            print(f"[{total_done}/{len(universe)}] {ticker}: OK ({detail})")
        else:
            fail.append((ticker, detail))
            print(f"[{total_done}/{len(universe)}] {ticker}: FAIL — {detail}")
        sys.stdout.flush()

        fetched_in_batch += 1
        if fetched_in_batch >= args.batch_size and i < len(todo) - 1:
            fetched_in_batch = 0
            print(f"  >> Pausing {args.pause}s for rate limit... ({len(ok)} OK so far)")
            sys.stdout.flush()
            time.sleep(args.pause)

    print(f"\n{'='*60}")
    print(f"DONE: {len(ok)} OK, {len(fail)} FAIL out of {len(universe)}")
    print(f"OK:   {sorted(ok)}")
    if fail:
        print(f"\nFailed ({len(fail)}):")
        for t, r in fail:
            print(f"  {t}: {r}")


if __name__ == "__main__":
    main()
