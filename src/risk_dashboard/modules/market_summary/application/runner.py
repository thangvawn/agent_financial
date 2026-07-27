"""Main runner orchestrator for Market Summary Telegram delivery."""

from __future__ import annotations

import os
import logging
import hashlib
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Any

from risk_dashboard.modules.market_summary.application.summarizer import MarketSummarizer
from risk_dashboard.modules.market_summary.domain.policies import SessionCompletionPolicy
from risk_dashboard.modules.market_summary.domain.trading_calendar import TradingCalendar, VietnamExchangeTradingCalendar
from risk_dashboard.modules.market_summary.infrastructure.data_provider import MarketDataProvider, VnstockMarketDataProvider
from risk_dashboard.modules.market_summary.infrastructure.delivery_repository import DeliveryRepository
from risk_dashboard.modules.market_summary.infrastructure.telegram_client import TelegramClient
from risk_dashboard.modules.market_summary.presentation.telegram_renderer import pack_sections, render_report_sections

logger = logging.getLogger(__name__)
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def compute_payload_hash(chunks: list[str]) -> str:
    """Computes SHA256 hash of concatenated payload chunks for invariance checking."""
    content = "\n---CHUNK---\n".join(chunks).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class MarketSummaryRunner:
    def __init__(

        self,
        data_provider: MarketDataProvider | None = None,
        trading_calendar: TradingCalendar | None = None,
        repository: DeliveryRepository | None = None,
        telegram_client: TelegramClient | None = None,
        worker_id: str = "default_runner",
    ) -> None:
        self.data_provider = data_provider or VnstockMarketDataProvider()
        self.trading_calendar = trading_calendar or VietnamExchangeTradingCalendar()
        self.repository = repository or DeliveryRepository()
        self.telegram_client = telegram_client
        self.worker_id = worker_id

    def run(
        self,
        target_date: date | None = None,
        mode: str = "fast",
        force: bool = False,
        dry_run: bool = False,
        allow_incomplete_data: bool = False,
        allow_fixture_delivery: bool = False,
    ) -> dict[str, Any]:
        """Runs the market summary pipeline end-to-end with atomic lock & partial recovery."""
        today = target_date or datetime.now(LOCAL_TZ).date()

        # 1. Trading Calendar Check
        if not self.trading_calendar.is_trading_day(today):
            logger.info(f"Skipping market summary: {today} is not a trading day.")
            return {"status": "skipped", "reason": "not_trading_day", "date": str(today)}

        # 2. Build Report Data
        summarizer = MarketSummarizer(self.data_provider)
        report = summarizer.build_report(report_date=today, mode=mode)

        # Guard against accidental fixture delivery without explicit flag
        if report.provenance.data_mode == "fixture" and not dry_run and not allow_fixture_delivery:
            raise PermissionError("Attempted live delivery with fixture data without --allow-fixture-delivery flag.")

        # 3. Session Completion Validation
        vnindex_metric = next((m for m in report.indices if m.symbol == "VN-Index"), None)
        total_breadth = (report.breadth.advancers + report.breadth.decliners + report.breadth.unchanged) if report.breadth else 0

        policy = SessionCompletionPolicy()
        completion = policy.validate(
            vnindex_latest_date=report.quality.market_date,
            expected_date=today,
            vnindex_close=vnindex_metric.close if vnindex_metric else 0.0,
            vnindex_volume=vnindex_metric.volume if vnindex_metric else 0,
            total_breadth_stocks=total_breadth,
        )

        if not completion.is_complete and not allow_incomplete_data:
            logger.warning(f"Market data incomplete: {completion.reason}")
            return {
                "status": "skipped",
                "reason": "data_incomplete",
                "details": completion.reason,
                "missing": completion.missing_fields,
            }

        # 4. Render HTML Sections & Pack Chunks
        sections = render_report_sections(report, mode=mode)
        chunks = pack_sections(sections)
        current_hash = compute_payload_hash(chunks)

        if dry_run:
            logger.info(f"Dry run complete for {today}. Rendered {len(chunks)} chunk(s).")
            return {
                "status": "dry_run_success",
                "date": str(today),
                "mode": mode,
                "payload_hash": current_hash,
                "chunks_count": len(chunks),
                "rendered_html": "\n\n--- CHUNK BREAK ---\n\n".join(chunks),
                "report": report.model_dump(),
            }

        # 5. Acquire Atomic Delivery Lock
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable is missing.")

        client = self.telegram_client or TelegramClient(token=token, chat_id=chat_id)
        report_date_str = str(today)

        delivery_id, acquired = self.repository.acquire_delivery_lock(
            report_date=report_date_str,
            chat_id=chat_id,
            mode=mode,
            worker_id=self.worker_id,
        )

        if not acquired and not force:
            logger.info(f"Delivery already sent or locked for date {report_date_str}, mode {mode}.")
            return {"status": "skipped", "reason": "already_delivered_or_locked", "delivery_id": delivery_id}

        # 6. Check Policy B (Replace & Supersede if Payload Hash changed)
        existing_hash = self.repository.get_delivery_payload_hash(delivery_id)
        if existing_hash and existing_hash != current_hash:
            logger.warning(f"Payload hash changed ({existing_hash[:8]} -> {current_hash[:8]}). Marking old attempt superseded and starting fresh attempt.")
            self.repository.update_delivery_status(delivery_id, status="superseded", last_error=f"Superseded by new payload {current_hash[:8]}")
            # Re-acquire delivery lock for clean fresh delivery attempt
            delivery_id, acquired = self.repository.acquire_delivery_lock(
                report_date=report_date_str,
                chat_id=chat_id,
                mode=mode,
                worker_id=self.worker_id,
            )

        self.repository.update_delivery_status(delivery_id, status="sending", payload_hash=current_hash)
        sent_chunk_indices = self.repository.get_sent_chunk_indices(delivery_id)
        sent_msg_ids: list[int] = []
        failed_chunks: list[int] = []

        try:
            for idx, chunk_text in enumerate(chunks):
                if idx in sent_chunk_indices:
                    logger.info(f"Chunk {idx} already delivered previously, skipping.")
                    continue

                chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                try:
                    resp = client.send_html_message(chunk_text)
                    msg_id = resp.get("result", {}).get("message_id", 0)
                    sent_msg_ids.append(msg_id)
                    self.repository.record_chunk_sent(
                        delivery_id=delivery_id,
                        chunk_index=idx,
                        telegram_message_id=msg_id,
                        payload_hash=chunk_hash,
                    )
                except Exception as chunk_exc:
                    logger.error(f"Failed to send chunk {idx}: {chunk_exc}")
                    self.repository.record_chunk_failed(
                        delivery_id=delivery_id,
                        chunk_index=idx,
                        last_error=str(chunk_exc),
                    )
                    failed_chunks.append(idx)

            if failed_chunks:
                self.repository.update_delivery_status(
                    delivery_id,
                    status="partial",
                    last_error=f"Failed to send {len(failed_chunks)} chunk(s): {failed_chunks}",
                )
                return {
                    "status": "partial",
                    "delivery_id": delivery_id,
                    "date": report_date_str,
                    "mode": mode,
                    "failed_chunks": failed_chunks,
                }

            self.repository.update_delivery_status(delivery_id, status="sent")
            return {
                "status": "sent",
                "delivery_id": delivery_id,
                "date": report_date_str,
                "mode": mode,
                "chunks_sent": len(chunks),
                "message_ids": sent_msg_ids,
            }

        except Exception as exc:
            logger.error(f"Failed to deliver market summary: {exc}")
            self.repository.update_delivery_status(
                delivery_id,
                status="failed",
                last_error=str(exc),
            )
            raise
