"""Cached, optional AI translation for news digest delivery."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import requests

from risk_dashboard.platform.database import open_app_state_db


class NewsTranslator:
    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        self.model = (model or os.getenv("TELEGRAM_TRANSLATION_MODEL", "gpt-4o-mini")).strip()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

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
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Bạn là biên tập viên tài chính. Dịch sang tiếng Việt rõ ràng, "
                                "trung tính, giữ nguyên số liệu, tên riêng và ticker. Không thêm "
                                "nhận định hoặc dữ kiện mới. Trả JSON gồm headline_vi và summary_vi."
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(
                                {"headline": headline, "summary": summary},
                                ensure_ascii=False,
                            ),
                        },
                    ],
                },
                timeout=30,
            )
            payload = response.json()
            if response.status_code >= 400 or not payload.get("choices"):
                raise RuntimeError("translation request rejected")
            content = payload["choices"][0]["message"]["content"]
            translated = json.loads(content)
            result = {
                "headline_vi": str(translated.get("headline_vi") or headline)[:500],
                "summary_vi": str(translated.get("summary_vi") or summary)[:1200],
            }
            self._store_cached(fingerprint, result)
            return result
        except (requests.RequestException, ValueError, KeyError, TypeError, RuntimeError):
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
