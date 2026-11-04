from copy import deepcopy
from datetime import date, timedelta

import pytest

from risk_dashboard.modules.data_hub.domain.screener.indicators import (
    canonical_bars,
    features,
    percentile,
)


def history(n=300, multiplier=1, end=date(2026, 10, 30)):
    days = []
    while len(days) < n:
        if end.weekday() < 5:
            days.append(end.isoformat())
        end -= timedelta(days=1)
    bars = []
    for i, day in enumerate(reversed(days)):
        c = (40000 + i * 30) * multiplier
        bars.append(
            dict(
                date=day,
                open=c - 100 * multiplier,
                high=c + 400 * multiplier,
                low=c - 400 * multiplier,
                close=c,
                volume=1e6,
                matched_turnover_vnd=40e9,
                is_final=True,
            )
        )
    return dict(
        source="fixture",
        price_basis="corporate_action_adjusted",
        price_unit="VND",
        volume_basis="split_adjusted",
        adjustment_reference="fixture verified factors",
        return_basis="price",
        bars=bars,
    )


def test_rvol_and_breakout_reference_exclude_today_and_future():
    p = history()
    p["bars"][-1].update(high=52000, close=51500, low=49000, open=50000, volume=2e6)
    bars, errors = canonical_bars(p, "2026-10-30")
    assert not errors
    f = features(bars)
    assert f["rvol20"] == 2
    assert f["hh60"] == p["bars"][-2]["high"]
    p["bars"].append(dict(date="2026-11-02", close=None, is_final=True))
    assert features(canonical_bars(p, "2026-10-30")[0]) == f


def test_missing_invalid_and_duplicate_bars_not_filled():
    p = history()
    p["bars"][-1]["high"] = None
    assert canonical_bars(p, "2026-10-30")[1] == ["invalid_ohlcv"]
    p = history()
    p["bars"].append(deepcopy(p["bars"][-1]))
    assert canonical_bars(p, "2026-10-30")[1] == ["duplicate_session"]
    p = history()
    p.pop("price_basis")
    assert canonical_bars(p, "2026-10-30")[1] == ["adjustment_unverified"]


def test_scale_invariant_atr_features_and_percentile_ties():
    a = features(canonical_bars(history(), "2026-10-30")[0])
    b = features(canonical_bars(history(multiplier=0.5), "2026-10-30")[0])
    for key in ["rvol20", "rsi14", "extension", "slope50", "clv", "cmf20"]:
        assert a[key] == pytest.approx(b[key])
    assert percentile({str(i): 2 for i in range(20)}) == {str(i): 50 for i in range(20)}
    assert percentile({"A": 1, "B": 2}) == {}


def test_zero_volume_flat_series_and_incomplete_session():
    p = history()
    for b in p["bars"]:
        b.update(open=100, high=100, low=100, close=100, volume=0)
    f = features(canonical_bars(p, "2026-10-30")[0])
    assert f["cmf20"] is None and f["rvol20"] is None and f["rsi14"] == 50
    p["bars"][-1]["is_final"] = False
    assert canonical_bars(p, "2026-10-30")[0][-1]["date"] == "2026-10-29"


from risk_dashboard.modules.data_hub.application.stock_screener import (
    ScreenerQueryError,
    StockScreenerService,
)
from risk_dashboard.modules.data_hub.domain.screener.engine import build_snapshot
from risk_dashboard.modules.data_hub.domain.screener.rules import PRESETS, TECHNICAL, evaluate
from risk_dashboard.modules.data_hub.infrastructure.screener_store import ScreenerStore


def bundle(count=30):
    h = history()
    for bar in h["bars"][-21:-1]:
        bar.update(high=bar["close"] + 200, low=bar["close"] - 800)
    # Strong upper close, normal historical prices and one volume expansion.
    h["bars"][-1].update(open=48700, low=48600, high=49400, close=49300, volume=2e6)
    quotes = [
        dict(
            symbol=f"X{i:02}",
            security_type="common_stock",
            exchange="HOSE",
            industry="Công nghệ",
            price=49300,
            market_cap=count - i,
        )
        for i in range(count)
    ]
    histories = {q["symbol"]: deepcopy(h) for q in quotes}
    benchmark = history(multiplier=0.02)
    return (
        quotes,
        histories,
        {"VNINDEX": benchmark},
        dict(
            sessions=[b["date"] for b in h["bars"]],
            source="fixture exchange calendar",
            valid_through="2026-11-02",
        ),
    )


def test_scan_before_pagination_scores_fixed_and_cursors_pin_snapshot(tmp_path):
    q, h, b, cal = bundle(30)
    snap = build_snapshot(q, h, b, as_of="2026-10-30", calendar=cal)
    snap["session_verified"] = True
    store = ScreenerStore(tmp_path)
    store.save_snapshot(snap)
    svc = StockScreenerService(store)
    first = svc.query(q, preset="money_inflow", limit=20)
    assert first["matched"] == 30 and first["returned"] == 20 and first["unknown"] == 0
    second = svc.query(q, preset="money_inflow", limit=20, cursor=first["next_cursor"])
    assert len(second["items"]) == 10
    assert not ({r["symbol"] for r in first["items"]} & {r["symbol"] for r in second["items"]})
    big = svc.query(q, preset="money_inflow", limit=100)
    assert [r["screening"]["score"] for r in first["items"]] == [
        r["screening"]["score"] for r in big["items"][:20]
    ]
    with pytest.raises(ScreenerQueryError):
        svc.query(q, preset="breakout", cursor=first["next_cursor"])
    with pytest.raises(ScreenerQueryError):
        svc.query(q, cursor="not-json")


def test_counts_distinguish_unknown_stale_ineligible_and_no_match():
    q, h, b, cal = bundle()
    h["X00"].pop("price_basis")
    h["X01"]["bars"].pop()
    for bar in h["X02"]["bars"]:
        bar["matched_turnover_vnd"] = 1e6
    h["X03"]["bars"].pop(-5)
    snap = build_snapshot(q, h, b, as_of="2026-10-30", calendar=cal)
    states = {r["symbol"]: r["signals"]["money_inflow"]["status"] for r in snap["rows"]}
    assert (
        states["X00"] == "unknown"
        and states["X01"] == "stale"
        and states["X02"] == "not_eligible"
        and states["X03"] == "unknown"
    )
    assert states["X04"] == "evaluated"


def test_all_rules_explain_unknown_instead_of_using_zero():
    for p in (*PRESETS, *TECHNICAL):
        result = evaluate(p, {})
        assert result["status"] == "unknown" and not result["matched"] and result["conditions"]
    assert evaluate("above_ma20", {"close": 20, "sma20": 10})["matched"]
    assert not evaluate("high_dividend", {"dividend_yield": 0.09})["matched"]


def test_score_is_unknown_with_small_cross_section_without_hiding_match():
    q, h, b, cal = bundle(3)
    snap = build_snapshot(q, h, b, as_of="2026-10-30", calendar=cal)
    s = snap["rows"][0]["signals"]["money_inflow"]
    assert s["matched"] and s["score"] is None
    assert s["score_missing_fields"]


from risk_dashboard.modules.data_hub.application.screener_job import collect, import_bundle
from risk_dashboard.modules.data_hub.domain.screener.fundamentals import (
    foreign_features,
    fundamental_features,
)
from risk_dashboard.modules.data_hub.infrastructure.screener_provider import (
    ProviderUnavailable,
    from_trade_history,
)


def test_foreign_flow_uses_real_values_not_last_price_and_rejects_missing():
    _, _, _, cal = bundle()
    points = [
        dict(
            date=d,
            is_final=True,
            available_at=d + "T08:00:00Z",
            buy_value=30e9,
            sell_value=10e9,
            matched_turnover_vnd=100e9,
        )
        for d in cal["sessions"][-20:]
    ]
    payload = dict(source="test", scope="matched", value_unit="VND", items=points)
    f, err = foreign_features(payload, "2026-10-30", cal["sessions"])
    assert (
        not err
        and f["foreign_ratio5"] == pytest.approx(0.2)
        and evaluate("foreign_favorite", f)["matched"]
    )
    points.pop()
    assert foreign_features(payload, "2026-10-30", cal["sessions"])[1] == [
        "foreign_history_incomplete"
    ]


def test_future_financial_report_and_banks_never_match_industrial_rules():
    record = dict(
        source="fixture",
        complete=True,
        available_at="2026-11-02",
        period_end="2026-09-30",
        profile="non_financial",
    )
    assert fundamental_features(record, {}, "2026-10-30")[0] == {}
    record.update(available_at="2026-10-01", profile="bank")
    assert fundamental_features(record, {}, "2026-10-30")[1] == ["financial_sector_profile_pending"]


def test_provider_parser_does_not_create_turnover_or_adjust_volume_through_rights():
    records = []
    for bar in history(30)["bars"]:
        records.append(
            dict(
                trading_date=bar["date"],
                open_adjusted=bar["open"],
                high_adjusted=bar["high"],
                low_adjusted=bar["low"],
                close_adjusted=bar["close"],
                close=bar["close"],
                matched_volume=bar["volume"],
            )
        )
    p = from_trade_history("AAA", records, source="fixture")
    assert all(b["matched_turnover_vnd"] is None for b in p["bars"])
    assert p["volume_basis"] == "as_traded_no_splits"
    records[-2]["close"] = records[-2]["close"] * 2
    assert from_trade_history("AAA", records, source="fixture")["volume_basis"] == "unverified"


def test_import_validates_all_symbols_before_writing_and_job_capability_backoff(tmp_path):
    store = ScreenerStore(tmp_path)
    q, h, b, cal = bundle(2)
    inputs = {k: dict(security_type="common_stock", history=v) for k, v in h.items()}
    inputs["X01"]["history"]["bars"][-1]["low"] = None
    with pytest.raises(ValueError):
        import_bundle(dict(calendar=cal, inputs=inputs), store)
    assert not list(tmp_path.glob("inputs/*"))
    calls = []

    def unavailable():
        calls.append(1)
        raise ProviderUnavailable("missing capability")

    result = collect(lambda: q, store, unavailable, delay=0)
    assert result["status"] == "provider_unavailable"
    collect(lambda: q, store, unavailable, delay=0)
    assert len(calls) == 1


def test_all_presets_have_matching_example_and_missing_fields_fail_closed():
    common = dict(
        close=200,
        prev_close=190,
        prev_high=195,
        sma20=198,
        sma50=195,
        sma200=180,
        sma200_10ago=179,
        prev_sma20=189,
        atr14_prev=2,
        hh60=198,
        extension=1,
        slope50=0.2,
        rs63=0.3,
        rs63_pct=80,
        rvol20=2,
        clv=0.9,
        cmf20=0.2,
        rsi_recent_min=25,
        prev_rsi14=34,
        rsi14=40,
        contraction=0.5,
        bb_percentile=10,
        volume_contraction=0.5,
        distance_high=0.03,
    )
    examples = {
        "breakout": common,
        "strong_trend": common,
        "money_inflow": common,
        "bottom_fishing": common,
        "vcp_pattern": common,
        "overbought_peak": dict(extension=3, rsi14=80),
        "bearish_reversal": dict(
            prev_close=100, prev_sma20=100, below_ma_atr=0.5, rvol20=1.5, clv=0.2
        ),
        "dumping_signal": dict(fall_atr=2, rvol20=3, clv=0.1, cmf20=-0.3),
        "foreign_favorite": dict(foreign_ratio5=0.03, foreign_ratio20=0.02, foreign_positive5=4),
        "high_dividend": dict(
            dividend_yield=0.06,
            dividend_yield_pct_rank=80,
            payout=0.5,
            cash_coverage=2,
            dividend_earnings=2000,
            latest_cfo=1e9,
        ),
        "regular_cash_div": dict(
            cash_years=3,
            dps_retention=0.9,
            payout=0.5,
            cash_coverage=2,
            dividend_earnings=2000,
            latest_cfo=1e9,
        ),
        "value_investing": dict(
            eps_ttm=1000,
            equity=1e12,
            ebitda_ttm=1e9,
            enterprise_value=1e12,
            quality_pct=80,
            value_pct=80,
        ),
    }
    for key, values in examples.items():
        result = evaluate(key, values)
        assert result["matched"], (key, result)
        for field in result["conditions"][0]["values"]:
            reduced = {k: v for k, v in values.items() if k != field}
            assert not evaluate(key, reduced)["matched"], (key, field)


def test_public_api_validates_query_and_scans_whole_cached_universe(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from risk_dashboard.modules.data_hub.api import public

    q, h, b, cal = bundle(60)
    store = ScreenerStore(tmp_path)
    snap = build_snapshot(q, h, b, as_of="2026-10-30", calendar=cal)
    snap["session_verified"] = True
    store.save_snapshot(snap)
    monkeypatch.setattr(public, "_screener", StockScreenerService(store))
    monkeypatch.setattr(public._vn_market, "_load_json", lambda path: {"items": q})
    app = FastAPI()
    app.include_router(public.router)
    with TestClient(app) as client:
        response = client.get(
            "/data-hub/vn-market/screener", params={"preset": "money_inflow", "limit": 20}
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["matched"] == 60 and len(payload["items"]) == 20
        for params in (
            {"preset": "unknown"},
            {"limit": 10000},
            {"snapshot_id": "../../other"},
            {"cursor": "%"},
        ):
            assert client.get("/data-hub/vn-market/screener", params=params).status_code == 422


def test_checkpoint_job_retains_good_input_when_provider_fails(tmp_path):
    q, h, b, cal = bundle(3)
    q = [{**row, "symbol": sym} for row, sym in zip(q, ["AAA", "BBB", "CCC"])]
    store = ScreenerStore(tmp_path)
    store.write("inputs/AAA.json", {"history": history(), "security_type": "common_stock"})

    class Provider:
        def calendar(self):
            return cal

        def benchmark(self, s):
            return {"history": history()}

        def equity(self, s):
            raise ProviderUnavailable("unavailable")

    result = collect(lambda: q, store, Provider, delay=0)
    assert result["status"] == "partial" and store.input("AAA")["history"]["bars"]
    assert store.snapshot()["universe_total"] == 3


def test_same_day_late_reports_are_not_available_at_signal_cutoff():
    from risk_dashboard.modules.data_hub.domain.screener.fundamentals import published

    report = dict(
        source="fixture",
        complete=True,
        period_end="2026-09-30",
        available_at="2026-10-30T18:00:00+07:00",
    )
    assert not published(report, "2026-10-30")
    report["available_at"] = "2026-10-30T15:30:00+07:00"
    assert published(report, "2026-10-30")
    report["period_end"] = "broken-date"
    assert not published(report, "2026-10-30")


def test_financial_and_dividend_features_respect_cash_events_and_common_share_basis():
    report = dict(
        source="fixture",
        complete=True,
        available_at="2026-10-20",
        period_end="2026-09-30",
        profile="non_financial",
        valuation_date="2026-10-30",
        raw_close=50000,
        net_income_ttm=100e9,
        cfo_ttm=120e9,
        equity=500e9,
        eps_ttm=4000,
        ebitda_ttm=130e9,
        ebit_ttm=110e9,
        enterprise_value=1000e9,
        net_debt=100e9,
        roe_ttm=0.2,
    )
    report["annual"] = [
        dict(
            source="fixture",
            complete=True,
            available_at=f"{y + 1}-03-01",
            period_end=f"{y}-12-31",
            cfo=100e9,
            cash_dividends_paid=40e9,
            eps=4000,
            regular_dividend_dps=2000,
            dividend_complete=True,
        )
        for y in (2023, 2024, 2025)
    ]
    events = dict(
        source="fixture",
        complete_through="2026-10-30",
        items=[
            dict(
                type="cash",
                regular=True,
                dps=3000,
                announced_at=f"{y}-01-01",
                ex_date=f"{y}-06-01",
                paid_at=f"{y}-07-01",
                share_basis_date="2026-10-30",
            )
            for y in (2023, 2024, 2025, 2026)
        ],
    )
    events["items"].append(
        dict(
            type="stock",
            regular=True,
            dps=5000,
            announced_at="2026-01-01",
            ex_date="2026-06-01",
            paid_at="2026-07-01",
            share_basis_date="2026-10-30",
        )
    )
    f, errors = fundamental_features(report, events, "2026-10-30")
    assert not errors and f["dividend_yield"] == 0.06 and f["cash_years"] == 3
    assert f["payout"] == 0.5 and f["cash_coverage"] == 2.5 and f["dps_retention"] == 1
    assert evaluate("regular_cash_div", f)["matched"]
    f["dividend_yield_pct_rank"] = 80
    assert evaluate("high_dividend", f)["matched"]


def test_combined_missing_reasons_count_each_symbol_once(tmp_path):
    q, h, b, cal = bundle(2)
    for p in h.values():
        p.pop("price_basis")
    store = ScreenerStore(tmp_path)
    snap = build_snapshot(q, h, b, as_of="2026-10-30", calendar=cal)
    store.save_snapshot(snap)
    r = StockScreenerService(store).query(q, preset="breakout", technical="above_ma20")
    assert r["missing_reasons"]["adjustment_unverified"] == 2 and r["unknown"] == 2
    assert r["evaluated"] + r["unknown"] + r["stale"] + r["not_eligible"] == r["scope_total"]


def test_benchmark_gaps_do_not_produce_relative_strength():
    stock = canonical_bars(history(), "2026-10-30")[0]
    benchmark = deepcopy(stock)
    del benchmark[-10]
    f = features(stock, benchmark)
    assert f["rs63"] is None
    # Gap after the skipped last month doesn't invalidate older momentum windows.
    assert f["momentum12"] is not None
    del benchmark[-35]
    f = features(stock, benchmark)
    assert f["momentum12"] is None and f["momentum6"] is None


def test_signal_dates_and_missing_reasons_describe_only_selected_rule():
    q, h, b, cal = bundle()
    snap = build_snapshot(q, h, b, as_of="2026-10-30", calendar=cal)
    signal = snap["rows"][0]["signals"]["money_inflow"]
    assert signal["matched"] and signal["observed_on"] == "2026-10-30"
    assert signal["triggered_on"] is None
    assert snap["rows"][0]["signals"]["foreign_favorite"]["reason_codes"] == [
        "foreign_history_missing"
    ]


def test_collector_resumes_frozen_queue_despite_market_cap_changes(tmp_path):
    q, _, _, cal = bundle(3)
    q = [{**row, "symbol": sym} for row, sym in zip(q, ["AAA", "BBB", "CCC"])]
    store = ScreenerStore(tmp_path)
    store.write("calendar.json", cal)
    seen = []

    class Provider:
        def calendar(self):
            return cal

        def benchmark(self, symbol):
            return {"history": history()}

        def equity(self, symbol):
            seen.append(symbol)
            return {"history": history(), "security_type": "common_stock"}

    collect(lambda: q, store, Provider, max_symbols=1, delay=0)
    checkpoint = store.read("collection.json")
    checkpoint["retry_after"] = 0
    store.write("collection.json", checkpoint)
    q[0]["market_cap"], q[1]["market_cap"] = 1, 100
    collect(lambda: q, store, Provider, max_symbols=1, delay=0)
    assert seen == ["AAA", "BBB"]


def test_malformed_import_rejected_before_mutation(tmp_path):
    from risk_dashboard.modules.data_hub.application.screener_job import import_bundle

    store = ScreenerStore(tmp_path)
    _, _, _, cal = bundle(1)
    for payload in (
        [],
        {"calendar": {}},
        {"calendar": cal, "inputs": {"AAA": []}},
        {"calendar": cal, "inputs": {"AAA": {"history": {**history(), "bars": [None]}}}},
    ):
        with pytest.raises(ValueError):
            import_bundle(payload, store)
    assert not list(tmp_path.iterdir())


def test_collection_cycle_changes_only_after_verified_session_closes():
    from datetime import datetime
    from risk_dashboard.modules.data_hub.application.screener_job import collection_session

    calendar = {"sessions": ["2026-10-30", "2026-11-02"], "valid_through": "2026-11-02"}
    for timestamp, expected in [
        ("2026-11-02T15:59:59+07:00", "2026-10-30"),
        ("2026-11-02T16:00:00+07:00", "2026-11-02"),
        ("2026-11-01T23:59:59+07:00", "2026-10-30"),
    ]:
        assert collection_session(datetime.fromisoformat(timestamp), calendar) == expected


def test_expired_calendar_cannot_freeze_collector_forever():
    from datetime import datetime
    from risk_dashboard.modules.data_hub.application.screener_job import collection_session

    stale = {"sessions": ["2026-10-30"], "valid_through": "2026-11-01"}
    assert (
        collection_session(datetime.fromisoformat("2026-11-03T18:00:00+07:00"), stale)
        == "2026-11-03"
    )


def test_calendar_refresh_persists_new_validity_without_overwriting_old_snapshot(tmp_path):
    q, h, b, cal = bundle(1)
    old = build_snapshot(q, h, b, as_of="2026-10-30", calendar=cal)
    changed = {**cal, "valid_through": "2026-11-05", "sessions": [*cal["sessions"], "2026-11-02"]}
    new = build_snapshot(q, h, b, as_of="2026-10-30", calendar=changed)
    store = ScreenerStore(tmp_path)
    store.save_snapshot(old)
    store.save_snapshot(new)
    assert store.snapshot()["calendar_valid_through"] == "2026-11-05"
    assert store.snapshot(old["snapshot_id"]) == old
