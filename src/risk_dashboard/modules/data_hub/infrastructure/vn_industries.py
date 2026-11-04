"""ICB level-3 classification, independently cached from quotes and technical signals."""

from __future__ import annotations

import json
import logging
import re
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

from .screener_store import ScreenerStore

URL = "https://iq.vietcap.com.vn/api/iq-insight-service/v2/company/search-bar?language=1"
SEED = Path(__file__).with_name("data") / "vn_industries.json"
LOG = logging.getLogger(__name__)


def parse_classification(payload):
    industries, symbols = {}, {}
    for row in payload.get("data", []):
        if not isinstance(row, dict) or row.get("isIndex"):
            continue
        symbol = str(row.get("code", "")).upper()
        sector = row.get("icbLv3") or {}
        code = str(sector.get("code", ""))
        name = str(sector.get("name") or "").strip()
        if (
            not re.fullmatch(r"[A-Z0-9]{3,12}", symbol)
            or not re.fullmatch(r"\d{4}", code)
            or not name
        ):
            continue
        if symbol in symbols and symbols[symbol] != code:
            raise ValueError("Conflicting industry classification")
        industries[code], symbols[symbol] = name, code
    if not symbols:
        raise ValueError("No valid industry data")
    return {
        "schema_version": 1,
        "taxonomy": "ICB",
        "level": 3,
        "source": "Vietcap",
        "source_url": URL,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "industries": industries,
        "symbols": symbols,
    }


def valid(payload):
    return bool(
        isinstance(payload, dict)
        and payload.get("schema_version") == 1
        and payload.get("level") == 3
        and payload.get("source")
        and payload.get("retrieved_at")
        and isinstance(payload.get("industries"), dict)
        and isinstance(payload.get("symbols"), dict)
        and payload["symbols"]
        and all(
            isinstance(s, str)
            and re.fullmatch(r"[A-Z0-9]{3,12}", s)
            and isinstance(code, str)
            and re.fullmatch(r"\d{4}", code)
            and isinstance(payload["industries"].get(code), str)
            and bool(payload["industries"][code].strip())
            for s, code in payload["symbols"].items()
        )
    )


class VnIndustryCatalog:
    def __init__(self, cache_dir, seed=SEED):
        self.store = ScreenerStore(cache_dir)
        self.seed = Path(seed)
        self._lock = threading.Lock()

    def read(self):
        cached = self.store.read("industries.json")
        if valid(cached):
            return cached
        try:
            bundled = json.loads(self.seed.read_text(encoding="utf-8"))
            return bundled if valid(bundled) else {}
        except (OSError, ValueError):
            return {}

    def refresh(self):
        """Called by scheduler only. A click never waits on an external classification API."""
        if not self._lock.acquire(blocking=False):
            return self.read()
        try:
            previous = self.read()
            try:
                age = datetime.now(timezone.utc) - datetime.fromisoformat(previous["retrieved_at"])
                if 0 <= age.total_seconds() < 86400:
                    return previous
            except (KeyError, TypeError, ValueError):
                pass
            response = requests.get(
                URL,
                headers={"Accept": "application/json", "User-Agent": "NorthstarFinanceLab/1.0"},
                timeout=15,
            )
            response.raise_for_status()
            result = parse_classification(response.json())
            if len(result["symbols"]) < max(100, len(previous.get("symbols", {})) * 0.8):
                raise ValueError("Incomplete industry response; retaining last good catalog")
            self.store.write("industries.json", result)
            return result
        except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
            LOG.warning("Industry refresh unavailable: %s", type(exc).__name__)
            return self.read()
        finally:
            self._lock.release()

    def enrich(self, quotes):
        data = self.read()
        names, lookup = data.get("industries", {}), data.get("symbols", {})
        rows = []
        for quote in quotes:
            code = lookup.get(str(quote.get("symbol", "")).upper())
            # Classification is a sourced lookup, never inferred from the company name.
            rows.append({**quote, "industry_code": code, "industry": names.get(code)})
        counts = Counter(r["industry_code"] for r in rows)
        options = sorted(
            (
                {"code": code, "name": names[code], "count": count}
                for code, count in counts.items()
                if code
            ),
            key=lambda r: r["name"],
        )
        coverage = {
            "source": data.get("source"),
            "taxonomy": "ICB",
            "level": 3,
            "retrieved_at": data.get("retrieved_at"),
            "total": len(rows),
            "classified": len(rows) - counts[None],
            "unclassified": counts[None],
        }
        return rows, options, coverage
