"""Scan and rank the complete eligible universe before any UI filters or pagination."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from hashlib import sha256

from .fundamentals import foreign_features, fundamental_features
from .indicators import average, canonical_bars, features, percentile
from .rules import PRESETS, TECHNICAL, VERSION, catalog, evaluate

RANK_FEATURES = (
    "rs63",
    "log_rvol",
    "clv",
    "slope50",
    "cmf20",
    "rsi_change",
    "neg_contraction",
    "neg_bb_width",
    "neg_volume_contraction",
    "extension",
    "rsi14",
    "below_ma_atr",
    "neg_clv",
    "fall_atr",
    "neg_cmf",
    "foreign_ratio5",
    "foreign_ratio20",
    "cash_years",
    "neg_dps_cv",
    "momentum6",
    "momentum12",
)
BENCHMARKS = {"HOSE": "VNINDEX", "HSX": "VNINDEX", "HNX": "HNXINDEX", "UPCOM": "UPCOMINDEX"}


def build_snapshot(
    universe,
    histories,
    benchmarks,
    *,
    as_of,
    calendar,
    fundamentals=None,
    dividends=None,
    foreign=None,
):
    date.fromisoformat(as_of)
    sessions = sorted(set(d for d in calendar.get("sessions", []) if d <= as_of))
    calendar_ok = bool(
        sessions
        and sessions[-1] == as_of
        and calendar.get("source")
        and calendar.get("valid_through", "") >= as_of
    )
    rows = []
    bench = {key: canonical_bars(value, as_of)[0] for key, value in benchmarks.items()}
    for quote in sorted(universe, key=lambda x: x["symbol"]):
        symbol = quote["symbol"]
        payload = histories.get(symbol, {})
        bars, errors = canonical_bars(payload, as_of)
        if bars and payload.get("price_unit") != "VND":
            errors.append("price_unit_unknown")
        status = "eligible"
        if not calendar_ok:
            errors.append("calendar_missing")
        if not bars or errors:
            status = "unknown"
        elif bars[-1]["date"] != as_of:
            status = "stale"
            errors.append("history_stale")
        elif quote.get("security_type") != "common_stock":
            status = "not_eligible"
            errors.append("not_common_stock")
        elif quote.get("suspended") is True or bars[-1]["volume"] == 0:
            status = "not_eligible"
            errors.append("not_trading")
        expected = [d for d in sessions if bars and d >= bars[0]["date"]]
        if status == "eligible" and expected != [b["date"] for b in bars]:
            status = "unknown"
            errors.append("missing_sessions")
        benchmark_id = BENCHMARKS.get(str(quote.get("exchange", "")).upper())
        bm = bench.get(benchmark_id, [])
        bmp = benchmarks.get(benchmark_id, {})
        # Both series must declare a compatible return convention.
        if (
            not payload.get("return_basis")
            or payload.get("return_basis") != bmp.get("return_basis")
            or not bm
            or bm[-1]["date"] != as_of
        ):
            bm = []
        f = features(bars, bm) if bars else {}
        if status == "eligible":
            if f.get("median_turnover20") is None:
                status = "unknown"
                errors.append("turnover_history_missing")
            elif f["median_turnover20"] < 5e9 or f["traded_sessions20"] < 18:
                status = "not_eligible"
                errors.append("insufficient_liquidity")
        extra, extra_errors = fundamental_features(
            (fundamentals or {}).get(symbol), (dividends or {}).get(symbol), as_of
        )
        f.update(extra)
        flows, flow_errors = foreign_features((foreign or {}).get(symbol), as_of, sessions)
        f.update(flows)
        rows.append(
            {
                "symbol": symbol,
                "quote": quote,
                "features": f,
                "eligibility": status,
                "reason_codes": errors,
                "fundamental_errors": extra_errors,
                "foreign_errors": flow_errors,
                "data_as_of": bars[-1]["date"] if bars else None,
                "source": payload.get("source"),
                "adjustment_reference": payload.get("adjustment_reference"),
            }
        )
    eligible = [r for r in rows if r["eligibility"] == "eligible"]

    def rank(group, field, dest=None):
        ranks = percentile({r["symbol"]: r["features"].get(field) for r in group})
        for r in group:
            r["features"][dest or field + "_pct"] = ranks.get(r["symbol"])

    for field in RANK_FEATURES:
        rank(eligible, field)
    rank(
        [r for r in eligible if (r["features"].get("dividend_yield") or 0) > 0],
        "dividend_yield",
        "dividend_yield_pct_rank",
    )
    sectors = defaultdict(list)
    for r in eligible:
        sector = r["quote"].get("industry") or r["quote"].get("sector")
        if sector:
            sectors[sector].append(r)
        r["features"]["momentum_score"] = average(
            [r["features"].get("momentum6_pct"), r["features"].get("momentum12_pct")]
        )
    for sector, group in sectors.items():
        financial_group = [
            r
            for r in group
            if all(
                (r["features"].get(k) or 0) > 0
                for k in ("eps_ttm", "equity", "ebitda_ttm", "enterprise_value", "net_income_ttm")
            )
        ]
        for field in (
            "roe_ttm",
            "cash_profit_quality",
            "neg_leverage",
            "earnings_yield",
            "ebit_yield",
        ):
            rank(financial_group, field)
        for r in financial_group:
            f = r["features"]
            f["quality"] = average(
                [f.get(k + "_pct") for k in ("roe_ttm", "cash_profit_quality", "neg_leverage")]
            )
            f["value"] = average([f.get(k + "_pct") for k in ("earnings_yield", "ebit_yield")])
        rank(financial_group, "quality")
        rank(financial_group, "value")
    for r in rows:
        signals = {}
        for key in (*PRESETS, *TECHNICAL):
            result = evaluate(key, r["features"])
            required = (
                210
                if key == "strong_trend"
                else 200
                if key in ("vcp_pattern", "above_ma200")
                else 80
                if key
                not in ("high_dividend", "regular_cash_div", "value_investing", "foreign_favorite")
                else 21
            )
            reasons = list(r["reason_codes"])
            if r["eligibility"] != "eligible":
                result.update(status=r["eligibility"], matched=False, score=None)
            elif r["features"].get("bars", 0) < required:
                result.update(status="unknown", matched=False, score=None)
                reasons.append("insufficient_history")
            elif result["status"] == "unknown":
                reasons.extend(
                    r["foreign_errors"]
                    if key == "foreign_favorite"
                    else r["fundamental_errors"]
                    if key
                    in ("high_dividend", "regular_cash_div", "value_investing", "foreign_favorite")
                    else ["indicator_missing"]
                )
            result.update(
                reason_codes=sorted(set(reasons)),
                as_of=as_of,
                formula_version=VERSION,
                observed_on=as_of,
                triggered_on=as_of
                if result["matched"] and key in ("bottom_fishing", "bearish_reversal")
                else None,
            )
            signals[key] = result
        r["signals"] = signals
    digest = sha256(
        json.dumps(
            {"as_of": as_of, "version": VERSION, "calendar": calendar, "rows": rows},
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()[:24]
    return {
        "snapshot_id": digest,
        "formula_version": VERSION,
        "as_of": as_of,
        "calendar_valid_through": calendar.get("valid_through"),
        "universe_id": sha256("|".join(r["symbol"] for r in rows).encode()).hexdigest()[:16],
        "catalog": catalog(),
        "rows": rows,
        "universe_total": len(rows),
        "eligibility_counts": dict(Counter(r["eligibility"] for r in rows)),
    }
