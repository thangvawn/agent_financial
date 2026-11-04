"""Serve the real commodity/history APIs with isolated DB/cache and public fixtures."""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/playwright/commodities-fixed"
OUT.mkdir(parents=True, exist_ok=True)

with tempfile.TemporaryDirectory(prefix="northstar-commodity-fixed-") as directory:
    scratch = Path(directory)
    os.environ.update(
        PYTHON_DOTENV_DISABLED="1",
        RISK_DASHBOARD_DB_PATH=str(scratch / "state.db"),
        RISK_DASHBOARD_APP_STATE_DB=str(scratch / "state.db"),
        RISK_DASHBOARD_SQLITE=str(scratch / "state.db"),
        ENABLE_SOCIAL_WORKER="0",
        ENABLE_TELEGRAM_NEWS_SCHEDULER="0",
        ENABLE_VN_MARKET_SCHEDULER="0",
        ENABLE_VN_SCREENER="0",
        VN_SCREENER_CACHE_DIR=str(scratch / "screener"),
        MPLCONFIGDIR="/private/tmp/northstar-review-matplotlib",
    )
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from risk_dashboard.app.bootstrap.app_factory import SPAStaticFiles
    from risk_dashboard.modules.auth.api.public import router as auth
    from risk_dashboard.modules.market_portfolio.api.public import router as commodities
    from risk_dashboard.modules.data_hub.api.public import router as history
    from risk_dashboard.modules.data_hub.application import global_market_feed as feed, services
    from risk_dashboard.modules.market_portfolio.application import commodity_feed
    import uvicorn

    quotes = json.loads((ROOT / "output/playwright/commodities/quotes.json").read_text())["items"]
    histories = json.loads((ROOT / "output/playwright/commodities/histories.json").read_text())
    producer = feed.GlobalMarketFeedProducer(cache_dir=scratch / "feed")
    control = {"version": 0, "history_error": False, "history_empty": False, "partial": False}
    counts = {"quotes": 0, "histories": {}}

    def now():
        return datetime.now(timezone.utc).isoformat()

    def quote_fixture():
        counts["quotes"] += 1
        items = []
        for item in quotes:
            if control["partial"] and item["symbol"] == "XAU":
                continue
            row = {**item, "group": "commodities", "updated_at": now(), "fetched_at": now()}
            if row["symbol"] == "XAU":
                row["price"] = 4000 + control["version"] * 100
            items.append(row)
        return {"items": items, "as_of": now()}

    def history_fixture(*, instrument, period, interval):
        key = f"{instrument.symbol}:{period}"
        counts["histories"][key] = counts["histories"].get(key, 0) + 1
        if control["history_error"]:
            raise RuntimeError("QA provider unavailable")
        points = json.loads(json.dumps(histories.get(instrument.symbol, {}).get("points", [])))
        points = points[-{"1mo": 22, "3mo": 66, "6mo": 132, "1y": 260}.get(period, 66) :]
        for point in points:
            for field in ["open", "high", "low", "close"]:
                point[field] += control["version"] * 100
        return {
            "points": [] if control["history_empty"] else points,
            "as_of": now(),
            "source": "yahoo_finance",
        }

    producer._fetch_yahoo_snapshot = quote_fixture
    producer._fetch_yahoo_history = history_fixture
    producer._fetch_vnstock_history = history_fixture
    commodity_feed.GlobalMarketFeedProducer = lambda **kw: producer
    services.GlobalMarketFeedProducer = lambda **kw: producer
    producer.snapshot(force_refresh=True)
    app = FastAPI()
    app.include_router(auth, prefix="/api/v1/public")
    app.include_router(commodities, prefix="/api/v1")
    app.include_router(history, prefix="/api/v1/public")

    @app.post("/__qa/control")
    def set_control(body: dict):
        control.update({k: v for k, v in body.items() if k in control})
        if body.get("expire_history"):
            feed._MEM_HISTORY_CACHE.clear()
            for path in (scratch / "feed/history").glob("*.json"):
                payload = json.loads(path.read_text())
                payload["as_of"] = "2000-01-01T00:00:00+00:00"
                path.write_text(json.dumps(payload))
        if body.get("reset_throttle"):
            feed._HISTORY_FORCED_AT.clear()
        producer.snapshot(force_refresh=True)
        return {"control": control, "counts": counts}

    @app.get("/__qa/stats")
    def stats():
        return counts

    app.mount(
        "/dashboard-static", SPAStaticFiles(directory=ROOT / "output/playwright/commodities/dist")
    )
    user = (
        TestClient(app)
        .post(
            "/api/v1/public/auth/register",
            json={
                "email": "commodity-fix@example.test",
                "name": "QA",
                "password": "Temporary-QA-Only-12345!",
            },
        )
        .json()
    )
    session_path = OUT / "session.json"
    session_path.write_text(json.dumps(user))
    session_path.chmod(0o600)
    try:
        with patch(
            "requests.sessions.Session.request", side_effect=RuntimeError("QA forbids network")
        ):
            uvicorn.run(app, host="127.0.0.1", port=5192, log_level="warning")
    finally:
        session_path.unlink(missing_ok=True)
