"""CLI entrypoint for Daily Micro-Learning Telegram Push."""

from __future__ import annotations

import argparse
import logging
import sys
from dotenv import load_dotenv

from risk_dashboard.modules.learning.application.query_handler import DEFAULT_LEARNING_CARDS, render_learning_card
from risk_dashboard.modules.learning.infrastructure.delivery_repository import LearningDeliveryRepository
from risk_dashboard.platform.telegram import TelegramClient, TelegramConfig

logger = logging.getLogger("risk_dashboard.telegram_learn")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Daily Micro-Learning Telegram Card Push CLI")
    parser.add_argument("--daily-card", action="store_true", help="Send daily micro-learning card push")
    parser.add_argument("--dry-run", action="store_true", help="Render card without sending via Telegram API")
    parser.add_argument("--force", action="store_true", help="Bypass delivery deduplication check")
    parser.add_argument("--chat-id", type=str, default=None, help="Target Chat ID override")
    parser.add_argument("--user-id", type=str, default="default_user", help="Target User ID")
    parser.add_argument("--output", type=str, default=None, help="Save HTML output to specified file path")

    args = parser.parse_args()

    config = TelegramConfig.from_env()
    target_chat_id = args.chat_id or (config.learn_chat_id if config else None) or "default_chat"
    if not args.dry_run and (not config or not config.bot_token):
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_LEARN_CHAT_ID is missing.")
        sys.exit(1)

    repo = LearningDeliveryRepository()
    card = DEFAULT_LEARNING_CARDS[0]

    if not args.force and repo.is_delivered(target_chat_id, args.user_id, card.card_id):
        print(f"Skipped: Daily card '{card.card_id}' already delivered to chat {target_chat_id} user {args.user_id}")
        return

    sections = render_learning_card(card)
    content = sections[0]

    if args.dry_run:
        print("Status: dry_run_success")
        print("\n--- RENDERED LEARNING CARD ---\n")
        print(content)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Output saved to {args.output}")
        return

    client = TelegramClient(token=config.bot_token, chat_id=target_chat_id)
    res = client.send_message(chat_id=target_chat_id, text=content)
    repo.record_delivery(chat_id=target_chat_id, user_id=args.user_id, card_id=card.card_id, telegram_message_id=res.message_id)
    print(f"Status: sent, message_id: {res.message_id}")


if __name__ == "__main__":
    main()
