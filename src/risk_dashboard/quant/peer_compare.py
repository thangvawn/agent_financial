"""
Peer comparison module — compare a ticker's financial metrics against
a peer group of cached tickers within the same industry.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from risk_dashboard.data.financials import (
    FinancialDataError,
    _financial_cache_dir,
    get_financial_dataset,
    load_cached_financial_dataset,
)
from risk_dashboard.quant.financial_analysis import analyze_financial_dataset
from risk_dashboard.schemas.financials import FinancialAnalysisResponse, FinancialMetricSnapshot

logger = logging.getLogger(__name__)

_COMPARE_FIELDS: list[tuple[str, str, bool]] = [
    ("revenue_growth_yoy_pct", "Tăng trưởng DT YoY (%)", True),
    ("net_income_growth_yoy_pct", "Tăng trưởng LN ròng YoY (%)", True),
    ("gross_margin_pct", "Biên gộp (%)", True),
    ("operating_margin_pct", "Biên HĐKD (%)", True),
    ("net_margin_pct", "Biên ròng (%)", True),
    ("roe_pct", "ROE (%)", True),
    ("roa_pct", "ROA (%)", True),
    ("roic_pct", "ROIC (%)", True),
    ("debt_to_equity", "D/E", False),
    ("current_ratio", "Current Ratio", True),
    ("ocf_to_net_income", "OCF/NI", True),
    ("asset_turnover", "Asset Turnover", True),
]


@dataclass
class PeerMetric:
    field: str
    label: str
    ticker_value: float | None
    peer_avg: float | None
    peer_median: float | None
    rank: int | None = None
    total_peers: int = 0
    higher_is_better: bool = True


@dataclass
class PeerCompareResult:
    ticker: str
    peer_tickers: list[str] = field(default_factory=list)
    industry: str | None = None
    metrics: list[PeerMetric] = field(default_factory=list)
    peer_details: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "peer_tickers": self.peer_tickers,
            "industry": self.industry,
            "metrics": [
                {
                    "field": m.field,
                    "label": m.label,
                    "ticker_value": m.ticker_value,
                    "peer_avg": round(m.peer_avg, 2) if m.peer_avg is not None else None,
                    "peer_median": round(m.peer_median, 2) if m.peer_median is not None else None,
                    "rank": m.rank,
                    "total_peers": m.total_peers,
                    "higher_is_better": m.higher_is_better,
                }
                for m in self.metrics
            ],
            "peer_details": self.peer_details,
        }


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def list_cached_tickers() -> list[str]:
    cache_dir = _financial_cache_dir()
    return sorted(
        p.stem.upper()
        for p in cache_dir.glob("*.json")
        if p.stem.upper() != ""
    )


def _analyze_ticker(ticker: str) -> FinancialAnalysisResponse | None:
    try:
        dataset = get_financial_dataset(ticker)
        return analyze_financial_dataset(dataset)
    except FinancialDataError:
        return None


def compare_peers(
    ticker: str,
    peer_tickers: list[str] | None = None,
) -> PeerCompareResult:
    """
    Compare ``ticker`` against a set of peers.
    If ``peer_tickers`` is not provided, auto-discover from cache
    (same industry if available, else all cached).
    """
    target = _analyze_ticker(ticker.upper())
    if target is None:
        return PeerCompareResult(ticker=ticker.upper())

    if peer_tickers is None:
        all_cached = list_cached_tickers()
        if target.industry:
            candidates = []
            for t in all_cached:
                if t == ticker.upper():
                    continue
                ds = load_cached_financial_dataset(t)
                if ds and ds.industry and ds.industry.lower() == target.industry.lower():
                    candidates.append(t)
            peer_tickers = candidates if candidates else [t for t in all_cached if t != ticker.upper()]
        else:
            peer_tickers = [t for t in all_cached if t != ticker.upper()]

    peer_analyses: list[tuple[str, FinancialMetricSnapshot]] = []
    peer_details: list[dict[str, Any]] = []

    for pt in peer_tickers[:20]:
        pa = _analyze_ticker(pt)
        if pa and pa.summary.revenue is not None:
            peer_analyses.append((pt, pa.summary))
            detail: dict[str, Any] = {"ticker": pt}
            for fname, _, _ in _COMPARE_FIELDS:
                detail[fname] = getattr(pa.summary, fname, None)
            peer_details.append(detail)

    target_summary = target.summary
    all_summaries = [(ticker.upper(), target_summary)] + peer_analyses

    metrics: list[PeerMetric] = []
    for fname, label, higher_better in _COMPARE_FIELDS:
        t_val = getattr(target_summary, fname, None)
        peer_vals = [getattr(s, fname) for _, s in peer_analyses if getattr(s, fname, None) is not None]

        avg = sum(peer_vals) / len(peer_vals) if peer_vals else None
        med = _median(peer_vals)

        rank = None
        if t_val is not None and peer_vals:
            if higher_better:
                rank = sum(1 for v in peer_vals if v > t_val) + 1
            else:
                rank = sum(1 for v in peer_vals if v < t_val) + 1

        metrics.append(PeerMetric(
            field=fname,
            label=label,
            ticker_value=round(t_val, 2) if t_val is not None else None,
            peer_avg=avg,
            peer_median=med,
            rank=rank,
            total_peers=len(peer_vals) + 1,
            higher_is_better=higher_better,
        ))

    return PeerCompareResult(
        ticker=ticker.upper(),
        peer_tickers=[pt for pt, _ in peer_analyses],
        industry=target.industry,
        metrics=metrics,
        peer_details=peer_details,
    )
