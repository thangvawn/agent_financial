from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from risk_dashboard.data import watchlist_prices as watchlist_prices_mod

_PANEL: pd.DataFrame | None = None
_PANEL_SOURCE: str | None = None
_PANEL_LOAD_ERROR: str | None = None
_PANEL_LOAD_HINT: str | None = None
_PANEL_LOCK = threading.RLock()


@dataclass
class PanelUnavailableError(RuntimeError):
    detail: dict[str, str]

    def __str__(self) -> str:
        return self.detail.get("message", "Panel not loaded")


def _set_panel_load_diagnostics(error: str | None, hint: str | None = None) -> None:
    global _PANEL_LOAD_ERROR, _PANEL_LOAD_HINT
    with _PANEL_LOCK:
        _PANEL_LOAD_ERROR = error
        _PANEL_LOAD_HINT = hint


def _panel_not_loaded_detail() -> dict[str, str]:
    with _PANEL_LOCK:
        return {
            "message": "Panel not loaded",
            "error": _PANEL_LOAD_ERROR or "Backend chưa nạp được training panel.",
            "hint": _PANEL_LOAD_HINT or "Tạo lại panel parquet trong `data/cache` rồi restart backend.",
        }


def get_panel() -> pd.DataFrame:
    """Return a defensive copy of the loaded panel. Callers may freely mutate the result."""
    with _PANEL_LOCK:
        if _PANEL is None:
            raise PanelUnavailableError(_panel_not_loaded_detail())
        return _PANEL.copy()


def set_panel_for_testing(df: pd.DataFrame) -> None:
    global _PANEL, _PANEL_SOURCE
    with _PANEL_LOCK:
        _PANEL = df.copy()
        _PANEL_SOURCE = "testing"
    _set_panel_load_diagnostics(None, None)


def set_panel_from_frame(df: pd.DataFrame, *, source: str) -> None:
    global _PANEL, _PANEL_SOURCE
    staged = df.copy()
    staged["date"] = pd.to_datetime(staged["date"])
    with _PANEL_LOCK:
        _PANEL = staged
        _PANEL_SOURCE = source
    _set_panel_load_diagnostics(None, None)


def _discover_default_panel_path() -> tuple[Path | None, str | None, str | None]:
    model_dir = Path("data/models")
    for report_path in sorted(
        model_dir.glob("risk_model_vnindex*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        panel_path = report.get("panel_path")
        if isinstance(panel_path, str):
            candidate = Path(panel_path)
            if candidate.exists():
                return candidate, None, None
            local_candidate = Path("data/cache") / candidate.name
            if local_candidate.exists():
                return local_candidate, None, None
            return (
                None,
                f"Model report '{report_path.name}' đang tham chiếu tới panel không còn tồn tại: {candidate}",
                "Chạy lại `risk-fetch-universe --start 2015-01-01 --end 2026-03-29 --out ./data/cache` hoặc khôi phục file parquet rồi restart backend.",
            )

    cache_dir = Path("data/cache")
    candidates = sorted(cache_dir.glob("panel_*.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0], None, None

    universe_manifests = sorted(
        cache_dir.glob("market_universe_manifest_*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if universe_manifests:
        latest_manifest = universe_manifests[0]
        try:
            manifest = json.loads(latest_manifest.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
        missing_panel_path = manifest.get("training_panel_parquet")
        if isinstance(missing_panel_path, str):
            return (
                None,
                f"Manifest '{latest_manifest.name}' cho thấy panel đã từng được tạo nhưng file hiện bị thiếu: {missing_panel_path}",
                "Tái tạo lại cache bằng `risk-fetch-universe ... --out ./data/cache` hoặc nạp panel thủ công qua `/admin/load-panel`.",
            )

    return (
        None,
        "Không tìm thấy training panel trong `data/cache` và cũng không có model report trỏ tới file hợp lệ.",
        "Sinh lại panel bằng pipeline ingest/fetch rồi restart backend.",
    )


def autoload_default_panel() -> bool:
    candidate, error, hint = _discover_default_panel_path()
    if candidate is None:
        _set_panel_load_diagnostics(error, hint)
        return False
    try:
        panel = pd.read_parquet(candidate)
    except Exception as exc:
        _set_panel_load_diagnostics(
            f"Đọc panel thất bại tại '{candidate}': {exc}",
            "Kiểm tra file parquet có bị hỏng không hoặc tạo lại panel mới.",
        )
        return False
    set_panel_from_frame(panel, source=str(candidate))
    return True


def panel_status() -> dict[str, object]:
    with _PANEL_LOCK:
        if _PANEL is None or _PANEL.empty:
            return {
                "loaded": False,
                "rows": 0,
                "start_date": None,
                "end_date": None,
                "source": None,
                "error": _PANEL_LOAD_ERROR,
                "hint": _PANEL_LOAD_HINT,
            }
        panel = _PANEL.copy()
        source = _PANEL_SOURCE
    panel["date"] = pd.to_datetime(panel["date"])
    return {
        "loaded": True,
        "rows": int(len(panel)),
        "start_date": panel["date"].min().date().isoformat(),
        "end_date": panel["date"].max().date().isoformat(),
        "source": source,
        "error": None,
        "hint": None,
    }


def panel_date_range() -> tuple[str | None, str | None]:
    with _PANEL_LOCK:
        if _PANEL is None or _PANEL.empty:
            return None, None
        panel = _PANEL.copy()
    panel["date"] = pd.to_datetime(panel["date"])
    return panel["date"].min().date().isoformat(), panel["date"].max().date().isoformat()


def _startup_sync_watchlist_prices(logger) -> None:
    raw = os.getenv("WATCHLIST_PRICE_SYNC_TICKERS", "").strip()
    if not raw:
        return
    parts = [x.strip() for x in raw.split(",") if x.strip()]
    try:
        out = watchlist_prices_mod.sync_watchlist_tickers(parts)
        logger.info(
            "WATCHLIST_PRICE_SYNC_TICKERS: ok=%s errors=%s",
            out.get("synced"),
            list((out.get("errors") or {}).keys()),
        )
    except Exception as exc:
        logger.warning("WATCHLIST_PRICE_SYNC_TICKERS failed: %s", exc)


def startup_initialize_runtime(*, logger) -> None:
    global _PANEL_SOURCE
    if _PANEL is None:
        loaded = autoload_default_panel()
        logger.info("Panel autoload: %s (source=%s)", "OK" if loaded else "FAIL", _PANEL_SOURCE)
    _startup_sync_watchlist_prices(logger)
