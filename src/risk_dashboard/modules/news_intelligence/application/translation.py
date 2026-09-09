"""Cached, optional AI translation for news digest delivery."""

from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import json
import os
from typing import Any

from risk_dashboard.platform.ai_runtime.contracts import (
    ModelMessage,
    ModelSettings,
    ModelTask,
)
from risk_dashboard.platform.ai_runtime.factory import get_default_provider
from risk_dashboard.platform.ai_runtime.provider import LLMProvider
from risk_dashboard.platform.database import open_app_state_db


def _run_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class NewsTranslator:
    def __init__(
        self,
        *,
        provider: LLMProvider | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        if provider is not None:
            self.provider = provider
        else:
            try:
                self.provider = get_default_provider()
            except Exception:
                self.provider = None
        self.api_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        self.model = (model or getattr(self.provider, "default_model", "gemini-3.5-flash")).strip()

    @property
    def enabled(self) -> bool:
        return self.provider is not None

    def translate_item(self, item: dict[str, Any]) -> dict[str, str]:
        headline = str(item.get("headline") or "")
        summary = str(item.get("summary") or item.get("why_it_matters") or "")
        if not self.enabled or not headline:
            return {"headline_vi": headline, "summary_vi": summary}
        fingerprint = hashlib.sha256(f"{headline}\n{summary}".encode("utf-8")).hexdigest()
        cached = self._get_cached(fingerprint)
        if cached:
            return cached
        try:
            task = ModelTask(
                task_type="news_translation",
                system_instructions_ref="news.translation.v1",
                messages=(
                    ModelMessage(
                        role="system",
                        content=(
                            "Bạn là biên tập viên tài chính. Dịch sang tiếng Việt rõ ràng, "
                            "trung tính, giữ nguyên số liệu, tên riêng và ticker. Không thêm "
                            "nhận định hoặc dữ kiện mới. Trả JSON gồm headline_vi và summary_vi."
                        ),
                    ),
                    ModelMessage(
                        role="user",
                        content=json.dumps(
                            {"headline": headline, "summary": summary},
                            ensure_ascii=False,
                        ),
                    ),
                ),
                settings=ModelSettings(
                    temperature=0.1,
                    response_format="json_object",
                ),
                correlation_id=f"news-trans-{fingerprint[:12]}",
            )
            model_result = _run_sync(self.provider.generate(task))
            translated = model_result.parsed or {}
            if not translated and model_result.text:
                try:
                    translated = json.loads(model_result.text)
                except Exception:
                    translated = {}
            result = {
                "headline_vi": str(translated.get("headline_vi") or headline)[:500],
                "summary_vi": str(translated.get("summary_vi") or summary)[:1200],
            }
            self._store_cached(fingerprint, result)
            return result
        except Exception:
            return {"headline_vi": headline, "summary_vi": summary}

    @staticmethod
    def _get_cached(fingerprint: str) -> dict[str, str] | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                "SELECT headline_vi, summary_vi FROM telegram_news_translations WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
        if not row:
            return None
        return {"headline_vi": row["headline_vi"], "summary_vi": row["summary_vi"]}

    @staticmethod
    def _store_cached(fingerprint: str, result: dict[str, str]) -> None:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO telegram_news_translations
                  (fingerprint, headline_vi, summary_vi, translated_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (fingerprint, result["headline_vi"], result["summary_vi"]),
            )
