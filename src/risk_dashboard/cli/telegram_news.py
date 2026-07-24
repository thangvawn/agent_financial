from __future__ import annotations

import argparse
import json

from dotenv import load_dotenv

from risk_dashboard.modules.news_intelligence.application.telegram_digest import (
    TelegramDigestConfig,
    TelegramDigestService,
)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Send Northstar News digests to Telegram")
    parser.add_argument("action", choices=("test", "day", "week", "month"))
    parser.add_argument("--force", action="store_true", help="Ignore delivery deduplication")
    args = parser.parse_args()

    config = TelegramDigestConfig.from_env()
    if config is None:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first.")
    service = TelegramDigestService(config)
    result = service.send_test() if args.action == "test" else service.send_digest(
        args.action,
        force=args.force,
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
