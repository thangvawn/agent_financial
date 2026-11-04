"""UI-only commodity QA with isolated auth DB and copied public data."""
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'output/playwright/commodities'
scratch = Path(tempfile.mkdtemp(prefix='northstar-commodity-qa-'))
os.environ.update(PYTHON_DOTENV_DISABLED='1', RISK_DASHBOARD_DB_PATH=str(scratch/'state.db'), RISK_DASHBOARD_APP_STATE_DB=str(scratch/'state.db'), RISK_DASHBOARD_SQLITE=str(scratch/'state.db'), ENABLE_SOCIAL_WORKER='0', ENABLE_TELEGRAM_NEWS_SCHEDULER='0', ENABLE_VN_MARKET_SCHEDULER='0')
from fastapi import FastAPI
from fastapi.testclient import TestClient
from risk_dashboard.app.bootstrap.app_factory import SPAStaticFiles
from risk_dashboard.modules.auth.api.public import router as auth
import uvicorn

app = FastAPI()
app.include_router(auth, prefix='/api/v1/public')
@app.get('/api/v1/market-portfolio/market-data/commodities/snapshot')
def quotes():
    return json.loads((OUTPUT/'quotes.json').read_text())
@app.get('/api/v1/public/data-hub/instruments/{symbol}/history')
def history(symbol: str, period: str = '3mo', interval: str = '1d'):
    payload = json.loads((OUTPUT/'histories.json').read_text()).get(symbol, {'points': [], 'source': 'yahoo_finance', 'freshness': 'degraded'})
    payload['points'] = payload['points'][-{'1mo':22, '3mo':66, '6mo':132, '1y':260}.get(period,66):]
    return payload
@app.get('/api/v1/public/data-hub/global-terminal')
def terminal():
    return {'items': [], 'groups': [], 'widgets': {}, 'freshness': 'stale'}
app.mount('/dashboard-static', SPAStaticFiles(directory=OUTPUT/'dist'))
user = TestClient(app).post('/api/v1/public/auth/register', json={'email':'commodities-qa@example.test', 'name':'QA', 'password':'QA-only-temporary-12345!'}).json()
p = OUTPUT/'session.json'
p.write_text(json.dumps(user)); p.chmod(0o600)
uvicorn.run(app, host='127.0.0.1', port=5191, log_level='warning')
