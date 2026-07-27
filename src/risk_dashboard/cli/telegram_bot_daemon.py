"""Telegram Bot Daemon process for long-polling and interactive command routing."""

from __future__ import annotations

import argparse
import fcntl
import logging
import os
import signal
import sys
import time
from typing import Any
from dotenv import load_dotenv

from risk_dashboard.modules.financials_product.application.query_handler import FinancialsTelegramQueryHandler
from risk_dashboard.modules.learning.application.query_handler import LearningTelegramQueryHandler
from risk_dashboard.modules.learning.application.quiz_handler import QuizTelegramHandler
from risk_dashboard.modules.market_summary.application.query_handler import MarketTelegramQueryHandler
from risk_dashboard.modules.news_intelligence.application.query_handler import NewsTelegramQueryHandler
from risk_dashboard.platform.telegram import (
    TelegramAccessControl,
    TelegramClient,
    TelegramClientError,
    TelegramCommandRouter,
    TelegramConfig,
    TelegramUpdateReceiver,
    TelegramUpdateRepository,
)
from risk_dashboard.platform.telegram.command_parser import ParsedCommand, parse_update

from pathlib import Path

logger = logging.getLogger("risk_dashboard.telegram_bot_daemon")


class DaemonLockError(Exception):
    pass


def get_lock_file_path() -> Path:
    env_path = os.getenv("TELEGRAM_DAEMON_LOCK_FILE", "var/run/telegram_bot_daemon.lock").strip()
    path = Path(env_path).expanduser()
    if not path.is_absolute():
        project_root = Path(__file__).resolve().parents[3]
        path = project_root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def acquire_singleton_lock() -> Any:
    lock_path = get_lock_file_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        return lock_file
    except (IOError, OSError):
        raise DaemonLockError(f"Another Telegram update consumer is active ({lock_path}).")


class TelegramBotDaemon:
    def __init__(
        self,
        config: TelegramConfig,
        client: TelegramClient | None = None,
        receiver: TelegramUpdateReceiver | None = None,
        repository: TelegramUpdateRepository | None = None,
        access_control: TelegramAccessControl | None = None,
        router: TelegramCommandRouter | None = None,
    ) -> None:
        self.config = config
        self.client = client or TelegramClient(token=config.bot_token, chat_id=config.default_chat_id)
        self.receiver = receiver or TelegramUpdateReceiver(token=config.bot_token)
        self.repository = repository or TelegramUpdateRepository()
        self.access_control = access_control or TelegramAccessControl()
        self.router = router or TelegramCommandRouter()
        self.running = True

        # Register handlers for all 4 modules (Market, News, Learn, BCTC)
        market_query_handler = MarketTelegramQueryHandler()
        news_query_handler = NewsTelegramQueryHandler()
        learning_query_handler = LearningTelegramQueryHandler()
        financials_query_handler = FinancialsTelegramQueryHandler()
        self.quiz_handler = QuizTelegramHandler()

        self.router.register("/market", market_query_handler.handle)
        self.router.register("/news", news_query_handler.handle)
        self.router.register("/learn", learning_query_handler.handle)
        self.router.register("/bctc", financials_query_handler.handle)
        self.router.register("/quiz", self.quiz_handler.handle_command)
        self.router.register("/callback", self._handle_callback)

    def _handle_callback(self, cmd: ParsedCommand) -> list[str]:
        if cmd.callback_data and cmd.callback_data.startswith("quiz:"):
            return self.quiz_handler.handle_callback(cmd)
        return ["⚠️ Callback không được hỗ trợ."]

    def stop(self) -> None:
        logger.info("Stopping Telegram Bot Daemon...")
        self.running = False

    def run_once(self) -> int:
        """Polls and processes one batch of updates. Returns count of processed updates."""
        offset = self.repository.get_next_offset()
        updates = self.receiver.get_updates(offset=offset, poll_timeout=2)
        processed_count = 0

        for update in updates:
            parsed = parse_update(update)
            if not parsed:
                continue

            update_id = parsed.update_id
            if self.repository.is_processed(update_id):
                logger.debug(f"Skipping already processed update_id={update_id}")
                continue

            logger.info(
                f"Processing update_id={update_id}: command={parsed.command}, cb_id={parsed.callback_query_id}, "
                f"chat_id={parsed.chat_id}, user_id={parsed.user_id}, text='{parsed.text}'"
            )

            self.repository.record_received(
                update_id=update_id,
                chat_id=parsed.chat_id,
                user_id=parsed.user_id,
                command=parsed.command,
            )

            # Check access control
            if parsed.command and not self.access_control.check_access(
                parsed.command, parsed.chat_id, parsed.user_id
            ):
                logger.warning(
                    f"Access DENIED for command {parsed.command} from user {parsed.user_id} in chat {parsed.chat_id}"
                )
                self.repository.mark_status(update_id, "access_denied")
                try:
                    self.client.send_message(
                        chat_id=parsed.chat_id,
                        text="⛔ <b>Bạn không có quyền truy cập lệnh này.</b>",
                    )
                except Exception:
                    pass

                if parsed.callback_query_id:
                    try:
                        self.client.answer_callback_query(
                            parsed.callback_query_id,
                            text="⛔ Bạn không có quyền truy cập lệnh này.",
                        )
                    except Exception:
                        pass
                continue

            self.repository.mark_status(update_id, "processing")
            try:
                responses, reply_markup = self.router.dispatch(parsed)
                logger.info(
                    f"Dispatched command {parsed.command} for update_id={update_id}: "
                    f"responses_count={len(responses)}, reply_markup={reply_markup is not None}"
                )
                for text in responses:
                    res = self.client.send_message(
                        chat_id=parsed.chat_id,
                        text=text,
                        reply_markup=reply_markup,
                    )
                    logger.info(f"Sent response message_id={res.message_id} to chat_id={parsed.chat_id}")

                if parsed.callback_query_id:
                    first_resp = responses[0] if responses else ""
                    import re
                    clean_toast = re.sub(r"<[^>]+>", "", first_resp.split("\n")[0]).strip()
                    logger.info(f"Answering callback_query cb_id={parsed.callback_query_id} with toast='{clean_toast}'")
                    try:
                        ok = self.client.answer_callback_query(parsed.callback_query_id, text=clean_toast[:200])
                        logger.info(f"answer_callback_query result: ok={ok}")
                    except Exception as err:
                        logger.error(f"Error calling answer_callback_query: {err}")

                self.repository.mark_status(update_id, "processed")
                processed_count += 1
            except Exception as exc:
                logger.error(f"Error processing update {update_id}: {exc}")
                self.repository.mark_status(update_id, "failed_terminal", error=str(exc))

        return processed_count

    def start(self) -> None:
        logger.info("Starting Telegram Bot Daemon...")
        self.receiver.check_webhook_conflict()

        # Signal handlers for graceful shutdown
        def handle_signal(sig, frame):
            self.stop()

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        logger.info("Daemon is polling for inbound updates. Press Ctrl+C to exit.")
        while self.running:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Unexpected error in polling loop: {e}")
                time.sleep(2.0)
            time.sleep(0.5)

        logger.info("Telegram Bot Daemon shut down cleanly.")


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        _lock_file = acquire_singleton_lock()
    except DaemonLockError as err:
        logger.error(f"Daemon lock error: {err}")
        sys.exit(1)

    config = TelegramConfig.from_env()
    if not config:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_DEFAULT_CHAT_ID is missing from environment.")
        sys.exit(1)

    daemon = TelegramBotDaemon(config)
    try:
        daemon.start()
    except TelegramClientError as err:
        logger.error(f"Daemon initialization failed: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
