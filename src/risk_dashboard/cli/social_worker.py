"""Run the same durable Social queue in a separate process."""

from __future__ import annotations

import argparse
import json
import time

from risk_dashboard.modules.news_intelligence.application.social_worker import (
    run_once,
    schedule_due,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    while True:
        schedule_due()
        result = run_once()
        if result:
            print(json.dumps(result), flush=True)
        if args.once:
            break
        if not result:
            time.sleep(5)


if __name__ == "__main__":
    main()
