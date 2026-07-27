"""CLI entrypoint for BCTC Financial Report Telegram Alert & Digest Push."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dotenv import load_dotenv

from risk_dashboard.modules.financials_product.application.query_handler import (
    MOCK_BCTC_DATABASE,
    render_financial_snapshot,
)
from risk_dashboard.modules.financials_product.infrastructure.delivery_repository import FinancialsDeliveryRepository
from risk_dashboard.platform.telegram import TelegramClient, TelegramConfig

logger = logging.getLogger("risk_dashboard.telegram_bctc")


def get_watchlist() -> list[str]:
    raw = os.getenv("TELEGRAM_BCTC_WATCHLIST", "FPT,HPG,VNM,VCB").strip()
    return [t.strip().upper() for t in raw.split(",") if t.strip()]


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="BCTC Financial Report Telegram Push CLI")
    parser.add_argument("--ticker", type=str, default=None, help="Target stock ticker symbol (e.g. FPT)")
    parser.add_argument("--daily-digest", action="store_true", help="Send daily 20:00 BCTC summary digest")
    parser.add_argument("--dry-run", action="store_true", help="Render snapshot without sending via Telegram API")
    parser.add_argument("--force", action="store_true", help="Bypass delivery deduplication check")
    parser.add_argument("--chat-id", type=str, default=None, help="Target Chat ID override")
    parser.add_argument("--output", type=str, default=None, help="Save HTML output to specified file path")

    args = parser.parse_args()

    config = TelegramConfig.from_env()
    target_chat_id = args.chat_id or (config.bctc_chat_id if config else None) or "default_chat"
    if not args.dry_run and (not config or not config.bot_token):
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_BCTC_CHAT_ID is missing.")
        sys.exit(1)

    repo = FinancialsDeliveryRepository()
    watchlist = [args.ticker.upper()] if args.ticker else get_watchlist()

    snapshots = [MOCK_BCTC_DATABASE[t] for t in watchlist if t in MOCK_BCTC_DATABASE]
    if not snapshots:
        print(f"Skipped: No BCTC data found for requested tickers: {watchlist}")
        return

    snapshot = snapshots[0]

    if not args.force and repo.is_delivered(snapshot.ticker, snapshot.report_period, chat_id=target_chat_id):
        print(f"Skipped: BCTC '{snapshot.ticker}' ({snapshot.report_period}) already delivered to chat {target_chat_id}")
        return

    sections = render_financial_snapshot(snapshot)
    content = sections[0]

    if args.dry_run:
        print("Status: dry_run_success")
        print("\n--- RENDERED BCTC SNAPSHOT ---\n")
        print(content)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Output saved to {args.output}")
        return

    client = TelegramClient(token=config.bot_token, chat_id=target_chat_id)
    res = client.send_message(chat_id=target_chat_id, text=content)
    repo.record_delivery(
        ticker=snapshot.ticker,
        report_period=snapshot.report_period,
        chat_id=target_chat_id,
        telegram_message_id=res.message_id,
    )
    print(f"Status: sent, message_id: {res.message_id}")


if __name__ == "__main__":
    main()
