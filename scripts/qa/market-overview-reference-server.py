"""Reference-layout QA on a disposable auth DB and copied public quotes."""
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'output/market-overview-reference'
scratch = Path(tempfile.mkdtemp(prefix='northstar-overview-reference-'))
os.environ.update(
    PYTHON_DOTENV_DISABLED='1', RISK_DASHBOARD_DB_PATH=str(scratch / 'state.db'),
    RISK_DASHBOARD_APP_STATE_DB=str(scratch / 'state.db'), RISK_DASHBOARD_SQLITE=str(scratch / 'state.db'),
    ENABLE_SOCIAL_WORKER='0', ENABLE_TELEGRAM_NEWS_SCHEDULER='0', ENABLE_VN_MARKET_SCHEDULER='0',
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from risk_dashboard.app.bootstrap.app_factory import SPAStaticFiles
from risk_dashboard.modules.auth.api.public import router as auth
import uvicorn

app = FastAPI()
app.include_router(auth, prefix='/api/v1/public')

@app.get('/api/v1/public/data-hub/global-terminal')
def terminal():
    return json.loads((OUTPUT / 'global-quotes.json').read_text())

@app.get('/api/v1/public/data-hub/vn-market/heatmap')
def heatmap():
    return json.loads((OUTPUT / 'live-snapshot.json').read_text())

@app.get('/api/v1/public/data-hub/instruments/{symbol}/history')
def history(symbol: str):
    path = OUTPUT / f'history-{symbol}.json'
    return json.loads(path.read_text()) if path.is_file() else {'points': []}

app.mount('/dashboard-static', SPAStaticFiles(directory=OUTPUT / 'dist'))
user = TestClient(app).post('/api/v1/public/auth/register', json={
    'email': 'reference-qa@example.test', 'name': 'Overview QA', 'password': 'QA-only-temporary-12345!',
}).json()
assert user.get('session_id'), 'QA authentication setup failed'
(OUTPUT / 'qa-scratch.txt').write_text(str(scratch))
uvicorn.run(app, host='127.0.0.1', port=5194, log_level='warning')
