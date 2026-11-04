"""Atomic local artifacts; does not open the application/user database."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

# data_hub/infrastructure -> repository root (not src/data).
ROOT = Path(__file__).resolve().parents[5]


def cache_root():
    return Path(os.getenv("VN_SCREENER_CACHE_DIR", str(ROOT / "data" / "vn_screener")))


class ScreenerStore:
    def __init__(self, root=None):
        self.root = Path(root) if root else cache_root()

    def read(self, name):
        try:
            p = self.root / name
            if p.stat().st_size > 150_000_000:
                return {}
            result = json.loads(p.read_text())
            return result if isinstance(result, dict) else {}
        except (OSError, ValueError):
            return {}

    def write(self, name, payload):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=target.parent, delete=False
            ) as f:
                tmp = Path(f.name)
                json.dump(payload, f, ensure_ascii=False, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, target)
        finally:
            if tmp and tmp.exists():
                tmp.unlink()

    def input(self, symbol):
        if not re.fullmatch(r"[A-Z0-9]{2,12}", symbol):
            return {}
        return self.read(f"inputs/{symbol}.json")

    def save_snapshot(self, snapshot):
        key = snapshot["snapshot_id"]
        if not re.fullmatch(r"[a-f0-9]{24}", key):
            raise ValueError("Invalid snapshot id")
        path = f"snapshots/{key}.json"
        if not (self.root / path).exists():
            self.write(path, snapshot)
        self.write("latest.json", {"snapshot_id": key})

    def snapshot(self, key=None):
        key = key or self.read("latest.json").get("snapshot_id", "")
        if not re.fullmatch(r"[a-f0-9]{24}", key):
            return {}
        return self.read(f"snapshots/{key}.json")
