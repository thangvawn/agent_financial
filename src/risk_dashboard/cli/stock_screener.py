"""Manage EOD screener inputs without touching the user database.

python -m risk_dashboard.cli.stock_screener --import-bundle FILE --cache-dir DIR --quotes FILE
python -m risk_dashboard.cli.stock_screener --collect --cache-dir DIR --quotes FILE
python -m risk_dashboard.cli.stock_screener --build --cache-dir DIR --quotes FILE
"""

import argparse
import json
from pathlib import Path

from risk_dashboard.modules.data_hub.application.screener_job import collect, import_bundle
from risk_dashboard.modules.data_hub.application.stock_screener import StockScreenerService
from risk_dashboard.modules.data_hub.infrastructure.screener_store import ScreenerStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--quotes", required=True, type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--import-bundle", type=Path)
    group.add_argument("--collect", action="store_true")
    group.add_argument("--build", action="store_true")
    args = parser.parse_args()
    store = ScreenerStore(args.cache_dir)
    quotes = json.loads(args.quotes.read_text()).get("items", [])
    if args.import_bundle:
        import_bundle(json.loads(args.import_bundle.read_text()), store)
    if args.collect:
        result = collect(lambda: quotes, store)
    else:
        snap = StockScreenerService(store).rebuild(quotes)
        result = {
            k: snap[k]
            for k in (
                "snapshot_id",
                "formula_version",
                "as_of",
                "session_verified",
                "universe_total",
                "eligibility_counts",
            )
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
