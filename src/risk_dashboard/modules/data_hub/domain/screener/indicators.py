"""Pure calculations. Never synthesize missing OHLC or use a quote as a daily bar."""

from __future__ import annotations

import math
from datetime import date
from statistics import mean, median, pstdev, stdev


def number(value):
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def ratio(a, b):
    return a / b if a is not None and b is not None and b > 0 else None


def average(values):
    return mean(values) if values and all(x is not None for x in values) else None


def percentile(values, min_count=20):
    """Average ranks for ties; input is symbol -> finite value, fixed universe."""
    clean = sorted((v, k) for k, v in values.items() if number(v) is not None)
    if len(clean) < min_count:
        return {}
    result, i, n = {}, 0, len(clean)
    while i < n:
        j = i + 1
        while j < n and clean[j][0] == clean[i][0]:
            j += 1
        rank = 100 * ((i + j - 1) / 2) / (n - 1)
        for _, key in clean[i:j]:
            result[key] = rank
        i = j
    return result


def wilder(values, n):
    out = [None] * len(values)
    if len(values) < n:
        return out
    out[n - 1] = mean(values[:n])
    for i in range(n, len(values)):
        out[i] = (out[i - 1] * (n - 1) + values[i]) / n
    return out


def canonical_bars(payload, as_of):
    """Validate one coherent history; slicing precedes validation to prevent lookahead."""
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("bars"), list)
        or not payload["bars"]
    ):
        return [], ["history_missing"]
    if payload.get("price_basis") not in {"corporate_action_adjusted", "index_price"}:
        return [], ["adjustment_unverified"]
    if not payload.get("source") or not payload.get("adjustment_reference"):
        return [], ["provenance_missing"]
    if payload.get("price_unit") not in {"VND", "index_points"}:
        return [], ["price_unit_unknown"]
    if payload.get("volume_basis") not in {"split_adjusted", "as_traded_no_splits", "index"}:
        return [], ["volume_basis_unverified"]
    if payload.get("quality_flags"):
        return [], ["history_quality_flag"]
    out, seen = [], set()
    for raw in payload["bars"]:
        if not isinstance(raw, dict):
            return [], ["invalid_ohlcv"]
        day = str(raw.get("date", ""))[:10]
        try:
            date.fromisoformat(day)
        except ValueError:
            return [], ["invalid_session_date"]
        if day > as_of:
            continue
        if raw.get("is_final") is not True:
            continue
        if day in seen:
            return [], ["duplicate_session"]
        seen.add(day)
        bar = {key: number(raw.get(key)) for key in ("open", "high", "low", "close", "volume")}
        if (
            any(v is None for v in bar.values())
            or min(bar[k] for k in ("open", "high", "low", "close")) <= 0
        ):
            return [], ["invalid_ohlcv"]
        if (
            bar["volume"] < 0
            or not bar["low"]
            <= min(bar["open"], bar["close"])
            <= max(bar["open"], bar["close"])
            <= bar["high"]
        ):
            return [], ["invalid_ohlcv"]
        if raw.get("quality_flags"):
            return [], ["synthetic_or_flagged_bar"]
        bar.update(date=day, turnover=number(raw.get("matched_turnover_vnd")))
        out.append(bar)
    return sorted(out, key=lambda x: x["date"]), []


def features(bars, benchmark=None):
    """All window endpoints are explicit. Yesterday's ATR/volume baseline excludes t."""
    if len(bars) < 21:
        return {}
    c, h, low, v = ([b[key] for b in bars] for key in ("close", "high", "low", "volume"))
    n = len(c)

    def sma(size, end=n):
        return mean(c[end - size : end]) if end >= size else None

    tr = [max(h[i] - low[i], abs(h[i] - c[i - 1]), abs(low[i] - c[i - 1])) for i in range(1, n)]
    atrs = [None] + wilder(tr, 14)
    atr = atrs[-2]
    changes = [c[i] - c[i - 1] for i in range(1, n)]
    gains, losses = (
        wilder([max(x, 0) for x in changes], 14),
        wilder([max(-x, 0) for x in changes], 14),
    )
    rsis = [None] + [
        None if g is None else 50.0 if g == z == 0 else 100.0 if z == 0 else 100 - 100 / (1 + g / z)
        for g, z in zip(gains, losses)
    ]
    clvs = [ratio(c[i] - low[i], h[i] - low[i]) for i in range(n)]
    zero_ranges = sum(x is None for x in clvs[-20:])
    cmf = (
        ratio(
            sum((2 * x - 1) * vol if x is not None else 0 for x, vol in zip(clvs[-20:], v[-20:])),
            sum(v[-20:]),
        )
        if zero_ranges <= 2
        else None
    )
    rvol = ratio(v[-1], mean(v[-21:-1]))
    turnover = [b["turnover"] for b in bars[-21:-1]]
    f = {
        "bars": n,
        "close": c[-1],
        "prev_close": c[-2],
        "prev_high": h[-2],
        "sma20": sma(20),
        "prev_sma20": sma(20, n - 1),
        "sma50": sma(50),
        "sma200": sma(200),
        "sma200_10ago": sma(200, n - 10),
        "atr14_prev": atr,
        "hh60": max(h[-61:-1]) if n >= 61 else None,
        "rvol20": rvol,
        "log_rvol": math.log(rvol) if rvol and rvol > 0 else None,
        "clv": clvs[-1],
        "cmf20": cmf,
        "rsi14": rsis[-1],
        "prev_rsi14": rsis[-2],
        "rsi_recent_min": min(rsis[-6:-1]) if None not in rsis[-6:-1] else None,
        "rsi_change": rsis[-1] - rsis[-2] if rsis[-2] is not None else None,
        "extension": ratio(c[-1] - sma(20), atr),
        "fall_atr": ratio(c[-2] - c[-1], atr),
        "below_ma_atr": ratio(sma(20) - c[-1], atr),
        "slope50": ratio(sma(50) - sma(50, n - 10), 10 * atr) if n >= 60 and atr else None,
        "median_turnover20": median(turnover)
        if all(x is not None and x >= 0 for x in turnover)
        else None,
        "traded_sessions20": sum(x > 0 for x in v[-21:-1]),
        "volume": v[-1],
        "high_volatility": ratio(h[-1] - low[-1], c[-2]),
        "neg_clv": 1 - clvs[-1] if clvs[-1] is not None else None,
        "neg_cmf": -cmf if cmf is not None else None,
    }
    if n >= 200:
        atr10, atr60 = wilder(tr, 10)[-1], wilder(tr, 60)[-1]

        def width(end):
            return ratio(4 * pstdev(c[end - 20 : end]), mean(c[end - 20 : end]))

        widths = [width(end) for end in range(n - 126, n)]
        current_width = width(n)
        f.update(
            contraction=ratio(atr10, atr60),
            bb_width=current_width,
            bb_percentile=100
            * (
                sum(x < current_width for x in widths)
                + 0.5 * sum(x == current_width for x in widths)
            )
            / len(widths),
            volume_contraction=ratio(mean(v[-5:]), mean(v[-25:-5])),
            distance_high=ratio(max(h[-61:-1]) - c[-1], c[-1]),
        )
        for src, dest in [
            ("contraction", "neg_contraction"),
            ("bb_width", "neg_bb_width"),
            ("volume_contraction", "neg_volume_contraction"),
        ]:
            f[dest] = -f[src] if f[src] is not None else None
    if benchmark:
        bmap = {b["date"]: b["close"] for b in benchmark}

        def excess(start, end):
            if any(b["date"] not in bmap for b in bars[start : n + end + 1]):
                return None
            a, z = bmap.get(bars[start]["date"]), bmap.get(bars[end]["date"])
            return math.log(c[end] / c[start]) - math.log(z / a) if a and z else None

        f["rs63"] = excess(-64, -1) if n >= 64 else None
        if n >= 274:
            sigma = stdev([math.log(c[i] / c[i - 1]) for i in range(n - 252, n)]) * math.sqrt(252)
            f.update(
                momentum6=ratio(excess(-148, -22), sigma),
                momentum12=ratio(excess(-274, -22), sigma),
            )
    return f
