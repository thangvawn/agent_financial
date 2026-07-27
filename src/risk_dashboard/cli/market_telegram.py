"""CLI entrypoint for Market Summary Telegram Bot execution."""

from __future__ import annotations

import argparse
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

from risk_dashboard.modules.market_summary.application.runner import MarketSummaryRunner
from risk_dashboard.modules.market_summary.infrastructure.data_provider import FixtureMarketDataProvider, VnstockMarketDataProvider
from risk_dashboard.modules.market_summary.domain.trading_calendar import FixtureTradingCalendar

logger = logging.getLogger("risk_dashboard.market_telegram")


def main() -> None:
    # Auto load .env from workspace root
    load_dotenv()

    parser = argparse.ArgumentParser(description="Daily Market Summary Telegram Bot CLI")
    parser.add_argument("--mode", choices=["fast", "analytical"], default="analytical", help="Report mode (fast|analytical)")
    parser.add_argument("--date", type=str, default=None, help="Target date in YYYY-MM-DD format")
    parser.add_argument("--force", action="store_true", help="Bypass deduplication check")
    parser.add_argument("--dry-run", action="store_true", help="Run end-to-end without calling Telegram API")
    parser.add_argument("--no-llm", action="store_true", help="Use deterministic template (skip LLM synthesis)")
    parser.add_argument("--allow-incomplete-data", action="store_true", help="Force report generation even if data is incomplete")
    parser.add_argument("--use-fixture-provider", action="store_true", help="Use fixture mock provider for offline demo")
    parser.add_argument("--allow-fixture-delivery", action="store_true", help="Explicitly allow live Telegram delivery when using fixture data")
    parser.add_argument("--output", type=str, default=None, help="Save HTML output to specified file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    target_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else None

    # Determine provider and calendar
    if args.use_fixture_provider:
        provider = FixtureMarketDataProvider(base_date=target_date)
        calendar = FixtureTradingCalendar()
    else:
        provider = VnstockMarketDataProvider()
        calendar = None

    runner = MarketSummaryRunner(
        data_provider=provider,
        trading_calendar=calendar,
    )

    try:
        result = runner.run(
            target_date=target_date,
            mode=args.mode,
            force=args.force,
            dry_run=args.dry_run,
            allow_incomplete_data=args.allow_incomplete_data,
            allow_fixture_delivery=args.allow_fixture_delivery,
        )

        print(f"Status: {result.get('status')}")
        if result.get("reason"):
            print(f"Reason: {result.get('reason')}")

        if args.dry_run and result.get("rendered_html"):
            html_content = result["rendered_html"]
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"HTML output saved to {args.output}")
            else:
                print("\n--- RENDERED TELEGRAM HTML ---\n")
                print(html_content)

    except Exception as exc:
        logger.error(f"Execution failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
