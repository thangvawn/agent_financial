from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone

from risk_dashboard.modules.news_intelligence.application.telegram_digest import (
    TelegramDigestConfig,
    TelegramDigestService,
    due_periods,
)

_START_LOCK = threading.Lock()
_STARTED = False


def start_telegram_news_scheduler(logger: logging.Logger) -> None:
    global _STARTED
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    enabled = os.getenv("ENABLE_TELEGRAM_NEWS_SCHEDULER", "0").strip().lower() in {
        "1", "true", "on",
    }
    config = TelegramDigestConfig.from_env()
    if not enabled or config is None:
        logger.info("telegram news scheduler disabled or not configured")
        return
    with _START_LOCK:
        if _STARTED:
            return
        _STARTED = True
    thread = threading.Thread(
        target=_run_loop,
        args=(logger, config),
        daemon=True,
        name="telegram-news-scheduler",
    )
    thread.start()
    logger.info("telegram news scheduler started")


def _run_loop(logger: logging.Logger, config: TelegramDigestConfig) -> None:
    service = TelegramDigestService(config)
    while True:
        now = datetime.now(timezone.utc)
        for period in due_periods(now, config):
            try:
                result = service.send_digest(period)
                logger.info("telegram %s digest: %s", period, result["status"])
            except Exception:
                logger.exception("telegram %s digest failed", period)
        time.sleep(30)
