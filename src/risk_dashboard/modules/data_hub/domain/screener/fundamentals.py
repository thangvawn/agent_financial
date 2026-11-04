"""Point-in-time inputs. Ratios are derived, never taken from a live quote fallback."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from statistics import mean, pstdev

from .indicators import number, ratio


def known_at(value, as_of):
    try:
        at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone(timedelta(hours=7)))
        cutoff = datetime.fromisoformat(as_of + "T16:00:00+07:00")
        return at <= cutoff
    except (ValueError, TypeError):
        return False


def published(record, as_of):
    if not isinstance(record, dict):
        return False
    try:
        period = date.fromisoformat(record.get("period_end", ""))
    except (ValueError, TypeError):
        return False
    return bool(
        record.get("source")
        and record.get("complete") is True
        and known_at(record.get("available_at"), as_of)
        and period.isoformat() <= as_of
    )


def fundamental_features(record, events, as_of):
    if not published(record, as_of):
        return {}, ["fundamentals_missing_or_not_public"]
    if record.get("profile") != "non_financial":
        return {}, ["financial_sector_profile_pending"]
    if (date.fromisoformat(as_of) - date.fromisoformat(record["period_end"])).days > 180:
        return {}, ["fundamentals_stale"]
    names = (
        "net_income_ttm",
        "cfo_ttm",
        "equity",
        "eps_ttm",
        "ebitda_ttm",
        "net_debt",
        "ebit_ttm",
        "enterprise_value",
        "raw_close",
        "roe_ttm",
    )
    f = {key: number(record.get(key)) for key in names}
    # Raw valuation price and share basis must match the signal session, not a current quote.
    if record.get("valuation_date") != as_of:
        for key in ("raw_close", "enterprise_value"):
            f[key] = None
    if f["net_income_ttm"] and f["net_income_ttm"] > 0:
        f["cash_profit_quality"] = ratio(f["cfo_ttm"], f["net_income_ttm"])
    leverage = ratio(f["net_debt"], f["ebitda_ttm"])
    f["neg_leverage"] = -leverage if leverage is not None else None
    f["earnings_yield"] = ratio(f["eps_ttm"], f["raw_close"])
    f["ebit_yield"] = ratio(f["ebit_ttm"], f["enterprise_value"])
    annual = sorted(
        (x for x in record.get("annual", []) if published(x, as_of)), key=lambda x: x["period_end"]
    )[-3:]
    if len(annual) == 3 and [int(x["period_end"][:4]) for x in annual] == list(
        range(int(annual[-1]["period_end"][:4]) - 2, int(annual[-1]["period_end"][:4]) + 1)
    ):
        if (date.fromisoformat(as_of) - date.fromisoformat(annual[-1]["period_end"])).days > 550:
            annual = []
    else:
        annual = []
    if annual:
        cfos = [number(x.get("cfo")) for x in annual]
        cash = [number(x.get("cash_dividends_paid")) for x in annual]
        if all(x is not None for x in cfos + cash) and all(x >= 0 for x in cash):
            f["cash_coverage"] = ratio(sum(cfos), sum(cash))
            f["latest_cfo"] = cfos[-1]
        last = annual[-1]
        if last.get("dividend_complete") is True:
            f["dividend_earnings"] = number(last.get("eps"))
            f["payout"] = ratio(number(last.get("regular_dividend_dps")), f["dividend_earnings"])
    if (
        not isinstance(events, dict)
        or events.get("complete_through") != as_of
        or not events.get("source")
    ):
        return f, ["dividend_events_missing"]
    cutoff = (date.fromisoformat(as_of) - timedelta(days=365)).isoformat()
    known = [
        e
        for e in events.get("items", [])
        if e.get("type") == "cash"
        and e.get("regular") is True
        and known_at(e.get("announced_at"), as_of)
        and e.get("share_basis_date") == as_of
        and number(e.get("dps")) is not None
    ]
    f["dividend_yield"] = ratio(
        sum(number(e["dps"]) for e in known if cutoff < e.get("ex_date", "") <= as_of),
        f["raw_close"],
    )
    by_year = {}
    for e in known:
        if e.get("paid_at") and e["paid_at"][:10] <= as_of:
            year = int(e["paid_at"][:4])
            by_year[year] = by_year.get(year, 0) + number(e["dps"])
    year = int(as_of[:4]) - 1
    years = 0
    while by_year.get(year - years, 0) > 0:
        years += 1
    f["cash_years"] = years
    if years >= 3:
        dps = [by_year[y] for y in range(year - 2, year + 1)]
        f["dps_retention"] = ratio(dps[-1], dps[-2])
        f["neg_dps_cv"] = -pstdev(dps) / mean(dps)
    return f, []


def foreign_features(payload, as_of, expected_dates):
    if (
        not isinstance(payload, dict)
        or payload.get("value_unit") != "VND"
        or payload.get("scope") != "matched"
        or not payload.get("source")
    ):
        return {}, ["foreign_history_missing"]
    points = {}
    for p in payload.get("items", []):
        d = p.get("date", "")
        if d > as_of:
            continue
        if d in points:
            return {}, ["foreign_duplicate_session"]
        if p.get("is_final") is True and known_at(p.get("available_at"), as_of):
            points[d] = p
    selected = [points.get(d) for d in expected_dates[-20:]]
    if len(selected) != 20 or any(p is None for p in selected):
        return {}, ["foreign_history_incomplete"]
    vals = []
    for p in selected:
        buy, sell, turnover = (
            number(p.get(k)) for k in ("buy_value", "sell_value", "matched_turnover_vnd")
        )
        if any(x is None or x < 0 for x in (buy, sell, turnover)) or turnover == 0:
            return {}, ["foreign_values_invalid"]
        vals.append((buy - sell, turnover))
    return {
        "foreign_ratio5": sum(x for x, _ in vals[-5:]) / sum(y for _, y in vals[-5:]),
        "foreign_ratio20": sum(x for x, _ in vals) / sum(y for _, y in vals),
        "foreign_positive5": sum(x > 0 for x, _ in vals[-5:]),
    }, []
