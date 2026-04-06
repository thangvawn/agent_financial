from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from risk_dashboard.data.etl import align_mixed_frequency
from risk_dashboard.data.interfaces import MacroSource, MarketSource


def add_volume_trend_pct(df: pd.DataFrame, *, volume_col: str = "volume", window: int = 5) -> pd.DataFrame:
    """Thêm volume_1w_trend_pct (so 5 phiên gần vs 5 phiên trước)."""
    out = df.copy()
    v = out[volume_col].astype(float)
    recent = v.rolling(window).mean()
    prev = v.shift(window).rolling(window).mean()
    out["volume_1w_trend_pct"] = ((recent - prev) / prev.abs().replace(0, np.nan) * 100).replace(
        [np.inf, -np.inf], np.nan
    ).fillna(0.0)
    return out


@dataclass
class IngestManifest:
    ingest_id: str
    created_at: str
    market_source: str
    macro_source: str
    start: str
    end: str
    n_rows: int
    columns: list[str]


def build_training_panel(
    market: MarketSource,
    macro: MacroSource,
    start: date,
    end: date,
    *,
    add_volume_trend: bool = True,
) -> pd.DataFrame:
    """
    Gộp daily index + monthly macro → panel dùng cho quant (cùng schema như pipeline hiện tại).
    """
    daily = market.load_index_series(start, end)
    monthly = macro.load_macro_monthly(start, end)
    aligned = align_mixed_frequency(daily, monthly)
    if add_volume_trend:
        aligned = add_volume_trend_pct(aligned)
    return aligned


def run_ingest_to_parquet(
    market: MarketSource,
    macro: MacroSource,
    start: date,
    end: date,
    output_dir: str | Path,
    *,
    ingest_id: str | None = None,
    market_label: str = "market",
    macro_label: str = "macro",
) -> tuple[Path, Path]:
    """
    Xuất Parquet + manifest JSON. Trả về (path_parquet, path_manifest).
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    iid = ingest_id or str(uuid.uuid4())
    panel = build_training_panel(market, macro, start, end)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pq_path = out_dir / f"panel_{ts}_{iid[:8]}.parquet"
    panel.to_parquet(pq_path, index=False)

    manifest = IngestManifest(
        ingest_id=iid,
        created_at=datetime.now(timezone.utc).isoformat(),
        market_source=market_label,
        macro_source=macro_label,
        start=start.isoformat(),
        end=end.isoformat(),
        n_rows=len(panel),
        columns=list(panel.columns),
    )
    man_path = out_dir / f"manifest_{ts}_{iid[:8]}.json"
    man_path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")
    return pq_path, man_path
